package com.pandasolve.app.ui.sample

import com.pandasolve.app.domain.model.Album
import com.pandasolve.app.domain.model.TaskListItem
import com.pandasolve.app.ui.theme.Butter
import com.pandasolve.app.ui.theme.ButterDeep
import com.pandasolve.app.ui.theme.ButterShadow
import com.pandasolve.app.ui.theme.ButterSoft
import com.pandasolve.app.ui.theme.Coral
import com.pandasolve.app.ui.theme.CoralDeep
import com.pandasolve.app.ui.theme.CoralShadow
import com.pandasolve.app.ui.theme.CoralSoft
import com.pandasolve.app.ui.theme.Lav
import com.pandasolve.app.ui.theme.LavDeep
import com.pandasolve.app.ui.theme.LavShadow
import com.pandasolve.app.ui.theme.LavSoft
import com.pandasolve.app.ui.theme.Mint
import com.pandasolve.app.ui.theme.MintDeep
import com.pandasolve.app.ui.theme.MintShadow
import com.pandasolve.app.ui.theme.MintSoft
import com.pandasolve.app.ui.theme.Pink
import com.pandasolve.app.ui.theme.Sky
import com.pandasolve.app.ui.theme.SkyDeep
import com.pandasolve.app.ui.theme.SkyShadow
import com.pandasolve.app.ui.theme.SkySoft

private val tints = listOf(MintSoft, CoralSoft, LavSoft, SkySoft, ButterSoft)
private val albumColors = listOf(Mint, Coral, Lav, Sky, Butter)

/** Maps a backend album into the cute scrapbook-card model, resolving its
 *  palette from the stored colour key. */
fun Album.toSampleAlbum(): SampleAlbum {
    val (soft, line, shadow, deep) = when (color) {
        "sky" -> Quad(SkySoft, Sky, SkyShadow, SkyDeep)
        "lav" -> Quad(LavSoft, Lav, LavShadow, LavDeep)
        "coral" -> Quad(CoralSoft, Coral, CoralShadow, CoralDeep)
        "butter" -> Quad(ButterSoft, Butter, ButterShadow, ButterDeep)
        "pink" -> Quad(PinkSoftFallback, Pink, PinkShadowFallback, PinkDeepFallback)
        else -> Quad(MintSoft, Mint, MintShadow, MintDeep)
    }
    return SampleAlbum(
        name = name,
        sticker = emoji ?: "📚",
        count = taskCount,
        updated = updatedAt.take(10),
        soft = soft, line = line, shadow = shadow, deep = deep,
    )
}

private data class Quad(
    val a: androidx.compose.ui.graphics.Color,
    val b: androidx.compose.ui.graphics.Color,
    val c: androidx.compose.ui.graphics.Color,
    val d: androidx.compose.ui.graphics.Color,
)
private operator fun Quad.component1() = a
private operator fun Quad.component2() = b
private operator fun Quad.component3() = c
private operator fun Quad.component4() = d

private val PinkSoftFallback = com.pandasolve.app.ui.theme.PinkSoft
private val PinkShadowFallback = Pink
private val PinkDeepFallback = com.pandasolve.app.ui.theme.PinkDeep

/** Maps a backend task into the cute row model used by ThreadCard. */
fun TaskListItem.toRow(index: Int): SampleThread = SampleThread(
    glyph = if (inputKind == "image") "🖼" else "📝",
    isMath = false,
    preview = preview.ifBlank { "Без названия" },
    status = if (status == "done") TStatus.Done else TStatus.Talking,
    album = inputKind,
    albumColor = albumColors[index % albumColors.size],
    tint = tints[index % tints.size],
    stamp = createdAt.take(10),
    id = this.id,
)
