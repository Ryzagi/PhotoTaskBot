package com.pandasolve.app.ui.component

import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PhotoCamera
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.foundation.Canvas
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pandasolve.app.R
import com.pandasolve.app.i18n.LocalStrings
import com.pandasolve.app.ui.theme.Baloo
import com.pandasolve.app.ui.theme.Nunito
import com.pandasolve.app.ui.theme.cute

/** The blushing panda mascot. */
@Composable
fun Panda(modifier: Modifier = Modifier) {
    Image(painter = painterResource(R.drawable.ic_panda), contentDescription = "Панда", modifier = modifier)
}

/** Warm cream background with a faint notebook dot-grid. */
fun Modifier.dotPaper(paper: Color, dot: Color): Modifier = this.drawBehind {
    drawRect(paper)
    val step = 22.dp.toPx()
    val r = 1.4.dp.toPx()
    var y = step / 2
    while (y < size.height) {
        var x = step / 2
        while (x < size.width) {
            drawCircle(dot, r, Offset(x, y))
            x += step
        }
        y += step
    }
}

enum class Candy { Mint, Coral, Lav, Ghost }

/** Jelly candy button with a pressable bottom shadow. */
@Composable
fun CandyButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    variant: Candy = Candy.Mint,
    enabled: Boolean = true,
) {
    val c = cute
    val (face, label, shadow) = when (variant) {
        Candy.Mint  -> Triple(c.mint, c.mintDeep, c.mintShadow)
        Candy.Coral -> Triple(c.coral, c.coralDeep, c.coralShadow)
        Candy.Lav   -> Triple(c.lav, c.lavDeep, c.lavShadow)
        Candy.Ghost -> Triple(c.card, c.ink, c.line)
    }
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val depth = 5.dp
    val drop by animateDpAsState(if (pressed && enabled) 2.dp else depth, label = "candy")
    val shape = RoundedCornerShape(18.dp)

    Box(
        modifier
            .clip(shape)
            .background(shadow.copy(alpha = if (variant == Candy.Ghost) 0.9f else 1f))
    ) {
        Box(
            Modifier
                .fillMaxWidth()
                .padding(bottom = drop)
                .clip(shape)
                .background(face)
                .clickable(
                    interactionSource = interaction,
                    indication = null,
                    enabled = enabled,
                    onClick = onClick,
                )
                .padding(vertical = 15.dp, horizontal = 18.dp),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text,
                color = label,
                fontFamily = Baloo,
                fontWeight = FontWeight.W700,
                fontSize = 17.sp,
                textAlign = TextAlign.Center,
            )
        }
    }
}

/** The raised camera shutter that anchors the bottom bar. */
@Composable
fun ShutterButton(onClick: () -> Unit, modifier: Modifier = Modifier) {
    val c = cute
    Box(
        modifier
            .size(70.dp)
            .clip(CircleShape)
            .background(Brush.linearGradient(listOf(c.mint, c.sky)))
            .clickable(onClick = onClick)
            .drawBehind {
                // dashed inner ring
                drawCircle(
                    color = Color.White.copy(alpha = 0.75f),
                    radius = size.minDimension / 2 - 9.dp.toPx(),
                    style = Stroke(
                        width = 2.dp.toPx(),
                        pathEffect = PathEffect.dashPathEffect(floatArrayOf(6f, 7f)),
                    ),
                )
            },
        contentAlignment = Alignment.Center,
    ) {
        Icon(Icons.Filled.PhotoCamera, contentDescription = "Снять задачу", tint = Color.White, modifier = Modifier.size(30.dp))
    }
}

enum class CuteTab { Home, Profile, None }

/** Bottom navigation: home · raised shutter · profile. */
@Composable
fun CuteBottomBar(
    active: CuteTab,
    onHome: () -> Unit,
    onCamera: () -> Unit,
    onProfile: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val c = cute
    val t = LocalStrings.current
    Box(
        modifier
            .fillMaxWidth()
            .navigationBarsPadding()
            .height(92.dp)
            .background(Brush.verticalGradient(0f to Color.Transparent, 0.4f to c.paper, 1f to c.paper)),
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .align(Alignment.BottomCenter)
                .padding(start = 38.dp, end = 38.dp, bottom = 14.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.Bottom,
        ) {
            NavSide(t.navHome, active == CuteTab.Home, c.mintDeep, c.mintSoft, c.inkFaint, onHome) {
                HouseGlyph(
                    color = if (active == CuteTab.Home) c.mintDeep else c.inkFaint,
                    door = if (active == CuteTab.Home) c.mintSoft else c.paper,
                )
            }
            Spacer(Modifier.width(78.dp))
            NavSideAvatar(t.navProfile, active == CuteTab.Profile, c.mintDeep, c.mintSoft, c.inkFaint, onProfile)
        }
        // raised shutter
        Box(Modifier.align(Alignment.TopCenter).offset(y = 6.dp)) {
            ShutterButton(onClick = onCamera)
        }
    }
}

/** Hand-drawn doodle house (replaces the platform 🏠 emoji — consistent on every device). */
@Composable
private fun HouseGlyph(color: Color, door: Color, modifier: Modifier = Modifier) {
    Canvas(modifier.size(22.dp)) {
        val w = size.width
        val h = size.height
        // roof — chunky triangle with a flat top-cut, like a marker doodle
        val roof = Path().apply {
            moveTo(w * 0.50f, h * 0.02f)
            lineTo(w * 0.98f, h * 0.46f)
            lineTo(w * 0.02f, h * 0.46f)
            close()
        }
        drawPath(roof, color)
        // body
        drawRoundRect(
            color = color,
            topLeft = Offset(w * 0.14f, h * 0.42f),
            size = androidx.compose.ui.geometry.Size(w * 0.72f, h * 0.54f),
            cornerRadius = CornerRadius(w * 0.14f, w * 0.14f),
        )
        // door (paper cut-out)
        drawRoundRect(
            color = door,
            topLeft = Offset(w * 0.40f, h * 0.60f),
            size = androidx.compose.ui.geometry.Size(w * 0.20f, h * 0.36f),
            cornerRadius = CornerRadius(w * 0.08f, w * 0.08f),
        )
    }
}

@Composable
private fun NavSide(
    label: String,
    activeState: Boolean,
    activeColor: Color,
    activeBg: Color,
    idleColor: Color,
    onClick: () -> Unit,
    icon: @Composable () -> Unit,
) {
    val color = if (activeState) activeColor else idleColor
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.clickable(onClick = onClick)) {
        Box(
            Modifier.size(44.dp)
                .rotate(if (activeState) -5f else 0f)   // active tab = tilted sticker
                .clip(RoundedCornerShape(16.dp))
                .background(if (activeState) activeBg else Color.Transparent)
                .then(if (activeState) Modifier.border(2.dp, activeColor.copy(alpha = 0.45f), RoundedCornerShape(16.dp)) else Modifier),
            contentAlignment = Alignment.Center,
        ) { icon() }
        Spacer(Modifier.height(3.dp))
        Text(label.uppercase(), color = color, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, maxLines = 1, softWrap = false)
    }
}

@Composable
private fun NavSideAvatar(
    label: String,
    activeState: Boolean,
    activeColor: Color,
    activeBg: Color,
    idleColor: Color,
    onClick: () -> Unit,
) {
    val color = if (activeState) activeColor else idleColor
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.clickable(onClick = onClick)) {
        Box(
            Modifier.size(44.dp)
                .rotate(if (activeState) 5f else 0f)    // mirrored tilt on the right tab
                .clip(RoundedCornerShape(16.dp))
                .background(if (activeState) activeBg else Color.Transparent)
                .then(if (activeState) Modifier.border(2.dp, activeColor.copy(alpha = 0.45f), RoundedCornerShape(16.dp)) else Modifier),
            contentAlignment = Alignment.Center,
        ) {
            Panda(Modifier.size(30.dp).clip(CircleShape).background(Color.White))
        }
        Spacer(Modifier.height(3.dp))
        Text(label.uppercase(), color = color, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, maxLines = 1, softWrap = false)
    }
}
