# iOS port — bring SwiftUI client to Android parity

The `clients/ios` SwiftUI scaffold mirrors the Android architecture but predates all the
QA/feature rounds. This plan ports the **current Android feature set** onto it. Build
verification must happen in **Xcode** (the CLI here has no iOS SDK).

## Architecture mapping (Android → iOS, both already present)

| Android | iOS |
|---|---|
| `domain/model/Models.kt` (kotlinx.serialization) | `Domain/Models.swift` (Codable, snake_case) |
| `network/PandaApiService` (Retrofit) | `Network/APIClient.swift` (URLSession) |
| `data/repository/*Repository.kt` | `Data/*Repository.swift` |
| `auth/SupabaseAuth.kt` (+ authState) | `Auth/SupabaseAuth.swift` |
| `i18n/Localization.kt` (`Strings`/`LocalStrings`) | `Localization/Strings.swift` (+ `@Environment`) |
| `latex/LatexUnicode.kt` | reuse `Math/MathLatexView.swift` (iosMath) or a Swift `latexToUnicode` |
| `ui/feature/*` Compose screens | `Features/*` SwiftUI views + `@Observable` view models |
| `ui/Navigation.kt` (splash gate) | `App/RootView.swift` (auth gate) |

## Feature checklist (port to parity)

- **Models** — add `displayName/solvedCount/streak` to `Me`; `Solution.title`;
  `TaskDetail.albumId/inputText`; `Album`, `AlbumCreate/Update/Assign`, `ChatMessage/ChatThread/ChatSend`,
  `TaskUpdate`, `UpdateMe`. (DONE in this pass.)
- **APIClient** — add `patch`/`delete`; longer timeouts (R3-7… actually #7: 180s read for inline solve).
- **Repos** — `UserRepository`: `me` (+ `lastMe` cache), `updateLanguage`, `updateDisplayName`.
  `TaskRepository`: `list(album_id,q)`, `get` (+cache), `rename`, `chatHistory`, `sendChat`.
  `AlbumRepository` (new): list/create/update/delete/assign (+`lastCount`).
- **Auth** — session-restore gate (`authState: loading/signedIn/signedOut`) so cold start
  doesn't bounce to sign-in (Android #1). Google + Apple + email.
- **i18n** — `Strings` (ru/en) + a language store defaulting to **en**; selector on SignIn + Profile.
- **Home** (merged) — balance + streak + name (`display_name`); folder filter chips + `＋` create;
  search bar; day-grouped list (today/yesterday/earlier, collapsible); long-press → assign/rename;
  no mock fallback; cached stats for instant counts.
- **Task detail** — steps/answer via LaTeX; album badge (loads `album_id`); chat thread + input,
  3-free-message limit (`remaining`); cache for instant re-open; concurrent loads.
- **Solve/Camera** — photo + text modes; 180s timeout; poll until done.
- **Profile** — real stats; rename (pencil); notifications switch; language dropdown; top-up → Telegram.
- **Folders** — create/edit(+delete)/assign dialogs (shared), localized.
- **Insets** — safe-area handling so it fits all devices.

## Suggested pass order
1. **Data foundation** — Models, APIClient (patch/delete), repos, AppEnvironment wiring. ← start here
2. **Auth + i18n + RootView gate** — session restore, Strings, language store, SignIn.
3. **Home** (the big one) — merged screen.
4. **Task detail** (+ chat).
5. **Solve/Camera, Profile, Folders dialogs, insets** — polish.

## Notes
- Backend contract is `bot/openapi.json` (13 paths). Could later swap the hand-rolled client for
  the swift-openapi-generator output (the plugin is already wired in `Package.swift`).
- Verify each pass by building the app target in Xcode; fix any compile nits there.
