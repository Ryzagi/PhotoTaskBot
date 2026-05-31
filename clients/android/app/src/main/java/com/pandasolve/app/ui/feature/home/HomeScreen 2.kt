package com.pandasolve.app.ui.feature.home

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.compose.runtime.collectAsState
import com.pandasolve.app.ui.component.CuteBottomBar
import com.pandasolve.app.ui.component.CuteTab
import com.pandasolve.app.ui.component.Panda
import com.pandasolve.app.ui.component.ThreadCard
import com.pandasolve.app.ui.component.dotPaper
import com.pandasolve.app.ui.theme.Baloo
import com.pandasolve.app.ui.theme.Caveat
import com.pandasolve.app.ui.theme.Nunito
import com.pandasolve.app.ui.theme.cute

@Composable
fun HomeScreen(
    onCamera: () -> Unit,
    onArchive: () -> Unit,
    onProfile: () -> Unit,
    onTask: (String) -> Unit,
    onAlbums: () -> Unit,
    viewModel: HomeViewModel = hiltViewModel(),
) {
    val c = cute
    val s by viewModel.state.collectAsState()
    LaunchedEffect(Unit) { viewModel.refresh() }
    Box(Modifier.fillMaxSize().dotPaper(c.paper, c.ink.copy(alpha = 0.07f))) {
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp).padding(top = 10.dp, bottom = 96.dp),
        ) {
            // greeting + streak
            Row(verticalAlignment = Alignment.CenterVertically) {
                Panda(Modifier.size(40.dp))
                Spacer(Modifier.width(10.dp))
                Column(Modifier.weight(1f)) {
                    Text("с возвращением,", fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 18.sp, color = c.inkSoft)
                    Text(if (s.name.isNotBlank()) "${s.name} ✿" else "🐼", fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 19.sp, color = c.ink)
                }
                if (s.streak > 0) Pill("🔥 ${s.streak} дн.", c.butterSoft, c.butterDeep, c.butterShadow)
            }

            Spacer(Modifier.height(12.dp))

            // bamboo energy
            Column(
                Modifier.fillMaxWidth().clip(RoundedCornerShape(28.dp))
                    .background(Brush.linearGradient(listOf(c.mintSoft, Color.White)))
                    .border(2.dp, c.mint, RoundedCornerShape(28.dp))
                    .padding(16.dp),
            ) {
                Text("БАМБУК НА СЕГОДНЯ", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = c.mintDeep)
                Row(verticalAlignment = Alignment.Bottom) {
                    Text("${s.daily}", fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 44.sp, color = c.ink)
                    Spacer(Modifier.width(8.dp))
                    Text("решения", fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 16.sp, color = c.inkSoft, modifier = Modifier.padding(bottom = 12.dp))
                }
                Spacer(Modifier.height(8.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    val filled = s.daily.coerceIn(0, 5)
                    repeat(filled) { Leaf(c.mint, c.mintShadow); Spacer(Modifier.width(6.dp)) }
                    repeat(5 - filled) { Leaf(c.line, Color(0xFFE0D3BF)); Spacer(Modifier.width(6.dp)) }
                    Spacer(Modifier.weight(1f))
                    if (s.subscription > 0) Box(
                        Modifier.clip(RoundedCornerShape(999.dp)).background(c.butterSoft).padding(horizontal = 10.dp, vertical = 5.dp),
                    ) { Text("+${s.subscription} ⭐ донат", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 12.sp, color = c.butterDeep) }
                }
            }

            Spacer(Modifier.height(12.dp))

            // album quick-row
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (s.albums.isEmpty()) {
                    AlbumPill("📚 все", "${s.solvedCount}", c.lav, Color.White, c.lavShadow, filled = true, onClick = onAlbums)
                } else {
                    AlbumPill("📚 все", "${s.solvedCount}", c.lav, Color.White, c.lavShadow, filled = true, onClick = onAlbums)
                    s.albums.take(6).forEach { a ->
                        val swatch = when (a.color) {
                            "sky" -> c.sky; "lav" -> c.lav; "coral" -> c.coral; "butter" -> c.butter; "pink" -> c.pink; else -> c.mint
                        }
                        AlbumPill("${a.emoji ?: "📚"} ${a.name}", "${a.taskCount}", swatch, c.ink, c.line, onClick = onAlbums)
                    }
                }
            }

            Spacer(Modifier.height(16.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Text("Недавние беседы", fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 17.sp, color = c.ink)
                Text("все →", fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 17.sp, color = c.lavDeep)
            }
            Spacer(Modifier.height(12.dp))
            Column(verticalArrangement = Arrangement.spacedBy(11.dp)) {
                s.threads.forEach { t -> ThreadCard(t) { if (t.id.isNotBlank()) onTask(t.id) } }
            }
        }

        CuteBottomBar(
            active = CuteTab.None,
            onArchive = onArchive, onCamera = onCamera, onProfile = onProfile,
            modifier = Modifier.align(Alignment.BottomCenter),
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

@Composable
private fun AlbumPill(label: String, n: String, line: Color, fg: Color, shadow: Color, filled: Boolean = false, onClick: () -> Unit) {
    val c = cute
    Box(Modifier.clip(RoundedCornerShape(999.dp)).background(shadow)) {
        Row(
            Modifier.padding(bottom = 3.dp).clip(RoundedCornerShape(999.dp))
                .background(if (filled) line else c.card)
                .then(if (filled) Modifier else Modifier.border(2.dp, line, RoundedCornerShape(999.dp)))
                .clickable(onClick = onClick)
                .padding(horizontal = 13.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(label, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 12.sp, color = if (filled) Color.White else fg)
            Spacer(Modifier.width(6.dp))
            Text(n, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 12.sp, color = if (filled) Color.White.copy(alpha = .75f) else c.inkFaint)
        }
    }
}
