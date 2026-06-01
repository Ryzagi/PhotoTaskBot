package com.pandasolve.app.i18n

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Source of truth for the UI language. Persists to SharedPreferences and exposes
 * a flow the app root observes to provide [LocalStrings]. Defaults to English on
 * first run; the user can switch (ru/en) on the sign-in screen or in Profile.
 */
@Singleton
class LanguageManager @Inject constructor(
    @ApplicationContext ctx: Context,
) {
    private val prefs = ctx.getSharedPreferences("prefs_locale", Context.MODE_PRIVATE)

    private val _language = MutableStateFlow(prefs.getString(KEY, null) ?: "en")
    val language: StateFlow<String> = _language.asStateFlow()

    fun set(code: String) {
        val normalized = if (code.lowercase().startsWith("en")) "en" else "ru"
        prefs.edit().putString(KEY, normalized).apply()
        _language.value = normalized
    }

    companion object {
        private const val KEY = "ui_language"
    }
}
