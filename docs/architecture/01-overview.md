# 01 — System Overview

## Why we are doing this

PhotoTaskBot today is a Telegram-only product. Users submit a photo of a math problem (optionally with a text caption) or plain text, and receive a rendered LaTeX solution back as a PNG. The product works, the funnel is converting paid solves via Telegram Stars, and the owner wants to broaden distribution by shipping native Android (Kotlin) and iOS (Swift) clients.

The current backend was built around a single trusted client (the bot). For mobile we need:

1. A real authentication boundary (JWTs from Supabase Auth, not client-supplied numeric IDs).
2. An asynchronous solve API that does not hold a 10–30 second HTTP connection on cellular.
3. A user identity that does not assume Telegram as the only source.
4. Push notifications (APNs / FCM).
5. A history view (the bot stores history but never exposes it back).
6. A documented, versioned API surface (`openapi.json`).

The Telegram bot stays live the entire time. Mobile gets a parallel `/v1/*` API surface; the bot's existing endpoints become `/internal/*` behind an HMAC header.

## Current state (as of 2026-05)

```
┌──────────────────┐    HTTP, no auth, user_id   ┌─────────────────────┐
│  Telegram bot    │ ─────────────────────────►  │  FastAPI            │
│  (aiogram 3.8)   │                             │  bot/app/app.py     │
└──────────────────┘                             └──────────┬──────────┘
                                                            │
                                  ┌─────────────────────────┼──────────────────────┐
                                  ▼                         ▼                      ▼
                          ┌──────────────┐         ┌──────────────────┐   ┌──────────────────┐
                          │  Supabase    │         │  OpenAI GPT-5    │   │  Google Gemini   │
                          │  Postgres +  │         │  primary solver  │   │  fallback solver │
                          │  Storage     │         └──────────────────┘   └──────────────────┘
                          └──────────────┘
```

- Twelve endpoints under `/tasker/api/*`. All accept `user_id` as a form field.
- Bot reads the multipart response and renders LaTeX → PNG via local `pdflatex` + `pdftoppm`.
- Postgres tables: `users` (PK = Telegram ID INTEGER), `users_status` (limits per user), `tasks` (solution history JSON).
- Storage bucket `tasks/`, object path `/task_images/{telegram_id}/{file}.png`.
- No CI/CD. No tests covering the production paths. Two latent concurrency bugs (see `02-identity-and-auth.md` and `08-observability.md`).

## Target state

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Android      │  │ iOS          │  │ Telegram bot │
│ Compose +    │  │ SwiftUI +    │  │ (aiogram)    │
│ JLatexMath   │  │ iosMath      │  │              │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │ JWT             │ JWT             │ HMAC
       └────────┬────────┴─────────────────┘
                ▼
    ┌─────────────────────────────────────┐
    │  FastAPI                            │
    │    /v1/*    (mobile, JWT)           │
    │    /internal/*  (bot, HMAC)         │
    │  bot/services/* (shared logic)      │
    └────────┬────────────────────────────┘
             ▼
    ┌─────────────────────────────────────┐         ┌──────────────────┐
    │  Redis (arq queue + rate limits)    │ ──────► │ Solver workers   │
    └────────┬────────────────────────────┘         │ OpenAI + Gemini  │
             ▼                                      └────────┬─────────┘
    ┌─────────────────────────────────────┐                  │
    │  Supabase                           │ ◄────────────────┘
    │    Postgres (UUID PKs, RLS)         │
    │    Storage (signed URLs)            │
    │    Auth (issues JWTs)               │
    └─────────────────────────────────────┘
                                                ┌──────────────────────────┐
                                                │ APNs HTTP/2 + FCM HTTP v1│
                                                └──────────────────────────┘
```

Distinct from today:

1. **Two API surfaces, one service layer.** `bot/api/v1/` (public, JWT) and `bot/api/internal/` (bot, HMAC) both call into `bot/services/`. The Supabase wrapper (`bot/supabase_service.py`) becomes a thin DB adapter; business logic moves into services.
2. **Async solving.** `POST /v1/tasks` enqueues an arq job and returns immediately. Workers solve and push when done; clients poll or react to push. The bot still uses a synchronous `/internal/solve` for backward compatibility during the transition.
3. **UUID identity.** `users.id UUID` is the new PK. Telegram ID and Supabase Auth ID are nullable columns. See `02-identity-and-auth.md` for the full migration.
4. **Native LaTeX rendering on mobile.** Server returns the solution JSON; mobile renders math on-device (JLatexMath, iosMath). Bot keeps its pdflatex path.
5. **Push notifications.** New `user_devices` table. Backend talks APNs HTTP/2 and FCM HTTP v1 directly — no Firebase-as-APNs-proxy.

## Non-goals (explicit)

- In-app purchases on mobile. Mobile users top up via the Telegram bot deep link until we decide on RevenueCat vs. native IAP.
- A web frontend. Not in this release.
- A web admin console. Telegram admin commands stay.
- Server-side LaTeX rendering for mobile (mobile renders natively).

## Glossary

See [`../README.md#glossary`](../README.md#glossary).

## Reading order for new engineers

1. This doc.
2. `02-identity-and-auth.md` — the most load-bearing change. Read carefully.
3. `04-async-solving.md` — the second-most load-bearing change.
4. `03-backend-api.md` — the contract you'll implement against.
5. Then whichever vertical you own: `clients/android.md`, `clients/ios.md`, or back to architecture docs `05–09`.
