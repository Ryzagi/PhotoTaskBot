# 03 — Backend API

The live source of truth is `openapi.json`, served at `/openapi.json` and viewable at `/docs`. This file is the human-readable companion: invariants, error model, and the rationale behind shapes.

## Versioning

- **`/v1/*`** — mobile-facing, public. JWT-authenticated. Stable; breaking changes require a new major version (`/v2/*`).
- **`/internal/*`** — bot-facing, private network. HMAC-authenticated. May change without notice; both bot and backend ship together.
- **`/healthz`** — liveness, no auth.

Do not put the bot endpoints under `/v1/`. Mixing internal and public surfaces under one prefix is how internal endpoints leak.

## Auth

| Surface | Header | Verifier |
|---|---|---|
| `/v1/*` | `Authorization: Bearer <supabase_jwt>` | `bot/auth/jwt.py` (HS256, local verify) |
| `/internal/*` | `X-Internal-Auth: t=…;sig=…` | `bot/auth/internal.py` (HMAC-SHA256, ±60s) |

A request missing or failing auth returns `401`. A request with valid auth but insufficient privilege (e.g., admin route) returns `403`.

## Endpoints (mobile surface)

### Identity

| Method | Path | Body / params | Returns |
|---|---|---|---|
| `GET`  | `/v1/me` | — | `{id, telegram_linked, language_code, balance: {daily, subscription}, created_at}` |
| `POST` | `/v1/me` | `{language_code?}` | Updated `User` |
| `POST` | `/v1/auth/link/start` | — | `{code, expires_at}` |
| `POST` | `/v1/devices` | `{platform: "ios"\|"android", token, app_version, locale}` | `{id}` |
| `DELETE` | `/v1/devices/{token}` | — | `204` |

### Solving

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/v1/tasks` | `multipart`: `file`, `caption?` (image task) OR `application/json`: `{text}` (text task) | `{task_id, status: "pending"}` |
| `GET`  | `/v1/tasks/{id}` | — | `{id, status, created_at, input_kind, thumbnail_url?, solution?, error_code?}` |
| `GET`  | `/v1/tasks` | `?limit=20&before=<iso8601>` | `{items: [...], next_before?: <iso8601>}` |
| `POST` | `/v1/tasks/{id}/latex-to-text` | — | `{solution}` (Unicode-rendered) |

### Misc

| Method | Path | Returns |
|---|---|---|
| `GET` | `/v1/topup/url` | `{url: "tg://resolve?domain=PandaSolveBot&start=topup"}` |
| `GET` | `/v1/config` | `{daily_limit, max_image_bytes, supported_locales}` |
| `GET` | `/healthz` | `{status: "ok"}` |

## Endpoints (internal surface)

| Method | Path | Notes |
|---|---|---|
| `POST` | `/internal/users` | Upsert Telegram user (called by bot `/start`) |
| `POST` | `/internal/auth/link/confirm` | Bot calls this when user pastes a code |
| `POST` | `/internal/tasks/solve` | Synchronous solve for the bot. Image or text. Same response shape as legacy `/tasker/api/solve_task`. |
| `POST` | `/internal/topup` | Bot calls after successful Telegram Stars payment |
| `POST` | `/internal/broadcast` | Admin broadcast |
| `GET`  | `/internal/users` | Admin list (used for broadcasts) |

The bot's existing `/tasker/api/*` endpoints stay as `/internal/*` shims for one release cycle, then get removed.

## Error model

Every error response is the same shape. No bare strings, no inconsistent envelopes.

```json
{
  "error": {
    "code": "rate_limited",
    "message": "Daily limit reached. Try again after midnight UTC or top up via Telegram.",
    "details": { "retry_after_seconds": 23400 }
  }
}
```

Codes used (extend, do not invent ad-hoc):

| Code | HTTP | Meaning |
|---|---|---|
| `unauthorized` | 401 | Missing/bad/expired JWT |
| `forbidden` | 403 | Auth OK but not allowed |
| `not_found` | 404 | Resource does not exist or RLS hid it |
| `validation_failed` | 422 | Body failed pydantic validation; `details.fields` populated |
| `rate_limited` | 429 | Exceeded per-user or per-IP limit; `details.retry_after_seconds` |
| `daily_limit_reached` | 429 | Out of daily + subscription balance (distinct from generic rate limit) |
| `image_too_large` | 413 | Image larger than `max_image_bytes` |
| `unsupported_media` | 415 | Not jpeg/png/webp/heic |
| `solver_failed` | 502 | Both OpenAI and Gemini failed; task ends in `failed` status |
| `internal_error` | 500 | Unhandled; logged with trace id |

Validation errors include the offending field path so clients can highlight inputs.

## Async task lifecycle

`POST /v1/tasks` returns `202 Accepted` (not 200) with a `task_id`. The task lives in one of these states:

```
pending  ─────►  done
   │
   └──────────►  failed
```

There is no `cancelled` state today (no user-facing cancel). If we add it: introduce `cancelled` as terminal, never reachable from `done`/`failed`.

Clients should subscribe to push for `task.completed`, and also poll `GET /v1/tasks/{id}` every 2s while the screen is foregrounded — push is best-effort. Backend caps polling via rate limit.

`failed` is terminal. There is no automatic retry beyond what the worker does internally (OpenAI fails → Gemini fallback inside the worker job). If the worker raises after the fallback, the row is marked `failed` with `error_code` and the push delivers a "couldn't solve" message.

## Pagination

History uses **keyset pagination**, not OFFSET. Cursor is the `created_at` of the last item returned.

```
GET /v1/tasks?limit=20
→ { items: [...20 items, newest first...], next_before: "2026-05-21T10:00:00Z" }

GET /v1/tasks?limit=20&before=2026-05-21T10:00:00Z
→ { items: [...next 20...], next_before: "2026-05-19T17:33:00Z" }
```

Last page returns `next_before` absent. Limit is clamped server-side: `1 ≤ limit ≤ 50`.

## Idempotency

`POST /v1/tasks` accepts an `Idempotency-Key` header (UUID). If a request with the same key arrives within 24 hours, the existing task is returned instead of creating a new one. This prevents double-charging on flaky mobile networks. Storage: Redis with 24h TTL, key `idem:{user_id}:{idem_key}` → `task_id`.

## Signed URLs

Image and thumbnail paths returned in responses are **signed URLs** with a 1-hour TTL, generated by `supabase.storage.from_("tasks").create_signed_url(path, expires_in=3600)`. Never return raw `task_images/...` paths to clients.

## Caveats / things to remember

- The legacy bot endpoint shape (`message`, `answer`, `status_code` in the body) is **not** carried forward to `/v1/*`. Mobile gets clean HTTP semantics.
- The bot still wants the legacy shape for one release; `/internal/tasks/solve` returns the legacy envelope for compatibility, then we delete it.
- A `429` for "daily limit" is semantically different from a `429` for "rate limit." Use `daily_limit_reached` vs `rate_limited` so clients can show the right UI.
