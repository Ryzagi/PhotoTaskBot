package com.pandasolve.app.ui.feature.settings

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
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
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
import androidx.compose.ui.unit.DpOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.window.Dialog
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.compose.runtime.collectAsState
import com.pandasolve.app.i18n.EnStrings
import com.pandasolve.app.i18n.LocalStrings
import com.pandasolve.app.i18n.supportedLanguages
import com.pandasolve.app.ui.component.Candy
import com.pandasolve.app.ui.component.CandyButton
import com.pandasolve.app.ui.component.CuteBottomBar
import com.pandasolve.app.ui.component.CuteTab
import com.pandasolve.app.ui.component.Panda
import com.pandasolve.app.ui.component.dotPaper
import com.pandasolve.app.ui.theme.Baloo
import com.pandasolve.app.ui.theme.Nunito
import com.pandasolve.app.ui.theme.cute

@Composable
fun ProfileScreen(
    onHome: () -> Unit,
    onCamera: () -> Unit,
    onSignOut: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val c = cute
    val t = LocalStrings.current
    val s by viewModel.state.collectAsState()
    var showRename by remember { mutableStateOf(false) }
    var showTopUp by remember { mutableStateOf(false) }
    var selAch by remember { mutableStateOf<Ach?>(null) }
    var showAllAch by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { viewModel.refresh() }
    Box(Modifier.fillMaxSize().dotPaper(c.paper, c.ink.copy(alpha = 0.07f))) {
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp).padding(top = 14.dp, bottom = 96.dp),
        ) {
            Text(t.profileTitle, fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 24.sp, color = c.ink)

            Spacer(Modifier.height(12.dp))
            // hero
            Row(
                Modifier.fillMaxWidth().clip(RoundedCornerShape(28.dp))
                    .background(Brush.linearGradient(listOf(c.lavSoft, c.card)))
                    .border(2.dp, c.lav, RoundedCornerShape(28.dp)).padding(16.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Panda(Modifier.size(60.dp).clip(CircleShape).background(Color.White))
                Spacer(Modifier.width(14.dp))
                Column(Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(s.name, fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 21.sp, color = c.ink)
                        Spacer(Modifier.width(6.dp))
                        Text("✏️", fontSize = 14.sp, modifier = Modifier.clip(CircleShape).clickable { showRename = true }.padding(2.dp))
                    }
                    Text(s.email, fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 11.sp, color = c.inkSoft)
                }
                if (s.telegramLinked) Box(Modifier.clip(RoundedCornerShape(999.dp)).background(c.mintSoft).padding(horizontal = 10.dp, vertical = 4.dp)) {
                    Text(t.linkedTag, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.mintDeep)
                }
            }

            Spacer(Modifier.height(14.dp))
            // stats
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Stat("${s.streak}", t.statStreak, c.butterDeep, Modifier.weight(1f))
                Stat("${s.solved}", t.statSolved, c.mintDeep, Modifier.weight(1f))
                Stat("${s.albums}", t.statAlbums, c.lavDeep, Modifier.weight(1f))
            }

            Spacer(Modifier.height(16.dp))
            val isEn = t == EnStrings
            val achs = achievementsFor(c, s.solved, s.streak, s.albums, isEn)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Text(t.achievements, fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 14.sp, color = c.ink)
                Text(t.all, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 12.sp, color = c.lavDeep,
                    modifier = Modifier.clip(RoundedCornerShape(8.dp)).clickable { showAllAch = true }.padding(4.dp))
            }
            Spacer(Modifier.height(9.dp))
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                achs.forEach { a ->
                    Badge(a.emoji, if (a.cur >= a.target) a.bg else c.paper2, locked = a.cur < a.target) { selAch = a }
                }
            }

            Spacer(Modifier.height(18.dp))
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row2("🎋", c.mintSoft, t.rowTopUp, t.rowTopUpHint, t.rowTopUpTrail, c.inkSoft, onClick = { showTopUp = true })
                // Telegram linking hidden for now (R4-5) — re-enable when the link flow ships.
                // Row2("✈️", c.skySoft, t.rowTelegram, null,
                //     if (s.telegramLinked) t.rowTelegramLinked else t.rowTelegramUnlinked,
                //     if (s.telegramLinked) c.mintDeep else c.inkSoft)
                Box {
                    var langMenu by remember { mutableStateOf(false) }
                    Row2("🌍", c.lavSoft, t.rowLanguage, null,
                        supportedLanguages.firstOrNull { it.code == s.language }?.label ?: s.language,
                        c.lavDeep, onClick = { langMenu = true })
                    DropdownMenu(expanded = langMenu, onDismissRequest = { langMenu = false }, offset = DpOffset(170.dp, 0.dp)) {
                        supportedLanguages.forEach { opt ->
                            DropdownMenuItem(
                                text = { Text(opt.label) },
                                onClick = { viewModel.setLanguage(opt.code); langMenu = false },
                            )
                        }
                    }
                }
                Box {
                    var themeMenu by remember { mutableStateOf(false) }
                    val themeLabel = when (s.theme) {
                        "light" -> t.themeLight; "dark" -> t.themeDark; else -> t.themeSystem
                    }
                    Row2("🌗", c.skySoft, t.rowTheme, null, themeLabel, c.skyDeep, onClick = { themeMenu = true })
                    DropdownMenu(expanded = themeMenu, onDismissRequest = { themeMenu = false }, offset = DpOffset(170.dp, 0.dp)) {
                        listOf("system" to t.themeSystem, "light" to t.themeLight, "dark" to t.themeDark).forEach { (mode, lbl) ->
                            DropdownMenuItem(text = { Text(lbl) }, onClick = { viewModel.setTheme(mode); themeMenu = false })
                        }
                    }
                }
                // solve vs explain — in Explain mode the answer is hidden until tapped
                Box {
                    var modeMenu by remember { mutableStateOf(false) }
                    val modeLabel = if (s.solveMode == "explain") t.solveModeExplain else t.solveModeSolve
                    Row2("🧠", c.mintSoft, t.rowSolveMode, null, modeLabel, c.mintDeep, onClick = { modeMenu = true })
                    DropdownMenu(expanded = modeMenu, onDismissRequest = { modeMenu = false }, offset = DpOffset(170.dp, 0.dp)) {
                        listOf("solve" to t.solveModeSolve, "explain" to t.solveModeExplain).forEach { (mode, lbl) ->
                            DropdownMenuItem(text = { Text(lbl) }, onClick = { viewModel.setSolveMode(mode); modeMenu = false })
                        }
                    }
                }
                // notifications toggle
                Row(
                    Modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp)).background(c.card)
                        .border(2.dp, c.line, RoundedCornerShape(20.dp)).padding(start = 14.dp, end = 8.dp, top = 4.dp, bottom = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Box(Modifier.size(34.dp).clip(RoundedCornerShape(12.dp)).background(c.butterSoft), contentAlignment = Alignment.Center) { Text("🔔", fontSize = 16.sp) }
                    Spacer(Modifier.width(13.dp))
                    Column(Modifier.weight(1f)) {
                        Text(t.notifications, fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 14.sp, color = c.ink)
                        Text(t.notificationsHint.uppercase(), fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 10.sp, color = c.inkFaint)
                    }
                    Switch(checked = s.notifEnabled, onCheckedChange = { viewModel.setNotifications(it) })
                }
                Row2("👋", c.coralSoft, t.rowSignOut, null, "→", c.coralDeep, danger = true, onClick = { viewModel.signOut(onSignOut) })
            }
        }

        CuteBottomBar(CuteTab.Profile, onHome = onHome, onCamera = onCamera, onProfile = {}, modifier = Modifier.align(Alignment.BottomCenter))
    }

    if (showTopUp) {
        com.pandasolve.app.ui.feature.billing.TopUpSheet(
            onDismiss = { showTopUp = false },
            onPurchased = { viewModel.refresh() },
        )
    }

    // Achievement detail: description + progress + top-up CTA (R4-6).
    selAch?.let { a ->
        Dialog(onDismissRequest = { selAch = null }) {
            Column(
                Modifier.clip(RoundedCornerShape(24.dp)).background(c.paper).padding(22.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Text(a.emoji, fontSize = 44.sp)
                Spacer(Modifier.height(8.dp))
                Text(a.title, fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 18.sp, color = c.ink)
                Spacer(Modifier.height(4.dp))
                Text(a.desc, fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 13.sp, color = c.inkSoft)
                Spacer(Modifier.height(10.dp))
                Text("${a.cur.coerceAtMost(a.target)} / ${a.target}", fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 16.sp, color = c.mintDeep)
                Spacer(Modifier.height(16.dp))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    CandyButton(t.cancel, { selAch = null }, Modifier.weight(1f), Candy.Ghost)
                    CandyButton("🎋 " + t.chatTopUp, { selAch = null; showTopUp = true }, Modifier.weight(1f), Candy.Mint)
                }
            }
        }
    }

    // Full achievements gallery (R-add): all of them with progress, tap → detail.
    if (showAllAch) {
        AchievementsSheet(
            achs = achievementsFor(c, s.solved, s.streak, s.albums, t == EnStrings),
            onPick = { selAch = it; showAllAch = false },
            onDismiss = { showAllAch = false },
        )
    }

    if (showRename) {
        var name by remember { mutableStateOf(s.name) }
        Dialog(onDismissRequest = { showRename = false }) {
            Column(Modifier.clip(RoundedCornerShape(24.dp)).background(c.paper).padding(22.dp)) {
                Text(t.taskRename, fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 18.sp, color = c.ink)
                Spacer(Modifier.height(12.dp))
                Box(
                    Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(c.card)
                        .border(2.dp, c.mint, RoundedCornerShape(16.dp)).padding(horizontal = 14.dp, vertical = 12.dp),
                ) {
                    BasicTextField(
                        value = name, onValueChange = { name = it }, singleLine = true,
                        cursorBrush = SolidColor(c.mintDeep),
                        textStyle = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 15.sp, color = c.ink),
                    )
                }
                Spacer(Modifier.height(16.dp))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    CandyButton(t.cancel, { showRename = false }, Modifier.weight(1f), Candy.Ghost)
                    CandyButton(t.save, { viewModel.setName(name); showRename = false }, Modifier.weight(1f), Candy.Mint, enabled = name.isNotBlank())
                }
            }
        }
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
        Text(k.uppercase(), fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.inkSoft)
    }
}

private data class Ach(
    val emoji: String, val bg: Color, val title: String, val desc: String, val cur: Int, val target: Int,
)

/** The achievement catalog, scored against the user's real stats. Add rows here. */
private fun achievementsFor(
    c: com.pandasolve.app.ui.theme.CutePalette,
    solved: Int, streak: Int, albums: Int, en: Boolean,
): List<Ach> = listOf(
    Ach("🌱", c.mintSoft, if (en) "First solve" else "Первое решение",
        if (en) "Solve your first task" else "Реши свою первую задачу", solved, 1),
    Ach("🔥", c.butterSoft, if (en) "3-day streak" else "Серия 3 дня",
        if (en) "Solve 3 days in a row" else "Решай 3 дня подряд", streak, 3),
    Ach("✏️", c.coralSoft, if (en) "10 solutions" else "10 решений",
        if (en) "Solve 10 tasks" else "Реши 10 задач", solved, 10),
    Ach("🦉", c.skySoft, if (en) "25 solutions" else "25 решений",
        if (en) "Solve 25 tasks" else "Реши 25 задач", solved, 25),
    Ach("🎓", c.lavSoft, if (en) "3 folders" else "3 папки",
        if (en) "Create 3 folders" else "Создай 3 папки", albums, 3),
    Ach("📚", c.mintSoft, if (en) "5 folders" else "5 папок",
        if (en) "Create 5 folders" else "Создай 5 папок", albums, 5),
    Ach("📅", c.butterSoft, if (en) "Week streak" else "Серия 7 дней",
        if (en) "Solve 7 days in a row" else "Решай 7 дней подряд", streak, 7),
    Ach("💯", c.coralSoft, if (en) "100 solutions" else "100 решений",
        if (en) "Solve 100 tasks" else "Реши 100 задач", solved, 100),
    Ach("🌟", c.skySoft, if (en) "Month streak" else "Серия 30 дней",
        if (en) "Solve 30 days in a row" else "Решай 30 дней подряд", streak, 30),
    Ach("🏆", c.lavSoft, if (en) "500 solutions" else "500 решений",
        if (en) "Solve 500 tasks" else "Реши 500 задач", solved, 500),
)

/** Full-gallery dialog: every achievement as a row with progress; tap → detail. */
@Composable
private fun AchievementsSheet(achs: List<Ach>, onPick: (Ach) -> Unit, onDismiss: () -> Unit) {
    val c = cute
    val t = LocalStrings.current
    Dialog(onDismissRequest = onDismiss) {
        Column(Modifier.clip(RoundedCornerShape(28.dp)).background(c.paper).padding(20.dp).heightIn(max = 540.dp)) {
            Text(t.achievements, fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 20.sp, color = c.ink)
            Spacer(Modifier.height(2.dp))
            Text("${achs.count { it.cur >= it.target }} / ${achs.size}",
                fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 12.sp, color = c.mintDeep)
            Spacer(Modifier.height(14.dp))
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                achs.forEach { a ->
                    val done = a.cur >= a.target
                    Row(
                        Modifier.fillMaxWidth().clip(RoundedCornerShape(18.dp)).background(c.card)
                            .border(2.dp, c.line, RoundedCornerShape(18.dp)).clickable { onPick(a) }.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Box(Modifier.size(44.dp).clip(RoundedCornerShape(14.dp)).background(if (done) a.bg else c.paper2), contentAlignment = Alignment.Center) {
                            Text(a.emoji, fontSize = 22.sp, color = if (done) Color.Unspecified else Color.Black.copy(alpha = 0.25f))
                        }
                        Spacer(Modifier.width(12.dp))
                        Column(Modifier.weight(1f)) {
                            Text(a.title, fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 14.sp, color = c.ink)
                            Text(a.desc, fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 11.sp, color = c.inkSoft, maxLines = 1)
                        }
                        Spacer(Modifier.width(8.dp))
                        Text("${a.cur.coerceAtMost(a.target)}/${a.target}",
                            fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 12.sp, color = if (done) c.mintDeep else c.inkFaint)
                    }
                }
            }
        }
    }
}

@Composable
private fun Badge(emoji: String, bg: Color, locked: Boolean, onClick: () -> Unit = {}) {
    Box(
        Modifier.size(52.dp).clip(RoundedCornerShape(16.dp)).background(bg).clickable(onClick = onClick),
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
            Text(label, fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 14.sp, color = if (danger) c.coralDeep else c.ink)
            if (hint != null) Text(hint.uppercase(), fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 10.sp, color = c.inkFaint)
        }
        Text(trail, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = trailColor)
    }
}
