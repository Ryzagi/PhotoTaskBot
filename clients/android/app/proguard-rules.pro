# R8/ProGuard rules. NOTE: minification is currently OFF for release
# (isMinifyEnabled=false in build.gradle.kts) so these aren't exercised yet —
# they're staged for re-enabling R8 before a public Play production release.

# --- Optional/transitive classes referenced but not bundled ---
-dontwarn org.slf4j.**
-dontwarn javax.annotation.**
-dontwarn org.conscrypt.**
-dontwarn org.bouncycastle.**

# --- Networking (Retrofit / OkHttp / Ktor) ---
-dontwarn okhttp3.**
-dontwarn okio.**
-dontwarn retrofit2.**
-keepattributes Signature, Exceptions, *Annotation*, InnerClasses

# --- kotlinx.serialization: keep @Serializable models + generated serializers ---
-keepclassmembers class com.pandasolve.app.** {
    *** Companion;
}
-keepclasseswithmembers class com.pandasolve.app.** {
    kotlinx.serialization.KSerializer serializer(...);
}
-keep,includedescriptorclasses class com.pandasolve.app.**$$serializer { *; }
-keep class com.pandasolve.app.domain.model.** { *; }
