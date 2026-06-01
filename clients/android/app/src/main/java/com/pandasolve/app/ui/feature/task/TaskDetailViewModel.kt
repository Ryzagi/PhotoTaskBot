package com.pandasolve.app.ui.feature.task

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pandasolve.app.data.repository.AlbumRepository
import com.pandasolve.app.data.repository.TaskRepository
import com.pandasolve.app.latex.latexToUnicode
import com.pandasolve.app.ui.component.AlbumOption
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import timber.log.Timber

data class ProblemUi(val problem: String, val steps: List<String>, val answer: String)

data class TaskUiState(
    val status: String = "pending",      // pending | done | failed
    val condition: String = "",
    val problems: List<ProblemUi> = emptyList(),
    val albums: List<AlbumOption> = emptyList(),
    val albumName: String? = null,
    val live: Boolean = false,
)

@HiltViewModel
class TaskDetailViewModel @Inject constructor(
    private val taskRepo: TaskRepository,
    private val albumRepo: AlbumRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(TaskUiState())
    val state: StateFlow<TaskUiState> = _state.asStateFlow()

    fun load(taskId: String) {
        if (taskId.isBlank()) return
        viewModelScope.launch {
            runCatching {
                albumRepo.list().map { AlbumOption(it.id, it.name, it.emoji ?: "📚") }
            }.onSuccess { opts -> _state.update { it.copy(albums = opts) } }

            repeat(30) { // poll up to ~60s while pending
                val ok = runCatching {
                    val t = taskRepo.get(taskId)
                    val problems = t.solution?.solutions?.map { p ->
                        ProblemUi(
                            problem = latexToUnicode(p.problem),
                            steps = p.steps.map { latexToUnicode(it.content) },
                            answer = p.solution.joinToString("  ") { latexToUnicode(it.content) },
                        )
                    }.orEmpty()
                    _state.update { st ->
                        st.copy(
                            status = t.status,
                            condition = t.inputText?.let(::latexToUnicode)
                                ?: problems.firstOrNull()?.problem ?: st.condition,
                            problems = problems,   // real data only — no sample fallback
                            // resolve the persisted album (tasks.album_id) so the badge
                            // survives an app restart, not just an in-session assign.
                            albumName = t.albumId?.let { id -> st.albums.firstOrNull { a -> a.id == id }?.name },
                            live = true,
                        )
                    }
                    t.status
                }.getOrElse {
                    // Real load failed (e.g. task not found) — show a failed state, never mock.
                    Timber.w(it, "task load failed")
                    _state.update {
                        it.copy(status = "failed", condition = "Не удалось загрузить задачу", live = true)
                    }
                    return@launch
                }
                if (ok != "pending") return@launch
                delay(2000)
            }
        }
    }

    fun assignAlbum(taskId: String, album: AlbumOption?) {
        viewModelScope.launch {
            runCatching { albumRepo.assign(taskId, album?.id) }
                .onSuccess { _state.update { it.copy(albumName = album?.name) } }
                .onFailure { Timber.w(it, "assign album failed") }
        }
    }
}
