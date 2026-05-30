# 04 — Async Solving

The current bot holds an HTTP request open for the full duration of a solve (10–30 seconds, occasionally longer when the Gemini fallback kicks in). That's tolerable on Wi-Fi inside a desktop Telegram client. It is not acceptable on cellular iOS, where iOS will kill the foreground network request and the app at any time, with no resume.

So mobile uses an async pattern: enqueue, push, poll.

## Components

```
HTTP layer (FastAPI)            Queue (Redis, arq)         Workers (arq)
─────────────────────           ──────────────────         ─────────────
POST /v1/tasks                                              solve_task(id)
  ├─ rate-limit check                                       │
  ├─ daily-limit reserve                                    │
  ├─ upload image to Storage                                ├─ try OpenAI gpt-5-mini
  ├─ INSERT tasks (status=pending)                          ├─ on fail: try Gemini
  ├─ enqueue arq job                                        ├─ on success: UPDATE tasks (done)
  └─ return {task_id, status: pending}  ──► arq pickup ──►  │ on both fail: UPDATE tasks (failed)
                                                            └─ push notification
GET /v1/tasks/{id}
  └─ SELECT tasks WHERE id = $1
```

## Why arq, not Celery or RQ

| Lib | Async-native? | Operational complexity | Notes |
|---|---|---|---|
| **arq** | yes (asyncio) | low | Same event loop as FastAPI; tiny API; healthy maintenance |
| Celery | no (workers are sync) | high | Heavy, but battle-tested. Overkill here. |
| RQ | no | low | Sync workers; would require running OpenAI calls in threads |
| Dramatiq | optional | medium | Decent option but no async story for the solver path |

The solver is I/O-bound (httpx to OpenAI/Gemini, async file reads). arq lets us write the worker in plain `async def` and reuse the existing `TaskSolverGPT` and `GeminiSolver` classes verbatim.

## Reserve, then solve

Race condition to avoid: user has 1 daily solve left, taps "solve" twice in quick succession. Both requests pass the daily-limit check, both enqueue, both spend an OpenAI call, one of them returns 429 too late.

Fix: **reserve the limit slot inside the HTTP handler before enqueuing**, atomically:

```sql
-- Postgres function: returns -1 if no quota, otherwise the remaining balance
CREATE OR REPLACE FUNCTION reserve_solve(uid UUID) RETURNS INTEGER AS $$
DECLARE remaining INTEGER;
BEGIN
  -- Subscription limit goes first (paid balance is more valuable to keep around? actually
  -- opposite: spend it first so users don't hoard. Decision: spend daily first, then sub.)
  UPDATE users_status
     SET daily_limit = daily_limit - 1
   WHERE user_id = uid AND daily_limit > 0
   RETURNING daily_limit INTO remaining;

  IF FOUND THEN RETURN remaining; END IF;

  UPDATE users_status
     SET subscription_limit = subscription_limit - 1
   WHERE user_id = uid AND subscription_limit > 0
   RETURNING subscription_limit INTO remaining;

  IF FOUND THEN RETURN remaining; END IF;

  RETURN -1;
END;
$$ LANGUAGE plpgsql;
```

If the worker later fails (e.g., both solvers down), it **refunds**:

```sql
UPDATE users_status SET daily_limit = daily_limit + 1 WHERE user_id = ...;
-- or subscription_limit, tracked in the task row's "spent_from" column
```

This is the right design for a paid feature. The current bot code does not refund; the planned migration does.

### Spend ordering decision

Today's bot spends **daily first, then subscription**. We keep this. Rationale: if we spent subscription first, paying users could lose paid balance through nothing more than time passing (3 free solves a day they didn't ask for would otherwise vanish), which feels punitive.

A `users_status.spent_from TEXT` column on a *task-by-task* basis isn't needed because refund order doesn't matter — we refund into whichever bucket has room, preferring `subscription` (it persists across days, so user gets more).

## Job shape

```python
# bot/tasks/jobs.py
@arq_worker.task
async def solve_image_task(ctx, task_id: str):
    db = ctx["db"]
    task = await db.tasks.get(task_id)
    if task.status != "pending":
        return  # idempotency: someone re-enqueued

    image_bytes = await db.storage.download(task.image_path)
    caption = task.input_text

    try:
        solution = await gpt_solver.solve(io.BytesIO(image_bytes), caption=caption)
        model = "gpt-5-mini"
    except Exception as e:
        log.warning("gpt failed", error=str(e))
        try:
            solution = await gemini_solver.solve(io.BytesIO(image_bytes), caption=caption)
            model = "gemini-2.5-flash"
        except Exception as e2:
            await db.tasks.fail(task_id, error_code="solver_failed", error=str(e2))
            await db.billing.refund(task.user_id, task.spent_from)
            await push.send_failed(task.user_id, task_id)
            return

    await db.tasks.complete(task_id, solution=solution, model_used=model)
    await push.send_completed(task.user_id, task_id, preview=solution["solutions"][0]["problem"][:80])
```

`solve_text_task` is analogous, no image download.

## Retries

arq has built-in retries. Default policy:

```python
@arq_worker.task(max_tries=2, retry_backoff=True)
```

But: an OpenAI 429 or 5xx should retry; an OpenAI 400 (bad image) should not. The worker catches and classifies before re-raising.

```python
RETRYABLE = (httpx.TimeoutException, httpx.NetworkError, openai.RateLimitError, openai.APIStatusError)

try:
    await gpt_solver.solve(...)
except RETRYABLE:
    raise Retry()  # arq retries with backoff
except openai.BadRequestError:
    # the image itself is bad; don't waste a retry, go straight to Gemini
    ...
```

## Push triggers

| Event | Push topic | Payload |
|---|---|---|
| Task completed | `task.completed` | `{task_id, problem_preview, thumbnail_url}` |
| Task failed | `task.failed` | `{task_id, error_code}` |
| Daily limit reset (8am local, optional opt-in) | `daily.reset` | `{daily_limit}` |
| Balance topped up (after Telegram payment) | `balance.added` | `{added, total}` |

See [`07-push-notifications.md`](07-push-notifications.md) for the wire format and token lifecycle.

## SLO and budget

- **P50 latency from `POST /v1/tasks` to `done`:** 12 seconds.
- **P95:** 28 seconds.
- **Error budget (failed tasks):** 1% per rolling 24h. Above that, page on-call.
- **Worker concurrency:** start at 4 workers × 2 concurrent tasks = 8 in-flight solves. OpenAI tier-3 quotas comfortably exceed this. Scale via `ARQ_WORKERS` env var.

## Backwards compatibility

The bot still uses `/internal/tasks/solve` synchronously. The handler for that endpoint calls the same service-layer method but waits for the result instead of returning early. Both paths share the reserve-then-solve logic. This is documented and tested.

## Things you might be tempted to do, and shouldn't

- **Don't make the HTTP handler `await` the arq job result.** Defeats the entire point. Return immediately.
- **Don't store the queue position or ETA in the task row** to display "you are #3 in line." It's a flex that nobody asked for, and accurate queue depth in a distributed worker pool is hard. The status is `pending`, that's enough.
- **Don't bypass the queue for "small" or "fast" tasks.** Two paths to maintain, no real benefit.
- **Don't put the user's image bytes into the queue payload.** The payload is `{task_id}` only. Image lives in Supabase Storage, referenced by path.
