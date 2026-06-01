package com.pandasolve.app.ui.feature.albums

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pandasolve.app.data.repository.AlbumRepository
import com.pandasolve.app.ui.sample.SampleAlbum
import com.pandasolve.app.ui.sample.toSampleAlbum
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import timber.log.Timber

data class AlbumsUiState(
    val albums: List<SampleAlbum> = emptyList(),
    val live: Boolean = false,
)

@HiltViewModel
class AlbumsViewModel @Inject constructor(
    private val albumRepo: AlbumRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(AlbumsUiState())
    val state: StateFlow<AlbumsUiState> = _state.asStateFlow()

    fun refresh() {
        viewModelScope.launch {
            runCatching { albumRepo.list().map { it.toSampleAlbum() } }
                .onSuccess { list -> _state.value = AlbumsUiState(list, live = true) }
                .onFailure { Timber.w(it, "albums load failed") }
        }
    }

    fun create(name: String, emoji: String, color: String) {
        if (name.isBlank()) return
        viewModelScope.launch {
            runCatching { albumRepo.create(name.trim(), emoji, color) }
                .onSuccess { refresh() }
                .onFailure { Timber.w(it, "album create failed") }
        }
    }
}
