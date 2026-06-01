package com.pandasolve.app.ui.feature.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pandasolve.app.auth.SupabaseAuth
import com.pandasolve.app.data.repository.AlbumRepository
import com.pandasolve.app.data.repository.TaskRepository
import com.pandasolve.app.data.repository.UserRepository
import com.pandasolve.app.domain.model.Album
import com.pandasolve.app.domain.model.TaskListItem
import com.pandasolve.app.ui.sample.SampleThread
import com.pandasolve.app.ui.sample.toRow
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import timber.log.Timber

/** A day group of tasks. The label (today/yesterday/earlier) is localized in the UI by index. */
data class DayBucket(val date: String, val items: List<SampleThread>)

/**
 * The merged Home (R2-7): balance + stats + album filter chips + search + day-grouped
 * task list. No mock fallback — empty sections render empty. `live` = a successful load.
 */
data class HomeUiState(
    val name: String = "",
    val daily: Int = 0,
    val subscription: Int = 0,
    val streak: Int = 0,
    val solvedCount: Int = 0,
    val albums: List<Album> = emptyList(),
    val days: List<DayBucket> = emptyList(),
    val query: String = "",
    val selectedAlbumId: String? = null,
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
    private var searchJob: Job? = null

    /** Full load: profile + albums + tasks (current filter/query). */
    fun refresh() {
        viewModelScope.launch {
            runCatching {
                val me = userRepo.me()
                _state.update {
                    it.copy(
                        name = auth.currentEmail()?.substringBefore("@")
                            ?.replaceFirstChar { c -> c.uppercase() }.orEmpty(),
                        daily = me.balance.daily,
                        subscription = me.balance.subscription,
                        streak = me.streak,
                        solvedCount = me.solvedCount,
                        live = true,
                    )
                }
            }.onFailure { Timber.w(it, "home profile load failed") }

            runCatching { albumRepo.list() }
                .onSuccess { albums -> _state.update { it.copy(albums = albums) } }
                .onFailure { Timber.w(it, "home albums load failed") }

            reloadTasks()
        }
    }

    private fun reloadTasks() {
        viewModelScope.launch {
            val st = _state.value
            runCatching { taskRepo.list(limit = 50, before = null, albumId = st.selectedAlbumId, q = st.query) }
                .onSuccess { list -> _state.update { it.copy(days = group(list.items), live = true) } }
                .onFailure { Timber.w(it, "home tasks load failed") }
        }
    }

    fun setAlbumFilter(id: String?) {
        _state.update { it.copy(selectedAlbumId = id) }
        reloadTasks()
    }

    /** Search box: update text immediately, reload after a short debounce. */
    fun onQueryChange(text: String) {
        _state.update { it.copy(query = text) }
        searchJob?.cancel()
        searchJob = viewModelScope.launch {
            delay(300)
            reloadTasks()
        }
    }

    fun assignAlbum(taskId: String, albumId: String?) {
        viewModelScope.launch {
            runCatching { albumRepo.assign(taskId, albumId) }
                .onSuccess { refresh() }
                .onFailure { Timber.w(it, "assign album failed") }
        }
    }

    fun createAlbum(name: String, emoji: String, color: String) {
        if (name.isBlank()) return
        viewModelScope.launch {
            runCatching { albumRepo.create(name.trim(), emoji, color) }
                .onSuccess { refresh() }
                .onFailure { Timber.w(it, "create album failed") }
        }
    }

    fun updateAlbum(id: String, name: String, emoji: String, color: String) {
        viewModelScope.launch {
            runCatching { albumRepo.update(id, name.trim(), emoji, color) }
                .onSuccess { refresh() }
                .onFailure { Timber.w(it, "update album failed") }
        }
    }

    fun deleteAlbum(id: String) {
        viewModelScope.launch {
            runCatching { albumRepo.delete(id) }
                .onSuccess { if (_state.value.selectedAlbumId == id) setAlbumFilter(null) else refresh() }
                .onFailure { Timber.w(it, "delete album failed") }
        }
    }

    /** Group tasks by ISO date prefix; the API already returns newest-first. */
    private fun group(items: List<TaskListItem>): List<DayBucket> {
        val rows = items.mapIndexed { i, item -> item.createdAt.take(10) to item.toRow(i) }
        return rows.groupBy({ it.first }, { it.second }).entries.map { (date, its) ->
            DayBucket(date, its)
        }
    }
}
