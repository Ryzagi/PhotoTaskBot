package com.pandasolve.app.util

import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.ZoneOffset

/**
 * Convert a server ISO-8601 timestamp (UTC, e.g. "2026-06-09T22:30:00+00:00" or
 * "…Z") to the device-local calendar date as "yyyy-MM-dd".
 *
 * Tasks are grouped and labelled (Today / Yesterday / date) by this string, so
 * the day a task lands in must reflect the user's local clock, not UTC — a solve
 * at 01:00 local belongs to "today", even though it's still "yesterday" in UTC.
 * Falls back gracefully if the string has no offset or can't be parsed.
 */
fun localDateOf(iso: String): String = runCatching {
    OffsetDateTime.parse(iso)
        .atZoneSameInstant(ZoneId.systemDefault())
        .toLocalDate()
        .toString()
}.recoverCatching {
    // No timezone in the string → treat the wall-clock time as UTC.
    LocalDateTime.parse(iso)
        .atOffset(ZoneOffset.UTC)
        .atZoneSameInstant(ZoneId.systemDefault())
        .toLocalDate()
        .toString()
}.getOrElse { iso.take(10) }
