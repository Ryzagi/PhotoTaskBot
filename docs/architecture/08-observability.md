# 08 — Observability

You will not be able to diagnose a production incident on mobile without logs, metrics, traces, and crash reports. The bot lived without any of this; mobile cannot.

## Tools

| Concern | Tool | Why |
|---|---|---|
| Structured logs | `structlog` (already in `requirements.txt`) → JSON to stdout | Captured by container runtime |
| Log shipping | Loki + Promtail (self-hosted) **or** Datadog | Pick one — don't run both |
| Metrics | Prometheus + Grafana | Standard, free, plays nice with FastAPI |
| Tracing | OpenTelemetry → Tempo (or Datadog) | Optional at launch, valuable when debugging mobile→backend latency |
| Crash reporting | Sentry (single account, four projects: backend, android, ios, bot) | One SDK per language, decent free tier |
| Uptime | Better Uptime or UptimeRobot | `/healthz` every 60s from three regions |

## Log shape

```python
import structlog
log = structlog.get_logger()

log.info("task.created",
    user_id=str(user.id),
    task_id=str(task.id),
    input_kind="image",
    image_bytes=len(image_bytes),
    spent_from="daily",
)
```

Output (JSON, one line):

```json
{"event":"task.created","level":"info","timestamp":"2026-05-21T17:33:01.111Z","trace_id":"3f1…","user_id":"…","task_id":"…","input_kind":"image","image_bytes":482311,"spent_from":"daily"}
```

Required fields on every log line (via processor):

- `timestamp` ISO8601 UTC
- `level`
- `event` (snake_case, dotted namespace)
- `trace_id` (propagated via OpenTelemetry or generated per-request middleware)
- `service` (`backend` / `worker` / `bot`)
- `env` (`prod` / `staging` / `dev`)

## What to log

| Event | When | Required fields |
|---|---|---|
| `task.created` | After enqueue | `task_id, user_id, input_kind, spent_from` |
| `task.solved` | Worker success | `task_id, model_used, duration_ms` |
| `task.failed` | Worker exhausted retries | `task_id, error_code, error_detail` |
| `auth.signin` | JWT verified | `user_id, auth_user_id` |
| `auth.link.confirmed` | Telegram linked | `user_id, telegram_user_id` |
| `billing.refund` | Quota refunded after worker failure | `user_id, refunded_to` |
| `push.sent` | Push attempt | `user_id, topic, platform, status, latency_ms` |
| `rate_limited` | 429 | `user_id|ip, route, window, limit` |
| `solver.error` | OpenAI/Gemini error | `model, error_type, error_status` |

## What never to log

- Image bytes or base64 contents.
- Full solution JSON (it can contain user-submitted text we shouldn't replay).
- JWT contents (only `sub`, never the token itself).
- Supabase service-role key, OpenAI key, anything from `.env`.
- Personally identifying details beyond `user_id` (a UUID is fine; `email` is not).

A logging processor strips known-sensitive keys at the structlog layer.

## Metrics (Prometheus)

Exposed at `/metrics`, scraped every 15s.

| Metric | Type | Labels |
|---|---|---|
| `http_requests_total` | counter | `route, method, status` |
| `http_request_duration_seconds` | histogram | `route, method` |
| `tasks_pending` | gauge | — |
| `tasks_in_flight` | gauge | — |
| `tasks_completed_total` | counter | `model, status` |
| `task_solve_duration_seconds` | histogram | `model` |
| `solver_errors_total` | counter | `model, error_type` |
| `daily_limit_hits_total` | counter | — |
| `rate_limit_hits_total` | counter | `route, scope` |
| `push_sent_total` | counter | `platform, topic, status` |
| `db_query_duration_seconds` | histogram | `op` |

Dashboards (Grafana):

1. **Backend Overview**: request rate, error rate, P50/P95/P99 latency per route.
2. **Solver Health**: tasks/sec by model, success rate, P95 duration, OpenAI error breakdown.
3. **Queue**: depth, oldest-pending age, worker count.
4. **Push**: send rate by platform, success rate, 410 rate.
5. **Quota**: daily limits hit, subscription consumed, refunds.

## Tracing

OpenTelemetry instruments FastAPI, httpx, and asyncpg automatically. Spans of interest:

```
HTTP POST /v1/tasks (request_id=r1)
├── reserve_solve            12ms
├── storage.upload           340ms
├── thumbnail.generate       110ms
└── arq.enqueue              4ms

arq.solve_image_task (task_id=t1, parent_request_id=r1)
├── storage.download         180ms
├── openai.chat.completions  8400ms
├── db.tasks.complete        15ms
└── push.send                250ms
   ├── apns.send             190ms
   └── fcm.send              210ms
```

Propagate `trace_id` from the HTTP request through the queue job into the worker. arq supports this via job headers.

## Sentry

Backend: `sentry-sdk[fastapi]`. Sample rate 100% on errors, 10% on transactions in prod.

Mobile: Sentry Android, Sentry iOS. Capture unhandled exceptions, ANRs (Android), crashes, and slow frames.

Linkage: client sends a `x-trace-id` header; backend includes it in Sentry events. A crashed mobile session can be jumped from in Sentry to the backend trace.

## Alerting

Page (PagerDuty or Telegram bot, in this project a dedicated admin chat) on:

- Backend availability <99.5% over 5 minutes.
- `/healthz` failing from 2+ probe regions for 2 minutes.
- `task.failed` rate >5% over 10 minutes.
- Solver P95 >60s for 10 minutes.
- Push success rate <90% over 30 minutes.
- DB query P95 >500ms for 10 minutes.

Don't alert on individual errors (Sentry captures those). Alert on rates.

## The two existing latent bugs to instrument

When the migration happens, add tests **and** runtime assertions:

1. `decrement_daily_limit` race: add a Prometheus counter `daily_limit_negative_attempts_total`. Should always be zero. Alert if it goes nonzero — that means the atomic guard somehow failed.
2. `get_or_reset_balance` persistence: every `reset` increments `daily_limit_resets_total`. If a single user hits reset twice in the same UTC day, log `reset.duplicate` warning.

## Mobile client logging

Use the platform native logger (`Logcat`, `os.Logger`) for dev. In release, only crashes and `warning`+ events go to Sentry. No bulk shipping of mobile logs — too noisy, too expensive, mostly useless.

For deliberately captured client events (analytics), use PostHog. Don't conflate analytics with operational logs.
