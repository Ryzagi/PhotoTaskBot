package com.pandasolve.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.darkColorScheme
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

/**
 * Night edition: the same study notebook after midnight, under a warm desk lamp.
 * Espresso paper instead of cream, milky ink, and the pastel families become
 * "glow stickers" — Soft surfaces turn into deep tinted darks, Deep text colors
 * flip to bright pastels so contrast holds on the dark Softs.
 */
private val DarkCute = CutePalette(
    paper = Color(0xFF231C15),
    paper2 = Color(0xFF2C241B),
    card = Color(0xFF322A20),
    ink = Color(0xFFF2E7D6),
    inkSoft = Color(0xFFBCA98E),
    inkFaint = Color(0xFF7C6D58),
    line = Color(0xFF463B2D),

    mint = Color(0xFF63C495), mintDeep = Color(0xFFB7EBD2), mintShadow = Color(0xFF2F7D5B), mintSoft = Color(0xFF223A2E),
    lav = Color(0xFF9D8BE0), lavDeep = Color(0xFFD6CBFB), lavShadow = Color(0xFF6C57BC), lavSoft = Color(0xFF2E2842),
    coral = Color(0xFFF08A73), coralDeep = Color(0xFFFFC2B1), coralShadow = Color(0xFFBF5A41), coralSoft = Color(0xFF40291F),
    butter = Color(0xFFE9BC4F), butterDeep = Color(0xFFF7DD9B), butterShadow = Color(0xFFB98F2C), butterSoft = Color(0xFF3D331C),
    sky = Color(0xFF6FB4DE), skyDeep = Color(0xFFBCE0F7), skyShadow = Color(0xFF3E7FAB), skySoft = Color(0xFF20313D),
    pink = Color(0xFFE783AC), pinkDeep = Color(0xFFF9C2D8), pinkSoft = Color(0xFF3C2530),
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
fun PandaSolveTheme(dark: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    val palette = if (dark) DarkCute else CutePalette()
    val scheme = if (dark) {
        darkColorScheme(
            primary = palette.mint,
            onPrimary = palette.paper,
            primaryContainer = palette.mintSoft,
            onPrimaryContainer = palette.mintDeep,
            secondary = palette.lavDeep,
            secondaryContainer = palette.lavSoft,
            tertiary = palette.coralDeep,
            background = palette.paper,
            onBackground = palette.ink,
            surface = palette.card,
            onSurface = palette.ink,
            surfaceVariant = palette.paper2,
            outline = palette.line,
            error = palette.coralDeep,
        )
    } else CuteColors
    androidx.compose.runtime.CompositionLocalProvider(LocalCute provides palette) {
        MaterialTheme(
            colorScheme = scheme,
            typography = CuteTypography,
            shapes = CuteShapes,
            content = content,
        )
    }
}
