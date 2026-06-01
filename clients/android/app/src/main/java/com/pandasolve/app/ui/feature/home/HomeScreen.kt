package com.pandasolve.app.ui.feature.home

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pandasolve.app.domain.model.Album
import com.pandasolve.app.i18n.LocalStrings
import com.pandasolve.app.ui.component.AlbumEditorDialog
import com.pandasolve.app.ui.component.AlbumOption
import com.pandasolve.app.ui.component.AlbumPickerDialog
import com.pandasolve.app.ui.component.CuteBottomBar
import com.pandasolve.app.ui.component.CuteTab
import com.pandasolve.app.ui.component.Panda
import com.pandasolve.app.ui.component.ThreadCard
import com.pandasolve.app.ui.component.albumSwatch
import com.pandasolve.app.ui.component.dotPaper
import com.pandasolve.app.ui.theme.Baloo
import com.pandasolve.app.ui.theme.Caveat
import com.pandasolve.app.ui.theme.Nunito
import com.pandasolve.app.ui.theme.cute

@Composable
fun HomeScreen(
    onCamera: () -> Unit,
    onProfile: () -> Unit,
    onTask: (String) -> Unit,
    viewModel: HomeViewModel = hiltViewModel(),
) {
    val c = cute
    val s by viewModel.state.collectAsState()
    val t = LocalStrings.current
    LaunchedEffect(Unit) { viewModel.refresh() }

    var assignTaskId by remember { mutableStateOf<String?>(null) }
    var showCreate by remember { mutableStateOf(false) }
    var editAlbum by remember { mutableStateOf<Album?>(null) }

    Box(Modifier.fillMaxSize().dotPaper(c.paper, c.ink.copy(alpha = 0.07f))) {
        LazyColumn(
            Modifier.fillMaxSize(),
            contentPadding = PaddingValues(start = 20.dp, end = 20.dp, top = 10.dp, bottom = 96.dp),
        ) {
            // header: greeting + balance + album chips + search (one item)
            item {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Panda(Modifier.size(40.dp))
                    Spacer(Modifier.width(10.dp))
                    Column(Modifier.weight(1f)) {
                        Text(t.welcomeBack, fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 18.sp, color = c.inkSoft)
                        Text(if (s.name.isNotBlank()) "${s.name} ✿" else "🐼", fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 19.sp, color = c.ink)
                    }
                    if (s.streak > 0) Pill("🔥 ${s.streak} ${t.daysShort}", c.butterSoft, c.butterDeep, c.butterShadow)
                }

                Spacer(Modifier.height(12.dp))

                Column(
                    Modifier.fillMaxWidth().clip(RoundedCornerShape(28.dp))
                        .background(Brush.linearGradient(listOf(c.mintSoft, Color.White)))
                        .border(2.dp, c.mint, RoundedCornerShape(28.dp))
                        .padding(16.dp),
                ) {
                    Text(t.bambooToday, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = c.mintDeep)
                    Row(verticalAlignment = Alignment.Bottom) {
                        Text("${s.daily}", fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 44.sp, color = c.ink)
                        Spacer(Modifier.width(8.dp))
                        Text(t.solutions, fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 16.sp, color = c.inkSoft, modifier = Modifier.padding(bottom = 12.dp))
                    }
                    Spacer(Modifier.height(8.dp))
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        val filled = s.daily.coerceIn(0, 5)
                        repeat(filled) { Leaf(c.mint, c.mintShadow); Spacer(Modifier.width(6.dp)) }
                        repeat(5 - filled) { Leaf(c.line, Color(0xFFE0D3BF)); Spacer(Modifier.width(6.dp)) }
                        Spacer(Modifier.weight(1f))
                        if (s.subscription > 0) Box(
                            Modifier.clip(RoundedCornerShape(999.dp)).background(c.butterSoft).padding(horizontal = 10.dp, vertical = 5.dp),
                        ) { Text("+${s.subscription} ⭐ ${t.donate}", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 12.sp, color = c.butterDeep) }
                    }
                }

                Spacer(Modifier.height(12.dp))

                Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip("📚 все", "${s.solvedCount}", c.lav, c.lavShadow, selected = s.selectedAlbumId == null,
                        onClick = { viewModel.setAlbumFilter(null) }, onLongClick = {})
                    s.albums.forEach { a ->
                        FilterChip("${a.emoji ?: "📚"} ${a.name}", "${a.taskCount}", albumSwatch(a.color ?: "mint"), c.lavShadow,
                            selected = s.selectedAlbumId == a.id,
                            onClick = { viewModel.setAlbumFilter(a.id) },
                            onLongClick = { editAlbum = a })
                    }
                    PlusChip { showCreate = true }
                }

                Spacer(Modifier.height(14.dp))
                SearchField(s.query, t.searchHint) { viewModel.onQueryChange(it) }
                Spacer(Modifier.height(16.dp))
            }

            if (s.days.isEmpty()) {
                item {
                    Text(t.noTasks, fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 14.sp, color = c.inkFaint,
                        modifier = Modifier.padding(vertical = 24.dp))
                }
            } else {
                s.days.forEachIndexed { idx, day ->
                    item {
                        val label = when (idx) { 0 -> t.dayToday; 1 -> t.dayYesterday; else -> t.dayEarlier }
                        Row(verticalAlignment = Alignment.Bottom) {
                            Text(label, fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 16.sp, color = c.ink)
                            Spacer(Modifier.width(8.dp))
                            Text(day.date, fontFamily = Caveat, fontWeight = FontWeight.W600, fontSize = 14.sp, color = c.inkFaint)
                        }
                        Spacer(Modifier.height(10.dp))
                        Column(verticalArrangement = Arrangement.spacedBy(11.dp)) {
                            day.items.forEach { card ->
                                ThreadCard(
                                    card,
                                    onClick = { if (card.id.isNotBlank()) onTask(card.id) },
                                    onLongClick = { if (card.id.isNotBlank()) assignTaskId = card.id },
                                )
                            }
                        }
                        Spacer(Modifier.height(16.dp))
                    }
                }
            }
        }

        CuteBottomBar(
            active = CuteTab.Home,
            onHome = {}, onCamera = onCamera, onProfile = onProfile,
            modifier = Modifier.align(Alignment.BottomCenter),
        )
    }

    // long-press a task → assign to album
    assignTaskId?.let { tid ->
        AlbumPickerDialog(
            albums = s.albums.map { AlbumOption(it.id, it.name, it.emoji ?: "📚") },
            onDismiss = { assignTaskId = null },
            onPick = { album -> viewModel.assignAlbum(tid, album?.id); assignTaskId = null },
        )
    }
    // ＋ → create album
    if (showCreate) {
        AlbumEditorDialog(
            onDismiss = { showCreate = false },
            onSave = { name, emoji, color -> viewModel.createAlbum(name, emoji, color); showCreate = false },
        )
    }
    // long-press a chip → edit / delete album
    editAlbum?.let { a ->
        AlbumEditorDialog(
            initialName = a.name,
            initialEmoji = a.emoji ?: "📚",
            initialColor = a.color ?: "mint",
            isEdit = true,
            onDismiss = { editAlbum = null },
            onSave = { name, emoji, color -> viewModel.updateAlbum(a.id, name, emoji, color); editAlbum = null },
            onDelete = { viewModel.deleteAlbum(a.id); editAlbum = null },
        )
    }
}

@Composable
private fun Leaf(face: Color, shadow: Color) {
    Box(Modifier.size(22.dp).clip(RoundedCornerShape(8.dp, 8.dp, 8.dp, 2.dp)).background(shadow)) {
        Box(Modifier.fillMaxWidth().padding(bottom = 2.dp).height(20.dp).clip(RoundedCornerShape(8.dp, 8.dp, 8.dp, 2.dp)).background(face))
    }
}

@Composable
private fun Pill(text: String, bg: Color, fg: Color, shadow: Color) {
    Box(Modifier.clip(RoundedCornerShape(999.dp)).background(shadow)) {
        Box(Modifier.padding(bottom = 3.dp).clip(RoundedCornerShape(999.dp)).background(bg).padding(horizontal = 12.dp, vertical = 7.dp)) {
            Text(text, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 13.sp, color = fg)
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun FilterChip(
    label: String, n: String, accent: Color, shadow: Color, selected: Boolean,
    onClick: () -> Unit, onLongClick: () -> Unit,
) {
    val c = cute
    Box(Modifier.clip(RoundedCornerShape(999.dp)).background(shadow)) {
        Row(
            Modifier.padding(bottom = 3.dp).clip(RoundedCornerShape(999.dp))
                .background(if (selected) accent else c.card)
                .then(if (selected) Modifier else Modifier.border(2.dp, accent, RoundedCornerShape(999.dp)))
                .combinedClickable(onClick = onClick, onLongClick = onLongClick)
                .padding(horizontal = 13.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(label, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 12.sp, color = if (selected) Color.White else c.ink)
            Spacer(Modifier.width(6.dp))
            Text(n, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 12.sp, color = if (selected) Color.White.copy(alpha = .75f) else c.inkFaint)
        }
    }
}

@Composable
private fun PlusChip(onClick: () -> Unit) {
    val c = cute
    Box(Modifier.clip(RoundedCornerShape(999.dp)).background(c.lavShadow)) {
        Box(
            Modifier.padding(bottom = 3.dp).clip(RoundedCornerShape(999.dp)).background(c.lavSoft)
                .border(2.dp, c.lav, RoundedCornerShape(999.dp)).clickable(onClick = onClick)
                .padding(horizontal = 15.dp, vertical = 8.dp),
        ) {
            Text("＋", fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 14.sp, color = c.lavDeep)
        }
    }
}

@Composable
private fun SearchField(value: String, hint: String, onChange: (String) -> Unit) {
    val c = cute
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(999.dp)).background(c.card)
            .border(2.dp, c.line, RoundedCornerShape(999.dp)).padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text("🔍", fontSize = 14.sp)
        Spacer(Modifier.width(10.dp))
        BasicTextField(
            value = value, onValueChange = onChange, singleLine = true,
            cursorBrush = SolidColor(c.mintDeep),
            textStyle = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 14.sp, color = c.ink),
            modifier = Modifier.weight(1f),
            decorationBox = { inner ->
                if (value.isEmpty()) Text(hint, fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 14.sp, color = c.inkFaint)
                inner()
            },
        )
    }
}
