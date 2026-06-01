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

## R2-2. Chat on a solution ("спросить ещё") — DONE (needs migration 0005 + redeploy; re-test)
- **Resolution (backend):** migration `0005_task_messages.sql` (`task_messages(task_id, user_id,
  role, content, created_at)`); `GET`/`POST /v1/tasks/{id}/chat` (`ChatThread`/`ChatRequest`);
  `TaskService.chat`/`chat_history` build context from the task's problem+solution+prior turns and
  call `TaskSolverGPT.generate_chat_reply` (plain-text `responses.create`, no structured format),
  storing both turns. GPT-only for now (graceful fallback message on error). openapi 13 paths;
  37 tests + ruff green.
- **Resolution (client):** `ChatMessage`/`ChatThread`/`ChatSendRequest` models; `getChat`/`postChat`
  in the API + `TaskRepository.chatHistory`/`sendChat`; `TaskDetailViewModel` loads the thread and
  `sendChat` (with a `sending` flag); `TaskDetailScreen` renders the thread (`Bubble`s, LaTeX→Unicode)
  and the "спросить ещё" bar is now a live `BasicTextField` + send button ("панда печатает…" while sending).
- **Deploy:** apply `0005` + redeploy. **Future:** Gemini fallback for chat; streaming.
- **type:** feature · **area:** `bot/{migrations/0005,schemas/task,gpt_service,supabase_service,services/task_service,api/v1/tasks}`, client models/api/repo + TaskDetail VM/screen.
- **Symptom:** the "спросить ещё…" bar is inert (we removed the fake bubbles in #3; never wired).
- **Approach:** persist a per-task message thread (`task_messages(id, task_id, role, content,
  created_at)`); endpoint takes a question, calls the LLM with the original problem + solution +
  prior turns as context, stores both turns, returns the reply. Client renders the thread and
  sends. Costs a solve-credit? — decide (probably free or cheaper). Streaming optional.

## R2-3. Search over completed tasks — DONE (with R2-7; needs backend redeploy)
- **Resolution:** added `q` query param to `GET /v1/tasks` (ILIKE on `title`/`input_text`,
  PostgREST `.or_`, special chars stripped) → `TaskService.list` → `SupabaseService.list_tasks`.
  Client: `listTasks`/`TaskRepository.list` gain `q`; the merged Home has a search field with a
  300ms debounce in `HomeViewModel.onQueryChange`. Needs backend redeploy for `q` to work.
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

## R2-6. Long-press assign + album filter — DONE (with R2-7)
- **Resolution:** `ThreadCard` gained `onLongClick` (`combinedClickable`); long-press a task on
  Home opens `AlbumPickerDialog` → `HomeViewModel.assignAlbum` (persists via `tasks.album_id`).
  Album chips drive `setAlbumFilter(id)` → `?album_id=` (backend route already supported it);
  "📚 все" clears the filter. Client-only (backend filter pre-existed).
- **type:** feature · **area:** client list (merged Home per R2-7); backend filter already exists.
- **Symptom/ask:** long-tap a task in the main list → assign-album sheet; default = all tasks;
  selecting an album filters to only its tasks.
- **Note:** backend already supports `GET /v1/tasks?album_id=` (see `task_service.list`). This is
  mostly client UX: a long-press `combinedClickable` → album picker (reuse `AlbumPickerDialog`),
  and album filter chips driving the `album_id` param. Pairs with R2-7.

## R2-7. Merge Home + Archive into one screen — DONE (needs backend redeploy for search; re-test)
- **Resolution:** one Home now carries greeting/streak, balance, **album filter chips + ＋
  create pill**, **search field**, and a **day-grouped task list** (today/вчера/ранее).
  `HomeViewModel` absorbed `HistoryViewModel` (grouping) + filter/search/assign/create/edit/delete.
  Tap a card = open; **long-press = assign album**. Album chips filter; **long-press a chip =
  edit/delete** via a shared `AlbumEditorDialog` (create+edit+delete); `＋` = create. Extracted
  `AlbumPickerDialog` + `AlbumEditorDialog` + `AlbumOption` into `ui/component/AlbumDialogs.kt`.
  Bottom bar left tab is now **Home** (`CuteTab.Home`, "Главная"/"Home", 🏠). **Deleted**
  `ArchiveScreen`/`HistoryViewModel`/`AlbumsScreen`/`AlbumsViewModel` + the ARCHIVE/ALBUMS routes.
  Added client `updateAlbum` (PATCH) plumbing. Build green.
- **Known minors — FIXED:** day labels now localized (`dayToday/dayYesterday/dayEarlier` in
  `Strings`; `DayBucket` dropped `tape`, label chosen by index in the screen); removed dead
  `sampleThreads`/`sampleAlbums`/`SampleAlbum`/`toSampleAlbum`; Home list converted to `LazyColumn`
  (header is one item, each day group an item).
- **type:** refactor/feature · **area:** `ui/feature/home/*`, deleted history/albums, `Navigation.kt`, `CuteComponents`, `AlbumDialogs.kt`.
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

---

# Round 3 — post-retest (recorded 2026-06-01, all OPEN)

Captured after testing the merged-Home + chat build. Mix of quick polish, client
features, and a few backend pieces. Order/grouping at the end.

## R3-1. Chat input hidden by keyboard — FIXED (pending re-test)
- **Resolution:** chat bar gets `imePadding()` + `navigationBarsPadding()` so it rides above the
  keyboard; hoisted the scroll state and added `LaunchedEffect(chat.size, sending){ animateScrollTo(max) }`
  so the newest message stays visible.
- **type:** bug · **area:** `TaskDetailScreen.kt` (chat bar + scroll container).
- **Symptom:** typing in "спросить ещё" — the IME covers the input; the view doesn't scroll up.
- **Fix:** add `Modifier.imePadding()` to the chat bar (and/or the screen), and auto-scroll the
  content to the newest message on focus/send. The screen is a `verticalScroll` Column with the
  bar overlaid at `BottomCenter` — likely switch to a layout that lifts the bar above the IME
  (`Scaffold`/`imePadding`/`WindowInsets.ime`).

## R3-2. Task title shows raw LaTeX — FIXED (pending re-test)
- **Resolution:** `toRow` runs the preview through `latexToUnicode` (covers old rows too).
- **type:** bug · **area:** `ui/sample/Mappers.kt` `toRow` (preview) — or backend `_derive_title`.
- **Cause:** the LLM `title`/first-problem text contains LaTeX; the list shows it raw.
- **Fix:** run `latexToUnicode` on the preview in `toRow` (client), or strip LaTeX in
  `_derive_title` (backend). Client-side is simplest and covers old rows.

## R3-3. Rename a task (long-press) — DONE (needs redeploy + re-test)
- **Resolution:** `PATCH /v1/tasks/{id}` (`TaskUpdate.title`) → `TaskService.rename` → `update_task_title`. Client: long-press a task → chooser (To album / Rename); rename dialog → `HomeViewModel.renameTask`.
- **type:** feature · **area:** new `PATCH /v1/tasks/{id}` (title); long-press menu on Home.
- **Cause/approach:** `tasks.title` already exists (0004). Add an endpoint to update it +
  `TaskService`/`SupabaseService` method. Client: long-press a task → action sheet with
  **Assign album** + **Rename** (rename → text dialog → `PATCH`, refresh). Currently long-press
  only opens the album picker — needs a small chooser first.

## R3-4. Task detail doesn't show its album — VERIFY after redeploy (no new code)
- **Note:** R2-5 already returns `album_id` + resolves the badge; just confirm once the backend is redeployed.
- **type:** bug · **area:** R2-5 path; verify backend redeploy + the chip rendering.
- **Note:** R2-5 added `album_id` to `TaskDetail` + resolves the badge — confirm the backend was
  redeployed (field present) and the chip shows the album name, not "выбрать альбом". May also
  want it more prominent (label "Альбом: …").

## R3-5. Empty-search state — FIXED (pending re-test)
- **Resolution:** added `Strings.searchEmpty`; Home shows it when `query` is non-blank and no results.
- **type:** polish · **area:** `HomeScreen.kt` (empty branch).
- **Fix:** when `query` is non-blank and `days` is empty, show "Ничего не нашлось — попробуй
  иначе" / "Nothing here — try another search" (distinct from the no-tasks-yet message). Add a
  `Strings` key for it.

## R3-6. Rename user (display name) — DONE (needs migration 0006 + redeploy)
- **Resolution:** migration `0006` adds `users.display_name`; `MeResponse`/`UpdateMeRequest`/`User` carry it; `update_user_display_name` + `user_service.update_display_name`; `/v1/me` returns + updates it. Client: ✏️ next to the name → rename dialog → `SettingsViewModel.setName`; Home/Profile prefer `display_name` over the email prefix.
- **type:** feature · **area:** `users` display name (additive migration) + `POST /v1/me`;
  `SettingsScreen` name + pencil.
- **Approach:** add `users.display_name` (or reuse `first_name`); extend `UpdateMeRequest` +
  `MeResponse` with `display_name`; Profile shows the name with a ✏️ that opens a rename dialog →
  `POST /v1/me`. Home greeting then uses it too (instead of the email local-part).

## R3-7. Notifications On/Off switch — DONE (pref persists; delivery needs FCM)
- **Resolution:** `NotifPrefs` (SharedPreferences) + a Material `Switch` on Profile via `SettingsViewModel.setNotifications`. Persists the opt-in; actual push delivery still requires `google-services.json` (see push-setup.md). FCM registration should consult `NotifPrefs` once configured.
- **type:** feature · **area:** `SettingsScreen` row → `Switch`; `DeviceRepository` register/unregister.
- **Will it work?** Yes mechanically: ON → register FCM token (`/v1/devices`), OFF → unregister
  (`DELETE /v1/devices/{token}`); persist the pref (DataStore/SharedPrefs). **But** actual push
  delivery still needs the Firebase setup (`google-services.json`) from `docs/clients/push-setup.md`.
  So the switch controls opt-in; pushes arrive only once FCM is configured.

## R3-8. Profile action rows: bold font — FIXED (pending re-test)
- **Resolution:** `Row2` label weight W600→W800.
- **type:** polish · **area:** `SettingsScreen.kt` `Row2` label.
- **Fix:** bump the row label `FontWeight` (W600 → W700/W800) for "Пополнить бамбук", "Telegram", etc.

## R3-9. Home: remove the ✿ next to the nickname — FIXED (pending re-test)
- **Resolution:** greeting now shows just the name.
- **type:** polish · **area:** `HomeScreen.kt` greeting.
- **Fix:** drop the `"${s.name} ✿"` flower → just the name.

## R3-10. Home: bamboo leaves when balance > 5 — FIXED (pending re-test)
- **Resolution:** leaf row capped at 5; a `+N` mint badge shows the overflow (the big number is exact).
- **type:** bug/design · **area:** `HomeScreen.kt` leaf row.
- **Cause:** leaves are `repeat(daily.coerceIn(0,5))` — caps at 5, so >5 (e.g. via subscription)
  looks wrong. **Fix:** decide a representation for >5 — e.g. show 5 leaves + a "×N" / numeric
  badge, or render the number prominently and leaves as a small accent. Needs a design call.

## R3-11. Home: collapsible day groups — FIXED (pending re-test)
- **Resolution:** each day header is clickable with a ▾/▸ chevron; per-day `dayOpen` map (today open by default).
- **type:** feature · **area:** `HomeScreen.kt` day sections.
- **Cause:** the old Archive had collapsible days with a chevron; the merged Home shows all
  expanded. **Fix:** make each day header clickable with a ▸/▾ chevron toggling its task list
  (per-day expanded state; default today open).

## R3-12. Albums: "＋" emoji picker — FIXED (pending re-test)
- **Resolution:** a ＋ tile after the preset emojis opens a text field to paste any emoji (localized hint); highlights when a custom one is set.
- **type:** feature · **area:** `AlbumDialogs.kt` (`AlbumEditorDialog` emoji row).
- **Fix:** add a `＋` tile after the fixed `ALBUM_EMOJIS` that lets the user enter any emoji
  (a tiny text field accepting one glyph, or a larger emoji grid/system picker).

## R3-13. Albums: create/edit dialog not localized — FIXED (pending re-test)
- **Resolution:** added 13 `Strings` keys; `AlbumEditorDialog` + `AlbumPickerDialog` read `LocalStrings`.
- **type:** bug · **area:** `AlbumDialogs.kt` (+ `Strings`).
- **Cause:** `AlbumEditorDialog`/`AlbumPickerDialog` have hardcoded Russian ("Новый альбом",
  "НАЗВАНИЕ", "ЗНАЧОК", "ЦВЕТ", "Создать/Сохранить/Удалить/Отмена", "В какой альбом?",
  "Без альбома", placeholder). **Fix:** add `Strings` keys + read `LocalStrings.current`.

## R3-14. Layout doesn't fit the phone screen — FIXED (first pass, pending re-test)
- **Resolution:** edge-to-edge insets — `statusBarsPadding()` wraps the nav content (MainActivity), `navigationBarsPadding()` on the bottom bar + the task chat bar. If a specific screen still clips, point me at it.
- **type:** bug · **area:** screen roots (insets).
- **Cause (likely):** screens don't apply system-bar insets, so content sits under the status/nav
  bars. **Fix:** apply `WindowInsets.statusBars`/`navigationBars`/`safeDrawing` padding at the
  screen roots (or `Scaffold`); verify on-device. Related to R3-1 (ime insets).

## R3-15. Day headers: capitalize + format dates — FIXED (pending re-test)
- **Resolution:** labels capitalized; dates formatted `2026-05-30`→`30 мая`/`May 30` (lang from `LocalStrings`); slightly bigger/bolder. NOTE: exact screen-5 styling can be refined further if needed.
- **type:** polish · **area:** `HomeScreen.kt` day header + date formatting; `Strings`.
- **Fix:** "today" → "Today"/"Сегодня" (capitalized); format the date (ISO `2026-05-30` →
  "30 мая" / "May 30") instead of the raw prefix; match the tape/heading styling in
  `clients/design/screens-cute.html` (screen 5). Date formatting probably belongs in the VM or a
  small helper.

## R3-16. Free chat limit (3 then top-up) — DONE (needs migration 0005 already + redeploy)
- **Resolution:** `FREE_CHAT_LIMIT=3` per task in `TaskService` (`_remaining` counts user msgs); at the limit `chat()` returns without an LLM call. `ChatThread.remaining` surfaced. Client shows 'осталось N', blocks the input at 0 and shows the top-up prompt (`chatLimitReached`). NOTE: a one-tap top-up button (fetch `/v1/topup/url` + open Telegram) is a small follow-up; for now it directs to the Profile top-up row.
- **type:** feature · **area:** `bot/services/task_service.chat` + billing; client chat UI.
- **Approach:** allow N free assistant replies per task (or per user); count existing `user`
  messages in `task_messages`; when exceeded, return a limit signal (e.g. 402 / a flag) instead of
  calling the LLM. Client shows remaining ("осталось 2 из 3") and, when exhausted, a top-up prompt
  → Telegram deep link (`/v1/topup/url`). Decide free-count scope (per task vs per day) + whether
  it consumes the bamboo balance instead of a separate counter.

## Round-3 order / grouping
1. **Quick polish (client-only):** R3-9 (flower), R3-8 (bold), R3-2 (title LaTeX), R3-5 (empty
   search), R3-13 (localize album dialogs), R3-15 (day headers).
2. **Client UX:** R3-1 (chat keyboard), R3-11 (collapsible days), R3-14 (insets/fit),
   R3-12 (emoji picker +), R3-10 (>5 leaves — needs design call), R3-4 (verify album badge).
3. **Backend + client features:** R3-6 (rename user), R3-3 (rename task), R3-7 (notif switch),
   R3-16 (free chat limit).

---

# Round 4 — post-retest (recorded 2026-06-01)

## R4-1. Home name didn't match the renamed display name — FIXED
- **Cause:** `HomeViewModel` derived the greeting from the email prefix, ignoring `me.displayName`
  (only Profile used it). **Fix:** added `displayName(me)` helper used in initial state + refresh
  (prefers `display_name`, falls back to email prefix). Needs backend redeploy for `display_name`.

## R4-2. Returning from camera, Home renders in two stages (bottom then top) — OPEN (mitigated)
- **type:** bug (perf/layout) · **area:** `Navigation`/`HomeScreen`/insets.
- **Hypothesis:** on pop-back the destination recomposes; the bottom bar (simple, BottomCenter)
  paints before the LazyColumn settles, and/or `statusBarsPadding` recomputes after the camera
  teardown so the top shifts a frame later.
- **Mitigation shipped:** Home now seeds from cached `Me` (R4-4) + retains VM state, so content is
  present immediately instead of empty→full. **Re-test** — if the staged paint persists it likely
  needs a nav enter-transition / hoisting insets per-screen; profile on device.

## R4-3. Bottom-bar labels ("Главная"/"Профиль") clipped — FIXED (pending re-test)
- **Cause:** bar shrunk to 84dp (Round-1 #6) + longer labels → vertical clip. **Fix:** bar 84→92dp,
  Row bottom padding 22→14, labels `maxLines=1, softWrap=false`.

## R4-4. Solved/achievement counts wait for load — FIXED (session cache)
- **Resolution:** `UserRepository.lastMe` + `AlbumRepository.lastCount` cache the last load
  in-memory; `SettingsViewModel`/`HomeViewModel` seed their initial state from them, so counts show
  instantly on re-open and then refresh. (First-ever load still fetches; cache is per app session.)
- **Follow-up if needed:** persist the cache to DataStore to survive cold starts.

---

# Round 5 — post-retest (recorded 2026-06-01)

## R5-1. Task detail waits to load — FIXED (pending re-test)
- **Resolution:** `TaskRepository` now caches loaded `TaskDetail`s; `TaskDetailViewModel` paints
  instantly from cache on re-open. The first load is also faster: the task GET runs **concurrently**
  with albums + chat (previously it was queued behind both). `applyTask` re-resolves the album badge
  when albums arrive. Cache is per app session.
- **type:** perf · **area:** `data/repository/TaskRepository.kt`, `ui/feature/task/TaskDetailViewModel.kt`

## R5-2. Language selector on sign-in + EN default — FIXED (pending re-test)
- **Resolution:** `LanguageManager` now defaults to **en** on first run (was device-language).
  Sign-in screen got a RU/EN selector (chips, top-right) wired to `SignInViewModel.setLanguage` →
  `LanguageManager` → `LocalStrings` updates live. Localized the sign-in copy (greeting, title,
  subtitle, email/password labels, sign-in button, OR divider, terms) via new `Strings` keys.
- **type:** feature · **area:** `i18n/{LanguageManager,Localization}.kt`, `ui/feature/auth/{SignInScreen,SignInViewModel}.kt`

## R5-3. Backend: speed up loading solutions — FIXED (needs redeploy)
- **Root cause:** the slowness wasn't the DB read — it was **Supabase Storage signed-URL
  generation** the client never uses. `task_service.get` made 2 Storage round-trips per detail
  (thumbnail + image); `task_service.list` made **one per row** (up to 50 sequential calls).
  The list/detail SQL is already indexed (`tasks_user_created_idx`).
- **Fix:** stop generating those signed URLs (client renders math natively, shows no image) —
  `thumbnail_url`/`image_url` now return null. List drops from (1 + N) round-trips to 1; detail
  from 3 to 1. Re-add lazily / behind a `?thumbnails=true` flag if a client ever needs them.
- **type:** perf (backend) · **area:** `bot/services/task_service.py`. **Needs redeploy.**

---

# Round 6 — Android camera (recorded 2026-06-01)

## R6-1. Remove green framing brackets — FIXED
- Removed the 4 `CornerBracket` overlays (and the now-unused composable) from `SolveScreen`.
  The "наведи на задачу ✏️" hint stays.

## R6-2. Flashlight (torch) button — FIXED
- The top-right ⚡ button now toggles `camera.cameraControl.enableTorch()`. Captured the bound
  `Camera` from `bindToLifecycle`; button highlights (butter bg) when on; torch resets on rebind.

## R6-3. Pinch-to-zoom — FIXED
- Added `detectTransformGestures` on the preview `AndroidView`; pinch scales
  `cameraControl.setZoomRatio(current * zoom)` clamped to the camera's min/max zoom (stock-camera feel).

All three: client-only, build green. `SolveScreen.kt`.
