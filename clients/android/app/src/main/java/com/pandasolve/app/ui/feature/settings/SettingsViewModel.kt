package com.pandasolve.app.ui.feature.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pandasolve.app.auth.SupabaseAuth
import com.pandasolve.app.data.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import timber.log.Timber

data class ProfileUiState(
    val name: String = "Владислав",
    val email: String = "vladislav@mayflower.work",
    val daily: Int = 3,
    val subscription: Int = 2,
    val telegramLinked: Boolean = true,
    val solved: Int = 47,
    val albums: Int = 5,
    val streak: Int = 7,
    val live: Boolean = false,
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val userRepo: UserRepository,
    private val auth: SupabaseAuth,
) : ViewModel() {

    private val _state = MutableStateFlow(ProfileUiState())
    val state: StateFlow<ProfileUiState> = _state.asStateFlow()

    fun refresh() {
        viewModelScope.launch {
            // email comes from the Supabase session even before /v1/me succeeds
            val email = auth.currentEmail()
            runCatching {
                val me = userRepo.me()
                _state.value = _state.value.copy(
                    email = email ?: _state.value.email,
                    name = email?.substringBefore("@")?.replaceFirstChar { it.uppercase() } ?: _state.value.name,
                    daily = me.balance.daily,
                    subscription = me.balance.subscription,
                    telegramLinked = me.telegramLinked,
                    live = true,
                )
            }.onFailure {
                Timber.w(it, "profile load failed — keeping sample content")
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
