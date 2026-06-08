package com.pandasolve.app.ui.feature.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pandasolve.app.auth.SupabaseAuth
import com.pandasolve.app.data.repository.AlbumRepository
import com.pandasolve.app.data.repository.UserRepository
import com.pandasolve.app.i18n.LanguageManager
import com.pandasolve.app.push.NotifPrefs
import com.pandasolve.app.ui.theme.ThemeManager
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import timber.log.Timber

data class ProfileUiState(
    val name: String = "",
    val email: String = "",
    val daily: Int = 0,
    val subscription: Int = 0,
    val telegramLinked: Boolean = false,
    val solved: Int = 0,
    val albums: Int = 0,
    val streak: Int = 0,
    val language: String = "ru",
    val theme: String = "system",
    val notifEnabled: Boolean = true,
    val live: Boolean = false,
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val userRepo: UserRepository,
    private val albumRepo: AlbumRepository,
    private val languageManager: LanguageManager,
    private val themeManager: ThemeManager,
    private val notifPrefs: NotifPrefs,
    private val auth: SupabaseAuth,
) : ViewModel() {

    private val _state = MutableStateFlow(run {
        // Seed from the cached profile so counts show instantly on re-open (no spinner wait).
        val m = userRepo.lastMe
        val email = auth.currentEmail()
        ProfileUiState(
            language = languageManager.language.value,
            theme = themeManager.mode.value,
            notifEnabled = notifPrefs.enabled,
            email = email ?: "",
            name = m?.displayName?.takeIf { it.isNotBlank() }
                ?: email?.substringBefore("@")?.replaceFirstChar { it.uppercase() } ?: "",
            daily = m?.balance?.daily ?: 0,
            subscription = m?.balance?.subscription ?: 0,
            telegramLinked = m?.telegramLinked ?: false,
            solved = m?.solvedCount ?: 0,
            streak = m?.streak ?: 0,
            albums = albumRepo.lastCount ?: 0,
        )
    })
    val state: StateFlow<ProfileUiState> = _state.asStateFlow()

    /** Rename the user (display name) — persisted via POST /v1/me. */
    fun setName(name: String) {
        if (name.isBlank()) return
        _state.value = _state.value.copy(name = name.trim())
        viewModelScope.launch { runCatching { userRepo.updateDisplayName(name.trim()) } }
    }

    /** Push opt-in. Persists locally; FCM registration honours it once configured. */
    fun setNotifications(on: Boolean) {
        notifPrefs.enabled = on
        _state.value = _state.value.copy(notifEnabled = on)
    }

    /** Pick the theme: system | light | dark. Persists; MainActivity flips the app live. */
    fun setTheme(mode: String) {
        themeManager.set(mode)
        _state.value = _state.value.copy(theme = themeManager.mode.value)
    }

    /** Pick a UI language: persist locally (drives LocalStrings immediately) + sync to backend. */
    fun setLanguage(code: String) {
        languageManager.set(code)
        _state.value = _state.value.copy(language = languageManager.language.value)
        viewModelScope.launch { runCatching { userRepo.updateLanguage(languageManager.language.value) } }
    }

    fun refresh() {
        viewModelScope.launch {
            // email comes from the Supabase session even before /v1/me succeeds
            val email = auth.currentEmail()
            runCatching {
                val me = userRepo.me()
                val albumCount = runCatching { albumRepo.list().size }.getOrDefault(0)
                _state.value = _state.value.copy(
                    email = email ?: _state.value.email,
                    name = me.displayName?.takeIf { it.isNotBlank() }
                        ?: email?.substringBefore("@")?.replaceFirstChar { it.uppercase() } ?: _state.value.name,
                    daily = me.balance.daily,
                    subscription = me.balance.subscription,
                    telegramLinked = me.telegramLinked,
                    solved = me.solvedCount,
                    streak = me.streak,
                    albums = albumCount,
                    live = true,
                )
            }.onFailure {
                Timber.w(it, "profile load failed")
                if (email != null) _state.value = _state.value.copy(email = email, name = email.substringBefore("@").replaceFirstChar { c -> c.uppercase() })
            }
        }
    }

    fun signOut(done: () -> Unit) {
        viewModelScope.launch {
            runCatching { auth.signOut() }
            done()
        }
    }
}
