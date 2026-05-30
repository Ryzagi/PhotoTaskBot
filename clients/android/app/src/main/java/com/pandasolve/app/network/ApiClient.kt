package com.pandasolve.app.network

import com.pandasolve.app.BuildConfig
import com.pandasolve.app.auth.SupabaseAuth
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
