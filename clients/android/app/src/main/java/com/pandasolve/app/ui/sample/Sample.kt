package com.pandasolve.app.ui.sample

import androidx.compose.ui.graphics.Color

/** Row model shared by ThreadCard and the Home list (built from real tasks via toRow). */

enum class TStatus { Done, Talking }

data class SampleThread(
    val glyph: String,        // emoji or short math
    val isMath: Boolean,
    val preview: String,
    val status: TStatus,
    val album: String,
    val albumColor: Color,
    val tint: Color,
    val stamp: String,
    val id: String = "",      // real task id
)
