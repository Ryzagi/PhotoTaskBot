package com.pandasolve.app.auth

import android.content.Context
import androidx.credentials.CredentialManager
import androidx.credentials.GetCredentialRequest
import androidx.credentials.exceptions.NoCredentialException
import com.google.android.libraries.identity.googleid.GetGoogleIdOption
import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential
import com.pandasolve.app.BuildConfig
import dagger.hilt.android.qualifiers.ApplicationContext
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.createSupabaseClient
// supabase-kt 2.6.1 ships the auth module under the `gotrue` package even
// though the plugin class is now called `Auth` and the extension on the
// client is `client.auth`.
import io.github.jan.supabase.gotrue.Auth
import io.github.jan.supabase.gotrue.auth
import io.github.jan.supabase.gotrue.providers.Apple
import io.github.jan.supabase.gotrue.providers.Google
import io.github.jan.supabase.gotrue.providers.builtin.Email
import io.github.jan.supabase.gotrue.providers.builtin.IDToken
import java.security.MessageDigest
import java.security.SecureRandom
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Supabase Auth bridge.
 *
 * - Email / password: direct Supabase call.
 * - Google: Credential Manager → Google ID Token → Supabase IDToken provider.
 *   This stays fully in-app (one-tap) on Android 14+ devices that have a
 *   Google account configured.
 * - Apple: Supabase OAuth web flow (no native Apple SDK on Android). Opens
 *   in a Custom Tab; the redirect URI configured in Supabase points back to
 *   `com.pandasolve.app://login-callback` (declared in AndroidManifest.xml).
 *
 * Uses supabase-kt 2.x where the auth module is `gotrue-kt`; the public
 * extension is `client.auth`.
 */
@Singleton
class SupabaseAuth @Inject constructor(
    @ApplicationContext private val ctx: Context,
) {
    val client: SupabaseClient = createSupabaseClient(
        supabaseUrl = BuildConfig.SUPABASE_URL,
        supabaseKey = BuildConfig.SUPABASE_ANON_KEY,
    ) {
        install(Auth) {
            scheme = "com.pandasolve.app"
            host = "login-callback"
        }
    }

    fun isSignedIn(): Boolean = client.auth.currentSessionOrNull() != null

    suspend fun signInWithEmail(email: String, password: String) {
        client.auth.signInWith(Email) {
            this.email = email
            this.password = password
        }
    }

    /**
     * In-app Google sign-in via the Credential Manager API.
     *
     * Requires `BuildConfig.GOOGLE_WEB_CLIENT_ID` to be the **Web client ID**
     * from the Google Cloud Console (the one Supabase Auth uses) — not the
     * Android client ID.
     */
    suspend fun signInWithGoogle() {
        val nonceBytes = ByteArray(32).also { SecureRandom().nextBytes(it) }
        val rawNonce = nonceBytes.joinToString("") { "%02x".format(it) }
        val hashedNonce = MessageDigest.getInstance("SHA-256")
            .digest(rawNonce.toByteArray())
            .joinToString("") { "%02x".format(it) }

        val cm = CredentialManager.create(ctx)

        // Strategy: try GetGoogleIdOption first (silent for returning users), and
        // fall back to GetSignInWithGoogleOption (branded chooser, always works
        // for first-time sign-in) on NoCredentialException or DeveloperError.
        val cred = try {
            val option = GetGoogleIdOption.Builder()
                .setServerClientId(BuildConfig.GOOGLE_WEB_CLIENT_ID)
                .setFilterByAuthorizedAccounts(false)
                .setAutoSelectEnabled(true)
                .setNonce(hashedNonce)
                .build()
            val request = GetCredentialRequest.Builder().addCredentialOption(option).build()
            val response = cm.getCredential(ctx, request)
            GoogleIdTokenCredential.createFrom(response.credential.data)
        } catch (e: Exception) {
            // NoCredentialException / GetCredentialException(28444) → fall back.
            val fallback = GetSignInWithGoogleOption.Builder(BuildConfig.GOOGLE_WEB_CLIENT_ID)
                .setNonce(hashedNonce)
                .build()
            val request = GetCredentialRequest.Builder().addCredentialOption(fallback).build()
            val response = cm.getCredential(ctx, request)
            GoogleIdTokenCredential.createFrom(response.credential.data)
        }

        client.auth.signInWith(IDToken) {
            provider = Google
            idToken = cred.idToken
            nonce = rawNonce
        }
    }

    /**
     * Apple sign-in via Supabase's OAuth web flow. Opens a Custom Tab and
     * returns when the redirect URI fires.
     */
    suspend fun signInWithApple() {
        client.auth.signInWith(Apple)
    }

    suspend fun signOut() = client.auth.signOut()

    fun currentAccessToken(): String? = client.auth.currentSessionOrNull()?.accessToken

    fun currentEmail(): String? = client.auth.currentSessionOrNull()?.user?.email
}
