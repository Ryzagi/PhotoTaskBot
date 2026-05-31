package com.pandasolve.app.ui.feature.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pandasolve.app.auth.SupabaseAuth
import com.pandasolve.app.data.repository.AlbumRepository
import com.pandasolve.app.data.repository.UserRepository
import com.pandasolve.app.i18n.LanguageManager
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
    val live: Boolean = false,
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val userRepo: UserRepository,
    private val albumRepo: AlbumRepository,
    private val languageManager: LanguageManager,
    private val auth: SupabaseAuth,
) : ViewModel() {

    private val _state = MutableStateFlow(ProfileUiState(language = languageManager.language.value))
    val state: StateFlow<ProfileUiState> = _state.asStateFlow()

    /** Toggle ru ↔ en: persist locally (drives LocalStrings immediately) and sync to backend. */
    fun toggleLanguage() {
        val next = if (_state.value.language.startsWith("en")) "ru" else "en"
        languageManager.set(next)
        _state.value = _state.value.copy(language = next)
        viewModelScope.launch { runCatching { userRepo.updateLanguage(next) } }
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
                    name = email?.substringBefore("@")?.replaceFirstChar { it.uppercase() } ?: _state.value.name,
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
