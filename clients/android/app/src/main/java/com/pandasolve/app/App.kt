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
        mgr.createNotificationChannel(
            NotificationChannel("task_updates", "Решения", NotificationManager.IMPORTANCE_HIGH)
                .apply { description = "Уведомления о решённых задачах" }
        )
        mgr.createNotificationChannel(
            NotificationChannel("account", "Аккаунт", NotificationManager.IMPORTANCE_DEFAULT)
        )
        mgr.createNotificationChannel(
            NotificationChannel("promo", "Промо", NotificationManager.IMPORTANCE_LOW)
        )
    }
}

private class SentryBreadcrumbTree : Timber.Tree() {
    override fun log(priority: Int, tag: String?, message: String, t: Throwable?) {
        if (t != null) io.sentry.Sentry.captureException(t)
    }
}
