package com.pandasolve.app.ui.sample

import androidx.compose.ui.graphics.Color
import com.pandasolve.app.ui.theme.*

/** Demo content so the cute screens render fully without a live backend. */

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
)

data class SampleAlbum(
    val name: String,
    val sticker: String,
    val count: Int,
    val updated: String,
    val soft: Color,
    val line: Color,
    val shadow: Color,
    val deep: Color,
)

val sampleThreads = listOf(
    SampleThread("∫", true, "Найти ∫ sin²x dx на отрезке [0, π] через двойной угол", TStatus.Done, "матем", Mint, MintSoft, "5 мин"),
    SampleThread("📐", false, "Система с тремя неизвестными — фото из тетради", TStatus.Done, "геом", Coral, CoralSoft, "1 ч"),
    SampleThread("lim", true, "Предел sin x / x при x → 0 — что за доказательство?", TStatus.Talking, "4 сообщ.", Lav, LavSoft, "вчера"),
)

val sampleAlbums = listOf(
    SampleAlbum("Математика", "➗", 18, "5 мин назад", MintSoft, Mint, MintShadow, MintDeep),
    SampleAlbum("Английский", "🔤", 9, "вчера", SkySoft, Sky, SkyShadow, SkyDeep),
    SampleAlbum("Геометрия", "📐", 7, "2 дня", LavSoft, Lav, LavShadow, LavDeep),
    SampleAlbum("Тесты ЕГЭ", "✏️", 11, "28 мая", CoralSoft, Coral, CoralShadow, CoralDeep),
    SampleAlbum("Физика", "⚛️", 2, "26 мая", ButterSoft, Butter, ButterShadow, ButterDeep),
)
