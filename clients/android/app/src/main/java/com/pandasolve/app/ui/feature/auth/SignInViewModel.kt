package com.pandasolve.app.ui.feature.auth

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.messaging.FirebaseMessaging
import com.pandasolve.app.auth.AuthError
import com.pandasolve.app.auth.SupabaseAuth
import com.pandasolve.app.auth.toAuthError
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
    val error: AuthError? = null,
    // Short raw cause (class + message) shown under UNKNOWN errors during beta
    // so testers can screenshot the real reason (no Sentry DSN in these builds).
    val errorDetail: String? = null,
    // True after sign-up when Supabase requires email confirmation (no session yet).
    val pendingConfirmation: Boolean = false,
    // True once a password-recovery email has been requested.
    val resetEmailSent: Boolean = false,
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

    fun signInWithEmail(email: String, password: String) {
        if (email.isBlank() || password.isBlank()) {
            _state.update { it.copy(error = AuthError.EMPTY_FIELDS) }
            return
        }
        launchSignIn { auth.signInWithEmail(email, password) }
    }

    /**
     * Create an account. If Supabase requires email confirmation there's no
     * session yet → surface [SignInState.pendingConfirmation] so the UI asks the
     * user to check their inbox; otherwise we're signed in straight away.
     */
    fun signUpWithEmail(email: String, password: String) {
        viewModelScope.launch {
            if (email.isBlank() || password.isBlank()) {
                _state.update { it.copy(error = AuthError.EMPTY_FIELDS) }
                return@launch
            }
            _state.update { it.copy(busy = true, error = null, pendingConfirmation = false, resetEmailSent = false) }
            runCatching { auth.signUpWithEmail(email, password) }
                .onSuccess { signedInNow ->
                    if (signedInNow) {
                        registerFcm()
                        _state.update { it.copy(busy = false, signedIn = true) }
                    } else {
                        _state.update { it.copy(busy = false, pendingConfirmation = true) }
                    }
                }
                .onFailure { e ->
                    Timber.w(e, "sign-up failed")
                    _state.update { it.copy(busy = false, error = e.toAuthError(), errorDetail = e.shortDetail()) }
                }
        }
    }

    /**
     * Email a password-recovery link. Success here only means "Supabase accepted
     * the request" — it deliberately does not reveal whether the address has an
     * account, so the UI says "if that address is registered".
     */
    fun sendPasswordReset(email: String) {
        viewModelScope.launch {
            if (email.isBlank()) {
                _state.update { it.copy(error = AuthError.EMPTY_FIELDS) }
                return@launch
            }
            _state.update {
                it.copy(
                    busy = true, error = null, errorDetail = null,
                    pendingConfirmation = false, resetEmailSent = false,
                )
            }
            runCatching { auth.resetPassword(email) }
                .onSuccess { _state.update { it.copy(busy = false, resetEmailSent = true) } }
                .onFailure { e ->
                    Timber.w(e, "password reset request failed")
                    _state.update { it.copy(busy = false, error = e.toAuthError(), errorDetail = e.shortDetail()) }
                }
        }
    }

    fun signInWithGoogle() = launchSignIn { auth.signInWithGoogle() }

    fun signInWithApple() = launchSignIn { auth.signInWithApple() }

    private fun launchSignIn(block: suspend () -> Unit) {
        viewModelScope.launch {
            _state.update { it.copy(busy = true, error = null, errorDetail = null, pendingConfirmation = false, resetEmailSent = false) }
            runCatching { block() }
                .onSuccess {
                    registerFcm()
                    _state.update { it.copy(busy = false, signedIn = true) }
                }
                .onFailure { e ->
                    Timber.w(e, "sign-in failed")
                    _state.update { it.copy(busy = false, error = e.toAuthError(), errorDetail = e.shortDetail()) }
                }
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


/** Compact "ClassName: message" for beta diagnostics (max ~90 chars). */
private fun Throwable.shortDetail(): String {
    val root = generateSequence(this) { it.cause }.last()
    val name = root::class.simpleName ?: "Error"
    val msg = root.message?.take(70)?.trim().orEmpty()
    return if (msg.isEmpty()) name else "$name: $msg"
}
