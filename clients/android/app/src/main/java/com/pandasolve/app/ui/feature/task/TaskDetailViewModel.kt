package com.pandasolve.app.ui.feature.task

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pandasolve.app.data.repository.AlbumRepository
import com.pandasolve.app.data.repository.TaskRepository
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

data class AlbumOption(val id: String, val name: String, val emoji: String)

data class TaskUiState(
    val status: String = "done",         // pending | done | failed
    val condition: String = "14.  Найти производную f(x) = (x² − 4)/(x + 2) в точке x₀ = 3.",
    val problems: List<ProblemUi> = sampleProblems,
    val albums: List<AlbumOption> = emptyList(),
    val albumName: String? = null,
    val live: Boolean = false,
)

private val sampleProblems = listOf(
    ProblemUi(
        problem = "Найти производную f(x) = (x² − 4)/(x + 2) в точке x₀ = 3.",
        steps = listOf(
            "Сократим дробь: f(x) = (x−2)(x+2)/(x+2) = x − 2 при x ≠ −2.",
            "Берём производную: f′(x) = 1 — это линейная функция.",
            "Значение не зависит от точки x₀ = 3.",
        ),
        answer = "f′(3) = 1",
    ),
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
                            problem = p.problem,
                            steps = p.steps.map { it.content },
                            answer = p.solution.joinToString("  ") { it.content },
                        )
                    }.orEmpty()
                    _state.update {
                        it.copy(
                            status = t.status,
                            condition = t.inputText ?: it.condition,
                            problems = problems.ifEmpty { it.problems },
                            live = true,
                        )
                    }
                    t.status
                }.getOrElse {
                    Timber.w(it, "task load failed — keeping sample content")
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
