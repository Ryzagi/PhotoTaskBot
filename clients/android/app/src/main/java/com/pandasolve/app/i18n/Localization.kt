package com.pandasolve.app.i18n

import androidx.compose.runtime.staticCompositionLocalOf

/**
 * Lightweight in-app localization. The app's copy is provided through
 * [LocalStrings] so a language toggle can flip it without Activity recreation.
 *
 * Migrate a screen by reading `val t = LocalStrings.current` and using `t.*`
 * instead of hardcoded literals. RU is the default/source language.
 */
data class Strings(
    // nav
    val navArchive: String,
    val navProfile: String,
    // home
    val welcomeBack: String,
    val bambooToday: String,
    val solutions: String,
    val donate: String,
    val recent: String,
    val all: String,
    val daysShort: String,
    // profile
    val profileTitle: String,
    val linkedTag: String,
    val statStreak: String,
    val statSolved: String,
    val statAlbums: String,
    val achievements: String,
    val rowTopUp: String,
    val rowTopUpHint: String,
    val rowTopUpTrail: String,
    val rowTelegram: String,
    val rowTelegramLinked: String,
    val rowTelegramUnlinked: String,
    val rowLanguage: String,
    val rowNotifications: String,
    val rowNotificationsHint: String,
    val rowSignOut: String,
    val languageNameRu: String,
    val languageNameEn: String,
)

val RuStrings = Strings(
    navArchive = "архив",
    navProfile = "профиль",
    welcomeBack = "с возвращением,",
    bambooToday = "БАМБУК НА СЕГОДНЯ",
    solutions = "решения",
    donate = "донат",
    recent = "Недавние беседы",
    all = "все →",
    daysShort = "дн.",
    profileTitle = "Профиль",
    linkedTag = "тг ✓",
    statStreak = "дней стрик",
    statSolved = "решено",
    statAlbums = "альбомов",
    achievements = "Достижения 🏆",
    rowTopUp = "Пополнить бамбук",
    rowTopUpHint = "5 ⭐ = 1 решение",
    rowTopUpTrail = "телеграм →",
    rowTelegram = "Telegram",
    rowTelegramLinked = "привязан",
    rowTelegramUnlinked = "привязать →",
    rowLanguage = "Язык",
    rowNotifications = "Уведомления",
    rowNotificationsHint = "2 типа включено",
    rowSignOut = "Выйти",
    languageNameRu = "русский",
    languageNameEn = "english",
)

val EnStrings = Strings(
    navArchive = "archive",
    navProfile = "profile",
    welcomeBack = "welcome back,",
    bambooToday = "BAMBOO FOR TODAY",
    solutions = "solutions",
    donate = "donate",
    recent = "Recent threads",
    all = "all →",
    daysShort = "d.",
    profileTitle = "Profile",
    linkedTag = "tg ✓",
    statStreak = "day streak",
    statSolved = "solved",
    statAlbums = "albums",
    achievements = "Achievements 🏆",
    rowTopUp = "Top up bamboo",
    rowTopUpHint = "5 ⭐ = 1 solution",
    rowTopUpTrail = "telegram →",
    rowTelegram = "Telegram",
    rowTelegramLinked = "linked",
    rowTelegramUnlinked = "link →",
    rowLanguage = "Language",
    rowNotifications = "Notifications",
    rowNotificationsHint = "2 types enabled",
    rowSignOut = "Sign out",
    languageNameRu = "русский",
    languageNameEn = "english",
)

/** Map a backend `language_code` (e.g. "ru", "en", "en-US") to a string table. */
fun stringsFor(languageCode: String): Strings =
    if (languageCode.lowercase().startsWith("en")) EnStrings else RuStrings

val LocalStrings = staticCompositionLocalOf { RuStrings }
