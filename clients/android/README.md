# PandaSolve — Android

Native Android client. Kotlin + Jetpack Compose. Targets API 26+ (Android 8.0).

See [`/docs/clients/android.md`](../../docs/clients/android.md) for the full
architecture writeup.

## Quick start

```bash
# From this directory:
./gradlew :app:assembleDevDebug
./gradlew :app:installDevDebug

# Or open clients/android/ in Android Studio (Hedgehog or later).
```

Required environment for builds:

```
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
API_BASE_URL_DEV=https://api-dev.pandasolve.app
API_BASE_URL_PROD=https://api.pandasolve.app
SENTRY_DSN=...
```

These are read by `buildSrc` and surfaced as `BuildConfig` constants. Put them
in `~/.gradle/gradle.properties` (preferred) or `clients/android/local.properties`.

## Layout

```
app/
├── build.gradle.kts                 Module config
└── src/main/
    ├── AndroidManifest.xml
    ├── java/com/pandasolve/app/
    │   ├── App.kt                   Hilt entry, Sentry init, FCM init
    │   ├── MainActivity.kt          Single Activity host
    │   ├── ui/                      Compose screens, theme, components
    │   ├── domain/                  Models + use-cases
    │   ├── data/                    Repositories + mappers
    │   ├── network/                 Retrofit, OkHttp, generated client
    │   ├── auth/                    Supabase Auth wrapper, session store
    │   ├── db/                      Room (history cache)
    │   ├── push/                    FCM service + token registration
    │   ├── latex/                   JLatexMath wrapper
    │   └── analytics/               PostHog wrapper
    └── res/
        ├── values/                  ru (default)
        └── values-en/
```

## OpenAPI client codegen

`./gradlew :app:openApiGenerate` reads `../../bot/openapi.json` (committed
artifact emitted from the backend) and produces Kotlin coroutines + Retrofit2
services under `build/generated/openapi/`.

The backend's `make openapi` regenerates the JSON; commit it. Breaking the
contract → mobile CI fails until the JSON is updated.

## Release

See [`/docs/clients/android.md#release`](../../docs/clients/android.md#release).
