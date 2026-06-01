package com.pandasolve.app.ui.feature.auth

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.messaging.FirebaseMessaging
import com.pandasolve.app.auth.SupabaseAuth
import com.pandasolve.app.data.repository.DeviceRepository
import com.pandasolve.app.i18n.LanguageManager
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import timber.log.Timber

data class SignInState(
    val busy: Boolean = false,
    val signedIn: Boolean = false,
    val error: String? = null,
)

@HiltViewModel
class SignInViewModel @Inject constructor(
    @ApplicationContext private val ctx: Context,
    private val auth: SupabaseAuth,
    private val devices: DeviceRepository,
    private val languageManager: LanguageManager,
) : ViewModel() {

    private val _state = MutableStateFlow(SignInState(signedIn = auth.isSignedIn()))
    val state: StateFlow<SignInState> = _state.asStateFlow()

    /** Pick the UI language before signing in (drives LocalStrings app-wide). */
    fun setLanguage(code: String) = languageManager.set(code)

    init {
        // If already signed in (cold start), opportunistically register the FCM token.
        if (auth.isSignedIn()) viewModelScope.launch { registerFcm() }
    }

    fun signInWithEmail(email: String, password: String) = launchSignIn {
        if (email.isBlank() || password.isBlank()) error("Заполни почту и пароль")
        auth.signInWithEmail(email, password)
    }

    fun signInWithGoogle() = launchSignIn { auth.signInWithGoogle() }

    fun signInWithApple() = launchSignIn { auth.signInWithApple() }

    private fun launchSignIn(block: suspend () -> Unit) {
        viewModelScope.launch {
            _state.update { it.copy(busy = true, error = null) }
            runCatching { block() }
                .onSuccess {
                    registerFcm()
                    _state.update { it.copy(busy = false, signedIn = true) }
                }
                .onFailure { e -> _state.update { it.copy(busy = false, error = e.message) } }
        }
    }

    private suspend fun registerFcm() {
        try {
            val token = FirebaseMessaging.getInstance().token.await()
            devices.register(token)
        } catch (t: Throwable) {
            Timber.w(t, "FCM token registration failed (non-fatal)")
        }
    }
}
