package com.pandasolve.app.util

import java.time.Duration
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.ZoneOffset

/** Parse a server ISO-8601 timestamp to an offset-aware instant (falls back to
 *  treating a naive timestamp as UTC). Null if it can't be parsed. */
private fun parse(iso: String): OffsetDateTime? =
    runCatching { OffsetDateTime.parse(iso) }
        .recoverCatching { LocalDateTime.parse(iso).atOffset(ZoneOffset.UTC) }
        .getOrNull()

/**
 * Convert a server ISO-8601 timestamp (UTC) to the device-local calendar date as
 * "yyyy-MM-dd". Tasks are grouped/labelled by this, so it must reflect the user's
 * local clock, not UTC. Falls back to the raw date prefix if unparseable.
 */
fun localDateOf(iso: String): String =
    parse(iso)?.atZoneSameInstant(ZoneId.systemDefault())?.toLocalDate()?.toString()
        ?: iso.take(10)

/** Device-local time of day as "HH:mm" (e.g. "09:42"), or "" if unparseable. */
fun localTimeOf(iso: String): String {
    val t = parse(iso)?.atZoneSameInstant(ZoneId.systemDefault())?.toLocalTime() ?: return ""
    return "%02d:%02d".format(t.hour, t.minute)
}

/** Whole seconds between two ISO timestamps (solve duration), or null. */
fun solveSeconds(startIso: String, endIso: String): Long? {
    val a = parse(startIso) ?: return null
    val b = parse(endIso) ?: return null
    return Duration.between(a, b).seconds.takeIf { it in 0..86_400 }
}
