# 06 — Rate Limiting and Abuse

The mobile app turns this from a private bot backend into a public-facing API. We must assume bots, scrapers, and credential stuffers will find it within hours of the App Store listing going live.

## Layers

```
┌──────────────────────────────────────────────────────────┐
│  Cloudflare (or fronting CDN)                            │  IP / ASN reputation, WAF, bot mode
│  → blocks pure-bot traffic, rate-limits by IP            │
└──────────────────────┬───────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────┐
│  FastAPI ASGI middleware                                 │  Request-size cap, body validation
│  → 10 MB body limit, 30s timeout, request id             │
└──────────────────────┬───────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────┐
│  fastapi-limiter (Redis-backed)                          │  Per-IP and per-auth_user_id rate limits
└──────────────────────┬───────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────┐
│  Daily limit + subscription limit (atomic, in Postgres)  │  Business-level quota
└──────────────────────────────────────────────────────────┘
```

In-process rate limiters (e.g., `slowapi`) **under-count** behind multiple workers. Use Redis from day one.

## Limits

### Per IP

| Window | Limit | Notes |
|---|---|---|
| 1 minute | 30 requests | Generic public endpoints |
| 1 minute | 5 requests | `POST /v1/tasks` |
| 1 hour | 10 requests | `POST /v1/auth/link/start` |
| 1 day | 1000 requests | Hard cap regardless of authentication |

### Per `auth_user_id`

| Window | Limit | Notes |
|---|---|---|
| 1 minute | 10 solve requests | `POST /v1/tasks` |
| 1 minute | 60 reads | Everything else |
| 1 hour | 3 link codes | `POST /v1/auth/link/start` |

A signed-in user hits the auth-user limit before the IP limit. Anonymous traffic (no JWT) hits the IP limit. Pre-auth endpoints like `/v1/auth/link/start` get both.

### Solver-call concurrency

The solver is the expensive part. Bound it independently of HTTP rate limits.

```python
solver_semaphore = asyncio.Semaphore(int(os.getenv("SOLVER_MAX_CONCURRENT", "16")))

async def solve_with_cap(...):
    async with solver_semaphore:
        return await gpt_solver.solve(...)
```

A burst that gets past rate-limits still queues at the semaphore. Combined with the arq queue depth, this keeps OpenAI cost predictable.

## Image upload caps

| Limit | Value |
|---|---|
| Max bytes | 10,485,760 (10 MiB) |
| Max megapixels | 50 |
| Allowed MIME types | `image/jpeg`, `image/png`, `image/webp`, `image/heic` |
| Min dimensions | 100 × 100 |

Enforce at ASGI layer (`ContentLengthMiddleware`) to reject early before reading the body. A malicious 10 GiB upload should not consume worker memory.

```python
@app.middleware("http")
async def cap_body(request, call_next):
    cl = int(request.headers.get("content-length", 0))
    if cl > 10 * 1024 * 1024:
        return JSONResponse({"error": {"code": "image_too_large"}}, status_code=413)
    return await call_next(request)
```

Megapixel check happens after decoding (Pillow opens, checks `img.size`, closes). Reject before saving.

## Anti-abuse heuristics

These are not enabled at launch but should be in the codebase, dark-flagged:

1. **Duplicate-image hammering**: SHA-256 hash incoming images, if the same hash appears 5+ times for one user in 10 min, return cached solution and refund. This is already half-implemented (`users_status.last_processing_image_path`) but not enforced.
2. **Suspicious account creation**: brand-new Auth user (created <60s ago) submitting a solve from an IP with another fresh account in the last hour → flag for review.
3. **Telegram link code brute force**: 6 digits = 1M codes; with 3-codes-per-hour-per-IP limit, brute force is impractical, but log all failed attempts and alert above 100/hour from one IP.

## Cloudflare configuration

If we put CF in front (recommended):

- **Bot Fight Mode**: on.
- **WAF**: managed rules + a custom rule blocking common stuffing user agents (`curl`, `python-requests` without a custom UA, `Go-http-client`) from `/v1/auth/*`.
- **Rate limiting at the edge**: 60 req/min/IP on the whole `/v1/` prefix as a coarse safety net.
- **HTTP/3 + Brotli**: on.
- **TLS 1.3 only**.

CF does not help against authenticated abuse. Hence the per-user limits.

## Response shape for limits

```
HTTP/1.1 429 Too Many Requests
Retry-After: 23400
Content-Type: application/json

{
  "error": {
    "code": "rate_limited",      // or "daily_limit_reached"
    "message": "Try again in 6 hours or top up via Telegram.",
    "details": { "retry_after_seconds": 23400 }
  }
}
```

Always include `Retry-After`. iOS Safe Networking, OkHttp, and many SDKs will honor it.

## Things to test

1. 100 concurrent solves from one user with `daily_limit = 1` and `subscription_limit = 0` → exactly one succeeds, 99 return `daily_limit_reached`.
2. Same as above but `daily_limit = 0`, `subscription_limit = 1` → exactly one succeeds, spent from subscription.
3. Image exactly 10 MiB → accepted. 10 MiB + 1 byte → 413.
4. Solver-semaphore: 32 concurrent solves with `SOLVER_MAX_CONCURRENT=4` → queue lengthens but no error returned to the client (HTTP returns 202 immediately).
5. Brute-forcing a 6-digit link code: 4th attempt in the same hour → 429.
