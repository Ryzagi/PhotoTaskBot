import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.compose.compiler)
    alias(libs.plugins.hilt)
    alias(libs.plugins.ksp)
    alias(libs.plugins.openapi.generator)
}

// Gradle only auto-loads `gradle.properties` into project properties. Read
// `local.properties` (where the Android plugin already expects sdk.dir) too,
// so secrets like SUPABASE_URL or GOOGLE_WEB_CLIENT_ID can sit in one file.
val localProps = Properties().apply {
    val f = rootProject.file("local.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}

/** Read `key` from local.properties first, then -P / gradle.properties, then default. */
fun envProp(key: String, default: String = ""): String =
    localProps.getProperty(key)
        ?: project.findProperty(key) as? String
        ?: default

android {
    namespace = "com.pandasolve.app"
    compileSdk = 34

    defaultConfig {
        minSdk = 26
        targetSdk = 34
        versionCode = (System.getenv("CI_BUILD_NUMBER") ?: "1").toInt()
        versionName = "0.1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    flavorDimensions += "env"
    productFlavors {
        create("dev") {
            dimension = "env"
            applicationIdSuffix = ".dev"
            versionNameSuffix = "-dev"
            buildConfigField("String", "API_BASE_URL",
                "\"" + envProp("API_BASE_URL_DEV", "https://api-dev.pandasolve.app") + "\"")
        }
        create("prod") {
            dimension = "env"
            buildConfigField("String", "API_BASE_URL",
                "\"" + envProp("API_BASE_URL_PROD", "https://api.pandasolve.app") + "\"")
        }
    }

    defaultConfig {
        // Placeholders parse cleanly so the SupabaseClient constructor doesn't throw
        // at app startup. Override in local.properties (preferred) or
        // ~/.gradle/gradle.properties with the real values to actually sign in.
        buildConfigField("String", "SUPABASE_URL",
            "\"" + envProp("SUPABASE_URL", "https://example.supabase.co") + "\"")
        buildConfigField("String", "SUPABASE_ANON_KEY",
            "\"" + envProp("SUPABASE_ANON_KEY",
                "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzdHViIn0.stub") + "\"")
        buildConfigField("String", "SENTRY_DSN",
            "\"" + envProp("SENTRY_DSN") + "\"")
        // OAuth: web client ID from Google Cloud Console (NOT the Android client ID).
        buildConfigField("String", "GOOGLE_WEB_CLIENT_ID",
            "\"" + envProp("GOOGLE_WEB_CLIENT_ID") + "\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
        debug {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
}

openApiGenerate {
    generatorName.set("kotlin")
    inputSpec.set("$rootDir/../../bot/openapi.json")
    outputDir.set("$buildDir/generated/openapi")
    apiPackage.set("com.pandasolve.app.network.api")
    modelPackage.set("com.pandasolve.app.network.model")
    configOptions.put("library", "jvm-retrofit2")
    configOptions.put("serializationLibrary", "kotlinx_serialization")
    configOptions.put("dateLibrary", "kotlinx-datetime")
    configOptions.put("useCoroutines", "true")
}

// OpenAPI codegen is wired but NOT a compile dependency yet: our PandaApiService
// is hand-rolled for v1.0 of the build. Run `./gradlew openApiGenerate` manually
// when you want to regenerate, then swap PandaApiService.kt over to the generated
// types. Re-enable the auto-wire here once that swap happens.
// android.applicationVariants.all {
//     val variantName = name
//     tasks.named("compile${variantName.replaceFirstChar { it.uppercase() }}Kotlin").configure {
//         dependsOn("openApiGenerate")
//     }
// }

dependencies {
    implementation(libs.androidx.core)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.runtime)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.navigation.compose)

    implementation(libs.camerax.core)
    implementation(libs.camerax.camera2)
    implementation(libs.camerax.lifecycle)
    implementation(libs.camerax.view)

    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.compose.material3)
    implementation(libs.compose.material.icons.extended)
    debugImplementation(libs.compose.ui.tooling)

    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
    implementation(libs.hilt.nav.compose)

    implementation(libs.retrofit)
    implementation(libs.retrofit.kotlinx.serialization)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging)
    implementation(libs.kotlinx.serialization.json)

    implementation(libs.room.runtime)
    ksp(libs.room.compiler)
    implementation(libs.room.ktx)

    implementation(libs.datastore.preferences)
    implementation(libs.security.crypto)

    implementation(libs.coil.compose)

    implementation(libs.supabase.auth)
    implementation(libs.supabase.compose.auth)
    implementation(libs.supabase.storage)
    implementation(libs.ktor.client.okhttp)
    implementation(libs.credentials)
    implementation(libs.credentials.play.services.auth)
    implementation(libs.google.id)
    implementation(libs.browser)

    implementation(platform(libs.firebase.bom))
    implementation(libs.firebase.messaging)
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-play-services:1.8.1")

    // implementation(libs.math.view) // TODO: JitPack unavailable, re-enable when fixed
    implementation(libs.sentry.android)
    implementation(libs.posthog.android)
    implementation(libs.timber)

    testImplementation(libs.junit5)
    testImplementation(libs.turbine)
    testImplementation(libs.mockk)
}
