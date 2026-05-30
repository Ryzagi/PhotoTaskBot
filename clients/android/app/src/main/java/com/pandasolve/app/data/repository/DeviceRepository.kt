package com.pandasolve.app.data.repository

import android.content.Context
import android.content.pm.PackageManager
import com.pandasolve.app.domain.model.RegisterDeviceRequest
import com.pandasolve.app.network.PandaApiService
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DeviceRepository @Inject constructor(
    @ApplicationContext private val ctx: Context,
    private val api: PandaApiService,
) {
    suspend fun register(fcmToken: String) {
        api.registerDevice(
            RegisterDeviceRequest(
                platform = "android",
                token = fcmToken,
                appVersion = appVersion(),
                locale = Locale.getDefault().toLanguageTag(),
            )
        )
    }

    suspend fun unregister(fcmToken: String) {
        api.unregisterDevice(fcmToken)
    }

    private fun appVersion(): String = try {
        val info = ctx.packageManager.getPackageInfo(ctx.packageName, 0)
        info.versionName ?: "unknown"
    } catch (_: PackageManager.NameNotFoundException) {
        "unknown"
    }
}
