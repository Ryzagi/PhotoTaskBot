package com.pandasolve.app.ui.sample

import com.pandasolve.app.domain.model.TaskListItem
import com.pandasolve.app.latex.latexToUnicode
import com.pandasolve.app.util.localDateOf
import com.pandasolve.app.ui.theme.Butter
import com.pandasolve.app.ui.theme.ButterSoft
import com.pandasolve.app.ui.theme.Coral
import com.pandasolve.app.ui.theme.CoralSoft
import com.pandasolve.app.ui.theme.Lav
import com.pandasolve.app.ui.theme.LavSoft
import com.pandasolve.app.ui.theme.Mint
import com.pandasolve.app.ui.theme.MintSoft
import com.pandasolve.app.ui.theme.Sky
import com.pandasolve.app.ui.theme.SkySoft

private val tints = listOf(MintSoft, CoralSoft, LavSoft, SkySoft, ButterSoft)
private val albumColors = listOf(Mint, Coral, Lav, Sky, Butter)

/** Maps a backend task into the cute row model used by ThreadCard. */
fun TaskListItem.toRow(index: Int): SampleThread = SampleThread(
    glyph = if (inputKind == "image") "🖼" else "📝",
    isMath = false,
    preview = latexToUnicode(preview),   // blank → ThreadCard shows a localized "Untitled"
    status = if (status == "done") TStatus.Done else TStatus.Talking,
    album = inputKind,
    albumColor = albumColors[index % albumColors.size],
    tint = tints[index % tints.size],
    stamp = localDateOf(createdAt),
    id = this.id,
)
