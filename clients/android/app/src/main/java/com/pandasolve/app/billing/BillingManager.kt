package com.pandasolve.app.billing

import android.app.Activity
import android.content.Context
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.ConsumeParams
import com.android.billingclient.api.PendingPurchasesParams
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.PurchasesUpdatedListener
import com.android.billingclient.api.QueryProductDetailsParams
import com.pandasolve.app.data.repository.BillingRepository
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import timber.log.Timber

sealed interface BillingEvent {
    data class Success(val productId: String) : BillingEvent
    data class Error(val message: String) : BillingEvent
    data object Cancelled : BillingEvent
}

/** The Play product ids; must match the In-app products created in Play Console. */
private val PRODUCT_IDS = listOf("bamboo_20", "bamboo_50", "bamboo_100")

/**
 * Google Play Billing (consumables). Connects, queries the bamboo packs, launches
 * the purchase flow, then — on a PURCHASED result — verifies the token server-side
 * (/v1/billing/google/verify) and consumes it so it can be bought again.
 */
@Singleton
class BillingManager @Inject constructor(
    @ApplicationContext context: Context,
    private val billingRepo: BillingRepository,
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private val _products = MutableStateFlow<List<ProductDetails>>(emptyList())
    val products: StateFlow<List<ProductDetails>> = _products.asStateFlow()

    private val _events = MutableSharedFlow<BillingEvent>(extraBufferCapacity = 8)
    val events: SharedFlow<BillingEvent> = _events.asSharedFlow()

    private val listener = PurchasesUpdatedListener { result, purchases ->
        when (result.responseCode) {
            BillingClient.BillingResponseCode.OK ->
                purchases?.forEach { handlePurchase(it) }
            BillingClient.BillingResponseCode.USER_CANCELED ->
                _events.tryEmit(BillingEvent.Cancelled)
            else ->
                _events.tryEmit(BillingEvent.Error(result.debugMessage.ifBlank { "billing error ${result.responseCode}" }))
        }
    }

    private val client = BillingClient.newBuilder(context)
        .setListener(listener)
        .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())
        // Billing 8: let the library re-establish the service connection itself
        // instead of leaving the client dead after onBillingServiceDisconnected.
        .enableAutoServiceReconnection()
        .build()

    /** Connect (idempotent) and refresh the product list. Call when the top-up UI opens. */
    fun start() {
        if (client.isReady) {
            queryProducts()
            return
        }
        client.startConnection(object : BillingClientStateListener {
            override fun onBillingSetupFinished(result: BillingResult) {
                if (result.responseCode == BillingClient.BillingResponseCode.OK) queryProducts()
                else Timber.w("billing setup failed: ${result.debugMessage}")
            }
            override fun onBillingServiceDisconnected() {
                Timber.w("billing disconnected")
            }
        })
    }

    private fun queryProducts() {
        val params = QueryProductDetailsParams.newBuilder()
            .setProductList(
                PRODUCT_IDS.map { id ->
                    QueryProductDetailsParams.Product.newBuilder()
                        .setProductId(id)
                        .setProductType(BillingClient.ProductType.INAPP)
                        .build()
                },
            ).build()
        client.queryProductDetailsAsync(params) { result, queryResult ->
            if (result.responseCode != BillingClient.BillingResponseCode.OK) {
                Timber.w("queryProductDetails: ${result.debugMessage}")
                return@queryProductDetailsAsync
            }
            // Billing 8 reports products it could not fetch separately instead of
            // silently dropping them — worth a log line when a pack goes missing.
            queryResult.unfetchedProductList.forEach {
                Timber.w("product not fetched: ${it.productId} (${it.statusCode})")
            }
            _products.value = queryResult.productDetailsList.sortedBy { it.productId }
        }
    }

    /** Launch the Play purchase flow for a pack. Must be called with the current Activity. */
    fun buy(activity: Activity, product: ProductDetails) {
        val params = BillingFlowParams.newBuilder()
            .setProductDetailsParamsList(
                listOf(
                    BillingFlowParams.ProductDetailsParams.newBuilder()
                        .setProductDetails(product)
                        .build(),
                ),
            ).build()
        client.launchBillingFlow(activity, params)
    }

    private fun handlePurchase(purchase: Purchase) {
        if (purchase.purchaseState != Purchase.PurchaseState.PURCHASED) return
        val productId = purchase.products.firstOrNull() ?: return
        scope.launch {
            val verified = runCatching { billingRepo.verify(productId, purchase.purchaseToken) }
                .onFailure { Timber.w(it, "play verify failed") }
                .isSuccess
            if (!verified) {
                _events.tryEmit(BillingEvent.Error("verification failed"))
                return@launch
            }
            // Consume so the pack can be bought again. (Backend already granted credits.)
            client.consumeAsync(
                ConsumeParams.newBuilder().setPurchaseToken(purchase.purchaseToken).build(),
            ) { res, _ ->
                if (res.responseCode != BillingClient.BillingResponseCode.OK) {
                    Timber.w("consume failed: ${res.debugMessage}")
                }
            }
            _events.tryEmit(BillingEvent.Success(productId))
        }
    }
}
