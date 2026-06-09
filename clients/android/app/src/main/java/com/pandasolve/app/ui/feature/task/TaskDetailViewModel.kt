package com.pandasolve.app.ui.feature.task

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pandasolve.app.data.repository.AlbumRepository
import com.pandasolve.app.data.repository.TaskRepository
import com.pandasolve.app.domain.model.TaskDetail
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

data class ChatTurn(val fromMe: Boolean, val text: String, val imageUrl: String? = null)

data class TaskUiState(
    val status: String = "pending",      // pending | done | failed
    val condition: String = "",
    val problems: List<ProblemUi> = emptyList(),
    val albums: List<AlbumOption> = emptyList(),
    val albumName: String? = null,
    val taskAlbumId: String? = null,
    val chat: List<ChatTurn> = emptyList(),
    val sending: Boolean = false,
    val chatRemaining: Int = 3,   // free follow-up questions left
    val needTopUp: Boolean = false,  // 402 from chat → show top-up CTA
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
        // Instant paint from cache on re-open; the network refresh follows.
        taskRepo.cachedTask(taskId)?.let { applyTask(it) }
        viewModelScope.launch {
            // Albums (picker + badge) and chat load CONCURRENTLY with the task — the
            // task is what the user waits for, so it isn't queued behind them.
            launch {
                runCatching { albumRepo.list().map { AlbumOption(it.id, it.name, it.emoji ?: "📚") } }
                    .onSuccess { opts ->
                        _state.update { st ->
                            st.copy(albums = opts, albumName = st.taskAlbumId?.let { id -> opts.firstOrNull { it.id == id }?.name } ?: st.albumName)
                        }
                    }
                    .onFailure { Timber.w(it, "albums load failed") }
            }
            launch {
                runCatching { taskRepo.chatHistory(taskId) }
                    .onSuccess { thread -> _state.update { it.copy(chat = thread.messages.map { m -> ChatTurn(m.role == "user", latexToUnicode(m.content), m.imageUrl) }, chatRemaining = thread.remaining) } }
                    .onFailure { Timber.w(it, "chat history load failed") }
            }
            // Task — priority; poll while pending.
            repeat(30) {
                val status = runCatching { applyTask(taskRepo.get(taskId)) }.getOrElse {
                    Timber.w(it, "task load failed")
                    if (!_state.value.live) {
                        _state.update { it.copy(status = "failed", condition = "Не удалось загрузить задачу", live = true) }
                    }
                    return@launch
                }
                if (status != "pending") return@launch
                delay(2000)
            }
        }
    }

    /** Map a fetched task into UI state (resolving the album badge from loaded albums). */
    private fun applyTask(t: TaskDetail): String {
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
                condition = t.inputText?.let(::latexToUnicode) ?: problems.firstOrNull()?.problem ?: st.condition,
                problems = problems,
                taskAlbumId = t.albumId,
                albumName = t.albumId?.let { id -> st.albums.firstOrNull { a -> a.id == id }?.name } ?: st.albumName,
                live = true,
            )
        }
        return t.status
    }

    fun assignAlbum(taskId: String, album: AlbumOption?) {
        viewModelScope.launch {
            runCatching { albumRepo.assign(taskId, album?.id) }
                .onSuccess { _state.update { it.copy(albumName = album?.name) } }
                .onFailure { Timber.w(it, "assign album failed") }
        }
    }

    fun sendChat(taskId: String, message: String) {
        if (taskId.isBlank() || message.isBlank() || _state.value.sending) return
        viewModelScope.launch {
            _state.update { it.copy(sending = true) }
            runCatching { taskRepo.sendChat(taskId, message.trim()) }
                .onSuccess { thread ->
                    _state.update { it.copy(chat = thread.messages.map { m -> ChatTurn(m.role == "user", latexToUnicode(m.content), m.imageUrl) }, chatRemaining = thread.remaining, sending = false, needTopUp = false) }
                }
                .onFailure { e ->
                    Timber.w(e, "send chat failed")
                    val outOfQuota = (e as? retrofit2.HttpException)?.code() == 402
                    _state.update { it.copy(sending = false, needTopUp = outOfQuota || it.needTopUp) }
                }
        }
    }

    fun sendChatImage(taskId: String, bytes: ByteArray, caption: String) {
        if (taskId.isBlank() || bytes.isEmpty() || _state.value.sending) return
        viewModelScope.launch {
            _state.update { it.copy(sending = true) }
            runCatching { taskRepo.sendChatImage(taskId, bytes, caption.trim()) }
                .onSuccess { thread ->
                    _state.update { it.copy(chat = thread.messages.map { m -> ChatTurn(m.role == "user", latexToUnicode(m.content), m.imageUrl) }, chatRemaining = thread.remaining, sending = false, needTopUp = false) }
                }
                .onFailure { e ->
                    Timber.w(e, "send chat image failed")
                    val oq = (e as? retrofit2.HttpException)?.code() == 402
                    _state.update { it.copy(sending = false, needTopUp = oq || it.needTopUp) }
                }
        }
    }

    fun dismissTopUp() {
        _state.update { it.copy(needTopUp = false) }
    }
}
