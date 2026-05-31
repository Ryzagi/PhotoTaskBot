package com.pandasolve.app.i18n

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Source of truth for the UI language. Persists to SharedPreferences and exposes
 * a flow the app root observes to provide [LocalStrings]. Defaults to the device
 * language on first run (ru/en supported; anything else → ru).
 */
@Singleton
class LanguageManager @Inject constructor(
    @ApplicationContext ctx: Context,
) {
    private val prefs = ctx.getSharedPreferences("prefs_locale", Context.MODE_PRIVATE)

    private val _language = MutableStateFlow(
        prefs.getString(KEY, null) ?: defaultDeviceLanguage(),
    )
    val language: StateFlow<String> = _language.asStateFlow()

    fun set(code: String) {
        val normalized = if (code.lowercase().startsWith("en")) "en" else "ru"
        prefs.edit().putString(KEY, normalized).apply()
        _language.value = normalized
    }

    private fun defaultDeviceLanguage(): String =
        if (Locale.getDefault().language.startsWith("en")) "en" else "ru"

    companion object {
        private const val KEY = "ui_language"
    }
}
