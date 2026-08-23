package com.pandasolve.app.push

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/** Persisted push opt-in. FCM registration (when configured) should honour this. */
@Singleton
class NotifPrefs @Inject constructor(@ApplicationContext ctx: Context) {
    private val prefs = ctx.getSharedPreferences("prefs_notif", Context.MODE_PRIVATE)

    var enabled: Boolean
        get() = prefs.getBoolean(KEY, true)
        set(value) = prefs.edit().putBoolean(KEY, value).apply()

    private companion object { const val KEY = "push_enabled" }
}
