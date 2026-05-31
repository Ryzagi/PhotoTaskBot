package com.pandasolve.app.ui

import androidx.lifecycle.ViewModel
import com.pandasolve.app.auth.AuthState
import com.pandasolve.app.auth.SupabaseAuth
import com.pandasolve.app.i18n.LanguageManager
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.StateFlow

/** Top-level gate: the nav graph waits on auth before picking a start screen, and
 *  reads the UI language so the whole tree can be re-provided when it changes. */
@HiltViewModel
class RootViewModel @Inject constructor(
    auth: SupabaseAuth,
    language: LanguageManager,
) : ViewModel() {
    val authState: StateFlow<AuthState> = auth.authState
    val language: StateFlow<String> = language.language
}
