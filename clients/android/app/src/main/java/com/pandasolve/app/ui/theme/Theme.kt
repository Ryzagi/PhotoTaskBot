package com.pandasolve.app.ui.theme

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

/**
 * The cute palette carries more accent families than Material's ColorScheme
 * can hold (mint/lavender/coral/butter/sky/pink), so we expose it via a
 * CompositionLocal alongside the standard theme.
 */
@Immutable
data class CutePalette(
    val paper: Color = Paper,
    val paper2: Color = Paper2,
    val card: Color = CardWhite,
    val ink: Color = Ink,
    val inkSoft: Color = InkSoft,
    val inkFaint: Color = InkFaint,
    val line: Color = LineCol,

    val mint: Color = Mint, val mintDeep: Color = MintDeep, val mintShadow: Color = MintShadow, val mintSoft: Color = MintSoft,
    val lav: Color = Lav, val lavDeep: Color = LavDeep, val lavShadow: Color = LavShadow, val lavSoft: Color = LavSoft,
    val coral: Color = Coral, val coralDeep: Color = CoralDeep, val coralShadow: Color = CoralShadow, val coralSoft: Color = CoralSoft,
    val butter: Color = Butter, val butterDeep: Color = ButterDeep, val butterShadow: Color = ButterShadow, val butterSoft: Color = ButterSoft,
    val sky: Color = Sky, val skyDeep: Color = SkyDeep, val skyShadow: Color = SkyShadow, val skySoft: Color = SkySoft,
    val pink: Color = Pink, val pinkDeep: Color = PinkDeep, val pinkSoft: Color = PinkSoft,
)

val LocalCute = staticCompositionLocalOf { CutePalette() }

/** Convenience accessor: `cute.mint` inside composables. */
val cute: CutePalette
    @Composable get() = LocalCute.current

private val CuteShapes = Shapes(
    extraSmall = RoundedCornerShape(10.dp),
    small = RoundedCornerShape(14.dp),
    medium = RoundedCornerShape(20.dp),
    large = RoundedCornerShape(28.dp),
    extraLarge = RoundedCornerShape(34.dp),
)

private val CuteColors = lightColorScheme(
    primary = MintDeep,
    onPrimary = CardWhite,
    primaryContainer = MintSoft,
    onPrimaryContainer = MintDeep,
    secondary = LavDeep,
    secondaryContainer = LavSoft,
    tertiary = CoralDeep,
    background = Paper,
    onBackground = Ink,
    surface = CardWhite,
    onSurface = Ink,
    surfaceVariant = Paper2,
    outline = LineCol,
    error = CoralDeep,
)

@Composable
fun PandaSolveTheme(content: @Composable () -> Unit) {
    androidx.compose.runtime.CompositionLocalProvider(LocalCute provides CutePalette()) {
        MaterialTheme(
            colorScheme = CuteColors,
            typography = CuteTypography,
            shapes = CuteShapes,
            content = content,
        )
    }
}
