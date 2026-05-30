package com.pandasolve.app.ui.feature.albums

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.hilt.navigation.compose.hiltViewModel
import com.pandasolve.app.ui.component.Candy
import com.pandasolve.app.ui.component.CandyButton
import com.pandasolve.app.ui.component.CuteBottomBar
import com.pandasolve.app.ui.component.CuteTab
import com.pandasolve.app.ui.component.dotPaper
import com.pandasolve.app.ui.feature.history.Segmented
import com.pandasolve.app.ui.sample.SampleAlbum
import com.pandasolve.app.ui.theme.Baloo
import com.pandasolve.app.ui.theme.Caveat
import com.pandasolve.app.ui.theme.Nunito
import com.pandasolve.app.ui.theme.cute

@Composable
fun AlbumsScreen(
    onArchive: () -> Unit,
    onCamera: () -> Unit,
    onProfile: () -> Unit,
    viewModel: AlbumsViewModel = hiltViewModel(),
) {
    val c = cute
    val s by viewModel.state.collectAsState()
    var showCreate by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { viewModel.refresh() }
    Box(Modifier.fillMaxSize().dotPaper(c.paper, c.ink.copy(alpha = 0.07f))) {
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp).padding(top = 14.dp, bottom = 110.dp),
        ) {
            Text("Альбомы 🗂️", fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 24.sp, color = c.ink)
            Text("разложи задачи по темам", fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 18.sp, color = c.inkSoft)

            Spacer(Modifier.height(14.dp))
            Segmented(selected = 1, onByDate = onArchive, onAlbums = {})

            Spacer(Modifier.height(18.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.Bottom) {
                Text("Твои альбомы", fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 22.sp, color = c.ink)
                Text("${s.albums.size} штук", fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 19.sp, color = c.lavDeep)
            }

            Spacer(Modifier.height(14.dp))
            val cells: List<SampleAlbum?> = s.albums + listOf<SampleAlbum?>(null) // null = create card
            cells.chunked(2).forEach { row ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(13.dp)) {
                    row.forEach { album ->
                        Box(Modifier.weight(1f)) {
                            if (album == null) CreateCard { showCreate = true } else AlbumCard(album)
                        }
                    }
                    if (row.size == 1) Spacer(Modifier.weight(1f))
                }
                Spacer(Modifier.height(13.dp))
            }
        }

        CuteBottomBar(CuteTab.Archive, onArchive = onArchive, onCamera = onCamera, onProfile = onProfile, modifier = Modifier.align(Alignment.BottomCenter))
    }

    if (showCreate) {
        CreateAlbumDialog(
            onDismiss = { showCreate = false },
            onCreate = { name, emoji, color ->
                viewModel.create(name, emoji, color)
                showCreate = false
            },
        )
    }
}

private val EMOJIS = listOf("📚", "➗", "🔤", "📐", "✏️", "⚛️", "🧪", "🎨", "🌍", "🎵")
private val COLOR_KEYS = listOf("mint", "sky", "lav", "coral", "butter", "pink")

@Composable
private fun CreateAlbumDialog(onDismiss: () -> Unit, onCreate: (String, String, String) -> Unit) {
    val c = cute
    var name by remember { mutableStateOf("") }
    var emoji by remember { mutableStateOf(EMOJIS.first()) }
    var color by remember { mutableStateOf(COLOR_KEYS.first()) }

    fun swatch(key: String): Color = when (key) {
        "sky" -> c.sky; "lav" -> c.lav; "coral" -> c.coral; "butter" -> c.butter; "pink" -> c.pink; else -> c.mint
    }

    Dialog(onDismissRequest = onDismiss) {
        Column(
            Modifier.clip(RoundedCornerShape(28.dp)).background(c.paper).padding(22.dp),
        ) {
            Text("Новый альбом ✨", fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 22.sp, color = c.ink)
            Spacer(Modifier.height(16.dp))

            // name field
            Column(
                Modifier.fillMaxWidth().clip(RoundedCornerShape(18.dp)).background(c.card)
                    .border(2.dp, c.mint, RoundedCornerShape(18.dp)).padding(horizontal = 14.dp, vertical = 11.dp),
            ) {
                Text("НАЗВАНИЕ", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.inkFaint)
                Spacer(Modifier.height(3.dp))
                BasicTextField(
                    value = name, onValueChange = { name = it }, singleLine = true,
                    cursorBrush = SolidColor(c.mintDeep),
                    textStyle = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 15.sp, color = c.ink),
                    decorationBox = { inner ->
                        if (name.isEmpty()) Text("например, Химия", fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 15.sp, color = c.inkFaint)
                        inner()
                    },
                )
            }

            Spacer(Modifier.height(16.dp))
            Text("ЗНАЧОК", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.inkFaint)
            Spacer(Modifier.height(8.dp))
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                EMOJIS.forEach { e ->
                    Box(
                        Modifier.size(42.dp).clip(RoundedCornerShape(14.dp))
                            .background(if (e == emoji) c.mintSoft else c.card)
                            .border(2.dp, if (e == emoji) c.mint else c.line, RoundedCornerShape(14.dp))
                            .clickable { emoji = e },
                        contentAlignment = Alignment.Center,
                    ) { Text(e, fontSize = 20.sp) }
                }
            }

            Spacer(Modifier.height(16.dp))
            Text("ЦВЕТ", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.inkFaint)
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                COLOR_KEYS.forEach { key ->
                    Box(
                        Modifier.size(34.dp).clip(CircleShape).background(swatch(key))
                            .border(if (key == color) 3.dp else 0.dp, c.ink, CircleShape)
                            .clickable { color = key },
                    )
                }
            }

            Spacer(Modifier.height(22.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                CandyButton("Отмена", onDismiss, Modifier.weight(1f), Candy.Ghost)
                CandyButton("Создать", { onCreate(name, emoji, color) }, Modifier.weight(1f), Candy.Mint, enabled = name.isNotBlank())
            }
        }
    }
}

@Composable
private fun AlbumCard(a: SampleAlbum) {
    val c = cute
    Box(Modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp)).background(a.shadow)) {
        Column(
            Modifier.fillMaxWidth().padding(bottom = 4.dp).clip(RoundedCornerShape(20.dp)).background(a.soft)
                .border(2.dp, a.line, RoundedCornerShape(20.dp)).heightIn(min = 116.dp).padding(14.dp),
            verticalArrangement = Arrangement.SpaceBetween,
        ) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(a.sticker, fontSize = 30.sp)
                // washi tape
                Box(Modifier.padding(top = 2.dp).rotate(8f).size(width = 34.dp, height = 14.dp).background(Color.White.copy(alpha = 0.6f)))
            }
            Column {
                Text(a.name, fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 16.sp, color = c.ink)
                Spacer(Modifier.height(3.dp))
                Row(verticalAlignment = Alignment.Bottom) {
                    Text("${a.count} задач", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = a.deep)
                    Spacer(Modifier.width(6.dp))
                    Text(a.updated, fontFamily = Caveat, fontWeight = FontWeight.W600, fontSize = 14.sp, color = c.inkFaint)
                }
            }
        }
    }
}

@Composable
private fun CreateCard(onClick: () -> Unit) {
    val c = cute
    Column(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp)).background(c.lavSoft)
            .border(2.dp, c.lav, RoundedCornerShape(20.dp)).heightIn(min = 116.dp).clickable(onClick = onClick).padding(14.dp),
        horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center,
    ) {
        Box(Modifier.size(38.dp).clip(CircleShape).background(c.card), contentAlignment = Alignment.Center) {
            Text("+", fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 22.sp, color = c.lavDeep)
        }
        Spacer(Modifier.height(8.dp))
        Text("новый альбом", fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 13.sp, color = c.lavDeep)
    }
}
