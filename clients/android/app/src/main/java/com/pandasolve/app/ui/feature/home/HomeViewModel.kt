package com.pandasolve.app.ui.feature.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pandasolve.app.auth.SupabaseAuth
import com.pandasolve.app.data.repository.AlbumRepository
import com.pandasolve.app.data.repository.TaskRepository
import com.pandasolve.app.data.repository.UserRepository
import com.pandasolve.app.domain.model.Album
import com.pandasolve.app.ui.sample.SampleThread
import com.pandasolve.app.ui.sample.toRow
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import timber.log.Timber

/**
 * Loads real balance, stats, recent tasks and albums from the v1 API. No mock
 * fallback — empty sections render empty. `live` flags a successful load.
 */
data class HomeUiState(
    val name: String = "",
    val daily: Int = 0,
    val subscription: Int = 0,
    val streak: Int = 0,
    val solvedCount: Int = 0,
    val threads: List<SampleThread> = emptyList(),
    val albums: List<Album> = emptyList(),
    val live: Boolean = false,
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val userRepo: UserRepository,
    private val taskRepo: TaskRepository,
    private val albumRepo: AlbumRepository,
    private val auth: SupabaseAuth,
) : ViewModel() {

    private val _state = MutableStateFlow(HomeUiState())
    val state: StateFlow<HomeUiState> = _state.asStateFlow()

    fun refresh() {
        viewModelScope.launch {
            runCatching {
                val me = userRepo.me()
                val list = taskRepo.list(limit = 8, before = null)
                HomeUiState(
                    name = auth.currentEmail()?.substringBefore("@")
                        ?.replaceFirstChar { it.uppercase() }.orEmpty(),
                    daily = me.balance.daily,
                    subscription = me.balance.subscription,
                    streak = me.streak,
                    solvedCount = me.solvedCount,
                    threads = list.items.mapIndexed { i, item -> item.toRow(i) },
                    live = true,
                )
            }.onSuccess { _state.value = it }
                .onFailure { Timber.w(it, "home load failed") }

            runCatching { albumRepo.list() }
                .onSuccess { albums -> _state.update { it.copy(albums = albums) } }
                .onFailure { Timber.w(it, "home albums load failed") }
        }
    }
}
