import SwiftUI
import Sentry
import PostHog

@main
struct PandaSolveApp: App {
    @State private var environment: AppEnvironment

    init() {
        SentrySDK.start { options in
            options.dsn = Bundle.main.object(forInfoDictionaryKey: "SENTRY_DSN") as? String ?? ""
            options.tracesSampleRate = 0.1
        }
        let postHogConfig = PostHogConfig(apiKey: "<set-from-secrets>")
        PostHogSDK.shared.setup(postHogConfig)
        _environment = State(initialValue: AppEnvironment.live)
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(environment)
        }
    }
}
