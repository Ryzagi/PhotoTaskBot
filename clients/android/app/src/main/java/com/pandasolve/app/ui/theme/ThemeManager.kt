package com.pandasolve.app.ui.theme

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Theme preference: "system" | "light" | "dark". Persisted to SharedPreferences;
 * MainActivity observes [mode] above PandaSolveTheme so a change flips the app live.
 */
@Singleton
class ThemeManager @Inject constructor(@ApplicationContext ctx: Context) {
    private val prefs = ctx.getSharedPreferences("prefs_theme", Context.MODE_PRIVATE)
    private val _mode = MutableStateFlow(prefs.getString(KEY, null) ?: SYSTEM)
    val mode: StateFlow<String> = _mode.asStateFlow()

    fun set(value: String) {
        val v = if (value in setOf(LIGHT, DARK, SYSTEM)) value else SYSTEM
        prefs.edit().putString(KEY, v).apply()
        _mode.value = v
    }

    companion object {
        const val SYSTEM = "system"
        const val LIGHT = "light"
        const val DARK = "dark"
        private const val KEY = "ui_theme"
    }
}
