# R2-7 plan — merge Home + Archive into one screen

Combine the two near-duplicate screens (Home = design 2, Archive = design 5) into a
single **Home**, and fold in **R2-3 (search)** and **R2-6 (long-press assign + album
filter)** since they belong to the same surface. Do them here, not separately.

## Target screen (one scrollable Home)

```
┌───────────────────────────────────────────┐
│ 🐼  welcome, <name>            🔥 N дн.    │   greeting + streak  (keep)
│ ┌─ БАМБУК НА СЕГОДНЯ ──────────────┐       │   balance card       (keep)
│ │  3  решения   🌿🌿🌿            │       │
│ └─────────────────────────────────┘       │
│ [📚 все 47] [➗ матем 18] [🔤 англ 9] [＋] │   album row + create pill (filter chips)
│ ┌─ 🔍 поиск по решениям… ─────────┐        │   search bar (R2-3)
│ today ───────────────────────────         │
│   ▸ ThreadCard … (tap=open, long=assign)  │   day-grouped list (from Archive)
│   ▸ ThreadCard …                           │
│ yesterday ────────────────────────         │
│   ▸ ThreadCard …                           │
└───────────────────────────────────────────┘
        [ home ]    (⦿ camera)    [ profile ]      bottom bar (Archive tab → Home)
```

Behaviour:
- **Album row** = filter chips. Tap an album → list filters to that album (`?album_id=`),
  chip highlighted. Tap **📚 все** → clear filter (all tasks). Trailing **＋** pill → open
  `CreateAlbumDialog`. (Optional: long-press a pill → open full Albums management screen.)
- **Search bar** → debounced query → `?q=` (R2-3). Combinable with album filter.
- **List** is day-grouped (today / yesterday / earlier), reusing Archive's grouping. Empty
  state when no tasks / no matches (no mock).
- **ThreadCard**: tap → open task; **long-press → album-assign sheet** (R2-6), reusing
  `AlbumPickerDialog`. On assign, refresh the list so the row reflects it.

## Backend changes

1. **Search param** (R2-3): add `q: str | None = Query(None)` to `GET /v1/tasks`
   (`bot/api/v1/tasks.py`), thread through `TaskService.list(..., q=...)` →
   `SupabaseService.list_tasks(..., q=...)`. In the query: when `q` set, case-insensitive
   match on `title`/`input_text` — PostgREST `.or_("title.ilike.*q*,input_text.ilike.*q*")`
   (escape `%`/commas in `q`). Keyset pagination still by `created_at`.
2. `album_id` filter already exists on the route + service — no change.
3. Regenerate `bot/openapi.json`; add a unit test for the `q` filter shape if cheap.
4. **Deploy:** needs redeploy (new query param). No migration.

## Client changes

### Data layer
- `PandaApiService.listTasks(limit, before, albumId?, q?)` — add `@Query("album_id")`,
  `@Query("q")`.
- `TaskRepository.list(limit, before, albumId?, q?)` — pass through.

### `HomeViewModel` (absorbs `HistoryViewModel`)
- State adds: `query: String`, `selectedAlbumId: String?`, and the **day-grouped** list
  (`days: List<DayBucket>` — move `DayBucket` + the grouping helper out of HistoryViewModel),
  plus existing `name/daily/subscription/streak/solvedCount/albums`.
- `refresh()` loads me + albums + `taskRepo.list(limit=50, albumId=selectedAlbumId, q=query)`,
  groups rows by ISO date → buckets (reuse the Archive logic). No sample fallback.
- `setAlbumFilter(id?)`, `setQuery(text)` (debounce ~300 ms in the VM via a `MutableStateFlow`
  + `debounce` collector) → re-list. `assignAlbum(taskId, albumId?)` then refresh.
  `createAlbum(...)` (reuse AlbumRepository) then refresh albums.

### Components
- `ThreadCard` — add an `onLongClick: () -> Unit = {}` and switch its `clickable` to
  `combinedClickable(onClick, onLongClick)`. (`@OptIn(ExperimentalFoundationApi)`.)
- **Album row + ＋ pill**: extend the existing Home album row; append a `＋` `AlbumPill`
  whose onClick opens `CreateAlbumDialog`; chips reflect `selectedAlbumId` (highlight).
- **Bottom bar**: `CuteTab { Archive → Home, Profile, None }`; rename `onArchive` → `onHome`
  in `CuteBottomBar`; the left tab navigates to Home. Update the label string
  (`Strings.navArchive` → `navHome`, ru "главная" / en "home").
- **Search field**: a cute rounded text field above the list, bound to `query`.

### Shared dialogs (extract for reuse)
- Move `AlbumPickerDialog` (currently private in `TaskDetailScreen.kt`) and
  `CreateAlbumDialog` (private in `AlbumsScreen.kt`) into `ui/component/AlbumDialogs.kt` so
  Home + TaskDetail + Albums all share them.

### Navigation (`Navigation.kt`)
- Remove the `ARCHIVE` route + `ArchiveScreen` usage; delete `HistoryScreen.kt` +
  `HistoryViewModel.kt` (logic now in Home).
- All `onArchive = { goTab(ARCHIVE) }` call sites → `onHome = { goTab(HOME) }`.
- Home stays `startDestination` (after the auth SPLASH gate). `i18n` provider unchanged.
- **DECIDED: drop the dedicated Albums screen/route.** Album management is inline on Home:
  `＋` pill → `AlbumEditorDialog` (create); **long-press an album chip → same dialog in edit
  mode** (name/emoji/color **+ Delete** w/ confirm). Gesture language = tap-to-use,
  long-press-to-manage (matches task-card long-press-to-assign). Backend ready
  (`PATCH /v1/albums/{id}` + `DELETE`). Delete `AlbumsScreen.kt`/`AlbumsViewModel.kt` + ALBUMS route.
- **DECIDED: left bottom-bar tab = Home ("Главная"/"Home").**

## Implementation order (one focused pass)
1. **Backend `q`** + openapi + redeploy-note. (Small.)
2. **API/repo** `albumId`+`q` params.
3. **Extract dialogs** to `ui/component/AlbumDialogs.kt`; update TaskDetail/Albums imports.
4. **ThreadCard** long-press support.
5. **HomeViewModel** — absorb grouping + filter/search/assign/create; drop sample fallback.
6. **HomeScreen** — add search bar, day-grouped list, ＋ pill, chip highlight, long-press assign.
7. **Bottom bar + nav** — `CuteTab.Home`, rename callbacks, remove Archive route, delete
   History files, update all CuteBottomBar call sites.
8. Build, sweep `" 2"` dups, install, retest.

## Risks / notes
- **Long list perf**: Home becomes a long `verticalScroll` Column. If it grows, switch the
  task list to `LazyColumn` (day headers as items). Start simple; optimize if janky.
- **Debounced search** must cancel in-flight loads (use `flatMapLatest` on the query flow).
- **combinedClickable** is `ExperimentalFoundationApi` — annotate.
- Removing the Archive tab changes muscle memory; the left tab now = Home (same position).
- `Strings` gains `navHome` + search placeholder; remember EN + RU.
- Keep the empty/loading states honest (no sample) — consistent with #3/R2-4.

## Acceptance
- One Home screen; no separate Archive tab/route.
- Tasks grouped by day; tap opens, long-press assigns album (persists, R2-5).
- Album chips filter the list; ＋ creates an album inline (stays on Home).
- Search filters completed tasks by title/text (after backend `q` ships).
- No mock data anywhere on the screen.
