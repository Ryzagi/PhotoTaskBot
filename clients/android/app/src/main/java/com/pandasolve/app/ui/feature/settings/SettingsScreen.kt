package com.pandasolve.app.ui.feature.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.compose.runtime.collectAsState
import com.pandasolve.app.ui.component.CuteBottomBar
import com.pandasolve.app.ui.component.CuteTab
import com.pandasolve.app.ui.component.Panda
import com.pandasolve.app.ui.component.dotPaper
import com.pandasolve.app.ui.theme.Baloo
import com.pandasolve.app.ui.theme.Nunito
import com.pandasolve.app.ui.theme.cute

@Composable
fun ProfileScreen(
    onArchive: () -> Unit,
    onCamera: () -> Unit,
    onSignOut: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val c = cute
    val s by viewModel.state.collectAsState()
    LaunchedEffect(Unit) { viewModel.refresh() }
    Box(Modifier.fillMaxSize().dotPaper(c.paper, c.ink.copy(alpha = 0.07f))) {
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp).padding(top = 14.dp, bottom = 110.dp),
        ) {
            Text("Профиль", fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 24.sp, color = c.ink)

            Spacer(Modifier.height(12.dp))
            // hero
            Row(
                Modifier.fillMaxWidth().clip(RoundedCornerShape(28.dp))
                    .background(Brush.linearGradient(listOf(c.lavSoft, Color.White)))
                    .border(2.dp, c.lav, RoundedCornerShape(28.dp)).padding(16.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Panda(Modifier.size(60.dp).clip(CircleShape).background(Color.White))
                Spacer(Modifier.width(14.dp))
                Column(Modifier.weight(1f)) {
                    Text(s.name, fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 21.sp, color = c.ink)
                    Text(s.email, fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 11.sp, color = c.inkSoft)
                }
                if (s.telegramLinked) Box(Modifier.clip(RoundedCornerShape(999.dp)).background(c.mintSoft).padding(horizontal = 10.dp, vertical = 4.dp)) {
                    Text("тг ✓", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.mintDeep)
                }
            }

            Spacer(Modifier.height(14.dp))
            // stats
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Stat("${s.streak}", "дней стрик", c.butterDeep, Modifier.weight(1f))
                Stat("${s.solved}", "решено", c.mintDeep, Modifier.weight(1f))
                Stat("${s.albums}", "альбомов", c.lavDeep, Modifier.weight(1f))
            }

            Spacer(Modifier.height(16.dp))
            Text("Достижения 🏆", fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 14.sp, color = c.ink)
            Spacer(Modifier.height(9.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                Badge("🌱", c.mintSoft, false); Badge("🔥", c.butterSoft, false); Badge("💯", c.coralSoft, false)
                Badge("🦉", c.paper2, true); Badge("🎓", c.paper2, true)
            }

            Spacer(Modifier.height(18.dp))
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row2("🎋", c.mintSoft, "Пополнить бамбук", "5 ⭐ = 1 решение", "телеграм →", c.inkSoft)
                Row2("✈️", c.skySoft, "Telegram", "@vladislavrzhv", "привязан", c.mintDeep)
                Row2("🌍", c.lavSoft, "Язык", null, "русский", c.inkSoft)
                Row2("🔔", c.butterSoft, "Уведомления", "2 типа включено", "→", c.inkSoft)
                Row2("👋", c.coralSoft, "Выйти", null, "→", c.coralDeep, danger = true, onClick = { viewModel.signOut(onSignOut) })
            }
        }

        CuteBottomBar(CuteTab.Profile, onArchive = onArchive, onCamera = onCamera, onProfile = {}, modifier = Modifier.align(Alignment.BottomCenter))
    }
}

@Composable
private fun Stat(v: String, k: String, color: Color, modifier: Modifier) {
    val c = cute
    Column(
        modifier.clip(RoundedCornerShape(20.dp)).background(c.card).border(2.dp, c.line, RoundedCornerShape(20.dp)).padding(vertical = 12.dp, horizontal = 8.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(v, fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 26.sp, color = color)
        Spacer(Modifier.height(5.dp))
        Text(k.uppercase(), fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 9.sp, color = c.inkFaint)
    }
}

@Composable
private fun Badge(emoji: String, bg: Color, locked: Boolean) {
    Box(
        Modifier.size(52.dp).clip(RoundedCornerShape(16.dp)).background(bg),
        contentAlignment = Alignment.Center,
    ) { Text(emoji, fontSize = 24.sp, color = if (locked) Color.Black.copy(alpha = 0.25f) else Color.Unspecified) }
}

@Composable
private fun Row2(emoji: String, iconBg: Color, label: String, hint: String?, trail: String, trailColor: Color, danger: Boolean = false, onClick: () -> Unit = {}) {
    val c = cute
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp)).background(c.card)
            .border(2.dp, c.line, RoundedCornerShape(20.dp)).clickable(onClick = onClick).padding(horizontal = 14.dp, vertical = 11.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(Modifier.size(34.dp).clip(RoundedCornerShape(12.dp)).background(iconBg), contentAlignment = Alignment.Center) { Text(emoji, fontSize = 16.sp) }
        Spacer(Modifier.width(13.dp))
        Column(Modifier.weight(1f)) {
            Text(label, fontFamily = Baloo, fontWeight = FontWeight.W600, fontSize = 14.sp, color = if (danger) c.coralDeep else c.ink)
            if (hint != null) Text(hint.uppercase(), fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 10.sp, color = c.inkFaint)
        }
        Text(trail, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = trailColor)
    }
}
