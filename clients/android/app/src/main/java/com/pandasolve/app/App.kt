package com.pandasolve.app

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import dagger.hilt.android.HiltAndroidApp
import io.sentry.android.core.SentryAndroid
import timber.log.Timber

@HiltAndroidApp
class App : Application() {

    override fun onCreate() {
        super.onCreate()
        Timber.plant(if (BuildConfig.DEBUG) Timber.DebugTree() else SentryBreadcrumbTree())
        if (BuildConfig.SENTRY_DSN.isNotBlank()) {
            SentryAndroid.init(this) { options ->
                options.dsn = BuildConfig.SENTRY_DSN
                options.tracesSampleRate = if (BuildConfig.DEBUG) 1.0 else 0.1
            }
        }
        // PostHog: only init if the API key has been wired in via gradle.properties
        // — placeholder value would crash on init.
        // PostHogAndroid.setup(this, PostHogAndroidConfig(apiKey = "<your-key>"))
        createNotificationChannels()
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val mgr = getSystemService(NotificationManager::class.java) ?: return
        // Names come from string resources so they follow the device locale.
        mgr.createNotificationChannel(
            NotificationChannel(
                "task_updates", getString(R.string.channel_task_updates_name), NotificationManager.IMPORTANCE_HIGH,
            ).apply { description = getString(R.string.channel_task_updates_desc) }
        )
        mgr.createNotificationChannel(
            NotificationChannel("account", getString(R.string.channel_account_name), NotificationManager.IMPORTANCE_DEFAULT)
        )
        mgr.createNotificationChannel(
            NotificationChannel("promo", getString(R.string.channel_promo_name), NotificationManager.IMPORTANCE_LOW)
        )
    }
}

private class SentryBreadcrumbTree : Timber.Tree() {
    override fun log(priority: Int, tag: String?, message: String, t: Throwable?) {
        if (t != null) io.sentry.Sentry.captureException(t)
    }
}
