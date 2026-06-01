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

---

# Round 2 — post-retest (recorded 2026-05-31, all OPEN)

Captured after testing the Round-1 build. Several depend on each other; see "Order" at
the end. Items mix backend + client.

## R2-1. Task titles (photo tasks show "(фото)") — DONE backend (needs migration 0004 + redeploy)
- **Resolution:** added an optional `title` to the GPT solver prompt
  (`LATEX_TASK_HELPER_PROMPT_TEMPLATE_USER`) + the `Solution` schema. `mark_task_done` stores a
  derived title via `_derive_title()` (model's `title`, else first problem statement trimmed —
  so Gemini-fallback and title-less solves still get a label). New migration `0004_task_title.sql`
  (`tasks.title`). `list_tasks` selects it and `task_service.list` preview chain is now
  `title → input_text → "(фото)"`. **Client needs no change** — it already renders `preview`.
  `openapi.json` regenerated; 37 tests + ruff green.
- **Deploy:** apply `0004` (else `mark_task_done` errors writing the new column) + redeploy.
  Only **new** solves get titles; old image rows still show "(фото)" (no backfill).
- **type:** feature · **area:** `bot/constants.py`, `bot/schemas/task.py`, `bot/supabase_service.py`, `bot/services/task_service.py`, `bot/migrations/0004_task_title.sql`
- **Symptom:** list/preview shows "(фото)" for image tasks — no meaningful label.
- **Approach:** add a `title` field to the solver's JSON output (a short phrase capturing the
  task, in the task's language). Add `title` to the prompt schema in `constants.py`, persist it
  (new `tasks.title` column — additive migration `0004`), surface it on `TaskListItem`
  (fallback to `input_text`/"(фото)" when absent for old rows). Client shows `title` in
  list rows and Task detail header. **Foundation for R2-3 (search).**

## R2-2. Chat on a solution ("спросить ещё") — not working
- **type:** feature · **area:** new `POST /v1/tasks/{id}/chat` + a `task_messages` table;
  `gpt_service`/`gemini_service`; client `TaskDetailScreen` chat bar + a `ChatViewModel`.
- **Symptom:** the "спросить ещё…" bar is inert (we removed the fake bubbles in #3; never wired).
- **Approach:** persist a per-task message thread (`task_messages(id, task_id, role, content,
  created_at)`); endpoint takes a question, calls the LLM with the original problem + solution +
  prior turns as context, stores both turns, returns the reply. Client renders the thread and
  sends. Costs a solve-credit? — decide (probably free or cheaper). Streaming optional.

## R2-3. Search tab over completed tasks  (depends on R2-1)
- **type:** feature · **area:** `GET /v1/tasks?q=` (ILIKE on `title`/`input_text`), client search UI.
- **Approach:** add a `q` query param to the task list endpoint; case-insensitive match on
  title + input_text (+ maybe solution text). Client: a search field (folded into the merged
  Home per R2-7) filtering the list. Best after R2-1 so titles are searchable.

## R2-4. Albums screen flashes mock albums before real ones — FIXED (pending device re-test)
- **Resolution:** `AlbumsUiState` defaulted to `sampleAlbums` and only replaced them
  `if (list.isNotEmpty())` (so a zero-album user saw mock forever). Now defaults to empty and
  always sets the real result on load. Client-only — no backend redeploy needed.
- **type:** bug · **area:** `ui/feature/albums/AlbumsViewModel.kt` (+ Screen).
- **Symptom:** opening Albums shows sample albums for ~1s, then the real ones.
- **Cause:** same sample-default pattern we removed from Home/Archive/Profile — the Albums
  state still defaults to sample data.
- **Fix:** default to empty/loading, drop the sample fallback (mirror the #3 changes).

## R2-5. Task→album relation missing after app restart — FIXED (needs backend redeploy + re-test)
- **Resolution:** confirmed the relation was persisted (`tasks.album_id`) but never surfaced.
  Added `album_id` to the backend `TaskDetail` schema + `task_service.get` (`get_task` already
  `select("*")`), added `albumId` to the client `TaskDetail` model, and `TaskDetailViewModel.load()`
  now resolves `albumName` from the loaded album list by `albumId` — so the badge survives a
  restart, not just an in-session assign. No join table needed (one album per task).
  `openapi.json` regenerated; 37 tests + ruff green. **Needs backend redeploy** for the new
  `album_id` field to appear in `/v1/tasks/{id}`.
- **type:** bug · **area:** `bot/schemas/task.py` (TaskDetail), `bot/services/task_service.py`
  (`get`), client `Models.TaskDetail`, `TaskDetailViewModel.load()`, `TaskDetailScreen`.
- **Symptom:** assign an album, reopen app, open the task → album no longer shown.
- **Root cause (NOT a missing table):** the relation **is** persisted in `tasks.album_id`
  (one album per task). The bug is it's never surfaced: `TaskDetail` has no `album_id`/album
  fields on the backend OR client, and `load()` only sets `albumName` after an in-session
  assign — it never reads the stored album on open. So after restart there's nothing to show.
- **Fix:** add `album_id` (+ optional album name/emoji) to the backend `TaskDetail` schema and
  `task_service.get`, add the field to the client `TaskDetail` model, and have
  `TaskDetailViewModel.load()` populate `albumName` from it. A join table is only needed if we
  want **multiple** albums per task — not required for current one-album design.

## R2-6. Long-press to assign album from the list; filter shows only that album
- **type:** feature · **area:** client list (merged Home per R2-7); backend filter already exists.
- **Symptom/ask:** long-tap a task in the main list → assign-album sheet; default = all tasks;
  selecting an album filters to only its tasks.
- **Note:** backend already supports `GET /v1/tasks?album_id=` (see `task_service.list`). This is
  mostly client UX: a long-press `combinedClickable` → album picker (reuse `AlbumPickerDialog`),
  and album filter chips driving the `album_id` param. Pairs with R2-7.

## R2-7. Merge Home + Archive into one screen  (LARGE — do last)
- **type:** refactor/feature · **area:** `ui/feature/home/*`, `ui/feature/history/*`, `Navigation.kt`,
  `CuteComponents` bottom bar.
- **Ask:** Home and Archive (designs 2 & 5) are duplicative. Combine into one Home that has:
  the **search bar** (from Archive, R2-3), tasks **grouped by day** (today/yesterday/earlier),
  the **album row with a trailing "＋" pill** to create an album inline, and **long-press a task
  to assign an album** (R2-6). Filtering by album shows only that album's tasks; otherwise all.
- **Impact:** removes the Archive tab/route; bottom bar gets one fewer destination; fold
  `HistoryViewModel` logic into `HomeViewModel`. Touches nav graph + bottom bar layout.

## R2-8. Settings: language as a dropdown (not a toggle) — FIXED (pending device re-test)
- **Resolution:** added `supportedLanguages` (code+label list) in `i18n/Localization.kt`;
  the Profile "🌍 Язык" row now opens a Material3 `DropdownMenu` over that list and calls the
  generalized `SettingsViewModel.setLanguage(code)` (replaced `toggleLanguage`). Adding a
  language later = one entry in `supportedLanguages` (+ an `EnStrings`-style table). Client-only.
- **type:** polish · **area:** `i18n/Localization.kt`, `ui/feature/settings/SettingsScreen.kt`, `SettingsViewModel`.
- **Ask:** replace the ru↔en tap-toggle with a `DropdownMenu` so more languages can be added.
- **Note:** infra already supports it — `LanguageManager.set(code)` + `stringsFor(code)`; just
  add a menu listing available languages and call `setLanguage(code)` (rename `toggleLanguage`).

## Round-2 order / dependencies
1. **R2-5** (album relation) + **R2-4** (albums mock flash) — small, high-value correctness.
2. **R2-1** (titles) — unblocks R2-3; improves every list.
3. **R2-8** (language dropdown) — quick polish.
4. **R2-7** (merge Home+Archive) — large; absorbs **R2-3** (search) and **R2-6** (long-press
   assign + album filter), so do those *as part of* R2-7 rather than twice.
5. **R2-2** (chat) — independent, sizable feature; schedule on its own.
