// swift-tools-version: 5.10
import PackageDescription

let package = Package(
    name: "PandaSolve",
    // iOS 17+: the UI layer uses the @Observable macro and @Environment(Type.self).
    platforms: [.iOS(.v17)],
    products: [
        .library(name: "PandaSolveCore", targets: ["PandaSolveCore"]),
    ],
    dependencies: [
        .package(url: "https://github.com/supabase-community/supabase-swift.git", from: "2.20.0"),
        // 0.9.x tags predate SPM support (no Package.swift) — 2.x is the first SPM-ready line.
        .package(url: "https://github.com/kostub/iosMath.git", from: "2.0.0"),
        .package(url: "https://github.com/getsentry/sentry-cocoa.git", from: "8.36.0"),
        .package(url: "https://github.com/PostHog/posthog-ios.git", from: "3.13.0"),
        .package(url: "https://github.com/kishikawakatsumi/KeychainAccess.git", from: "4.2.2"),
    ],
    targets: [
        // NOTE: the swift-openapi-generator plugin was removed — the hand-rolled
        // APIClient replaced it and nothing imports the generated client. Re-add
        // the plugin + an openapi.yaml/openapi-generator-config.yaml here if the
        // generated client is ever wired in.
        .target(
            name: "PandaSolveCore",
            dependencies: [
                .product(name: "Supabase", package: "supabase-swift"),
                .product(name: "iosMath", package: "iosMath"),
                .product(name: "Sentry", package: "sentry-cocoa"),
                .product(name: "PostHog", package: "posthog-ios"),
                .product(name: "KeychainAccess", package: "KeychainAccess"),
            ],
            path: "PandaSolve",
            // App/ is the app-shell (@main + RootView) and Resources/ the asset
            // catalog — both belong to the Xcode app target (project.yml), not
            // this test/CI package target.
            exclude: ["App", "Localization", "Resources"]
        ),
        .testTarget(
            name: "PandaSolveCoreTests",
            dependencies: ["PandaSolveCore"],
            path: "PandaSolveTests"
        ),
    ]
)
