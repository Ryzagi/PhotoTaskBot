# Mobile QA backlog — on-device testing

First real-device test of the Android app against the live backend
(`https://panda-api.upword.live`, inline solve, no Redis/push yet).
Recorded 2026-05-31. Ordered roughly by priority.

Legend: **type** = bug | feature · **area** = where the fix likely lives.

---

## 1. Google session not persisted (must re-login every launch) — FIXED (pending device re-test)
- **Resolution:** root cause was a **synchronous** `isSignedIn()` at startup, run before
  supabase-kt finished its async `LoadingFromStorage → Authenticated` restore (the session
  *was* persisted — `multiplatform-settings-no-arg` is on the classpath). Added
  `SupabaseAuth.authState: StateFlow<AuthState>` (mapped from `auth.sessionStatus`), a
  `Routes.SPLASH` start destination, and a gate in `Navigation.kt` that waits on `authState`
  then routes to Home/SignIn once. Made `autoLoadFromStorage`/`alwaysAutoRefresh` explicit.
  Follow-up: returning-user FCM registration currently lives in `SignInViewModel.init`, which
  no longer runs for auto-restored sessions — move it once push is enabled.
- **type:** bug · **area:** `auth/SupabaseAuth.kt`, `ui/RootViewModel.kt`, `ui/Navigation.kt`
- **Symptom:** after Google sign-in, closing & reopening the app forces sign-in again.
- **Likely cause:** gotrue session isn't persisted/restored across process death — no
  persistent `SessionManager`/settings storage, or `isSignedIn()` is checked before the
  session is loaded from storage on cold start.
- **Fix direction:** configure the Supabase `Auth` plugin to persist the session
  (settings-backed session manager + `alwaysAutoRefresh`/auto-load from storage) and
  `await` session restore before routing SignIn → Home. Verify the refresh token
  survives an app kill.

## 2a. Assigning a task to an album doesn't stick — FIXED (pending device re-test)
- **Resolution:** same root cause as #2b — the task id reaching the screen was the
  hardcoded fake `"042"`, so `POST /v1/tasks/{id}/album` 404'd (`assign_task_album`
  matched no row). With the real id now threaded through, assign targets a real task and
  persists. Backend route/DB method were already correct.
- **type:** bug · **area:** `ui/feature/task/TaskDetailViewModel.kt`, `POST /v1/tasks/{id}/album`
- **Symptom:** album creation works, but assigning a solved answer to an album has no effect.
- **Likely cause:** the assign call fails or isn't refetched; verify the request body
  (`album_id`) and that the UI reloads the task/album after assigning.
- **Fix direction:** confirm the endpoint succeeds (check logcat for 4xx), then refresh
  task + album task_count on success.

## 2b. Tapping a solved task opens a MOCK task — FIXED (pending device re-test)
- **Resolution:** `HomeScreen` and `HistoryScreen` both called `onTask("042")` — a
  **hardcoded fake id** — for every row, and `SampleThread`/`toRow` had dropped the real
  task id entirely. Added `SampleThread.id`, populated it in `toRow`, and changed both
  taps to `onTask(t.id)` (guarded so blank-id sample rows aren't tappable).
  `TaskDetailViewModel` no longer falls back to sample problems: a real load shows real
  content, a failed load shows a "не удалось загрузить" state — never mock.
- **type:** bug · **area:** `ui/sample/{Sample,Mappers}.kt`, `HomeScreen.kt`, `HistoryScreen.kt`, `TaskDetailViewModel.kt`
- **Symptom:** opening an already-solved task from Home/Archive shows sample data, not the
  real solution.
- **Likely cause:** the real `task_id` isn't passed through navigation, or
  `GET /v1/tasks/{id}` fails and the VM falls back to sample data.
- **Fix direction:** ensure the real id flows Home/Archive → `Routes.task(id)` → fetch;
  surface a real error/empty state instead of silently showing mock data.

## 3. Remove mock data; implement real stats — FIXED (needs backend redeploy + device re-test)
- **Resolution (backend):** `MeResponse` now carries `solved_count` + `streak`;
  `SupabaseService.get_user_stats` counts done tasks (exact count) and `_compute_streak`
  derives the consecutive-day streak (ending today/yesterday). Wired into both `/v1/me`
  handlers; `openapi.json` regenerated; 37 tests + ruff green.
- **Resolution (client):** `Me` model gains `solvedCount`/`streak`. Home shows real name
  (from email), real streak pill (hidden when 0), and real solved count on the "все" pill;
  dropped the fake матем/англ/геом pills. Profile shows real solved/streak/albums (album
  count via `AlbumRepository`). `HomeViewModel`/`HistoryViewModel`/`SettingsViewModel`
  defaults are now honest (0/empty) with no sample fallback. Removed the hardcoded chat
  bubbles in `TaskDetailScreen`.
- **IMPORTANT:** the new fields only appear after the **backend is redeployed** to
  `panda-api.upword.live` (git pull + `docker compose up -d --build`). Until then the
  client defaults streak/solved to 0.
- **type:** feature · **area:** `bot/{schemas/user,services/user_service,supabase_service,api/v1/me}.py`, Home/Profile/History VMs+screens
- **Symptom:** hardcoded placeholders — streak 7, done tasks 47, albums 5, etc.
- **Fix direction:** drive Home from real values: balance (have), **streak**, **solved
  count**, **album count**. Backend likely needs to expose streak + counts on `/v1/me`
  (or a `/v1/me/stats`). Remove the static fallback numbers (keep a genuine empty/zero
  state, not fake data). Keep the offline "sample" fallback only if clearly labelled.

## 4. UI language switch (ru / en) — FOUNDATION DONE + core screens (pending device re-test)
- **Resolution:** added an in-app i18n layer (`i18n/Localization.kt` — `Strings` table with
  `RuStrings`/`EnStrings` + `LocalStrings` CompositionLocal) instead of resource extraction,
  so the toggle flips copy live with no Activity recreation. `i18n/LanguageManager.kt`
  persists the choice (SharedPreferences, defaults to device language); `RootViewModel`
  exposes it and `Navigation.kt` wraps the graph in `CompositionLocalProvider(LocalStrings …)`.
  The Profile "🌍 Язык" row is now a ru↔en toggle (`SettingsViewModel.toggleLanguage`) that
  also syncs `language_code` to the backend via `POST /v1/me`.
- **Migrated so far:** Profile (full), bottom nav labels, Home headers. The toggle works
  end-to-end and persists across launches.
- **REMAINING (mechanical follow-up):** Camera/Solve, Archive, Albums (+ create dialog),
  SignIn, TaskDetail labels, and assorted dialog copy still have hardcoded Russian — migrate
  each by adding keys to `Strings` and reading `LocalStrings.current`. Until then those
  screens stay Russian regardless of the toggle.
- **type:** feature · **area:** `i18n/*`, `ui/RootViewModel.kt`, `ui/Navigation.kt`, Profile/Home/CuteComponents

## 5. Remove "щелк!" caption on the photo/shutter button — FIXED (pending device re-test)
- **Resolution:** removed the `Text("щёлк! 📸", …)` label above the raised shutter in
  `ui/component/CuteComponents.kt` (`CuteBottomBar`). It was in the shared bottom bar, not
  `SolveScreen`.
- **type:** bug (polish) · **area:** `ui/component/CuteComponents.kt`

## 6. Layout too tall — content overflows — FIXED (pending device re-test)
- **Resolution (first pass):** compacted the bulkiest pieces — shared bottom bar 98→84dp,
  shutter 78→70dp (`CuteComponents.kt`); Home top pad 14→10, bottom 110→96, the bamboo
  number 54→44sp, card padding 20→16, and the inter-section spacers (18→12, 16→12, 22→16)
  in `HomeScreen.kt`.
- **Note:** "too tall" was somewhat ambiguous without a screenshot — this is a conservative
  compacting pass on Home + the bottom bar (which affects every tab). If a *specific* screen
  still feels off, point me at it and I'll tune that one.
- **type:** bug (polish) · **area:** `ui/component/CuteComponents.kt`, `ui/feature/home/HomeScreen.kt`

## 7. Increase timeout for real photo processing — FIXED (pending device re-test)
- **Resolution:** OkHttp had **no timeouts set**, so it used the 10s default read timeout
  while the inline solve (no Redis) holds `POST /v1/tasks` for 10–30s+. Set
  connect=30s, write=60s, read=180s, call=200s in `network/ApiClient.kt`. No coroutine
  `withTimeout` exists to cap it further. Long term: Redis async + push removes the long
  request entirely.
- **type:** bug · **area:** `network/ApiClient.kt` (OkHttp timeouts) + poll loop; backend inline solve
- **Symptom:** "timeout" caption appears while a real photo is being solved.
- **Likely cause:** inline solve (no Redis) holds the request 10–30s+; OkHttp
  read/call timeout and/or the client poll window are too short.
- **Fix direction:** raise OkHttp `readTimeout`/`callTimeout` (e.g. 60–90s) and extend the
  task-status poll duration. (Long term: enable Redis async + push so the request returns
  instantly — see `docs/clients/push-setup.md`.)

## 8. Markdown / LaTeX rendering shows raw commands (`\cdot`, etc.) — FIXED (pending device re-test)
- **Resolution:** added a dependency-free converter `latex/LatexUnicode.kt`
  (`latexToUnicode`) and applied it to problem/steps/answer/condition in
  `TaskDetailViewModel` (and in `MathBlock`/`MixedText`). Handles `\cdot`→·,
  `\times`→×, `\frac{a}{b}`→(a)/(b), `\sqrt{}`→√(), `^{}`/`_{}`→Unicode super/subscripts,
  Greek, relations/arrows, accents (`\dot`→ẋ, `\vec`→v⃗), strips `$`/`\(`/`\[`/`\left`,
  and strips the backslash off any unrecognised `\command` (so `\sin`→sin) instead of
  showing it raw.
- **Trade-off:** this is a *prettifier*, not a typesetter — no true fraction/matrix
  layout. If real math layout is wanted later, swap to JLatexMath/markwon ext-latex
  behind the same call site.
- **type:** bug · **area:** `latex/LatexUnicode.kt`, `latex/MathBlock.kt`, `TaskDetailViewModel.kt`
- **Symptom:** raw LaTeX like `\cdot`, `\dot` shows instead of rendered math.
- **Likely cause:** MathView was stubbed to plain monospace `Text`; LaTeX isn't rendered
  or converted to Unicode.
- **Fix direction:** either render LaTeX natively (JLatexMath/markwon ext-latex) or improve
  the LaTeX→Unicode conversion (`\cdot`→·, `\times`→×, `\frac`, super/subscripts).
  Walk the solution JSON: `type:"math"` → render, `type:"text"` → Compose `Text`.

---

## Suggested order
1. **#1 session persistence** (blocks everything — re-login every launch is brutal).
2. **#7 timeout** + **#2b mock-task** + **#2a album assign** (core solve loop must work).
3. **#8 markdown/LaTeX** (solutions must be readable).
4. **#3 real stats** (remove fake numbers).
5. **#5 caption** + **#6 layout** (polish).
6. **#4 language switch** (feature).

Notes: push (#FCM) and Redis async are intentionally deferred (`docs/clients/push-setup.md`).
