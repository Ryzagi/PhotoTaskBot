import SwiftUI
import Sentry

@main
struct PandaSolveApp: App {
    @State private var environment: AppEnvironment

    init() {
        // Mirror the Android client: only init Sentry when a DSN is configured,
        // so dev builds without one don't log startup errors.
        if let dsn = Bundle.main.object(forInfoDictionaryKey: "SENTRY_DSN") as? String, !dsn.isEmpty {
            SentrySDK.start { options in
                options.dsn = dsn
                options.tracesSampleRate = 0.1
            }
        }
        // PostHog: only init once the API key is wired in via Secrets.xcconfig
        // (placeholder value would spam failed requests) — same as Android.
        // PostHogSDK.shared.setup(PostHogConfig(apiKey: "<your-key>"))
        _environment = State(initialValue: AppEnvironment.live)
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(environment)
        }
    }
}
