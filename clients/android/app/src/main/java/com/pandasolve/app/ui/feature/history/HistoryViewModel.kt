package com.pandasolve.app.ui.feature.history

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pandasolve.app.data.repository.TaskRepository
import com.pandasolve.app.ui.sample.SampleThread
import com.pandasolve.app.ui.sample.sampleThreads
import com.pandasolve.app.ui.sample.toRow
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import timber.log.Timber

data class DayBucket(val tape: String, val date: String, val items: List<SampleThread>)

data class ArchiveUiState(
    val days: List<DayBucket> = sampleDays(),
    val total: Int = 47,
    val live: Boolean = false,
)

private fun sampleDays() = listOf(
    DayBucket("сегодня", "30 мая", sampleThreads.take(2)),
    DayBucket("вчера", "29 мая", sampleThreads.takeLast(2)),
    DayBucket("ранее", "28 мая", sampleThreads.take(1)),
)

@HiltViewModel
class HistoryViewModel @Inject constructor(
    private val taskRepo: TaskRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(ArchiveUiState())
    val state: StateFlow<ArchiveUiState> = _state.asStateFlow()

    fun refresh() {
        viewModelScope.launch {
            runCatching {
                val list = taskRepo.list(limit = 50, before = null)
                val rows = list.items.mapIndexed { i, item -> item.createdAt.take(10) to item.toRow(i) }
                // group by ISO date prefix, newest groups first (already sorted by API)
                val grouped = rows.groupBy({ it.first }, { it.second })
                val days = grouped.entries.mapIndexed { idx, (date, items) ->
                    val tape = when (idx) { 0 -> "сегодня"; 1 -> "вчера"; else -> "ранее" }
                    DayBucket(tape, date, items)
                }
                ArchiveUiState(days = days.ifEmpty { sampleDays() }, total = list.items.size, live = true)
            }.onSuccess { _state.value = it }
                .onFailure { Timber.w(it, "archive load failed — keeping sample content") }
        }
    }
}
