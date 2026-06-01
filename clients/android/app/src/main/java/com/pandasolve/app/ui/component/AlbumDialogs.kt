package com.pandasolve.app.ui.component

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.pandasolve.app.i18n.LocalStrings
import com.pandasolve.app.ui.theme.Baloo
import com.pandasolve.app.ui.theme.Nunito
import com.pandasolve.app.ui.theme.cute

/** Shared album reference used by the picker (id + display bits). */
data class AlbumOption(val id: String, val name: String, val emoji: String)

val ALBUM_EMOJIS = listOf("📚", "➗", "🔤", "📐", "✏️", "⚛️", "🧪", "🎨", "🌍", "🎵")
val ALBUM_COLOR_KEYS = listOf("mint", "sky", "lav", "coral", "butter", "pink")

@Composable
fun albumSwatch(key: String): Color {
    val c = cute
    return when (key) {
        "sky" -> c.sky; "lav" -> c.lav; "coral" -> c.coral; "butter" -> c.butter; "pink" -> c.pink; else -> c.mint
    }
}

/** Assign a task to an album (or clear it). */
@Composable
fun AlbumPickerDialog(
    albums: List<AlbumOption>,
    onDismiss: () -> Unit,
    onPick: (AlbumOption?) -> Unit,
) {
    val c = cute
    val t = LocalStrings.current
    Dialog(onDismissRequest = onDismiss) {
        Column(Modifier.clip(RoundedCornerShape(28.dp)).background(c.paper).padding(20.dp)) {
            Text(t.albumPickerTitle, fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 20.sp, color = c.ink)
            Spacer(Modifier.height(14.dp))
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                albums.forEach { a ->
                    Row(
                        Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(c.card)
                            .border(2.dp, c.line, RoundedCornerShape(16.dp))
                            .clickable { onPick(a) }.padding(horizontal = 14.dp, vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(a.emoji, fontSize = 18.sp)
                        Spacer(Modifier.width(12.dp))
                        Text(a.name, fontFamily = Baloo, fontWeight = FontWeight.W600, fontSize = 15.sp, color = c.ink)
                    }
                }
                if (albums.isEmpty()) {
                    Text(t.albumPickerEmpty,
                        fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 13.sp, color = c.inkFaint)
                }
                Row(
                    Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp))
                        .clickable { onPick(null) }.padding(horizontal = 14.dp, vertical = 12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("✕", fontSize = 16.sp, color = c.coralDeep)
                    Spacer(Modifier.width(12.dp))
                    Text(t.albumNone, fontFamily = Baloo, fontWeight = FontWeight.W600, fontSize = 15.sp, color = c.coralDeep)
                }
            }
        }
    }
}

/** Create (isEdit=false) or edit (isEdit=true, with onDelete) an album. */
@Composable
fun AlbumEditorDialog(
    initialName: String = "",
    initialEmoji: String = ALBUM_EMOJIS.first(),
    initialColor: String = ALBUM_COLOR_KEYS.first(),
    isEdit: Boolean = false,
    onDismiss: () -> Unit,
    onSave: (name: String, emoji: String, color: String) -> Unit,
    onDelete: (() -> Unit)? = null,
) {
    val c = cute
    val t = LocalStrings.current
    var name by remember { mutableStateOf(initialName) }
    var emoji by remember { mutableStateOf(initialEmoji) }
    var color by remember { mutableStateOf(initialColor) }
    var customIcon by remember { mutableStateOf(false) }

    Dialog(onDismissRequest = onDismiss) {
        Column(Modifier.clip(RoundedCornerShape(28.dp)).background(c.paper).padding(22.dp)) {
            Text(
                if (isEdit) t.albumEditTitle else t.albumNewTitle,
                fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 22.sp, color = c.ink,
            )
            Spacer(Modifier.height(16.dp))

            Column(
                Modifier.fillMaxWidth().clip(RoundedCornerShape(18.dp)).background(c.card)
                    .border(2.dp, c.mint, RoundedCornerShape(18.dp)).padding(horizontal = 14.dp, vertical = 11.dp),
            ) {
                Text(t.albumNameLabel, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.inkFaint)
                Spacer(Modifier.height(3.dp))
                BasicTextField(
                    value = name, onValueChange = { name = it }, singleLine = true,
                    cursorBrush = SolidColor(c.mintDeep),
                    textStyle = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 15.sp, color = c.ink),
                    decorationBox = { inner ->
                        if (name.isEmpty()) Text(t.albumNameHint, fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 15.sp, color = c.inkFaint)
                        inner()
                    },
                )
            }

            Spacer(Modifier.height(16.dp))
            Text(t.albumIconLabel, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.inkFaint)
            Spacer(Modifier.height(8.dp))
            val isCustom = emoji !in ALBUM_EMOJIS
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                ALBUM_EMOJIS.forEach { e ->
                    Box(
                        Modifier.size(42.dp).clip(RoundedCornerShape(14.dp))
                            .background(if (e == emoji && !customIcon) c.mintSoft else c.card)
                            .border(2.dp, if (e == emoji && !customIcon) c.mint else c.line, RoundedCornerShape(14.dp))
                            .clickable { emoji = e; customIcon = false },
                        contentAlignment = Alignment.Center,
                    ) { Text(e, fontSize = 20.sp) }
                }
                // "＋" — pick any other emoji
                Box(
                    Modifier.size(42.dp).clip(RoundedCornerShape(14.dp))
                        .background(if (isCustom || customIcon) c.mintSoft else c.card)
                        .border(2.dp, if (isCustom || customIcon) c.mint else c.line, RoundedCornerShape(14.dp))
                        .clickable { customIcon = true },
                    contentAlignment = Alignment.Center,
                ) { Text(if (isCustom) emoji else "＋", fontSize = if (isCustom) 20.sp else 18.sp, color = c.lavDeep) }
            }
            if (customIcon) {
                Spacer(Modifier.height(8.dp))
                Row(
                    Modifier.clip(RoundedCornerShape(14.dp)).background(c.card)
                        .border(2.dp, c.mint, RoundedCornerShape(14.dp)).padding(horizontal = 14.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    BasicTextField(
                        value = if (isCustom) emoji else "", onValueChange = { emoji = it.trim().take(4) }, singleLine = true,
                        cursorBrush = SolidColor(c.mintDeep),
                        textStyle = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 18.sp, color = c.ink),
                        decorationBox = { inner ->
                            if (!isCustom) Text(t.albumCustomIconHint, fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 13.sp, color = c.inkFaint)
                            inner()
                        },
                    )
                }
            }

            Spacer(Modifier.height(16.dp))
            Text(t.albumColorLabel, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.inkFaint)
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                ALBUM_COLOR_KEYS.forEach { key ->
                    Box(
                        Modifier.size(34.dp).clip(CircleShape).background(albumSwatch(key))
                            .border(if (key == color) 3.dp else 0.dp, c.ink, CircleShape)
                            .clickable { color = key },
                    )
                }
            }

            Spacer(Modifier.height(22.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                if (isEdit && onDelete != null) {
                    CandyButton(t.albumDelete, onDelete, Modifier.weight(1f), Candy.Ghost)
                } else {
                    CandyButton(t.cancel, onDismiss, Modifier.weight(1f), Candy.Ghost)
                }
                CandyButton(
                    if (isEdit) t.albumSave else t.albumCreate,
                    { onSave(name, emoji, color) }, Modifier.weight(1f), Candy.Mint, enabled = name.isNotBlank(),
                )
            }
        }
    }
}
