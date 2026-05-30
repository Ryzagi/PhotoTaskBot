package com.pandasolve.app.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.ExperimentalTextApi
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.pandasolve.app.R

// Variable fonts loaded with per-weight variation settings (API 26+).
@OptIn(ExperimentalTextApi::class)
private fun baloo(weight: Int) = Font(
    R.font.baloo2,
    weight = FontWeight(weight),
    variationSettings = FontVariation.Settings(FontVariation.weight(weight)),
)
@OptIn(ExperimentalTextApi::class)
private fun nunito(weight: Int) = Font(
    R.font.nunito,
    weight = FontWeight(weight),
    variationSettings = FontVariation.Settings(FontVariation.weight(weight)),
)
@OptIn(ExperimentalTextApi::class)
private fun caveat(weight: Int) = Font(
    R.font.caveat,
    weight = FontWeight(weight),
    variationSettings = FontVariation.Settings(FontVariation.weight(weight)),
)

/** Baloo 2 — chunky rounded display. */
val Baloo = FontFamily(baloo(500), baloo(600), baloo(700), baloo(800))

/** Nunito — warm rounded body / UI. */
val Nunito = FontFamily(nunito(400), nunito(500), nunito(600), nunito(700), nunito(800))

/** Caveat — handwritten margin notes. */
val Caveat = FontFamily(caveat(500), caveat(600), caveat(700))

val CuteTypography = Typography(
    displayLarge   = TextStyle(fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 46.sp, lineHeight = 48.sp),
    displayMedium  = TextStyle(fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 36.sp, lineHeight = 38.sp),
    displaySmall   = TextStyle(fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 28.sp, lineHeight = 32.sp),
    headlineLarge  = TextStyle(fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 26.sp, lineHeight = 30.sp),
    headlineMedium = TextStyle(fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 22.sp, lineHeight = 26.sp),
    headlineSmall  = TextStyle(fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 19.sp, lineHeight = 23.sp),
    titleLarge     = TextStyle(fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 18.sp, lineHeight = 22.sp),
    titleMedium    = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 15.sp, lineHeight = 20.sp),
    titleSmall     = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 13.sp, lineHeight = 18.sp),
    bodyLarge      = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 15.sp, lineHeight = 22.sp),
    bodyMedium     = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 13.5.sp, lineHeight = 19.sp),
    bodySmall      = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 12.sp, lineHeight = 16.sp),
    labelLarge     = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 13.sp, lineHeight = 16.sp),
    labelMedium    = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, lineHeight = 14.sp),
    labelSmall     = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 9.5.sp, lineHeight = 12.sp),
)
