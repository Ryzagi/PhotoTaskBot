# iOS Client

Swift + SwiftUI app under `clients/ios/`. Targets iOS 16.0 and above (>95% of devices in 2026). Built with Xcode 15.4+ and Swift 5.10+.

## Goals

Identical to Android: full bot parity sans payments, native math rendering, OpenAPI-generated network code, TestFlight in 5–6 weeks.

## Project structure

Single app target plus a `NotificationServiceExtension` target for rich pushes.

```
clients/ios/
├── PandaSolve.xcodeproj                    Project
├── PandaSolve/                              Main app target
│   ├── App/
│   │   ├── PandaSolveApp.swift              @main
│   │   └── AppEnvironment.swift             DI container
│   ├── Features/
│   │   ├── Auth/                            SignInView, SignInModel
│   │   ├── Home/
│   │   ├── Solve/
│   │   ├── Task/                            Solution detail
│   │   ├── History/
│   │   └── Settings/
│   ├── Domain/
│   │   ├── Models/                          User, Balance, Task, SolutionStep
│   │   └── UseCases/                        SignIn, SubmitTask, PollTask, ListHistory, RegisterDevice
│   ├── Data/
│   │   ├── Repositories/                    UserRepository, TaskRepository, DeviceRepository
│   │   └── Mappers/                         DTO ↔ domain
│   ├── Network/
│   │   ├── APIClient.swift                  URLSession wrapper
│   │   ├── AuthMiddleware.swift             swift-openapi middleware: attach JWT, handle 401
│   │   └── Generated/                       swift-openapi output
│   ├── Auth/
│   │   ├── SupabaseAuth.swift               supabase-swift
│   │   └── SessionStore.swift               Keychain
│   ├── Storage/                             SwiftData stores
│   ├── Push/
│   │   ├── PushService.swift                Token registration
│   │   └── NotificationCenter+Routing.swift Deep link from tap
│   ├── Math/
│   │   ├── MathView.swift                   iosMath wrapper
│   │   └── SolutionRenderer.swift           Walks Solution JSON
│   ├── Analytics/                           PostHog wrapper
│   ├── Localization/
│   │   ├── Localizable.xcstrings            String catalog
│   │   └── Strings+Generated.swift          Type-safe accessors (SwiftGen)
│   ├── Resources/
│   │   ├── Assets.xcassets
│   │   └── Info.plist
│   └── PandaSolve.entitlements
├── NotificationServiceExtension/            Rich push (downloads thumbnail and attaches)
├── PandaSolveTests/                          XCTest + Swift Testing
├── PandaSolveUITests/
├── Package.swift                            Swift Package Manager
├── .swiftformat
├── .swiftlint.yml
├── fastlane/                                Lanes for build, beta, release
└── README.md
```

## Architecture

**MVVM with `@Observable`.** Model classes use the `@Observable` macro (iOS 17+); for iOS 16 they conform to `ObservableObject` with `@Published` — wrap the macro usage behind a compatibility shim.

```
SwiftUI View  ↔  ViewModel (@Observable)  ─►  UseCase  ─►  Repository  ─►  APIClient | SwiftData
```

No Combine pipelines beyond what URLSession returns. Use Swift Concurrency (`async`/`await`, `AsyncSequence`).

## Key libraries (SPM)

| Concern | Package | Why |
|---|---|---|
| OpenAPI | `apple/swift-openapi-generator` + `swift-openapi-urlsession` | Native, supported by Apple |
| Auth | `supabase-community/supabase-swift` | Official Supabase Swift SDK |
| Keychain | `kishikawakatsumi/KeychainAccess` | Refresh token storage |
| LaTeX | `kostub/iosMath` | CoreGraphics LaTeX renderer |
| Image | Apple `PhotosUI.PhotosPicker` + `AVFoundation` | Native, no extra deps |
| Push | Apple `UserNotifications` + APNs (server side) | Native |
| Crash | `getsentry/sentry-cocoa` | Sentry |
| Analytics | `PostHog/posthog-ios` | PostHog |
| Strings | `SwiftGen/SwiftGen` | Type-safe localization |
| Lint/format | `realm/SwiftLint`, `nicklockwood/SwiftFormat` | Standard |
| Testing | XCTest, Swift Testing (Xcode 16+) | Native |

## Network layer

Use `swift-openapi-generator` (Apple project) to emit:

```swift
let client = Client(
    serverURL: URL(string: "https://api.pandasolve.app")!,
    transport: URLSessionTransport(),
    middlewares: [AuthMiddleware(session: supabaseSession), LocaleMiddleware(), TraceMiddleware()]
)

let task = try await client.createTask(body: .multipartForm([...])).ok.body
```

`AuthMiddleware` attaches `Authorization: Bearer <jwt>` and refreshes on 401 (single retry).

## LaTeX rendering

`iosMath` renders LaTeX into a CoreGraphics-backed `MTMathUILabel`. Wrap it for SwiftUI:

```swift
struct MathView: UIViewRepresentable {
    let latex: String
    func makeUIView(context: Context) -> MTMathUILabel {
        let label = MTMathUILabel()
        label.font = MTFontManager().latinModernFont(withSize: 18)
        return label
    }
    func updateUIView(_ view: MTMathUILabel, context: Context) {
        view.latex = latex
    }
}

struct SolutionView: View {
    let problem: Problem
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                MixedText(problem.problem)
                ForEach(Array(problem.steps.enumerated()), id: \.offset) { idx, block in
                    HStack(alignment: .top) {
                        Text("\(idx + 1).").bold()
                        BlockView(block: block)
                    }
                }
                Text("Ответ").font(.headline).padding(.top)
                ForEach(problem.solution, id: \.id) { BlockView(block: $0) }
            }
            .padding()
        }
    }
}
```

`MixedText` handles `text` blocks with inline `$...$` math by splitting on the math delimiters and rendering math runs through `iosMath`. SwiftUI's `Text` doesn't natively support inline custom views, so this becomes an `HStack`-of-runs layout.

## Auth flow

```swift
@main
struct PandaSolveApp: App {
    @State private var session: Session? = SessionStore.shared.load()

    var body: some Scene {
        WindowGroup {
            if let session {
                HomeView(session: session)
            } else {
                SignInView(onSignIn: { newSession in
                    SessionStore.shared.save(newSession)
                    session = newSession
                })
            }
        }
    }
}
```

Sign in:

- **Email / password** via Supabase.
- **Sign in with Apple** via `AuthenticationServices` (`ASAuthorizationAppleIDProvider`). Required by App Store guideline 4.8 if any third-party social sign-in is offered.
- **Sign in with Google** via Supabase OAuth + `ASWebAuthenticationSession`.

`SessionStore` keeps the refresh token in the Keychain (access-after-first-unlock). The access token is in memory only.

## Push (APNs)

1. After sign-in, request notification authorization (`UNUserNotificationCenter.current().requestAuthorization`).
2. Call `UIApplication.shared.registerForRemoteNotifications()`.
3. In `AppDelegate.didRegisterForRemoteNotificationsWithDeviceToken`, hex-encode and `POST /v1/devices`.
4. `NotificationServiceExtension` intercepts the push: downloads `thumbnail_url`, attaches as image, presents as rich notification.
5. Tap handler routes to `/task/{task_id}` via `NavigationStack` path binding.

`UNNotificationCategory` for "Solution ready" with a "View" action.

## Localization

`Localizable.xcstrings` (Xcode 15+ String Catalog). Default Russian, English variant. SwiftGen produces:

```swift
public enum L10n {
    public static let solveCta = Localizable.tr("solve_cta")
    public static func balanceDaily(_ p1: Int) -> String { … }
    public enum Solutions {
        public static func left(_ count: Int) -> String { … }
    }
}
```

Plurals via the string catalog's built-in `Localizable.stringsdict`-equivalent UI.

## Build configurations

`Debug` and `Release` schemes for each environment:

- `PandaSolve-Dev` → `https://api-dev.pandasolve.app`
- `PandaSolve` → `https://api.pandasolve.app`

Bundle IDs: `app.pandasolve.client.dev` and `app.pandasolve.client`. Separate provisioning profiles, separate Sentry projects.

## Quality gates

`.github/workflows/ios.yml`:

1. `swiftformat --lint .`
2. `swiftlint --strict`
3. `xcodebuild test -scheme PandaSolve -destination 'platform=iOS Simulator,OS=17.5,name=iPhone 15'`
4. Coverage: `xcrun xccov view --report ...` ≥70% on Domain/Data.

UI tests for sign in → solve → view solution.

## Release

`fastlane`:

```ruby
lane :beta do
  match(type: "appstore")
  build_app(scheme: "PandaSolve")
  upload_to_testflight(skip_waiting_for_build_processing: true)
end

lane :release do
  match(type: "appstore")
  build_app(scheme: "PandaSolve")
  upload_to_app_store(submit_for_review: false, skip_screenshots: true)
end
```

Build number = CI run number. Version bumped per release manually.

## App Store review notes

- **Demo account**: provide one (we have email auth).
- **Privacy nutrition labels**: see `09-security.md` for the data we collect.
- **Sign in with Apple**: enabled (4.8 requires it because we also offer Google).
- **No external purchase links**: the "Top up via Telegram" button is described as "Continue to our Telegram bot for purchases" and opens `tg://` → Safari fallback to `https://t.me/PandaSolveBot`. Apple has historically accepted this provided we don't advertise external pricing in-app. **Show no prices and no purchase calls-to-action** inside the iOS app — just "Top up" → opens Telegram. Re-read 3.1.3 before submission.
- **Encryption export**: the app uses standard iOS crypto only; no custom crypto. Mark `ITSAppUsesNonExemptEncryption = NO` in Info.plist.

## Open questions

- iPad: support but not optimize for v1. SwiftUI adapts.
- watchOS: out of scope.
- Mac Catalyst: out of scope. Reconsider after iOS launch.
- Dynamic Type and VoiceOver: must work for App Store accessibility scoring. Test at `accessibility5` and with VoiceOver enabled before submission.
