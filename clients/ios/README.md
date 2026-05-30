# PandaSolve — iOS

Native iOS client. Swift + SwiftUI. iOS 16+.

See [`/docs/clients/ios.md`](../../docs/clients/ios.md) for the full architecture writeup.

## Quick start

This directory contains the source tree and a `Package.swift` declaring
dependencies. Create the Xcode project on top:

1. Open Xcode → File → New → Project → iOS → App.
2. Product Name: `PandaSolve`. Bundle Identifier: `app.pandasolve.client`.
   Interface: SwiftUI. Language: Swift. Storage: SwiftData.
3. Save into `clients/ios/` (overwriting nothing).
4. In Xcode → File → Add Package Dependencies… add the URLs listed in
   `Package.swift` (supabase-swift, swift-openapi-generator, iosMath, sentry-cocoa,
   posthog-ios, KeychainAccess).
5. Replace the generated `ContentView.swift` and `PandaSolveApp.swift` with
   the files in `PandaSolve/App/`.
6. Drag the rest of `PandaSolve/` into the project.

## Build configurations

`PandaSolve-Dev` and `PandaSolve` schemes. `Info.plist` reads `API_BASE_URL`
from a build setting (xcconfig) so the same code targets both environments.

Environment values (put in `Config-Dev.xcconfig` and `Config-Prod.xcconfig`):

```
API_BASE_URL = https://api-dev.pandasolve.app
SUPABASE_URL = https://your-project.supabase.co
SUPABASE_ANON_KEY = ...
SENTRY_DSN = ...
```

## OpenAPI codegen

`swift-openapi-generator` is a build-time plugin. Add it to the main target
in the SPM manifest with `OpenAPIGenerator` plugin and point it at
`bot/openapi.json`. See `Package.swift` for the wiring.

## Release

See [`/docs/clients/ios.md#release`](../../docs/clients/ios.md#release).
Fastlane lanes for TestFlight and App Store are in `fastlane/Fastfile`
(create when ready to ship — not committed in the scaffold).
