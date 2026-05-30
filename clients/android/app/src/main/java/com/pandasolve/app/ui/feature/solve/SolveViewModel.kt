package com.pandasolve.app.ui.feature.solve

import android.content.Context
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pandasolve.app.data.repository.TaskRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class SolveState(
    val busy: Boolean = false,
    val createdTaskId: String? = null,
    val error: String? = null,
)

@HiltViewModel
class SolveViewModel @Inject constructor(
    @ApplicationContext private val ctx: Context,
    private val taskRepo: TaskRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(SolveState())
    val state: StateFlow<SolveState> = _state.asStateFlow()

    fun submitImage(uri: Uri, caption: String?) {
        viewModelScope.launch {
            _state.update { it.copy(busy = true, error = null) }
            runCatching {
                val bytes = ctx.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                    ?: error("could not read image")
                taskRepo.submitImage(bytes, caption)
            }
                .onSuccess { id -> _state.update { it.copy(busy = false, createdTaskId = id) } }
                .onFailure { e -> _state.update { it.copy(busy = false, error = e.message) } }
        }
    }

    fun submitImageBytes(bytes: ByteArray, caption: String?) {
        viewModelScope.launch {
            _state.update { it.copy(busy = true, error = null) }
            runCatching { taskRepo.submitImage(bytes, caption) }
                .onSuccess { id -> _state.update { it.copy(busy = false, createdTaskId = id) } }
                .onFailure { e -> _state.update { it.copy(busy = false, error = e.message) } }
        }
    }

    fun submitText(text: String) {
        viewModelScope.launch {
            _state.update { it.copy(busy = true, error = null) }
            runCatching { taskRepo.submitText(text) }
                .onSuccess { id -> _state.update { it.copy(busy = false, createdTaskId = id) } }
                .onFailure { e -> _state.update { it.copy(busy = false, error = e.message) } }
        }
    }
}
