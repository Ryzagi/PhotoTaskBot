package com.pandasolve.app.ui.feature.billing

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import com.pandasolve.app.billing.BillingEvent
import com.pandasolve.app.billing.BillingManager
import com.pandasolve.app.i18n.LocalStrings
import com.pandasolve.app.ui.theme.Baloo
import com.pandasolve.app.ui.theme.Nunito
import com.pandasolve.app.ui.theme.cute
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject

@HiltViewModel
class BillingViewModel @Inject constructor(
    val billing: BillingManager,
) : ViewModel()

private fun Context.findActivity(): Activity? {
    var ctx: Context? = this
    while (ctx is ContextWrapper) {
        if (ctx is Activity) return ctx
        ctx = ctx.baseContext
    }
    return null
}

/** Bottom dialog listing the bamboo packs (Play Billing). Verifies + grants server-side. */
@Composable
fun TopUpSheet(
    onDismiss: () -> Unit,
    onPurchased: () -> Unit,
    vm: BillingViewModel = hiltViewModel(),
) {
    val c = cute
    val t = LocalStrings.current
    val activity = LocalContext.current.findActivity()
    val products by vm.billing.products.collectAsState()

    LaunchedEffect(Unit) { vm.billing.start() }
    LaunchedEffect(Unit) {
        vm.billing.events.collect { e ->
            if (e is BillingEvent.Success) {
                onPurchased()
                onDismiss()
            }
        }
    }

    Dialog(onDismissRequest = onDismiss) {
        Column(Modifier.clip(RoundedCornerShape(28.dp)).background(c.paper).padding(22.dp)) {
            Text(t.rowTopUp, fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 22.sp, color = c.ink)
            Spacer(Modifier.height(16.dp))
            if (products.isEmpty()) {
                Text(
                    t.topUpUnavailable,
                    fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 14.sp, color = c.inkFaint,
                    modifier = Modifier.padding(vertical = 16.dp),
                )
            } else {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    products.forEach { p ->
                        val price = p.oneTimePurchaseOfferDetails?.formattedPrice.orEmpty()
                        Row(
                            Modifier.fillMaxWidth().clip(RoundedCornerShape(18.dp)).background(c.card)
                                .border(2.dp, c.mint, RoundedCornerShape(18.dp))
                                .clickable(enabled = activity != null) { activity?.let { vm.billing.buy(it, p) } }
                                .padding(horizontal = 16.dp, vertical = 14.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text("🎋", fontSize = 20.sp)
                            Spacer(Modifier.width(12.dp))
                            Text(
                                p.name.ifBlank { p.productId },
                                fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 15.sp, color = c.ink,
                                modifier = Modifier.weight(1f),
                            )
                            Text(price, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 14.sp, color = c.mintDeep)
                        }
                    }
                }
            }
        }
    }
}
