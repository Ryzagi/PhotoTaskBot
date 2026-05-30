package com.pandasolve.app.ui.feature.history

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pandasolve.app.ui.component.*
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.compose.runtime.collectAsState
import com.pandasolve.app.ui.theme.Baloo
import com.pandasolve.app.ui.theme.Caveat
import com.pandasolve.app.ui.theme.Nunito
import com.pandasolve.app.ui.theme.cute

@Composable
fun ArchiveScreen(
    onTask: (String) -> Unit,
    onCamera: () -> Unit,
    onProfile: () -> Unit,
    onAlbums: () -> Unit,
    viewModel: HistoryViewModel = hiltViewModel(),
) {
    val c = cute
    val s by viewModel.state.collectAsState()
    androidx.compose.runtime.LaunchedEffect(Unit) { viewModel.refresh() }
    val tapeColors = listOf(c.butter, c.sky, c.coral)
    Box(Modifier.fillMaxSize().dotPaper(c.paper, c.ink.copy(alpha = 0.07f))) {
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp).padding(top = 14.dp, bottom = 110.dp),
        ) {
            Text("Архив 📒", fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 24.sp, color = c.ink)
            Text("${s.total} задач решено", fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 18.sp, color = c.inkSoft)

            Spacer(Modifier.height(14.dp))
            Segmented(selected = 0, onByDate = {}, onAlbums = onAlbums)

            Spacer(Modifier.height(12.dp))
            Row(
                Modifier.fillMaxWidth().clip(RoundedCornerShape(999.dp)).background(c.card)
                    .border(2.dp, c.line, RoundedCornerShape(999.dp)).padding(horizontal = 16.dp, vertical = 11.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(Icons.Filled.Search, null, tint = c.inkFaint, modifier = Modifier.size(16.dp))
                Spacer(Modifier.width(10.dp))
                Text("найти задачу…", fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 14.sp, color = c.inkFaint)
            }

            s.days.forEachIndexed { i, day ->
                DayGroup(day.tape, day.date, day.items.size, tapeColors[i % tapeColors.size],
                    startOpen = i == 0, onTask = onTask, items = day.items)
            }
        }

        CuteBottomBar(CuteTab.Archive, onArchive = {}, onCamera = onCamera, onProfile = onProfile, modifier = Modifier.align(Alignment.BottomCenter))
    }
}

@Composable
fun Segmented(selected: Int, onByDate: () -> Unit, onAlbums: () -> Unit) {
    val c = cute
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(c.paper2).padding(5.dp),
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        SegBtn("📅 по дням", selected == 0, c.mintDeep, Modifier.weight(1f), onByDate)
        SegBtn("🗂 альбомы", selected == 1, c.lavDeep, Modifier.weight(1f), onAlbums)
    }
}

@Composable
private fun SegBtn(text: String, on: Boolean, onColor: Color, modifier: Modifier, onClick: () -> Unit) {
    val c = cute
    Box(
        modifier.clip(RoundedCornerShape(12.dp)).background(if (on) c.card else Color.Transparent).clickable(onClick = onClick).padding(vertical = 10.dp),
        contentAlignment = Alignment.Center,
    ) {
        Text(text, fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 13.sp, color = if (on) onColor else c.inkSoft)
    }
}

@Composable
private fun DayGroup(
    tape: String, when_: String, count: Int, tapeColor: Color,
    startOpen: Boolean, items: List<com.pandasolve.app.ui.sample.SampleThread>, onTask: (String) -> Unit,
) {
    val c = cute
    var open by remember { mutableStateOf(startOpen) }
    val rot by animateFloatAsState(if (open) 0f else -90f, label = "chev")
    Column(Modifier.padding(top = 16.dp)) {
        Row(
            Modifier.fillMaxWidth().clickable { open = !open },
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(Modifier.rotate(-1.5f).clip(RoundedCornerShape(8.dp)).background(tapeColor).padding(horizontal = 12.dp, vertical = 5.dp)) {
                Text(tape, fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 13.sp, color = c.ink)
            }
            Spacer(Modifier.width(10.dp))
            Text(when_, fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 18.sp, color = c.inkSoft)
            Spacer(Modifier.weight(1f))
            Text("$count", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 12.sp, color = c.inkFaint)
            Spacer(Modifier.width(8.dp))
            Box(Modifier.size(22.dp).clip(CircleShape).background(c.paper2), contentAlignment = Alignment.Center) {
                Icon(Icons.Filled.KeyboardArrowDown, null, tint = c.inkSoft, modifier = Modifier.size(14.dp).rotate(rot))
            }
        }
        AnimatedVisibility(open) {
            Column(Modifier.padding(top = 12.dp), verticalArrangement = Arrangement.spacedBy(11.dp)) {
                items.forEach { t -> ThreadCard(t) { onTask("042") } }
            }
        }
    }
}
