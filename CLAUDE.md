# PandaSolve / PhotoTaskBot

Photo-to-solution math helper. A user sends a photo (or text) of a problem and gets a
step-by-step solution back. Originally a Telegram bot + FastAPI backend; now also has
native **Android** and **iOS** clients on a shared `/v1/*` API.

## Repository layout

```
bot/                     Python backend + Telegram bot
  app/
    main.py              ← THE entrypoint (mounts /v1, /internal, legacy)
    app.py               legacy FastAPI (/tasker/api/* only) — fallback, do not run alone
    tg_app.py, routers.py  aiogram bot (calls /internal/* via InternalClient)
    deps.py              DI factories (get_db, get_*_service, get_queue)
  api/
    v1/                  mobile API: me, tasks, albums, devices, link, config (JWT auth)
    internal/            bot API: solve, users, link, topup (HMAC auth)
  auth/                  jwt.py (Supabase HS256), internal.py (HMAC), dependencies.py
  services/              user/task/album/billing/device services (business logic)
  supabase_service.py    DB adapter (Supabase Postgres + Storage)
  tasks/                 arq worker (jobs.py) — optional; solve runs inline without Redis
  push/                  APNs + FCM
  schemas/               Pydantic models for /v1/*
  migrations/*.sql       additive SQL; bot/migrate.py runner
  openapi.json           emitted contract; source of truth for mobile codegen
clients/
  android/               Kotlin + Jetpack Compose app (the active client)
  ios/                   SwiftUI scaffold (source tree + Package.swift)
  design/                HTML design mockups (screens-cute.html is the chosen direction)
docs/                    architecture / migration / runbook markdown
tests/unit/              pytest (auth, schemas, HMAC, openapi smoke)
```

## Run

```bash
make run        # uvicorn bot.app.main:app --host 0.0.0.0 --port 8000   ← use THIS, not bot.app.app
make worker     # arq worker (only needed if Redis is configured; otherwise solve is inline)
make bot        # the Telegram bot (python bot/app/tg_app.py)
make migrate    # python -m bot.migrate up   (needs DATABASE_URL); or paste SQL in Supabase editor
make test       # PYTHONPATH=. pytest tests/unit
make lint       # ruff
make openapi    # regenerate bot/openapi.json (CI fails if out of date)
```

Backend env (`.env`): `SUPABASE_URL`, `SUPABASE_KEY` (anon), **`SUPABASE_JWT_SECRET`** (verifies
mobile JWTs — required for `/v1/*`), `USER_EMAIL`/`USER_PASSWORD` (service login),
`OPENAI_API_KEY`, `GOOGLE_API_KEY`, `INTERNAL_AUTH_SECRET` (`openssl rand -hex 32`),
optional `REDIS_URL`, APNs/FCM/Sentry keys. See `.env.example`.

## Architecture

- **Two API surfaces, one service layer.** `/v1/*` (mobile, Supabase JWT, verified locally
  with HS256) and `/internal/*` (bot, HMAC `X-Internal-Auth`) both call into `bot/services/*`,
  which use `supabase_service.py`. The bot signs requests with `bot/internal_client.py`.
- **Identity (IMPORTANT): the live Supabase is the legacy bot schema.** Everything keys on
  **`user_id text`** (Telegram id for bot users; the Supabase-auth UUID stored as text for
  mobile users). `users`/`users_status`/`tasks` have `bigint` identity PKs. There is no UUID
  PK. Migrations are **additive only** (never change PKs — the live bot must keep working):
  `0001` adds `users.auth_user_id` + `account_links`; `0002` adds task-history columns +
  `user_devices`; `0003` adds `albums` + `tasks.album_id`. First mobile sign-in auto-creates a
  `users` row (`user_id = auth uuid`) and seeds `users_status` (daily limit 3).
- **Solving.** `POST /v1/tasks` reserves quota → uploads image → inserts a `pending` task.
  If Redis is configured it enqueues an arq job; **if not, it solves inline in-request**
  (`TaskService._solve_inline`, GPT primary → Gemini fallback) and marks the task done. The
  app polls `GET /v1/tasks/{id}`. Same reserve→solve→refund logic on both paths.
- **Albums** are theme collections (Математика, Английский, …) keyed on `user_id text`; a task
  has at most one `album_id`.

## Android client (`clients/android`)

- Compose + Material 3 + Hilt + Retrofit/OkHttp + Supabase-kt (gotrue) + CameraX. Cute
  "Sticker Study Notebook" theme: pastel palette, Baloo 2 / Nunito / Caveat fonts (bundled
  variable TTFs in `res/font`), hand-drawn panda mascot (`ic_panda.xml`), candy buttons,
  raised camera shutter in the bottom bar.
- Screens: SignIn, Home (bamboo balance + streak + live album row + threads), Camera
  (CameraX live preview → capture → submit), Task (steps + answer + chat + album picker),
  Archive (collapsible days), Albums (scrapbook + create dialog), Profile.
- ViewModels load from `/v1/*` and **fall back to sample data** when the backend is down, so
  the UI never looks broken (`live` flag tracks which).
- `bot/openapi.json` is the contract; `PandaApiService.kt` is hand-rolled to match it
  (swap to the generated client via `./gradlew openApiGenerate` later).

## Conventions

- Russian-first UI copy. Cyrillic look-alike chars in strings are intentional (ruff RUF001-3 off).
- Don't run `bot.app.app:app` alone — `/v1/*` 404s. Always `bot.app.main:app`.
- Keep migrations additive and idempotent (`IF NOT EXISTS`, `DO $$ … EXCEPTION WHEN duplicate_object`).
- When `/v1/*` schemas change, run `make openapi` and commit `bot/openapi.json`.

See `docs/` for deeper architecture/runbooks and the gotchas captured in agent memory.
