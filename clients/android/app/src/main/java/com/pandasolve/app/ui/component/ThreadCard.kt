package com.pandasolve.app.ui.component

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pandasolve.app.i18n.LocalStrings
import com.pandasolve.app.ui.sample.SampleThread
import com.pandasolve.app.ui.sample.TStatus
import com.pandasolve.app.ui.theme.Baloo
import com.pandasolve.app.ui.theme.Nunito
import com.pandasolve.app.ui.theme.cute

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun ThreadCard(t: SampleThread, onClick: () -> Unit, onLongClick: () -> Unit = {}) {
    val c = cute
    val s = LocalStrings.current
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .background(c.card)
            .border(2.dp, c.line, RoundedCornerShape(20.dp))
            .combinedClickable(onClick = onClick, onLongClick = onLongClick)
            .padding(11.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            Modifier.size(48.dp).clip(RoundedCornerShape(14.dp)).background(t.tint),
            contentAlignment = Alignment.Center,
        ) {
            if (t.isMath) Text(t.glyph, fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 16.sp, color = c.ink)
            else Text(t.glyph, fontSize = 22.sp)
        }
        Spacer(Modifier.width(13.dp))
        Column(Modifier.weight(1f)) {
            Text(t.preview.ifBlank { s.untitled }, fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 13.5.sp, color = c.ink,
                maxLines = 2, overflow = TextOverflow.Ellipsis, lineHeight = 17.sp)
            Spacer(Modifier.height(4.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                when (t.status) {
                    TStatus.Done -> Text("● " + s.statusSolved, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.mintDeep)
                    TStatus.Talking -> Text("◐ " + s.statusTalking, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.lavDeep)
                }
                Text("  ·  ", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.inkFaint)
                Text(t.album, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.inkSoft)
            }
        }
        Spacer(Modifier.width(8.dp))
        Text(t.stamp, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.inkFaint)
    }
}
