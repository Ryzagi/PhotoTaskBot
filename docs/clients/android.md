# Android Client

Kotlin + Jetpack Compose app under `clients/android/`. Targets Android 8.0 (API 26) and above. Compiles with Kotlin 2.0+ and AGP 8.5+.

## Goals

- Full feature parity with the Telegram bot (sans payments — see below).
- Native LaTeX rendering (no WebViews for math).
- Reuse the backend `openapi.json` for typed network code.
- Ship on the Play Store in 5–6 weeks of focused work.

## Module structure

Start as a single-module app. Split into `:feature:*` modules only if build times warrant it.

```
clients/android/
├── app/
│   ├── src/main/java/com/pandasolve/app/
│   │   ├── App.kt                       Application + Hilt entry
│   │   ├── ui/                          Compose screens, composables, theme
│   │   │   ├── theme/
│   │   │   ├── component/               Shared composables (MathBlock, TaskCard, …)
│   │   │   └── feature/
│   │   │       ├── auth/                Sign in
│   │   │       ├── home/                Balance + new task CTA
│   │   │       ├── solve/               Image picker + caption + submit + progress
│   │   │       ├── task/                Task detail (renders solution)
│   │   │       ├── history/             Paginated history list
│   │   │       └── settings/            Language, link Telegram, top up, support
│   │   ├── domain/
│   │   │   ├── model/                   User, Balance, Task, SolutionStep
│   │   │   └── usecase/                 SignIn, SubmitTask, PollTask, ListHistory, RegisterDevice
│   │   ├── data/
│   │   │   ├── repository/              UserRepository, TaskRepository, DeviceRepository
│   │   │   └── mapper/                  DTO ↔ domain
│   │   ├── network/
│   │   │   ├── ApiClient.kt             OkHttp + Retrofit + auth interceptor
│   │   │   └── (generated)              OpenAPI-generated services
│   │   ├── auth/
│   │   │   ├── SupabaseAuth.kt          Email + Google + Apple via supabase-kt
│   │   │   └── SessionStore.kt          Token persistence (EncryptedSharedPreferences)
│   │   ├── db/                          Room — history cache, drafts
│   │   ├── push/                        FCM service + token registration
│   │   ├── latex/                       JLatexMath integration helpers
│   │   └── analytics/                   PostHog wrapper
│   └── src/main/res/
│       ├── values/                      strings, colors, dimens, themes
│       ├── values-ru/                   Russian strings
│       └── …
├── build.gradle.kts
├── settings.gradle.kts
├── gradle/libs.versions.toml            Version catalog
└── README.md                            Build, run, release
```

## Architecture

**MVVM + light Clean.** ViewModels expose `StateFlow<UiState>`, never call Retrofit directly — they call use-cases which call repositories. Repositories own the network/db decision (Room cache + network refresh).

```
View (Compose)  ↔  ViewModel  ─►  UseCase  ─►  Repository  ─►  ApiClient | Room
```

No RxJava. No LiveData. Coroutines + Flow only.

## Key libraries

| Concern | Library | Why |
|---|---|---|
| UI | Jetpack Compose, Material 3 | Modern Android UI |
| Navigation | `androidx.navigation:navigation-compose` | Standard |
| DI | `dagger.hilt` | Compile-time, well-supported in Compose |
| Network | Retrofit 2 + OkHttp 5 + kotlinx.serialization | Standard |
| OpenAPI codegen | `openapi-generator` Gradle plugin | Generates Retrofit services from `openapi.json` |
| Auth | `io.github.jan-tennert.supabase:auth-kt` | Official-ish Supabase Kotlin SDK |
| Storage | `androidx.security:security-crypto` | EncryptedSharedPreferences for refresh token |
| DB | Room 2.6 | History cache |
| Image picking | `androidx.activity:activity-compose` + Photo Picker | No runtime permission on 13+ |
| Image compression | `coil-compose` + custom JPEG encoder | Coil for display, encoder for upload |
| LaTeX | `ru.noties.markwon:ext-latex` (JLatexMath under the hood) | Native math rendering |
| Push | `com.google.firebase:firebase-messaging` | FCM |
| Crash | `io.sentry:sentry-android` | Sentry |
| Analytics | `com.posthog:posthog-android` | PostHog |
| Logging | `com.jakewharton.timber:timber` | Bridged to Sentry breadcrumbs |
| Testing | JUnit5, Turbine, Compose UI test, MockK | Standard |
| Lint | Detekt, KtLint | Pre-commit + CI |

Pin every version in `gradle/libs.versions.toml`. Renovate or Dependabot for updates.

## Network layer

OkHttp interceptor chain:

1. **AuthInterceptor**: attaches `Authorization: Bearer <jwt>` from the Supabase session. On 401, calls `supabase.refreshSession()`, retries once.
2. **LocaleInterceptor**: attaches `Accept-Language`.
3. **TraceInterceptor**: attaches `x-trace-id` (UUID per request) for Sentry linkage.
4. **HttpLoggingInterceptor**: debug builds only.

Timeouts: connect 10s, read 30s (long enough for poll, short enough to not hang forever), write 30s.

## LaTeX rendering

Solution JSON shape (from the backend):

```kotlin
data class Solution(val solutions: List<Problem>)
data class Problem(val problem: String, val steps: List<Block>, val solution: List<Block>)
data class Block(val type: String /* "text"|"math" */, val content: String)
```

Render as:

```kotlin
@Composable
fun SolutionView(problem: Problem) {
    Column {
        Text(problem.problem.parseInlineMath())            // text + inline $math$
        problem.steps.forEachIndexed { i, b ->
            ListItem(headlineContent = { BlockView(b) }, leadingContent = { Text("${i+1}.") })
        }
        Spacer(Modifier.height(16.dp))
        Text("Ответ", style = MaterialTheme.typography.titleMedium)
        problem.solution.forEach { BlockView(it) }
    }
}

@Composable
fun BlockView(b: Block) = when (b.type) {
    "text" -> Text(b.content.parseInlineMath())
    "math" -> JLatexMathView(latex = b.content.unwrapDollars())
    else -> Text(b.content)
}
```

`JLatexMathView` is a `@Composable` that wraps a `MathView` from the `Math-View` library, sized to its measured intrinsic width.

Inline math (within a text block, `$...$`) is parsed and rendered with a `LinkedTextSpan`-style composable that flows math runs inline with prose. If that turns out to be fiddly, fall back to block-only math.

## Auth flow

```
Open app → SessionStore loaded?
                │
        yes ────┴──── no
        │             │
   refresh OK?    Show SignIn
        │             │
        ▼             ▼
      Home      Email / Google / Apple
                      │
                      ▼
              Supabase JWT in SessionStore
                      │
                      ▼
                    Home
```

Sign in with Google uses the Credential Manager API (one-tap on Android 14+). Sign in with Apple on Android uses Supabase's OAuth flow opening a `CustomTabsIntent` — required only if we want feature parity with iOS, otherwise omit.

## Push (FCM)

1. On sign-in, `FirebaseMessaging.getInstance().token.await()`.
2. Register with `POST /v1/devices`.
3. On `FirebaseMessagingService.onMessageReceived`, parse data payload, fetch task if needed, show notification via `NotificationCompat`.
4. Tap → deep link to `/task/{id}` route.

Notification channels (Android 8+):

| Channel | Importance | Topics |
|---|---|---|
| `task_updates` | HIGH | `task.completed`, `task.failed` |
| `account` | DEFAULT | `balance.added`, `daily.reset` |
| `promo` | LOW | `app.broadcast` |

## Localization

`strings.xml` (default: Russian), `values-en/strings.xml` (English). Mirror the bot's user-facing strings. Pluralization via `<plurals>`.

```xml
<string name="balance_daily">Дневной лимит: %1$d</string>
<string name="solve_cta">Решить задачу</string>
<plurals name="solutions_left">
    <item quantity="one">%d решение</item>
    <item quantity="few">%d решения</item>
    <item quantity="many">%d решений</item>
    <item quantity="other">%d решения</item>
</plurals>
```

## Build flavors

Two flavors: `dev` and `prod`.

- `dev` → `https://api-dev.pandasolve.app`
- `prod` → `https://api.pandasolve.app`

ApplicationId per flavor (`com.pandasolve.app` vs `com.pandasolve.app.dev`) so devs can have both installed.

## Quality gates

CI runs on every PR (`.github/workflows/android.yml`):

1. `./gradlew detekt ktlintCheck`
2. `./gradlew testDebugUnitTest`
3. `./gradlew connectedDebugAndroidTest` (emulator)
4. `./gradlew assembleDebug`
5. Bundle size report (`./gradlew :app:bundleRelease` + dump).

Mandatory: ≥70% unit test coverage on `domain/` and `data/`. UI tests for the golden path (sign in → solve → see solution).

## Release

1. Bump `versionCode` (from CI) + `versionName` in `app/build.gradle.kts`.
2. `./gradlew bundleRelease` produces `.aab`.
3. Sign with Play App Signing (Google manages the key).
4. Upload via Play Console → Internal track first.
5. After 1 week of internal testing → Closed beta (50 users).
6. After 1 week of beta → Production.

Crash-free sessions target: 99.7% before promoting from beta to prod.

## Privacy / Play data safety

Disclose:

- Personal info: name (Telegram first/last), email address (Supabase Auth).
- Photos and videos: user-submitted photos.
- App activity: task creation, completion (PostHog).
- App info and performance: crash logs (Sentry).
- Device or other IDs: FCM token.

All data is encrypted in transit (TLS 1.3) and at rest (Supabase). User can request deletion via Settings → Delete account.

## Open questions

- Tablet UX: support but not optimize for v1. Compose adapts.
- Wear OS / Android Auto: out of scope.
- Dark mode: yes, follow system (`MaterialTheme` with dynamic color on 12+).
- Offline solve viewing: yes, cache completed tasks in Room and let users open them with no network.
