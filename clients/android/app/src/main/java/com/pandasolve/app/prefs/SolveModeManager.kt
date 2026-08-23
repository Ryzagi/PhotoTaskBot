package com.pandasolve.app.prefs

import android.content.Context
import androidx.compose.runtime.staticCompositionLocalOf
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Solve mode: "solve" (default — show the answer) | "explain" (hide the answer behind
 * a tap-to-reveal spoiler so the student works through the steps first).
 *
 * Persisted to SharedPreferences. Provided through [LocalSolveMode] (sourced in
 * Navigation from RootViewModel) so any screen reads the live value.
 */
@Singleton
class SolveModeManager @Inject constructor(@ApplicationContext ctx: Context) {
    private val prefs = ctx.getSharedPreferences("prefs_solve_mode", Context.MODE_PRIVATE)
    private val _mode = MutableStateFlow(prefs.getString(KEY, null) ?: SOLVE)
    val mode: StateFlow<String> = _mode.asStateFlow()

    fun set(value: String) {
        val v = if (value == EXPLAIN) EXPLAIN else SOLVE
        prefs.edit().putString(KEY, v).apply()
        _mode.value = v
    }

    companion object {
        const val SOLVE = "solve"
        const val EXPLAIN = "explain"
        private const val KEY = "solve_mode"
    }
}

/** Live solve-mode for the composable tree; provided in Navigation. */
val LocalSolveMode = staticCompositionLocalOf { SolveModeManager.SOLVE }
