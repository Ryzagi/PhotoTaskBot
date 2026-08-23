import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.compose.compiler)
    alias(libs.plugins.hilt)
    alias(libs.plugins.ksp)
    alias(libs.plugins.openapi.generator)
    // Push (FCM): uncomment after adding app/google-services.json (see docs/clients/push-setup.md).
    // alias(libs.plugins.google.services)
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
    compileSdk = 36

    defaultConfig {
        minSdk = 26
        targetSdk = 36
        // Each Play upload needs a unique, higher code. Bump VERSION_CODE in
        // local.properties (or set CI_BUILD_NUMBER) before each upload.
        // Play requires a strictly higher versionCode per upload. Bump VERSION_CODE in
        // local.properties (or pass CI_BUILD_NUMBER) for each new internal-testing upload.
        versionCode = envProp("VERSION_CODE", System.getenv("CI_BUILD_NUMBER") ?: "2").toInt()
        versionName = "0.2.0"
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

    signingConfigs {
        // Release/upload signing for Play. Put these in local.properties (gitignored):
        //   RELEASE_KEYSTORE=/abs/path/upload-keystore.jks
        //   RELEASE_STORE_PASSWORD=...  RELEASE_KEY_ALIAS=upload  RELEASE_KEY_PASSWORD=...
        // Create one: keytool -genkeypair -v -keystore upload-keystore.jks \
        //   -alias upload -keyalg RSA -keysize 2048 -validity 10000
        val ksPath = envProp("RELEASE_KEYSTORE")
        if (ksPath.isNotBlank()) {
            create("release") {
                storeFile = file(ksPath)
                storePassword = envProp("RELEASE_STORE_PASSWORD")
                keyAlias = envProp("RELEASE_KEY_ALIAS")
                keyPassword = envProp("RELEASE_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            // Signed only when the RELEASE_* props are present; otherwise unsigned.
            signingConfig = signingConfigs.findByName("release")
            // R8 disabled for now so internal-testing AABs build without keep-rule
            // tuning. proguard-rules.pro is staged for re-enabling before public launch.
            isMinifyEnabled = false
            isShrinkResources = false
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

    // Google Play Billing — in-app purchases (adds the BILLING permission to the manifest).
    // Plain (Java) artifact, not billing-ktx: from 8.1.0 the -ktx AAR is compiled with
    // Kotlin 2.2 metadata, which the Kotlin 2.0.20 compiler here refuses to read.
    implementation("com.android.billingclient:billing:8.3.0")

    // implementation(libs.math.view) // TODO: JitPack unavailable, re-enable when fixed
    implementation(libs.sentry.android)
    implementation(libs.posthog.android)
    implementation(libs.timber)

    testImplementation(libs.junit5)
    testImplementation(libs.turbine)
    testImplementation(libs.mockk)
}
