package com.pandasolve.app.ui.feature.task

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.hilt.navigation.compose.hiltViewModel
import com.pandasolve.app.ui.component.AlbumOption
import com.pandasolve.app.ui.component.AlbumPickerDialog
import com.pandasolve.app.ui.component.Panda
import com.pandasolve.app.ui.component.dotPaper
import com.pandasolve.app.ui.theme.Baloo
import com.pandasolve.app.ui.theme.Nunito
import com.pandasolve.app.ui.theme.cute

@Composable
fun TaskDetailScreen(taskId: String, onBack: () -> Unit, viewModel: TaskDetailViewModel = hiltViewModel()) {
    val c = cute
    val s by viewModel.state.collectAsState()
    LaunchedEffect(taskId) { viewModel.load(taskId) }
    val first = s.problems.firstOrNull()
    var showPicker by remember { mutableStateOf(false) }
    var draft by remember { mutableStateOf("") }
    Box(Modifier.fillMaxSize().dotPaper(c.paper, c.ink.copy(alpha = 0.07f))) {
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp).padding(top = 14.dp, bottom = 100.dp),
        ) {
            // top
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(38.dp).clip(RoundedCornerShape(14.dp)).background(c.card).border(2.dp, c.line, RoundedCornerShape(14.dp)).clickable(onClick = onBack), contentAlignment = Alignment.Center) {
                    Text("‹", fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 20.sp, color = c.ink)
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("Задача №42", fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 16.sp, color = c.ink)
                    Text("9:42 · 11 сек", fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 10.sp, color = c.inkFaint)
                }
                Box(Modifier.size(38.dp).clip(RoundedCornerShape(14.dp)).background(c.coralSoft), contentAlignment = Alignment.Center) {
                    Text("💚", fontSize = 17.sp)
                }
            }

            Spacer(Modifier.height(14.dp))
            // album chip — tap to file the task into an album
            Row(
                Modifier.clip(RoundedCornerShape(999.dp)).background(c.lavSoft)
                    .clickable { showPicker = true }.padding(horizontal = 13.dp, vertical = 7.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Box(Modifier.size(9.dp).clip(RoundedCornerShape(3.dp)).background(c.mint))
                Spacer(Modifier.width(8.dp))
                Text("${s.albumName ?: "выбрать альбом"}  ⌄", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = c.lavDeep)
            }

            Spacer(Modifier.height(13.dp))
            // condition card with tape
            Box {
                Column(
                    Modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp)).background(c.card)
                        .border(2.dp, c.mint, RoundedCornerShape(20.dp)).padding(17.dp).padding(top = 4.dp),
                ) {
                    Text(s.condition,
                        fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 14.sp, color = c.ink, lineHeight = 20.sp)
                }
                Box(Modifier.offset(x = 18.dp, y = (-9).dp).rotate(-3f).clip(RoundedCornerShape(6.dp)).background(c.butter).padding(horizontal = 12.dp, vertical = 4.dp)) {
                    Text("УСЛОВИЕ", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.butterDeep)
                }
            }

            Spacer(Modifier.height(20.dp))
            if (s.status == "pending") {
                SectionLabel("🐼 решаю…", c.mintDeep, c.mintSoft)
                Step(1, "Панда читает условие и думает над решением…")
            } else {
                SectionLabel("📝 решение", c.mintDeep, c.mintSoft)
                first?.steps?.forEachIndexed { i, stepText -> Step(i + 1, stepText) }
            }

            Spacer(Modifier.height(18.dp))
            // answer
            Column(
                Modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp))
                    .background(Brush.linearGradient(listOf(c.mint, Color(0xFF9FE0BF)))).padding(18.dp),
            ) {
                Text("✓ ОТВЕТ", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = c.mintDeep)
                Spacer(Modifier.height(6.dp))
                Text(first?.answer ?: "…", fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 22.sp, color = Color(0xFF1F5E42))
            }

            Spacer(Modifier.height(22.dp))
            SectionLabel("💬 спроси панду", c.lavDeep, c.lavSoft)
            Spacer(Modifier.height(12.dp))
            if (s.chat.isEmpty()) {
                Text(
                    "Задай уточняющий вопрос по решению выше 🐼",
                    fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 14.sp, color = c.inkFaint,
                )
            } else {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    s.chat.forEach { turn -> Bubble(turn.text, me = turn.fromMe) }
                }
            }
            if (s.sending) {
                Spacer(Modifier.height(10.dp))
                Text("панда печатает…", fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 12.sp, color = c.lavDeep)
            }
        }

        // chat bar
        Row(
            Modifier.align(Alignment.BottomCenter).fillMaxWidth().padding(20.dp)
                .clip(RoundedCornerShape(999.dp)).background(c.card).border(2.dp, c.line, RoundedCornerShape(999.dp))
                .padding(start = 18.dp, top = 8.dp, bottom = 8.dp, end = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            BasicTextField(
                value = draft, onValueChange = { draft = it }, singleLine = true,
                cursorBrush = SolidColor(c.coralDeep),
                textStyle = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 14.sp, color = c.ink),
                modifier = Modifier.weight(1f),
                decorationBox = { inner ->
                    if (draft.isEmpty()) Text("спросить ещё…", fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 14.sp, color = c.inkFaint)
                    inner()
                },
            )
            Spacer(Modifier.width(8.dp))
            val canSend = draft.isNotBlank() && !s.sending
            Box(
                Modifier.size(40.dp).clip(CircleShape)
                    .background(Brush.linearGradient(listOf(c.coral, c.pink)))
                    .clickable(enabled = canSend) { viewModel.sendChat(taskId, draft); draft = "" },
                contentAlignment = Alignment.Center,
            ) {
                Icon(Icons.AutoMirrored.Filled.Send, null, tint = Color.White.copy(alpha = if (canSend) 1f else 0.5f), modifier = Modifier.size(17.dp))
            }
        }
    }

    if (showPicker) {
        AlbumPickerDialog(
            albums = s.albums,
            onDismiss = { showPicker = false },
            onPick = { album -> viewModel.assignAlbum(taskId, album); showPicker = false },
        )
    }
}

@Composable
private fun SectionLabel(text: String, color: Color, line: Color) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(text, fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 15.sp, color = color)
        Spacer(Modifier.width(9.dp))
        Box(Modifier.weight(1f).height(2.dp).clip(RoundedCornerShape(2.dp)).background(line))
    }
}

@Composable
private fun Step(n: Int, text: String) {
    val c = cute
    Row(Modifier.padding(top = 13.dp)) {
        Box(Modifier.size(26.dp).clip(CircleShape).background(c.mintSoft), contentAlignment = Alignment.Center) {
            Text("$n", fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 13.sp, color = c.mintDeep)
        }
        Spacer(Modifier.width(11.dp))
        Text(text, fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 13.5.sp, color = c.ink, lineHeight = 20.sp, modifier = Modifier.padding(top = 2.dp))
    }
}

@Composable
private fun Bubble(text: String, me: Boolean) {
    val c = cute
    Row(Modifier.fillMaxWidth(), horizontalArrangement = if (me) Arrangement.End else Arrangement.Start, verticalAlignment = Alignment.Bottom) {
        if (!me) { Panda(Modifier.size(28.dp)); Spacer(Modifier.width(6.dp)) }
        Box(
            Modifier.widthIn(max = 250.dp).clip(
                RoundedCornerShape(
                    topStart = 18.dp, topEnd = 18.dp,
                    bottomStart = if (me) 18.dp else 5.dp, bottomEnd = if (me) 5.dp else 18.dp,
                ),
            ).background(if (me) c.skySoft else c.card)
                .then(if (me) Modifier else Modifier.border(2.dp, c.line, RoundedCornerShape(topStart = 18.dp, topEnd = 18.dp, bottomStart = 5.dp, bottomEnd = 18.dp)))
                .padding(horizontal = 15.dp, vertical = 11.dp),
        ) {
            Text(text, fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 13.5.sp, color = if (me) c.skyDeep else c.ink, lineHeight = 19.sp)
        }
    }
}

