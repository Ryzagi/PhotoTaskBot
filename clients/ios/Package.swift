// swift-tools-version: 5.10
import PackageDescription

let package = Package(
    name: "PandaSolve",
    platforms: [.iOS(.v16)],
    products: [
        .library(name: "PandaSolveCore", targets: ["PandaSolveCore"]),
    ],
    dependencies: [
        .package(url: "https://github.com/supabase-community/supabase-swift.git", from: "2.20.0"),
        .package(url: "https://github.com/apple/swift-openapi-generator", from: "1.4.0"),
        .package(url: "https://github.com/apple/swift-openapi-runtime", from: "1.6.0"),
        .package(url: "https://github.com/apple/swift-openapi-urlsession", from: "1.0.2"),
        .package(url: "https://github.com/kostub/iosMath.git", from: "0.9.5"),
        .package(url: "https://github.com/getsentry/sentry-cocoa.git", from: "8.36.0"),
        .package(url: "https://github.com/PostHog/posthog-ios.git", from: "3.13.0"),
        .package(url: "https://github.com/kishikawakatsumi/KeychainAccess.git", from: "4.2.2"),
    ],
    targets: [
        .target(
            name: "PandaSolveCore",
            dependencies: [
                .product(name: "Supabase", package: "supabase-swift"),
                .product(name: "OpenAPIRuntime", package: "swift-openapi-runtime"),
                .product(name: "OpenAPIURLSession", package: "swift-openapi-urlsession"),
                .product(name: "iosMath", package: "iosMath"),
                .product(name: "Sentry", package: "sentry-cocoa"),
                .product(name: "PostHog", package: "posthog-ios"),
                .product(name: "KeychainAccess", package: "KeychainAccess"),
            ],
            path: "PandaSolve",
            exclude: ["App", "Localization"],
            plugins: [
                .plugin(name: "OpenAPIGenerator", package: "swift-openapi-generator"),
            ]
        ),
    ]
)
