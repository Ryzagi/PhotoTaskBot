package com.pandasolve.app.ui.feature.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pandasolve.app.data.repository.AlbumRepository
import com.pandasolve.app.data.repository.TaskRepository
import com.pandasolve.app.data.repository.UserRepository
import com.pandasolve.app.domain.model.Album
import com.pandasolve.app.ui.sample.SampleThread
import com.pandasolve.app.ui.sample.sampleThreads
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
 * Loads balance, recent tasks and albums from the v1 API. If the backend is
 * unreachable or the user isn't signed in, the UI keeps the sample content so
 * the screen never looks broken — `live` flags whether we're showing real data.
 */
data class HomeUiState(
    val daily: Int = 3,
    val subscription: Int = 2,
    val threads: List<SampleThread> = sampleThreads,
    val albums: List<Album> = emptyList(),   // empty → Home shows its static pills
    val live: Boolean = false,
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val userRepo: UserRepository,
    private val taskRepo: TaskRepository,
    private val albumRepo: AlbumRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(HomeUiState())
    val state: StateFlow<HomeUiState> = _state.asStateFlow()

    fun refresh() {
        viewModelScope.launch {
            runCatching {
                val me = userRepo.me()
                val list = taskRepo.list(limit = 8, before = null)
                HomeUiState(
                    daily = me.balance.daily,
                    subscription = me.balance.subscription,
                    threads = list.items.mapIndexed { i, item -> item.toRow(i) }.ifEmpty { sampleThreads },
                    live = true,
                )
            }.onSuccess { _state.value = it }
                .onFailure { Timber.w(it, "home load failed — keeping sample content") }

            runCatching { albumRepo.list() }
                .onSuccess { albums -> _state.update { it.copy(albums = albums) } }
                .onFailure { Timber.w(it, "home albums load failed") }
        }
    }
}
