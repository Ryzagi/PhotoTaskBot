package com.pandasolve.app.auth

import java.io.IOException

/**
 * Coarse, localizable classification of auth failures. The ViewModel stores one
 * of these (not a raw message) so the UI can render friendly RU/EN copy.
 * [CANCELLED] (e.g. the user dismisses the Google chooser) renders nothing.
 */
enum class AuthError {
    EMPTY_FIELDS,
    INVALID_CREDENTIALS,
    USER_EXISTS,
    WEAK_PASSWORD,
    INVALID_EMAIL,
    EMAIL_NOT_CONFIRMED,
    RATE_LIMITED,
    NETWORK,
    CANCELLED,
    UNKNOWN,
}

/**
 * Map a thrown exception to an [AuthError]. supabase-kt versions differ in the
 * typed errors they expose, so we classify on the (lower-cased) message + class
 * name, which is stable across versions. Order matters — network/cancel first.
 */
fun Throwable.toAuthError(): AuthError {
    val msg = (message ?: "").lowercase()
    val name = (this::class.simpleName ?: "").lowercase()
    return when {
        this is IOException || "host" in msg || "failed to connect" in msg ||
            "timeout" in msg || "timed out" in msg || "unable to resolve" in msg -> AuthError.NETWORK
        "cancel" in msg || "cancel" in name -> AuthError.CANCELLED
        "already registered" in msg || "already been registered" in msg ||
            "user_already_exists" in msg || "already exists" in msg -> AuthError.USER_EXISTS
        "email not confirmed" in msg || "email_not_confirmed" in msg ||
            "not confirmed" in msg -> AuthError.EMAIL_NOT_CONFIRMED
        "weak_password" in msg ||
            ("password" in msg && ("least" in msg || "short" in msg || "weak" in msg)) -> AuthError.WEAK_PASSWORD
        "invalid login credentials" in msg || "invalid_credentials" in msg ||
            "invalid credentials" in msg -> AuthError.INVALID_CREDENTIALS
        "validate email" in msg || "invalid format" in msg || "invalid email" in msg ||
            "invalid_email" in msg -> AuthError.INVALID_EMAIL
        "rate limit" in msg || "only request this after" in msg ||
            "too many" in msg || "over_email_send_rate_limit" in msg -> AuthError.RATE_LIMITED
        else -> AuthError.UNKNOWN
    }
}
