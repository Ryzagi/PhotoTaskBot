package com.pandasolve.app.data.repository

import com.pandasolve.app.domain.model.PlayVerifyRequest
import com.pandasolve.app.domain.model.PlayVerifyResponse
import com.pandasolve.app.network.PandaApiService
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BillingRepository @Inject constructor(
    private val api: PandaApiService,
) {
    /** Server-verify a Play purchase token and grant credits. Throws on failure. */
    suspend fun verify(productId: String, purchaseToken: String): PlayVerifyResponse =
        api.verifyPlayPurchase(PlayVerifyRequest(productId = productId, purchaseToken = purchaseToken))
}
