package com.pandasolve.app.network

import com.pandasolve.app.BuildConfig
import com.pandasolve.app.auth.SupabaseAuth
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.serialization.json.Json
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Response
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import okhttp3.MediaType.Companion.toMediaType

@Singleton
class ApiClient @Inject constructor(
    private val auth: SupabaseAuth,
) {
    val retrofit: Retrofit by lazy { build() }

    private fun build(): Retrofit {
        val logging = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BODY
                    else HttpLoggingInterceptor.Level.NONE
        }
        val ok = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(auth))
            .addInterceptor(logging)
            // Without Redis the backend solves inline, so POST /v1/tasks holds the
            // request for the whole solve (GPT + Gemini fallback). The default 10s
            // read timeout fires mid-solve and surfaces as "timeout". Give it room.
            .connectTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)     // image upload
            .readTimeout(180, TimeUnit.SECONDS)     // inline solve can be slow
            .callTimeout(200, TimeUnit.SECONDS)     // overall hard cap
            .build()
        val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }
        return Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(ok)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
    }
}

private class AuthInterceptor(private val auth: SupabaseAuth) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = auth.currentAccessToken()
        val req = if (token != null) {
            chain.request().newBuilder().addHeader("Authorization", "Bearer $token").build()
        } else chain.request()
        return chain.proceed(req)
    }
}
