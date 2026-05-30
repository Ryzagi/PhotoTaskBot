# Runbook — Deploy the backend

## Quick reference

```
git push origin main          → CI runs                 → image pushed
                              → fly deploy / k8s rollout → new pods serve traffic
```

Total time, healthy push: ~5 minutes.

## Pre-deploy checklist

- [ ] All tests green on `main` (CI: ruff, mypy, pytest, integration).
- [ ] No open `priority/critical` issues for the affected service.
- [ ] `docs/migrations/` has an entry if this deploy includes a schema change.
- [ ] If a schema change: it has been **applied to prod DB first** (separate runbook step) and is backward-compatible with the currently-running code.

## Standard deploy

1. **Merge to `main`.** Squash-merge from a reviewed PR.
2. **CI builds.** GitHub Actions (`.github/workflows/backend.yml`):
   - Lint (`ruff`).
   - Type check (`mypy`).
   - Tests (`pytest -x`).
   - Build Docker image, tag with `git sha`, push to registry.
3. **Auto-deploy** (Fly / Render / Railway / your VPS): the platform pulls the new image and rolls pods one by one. Health check is `GET /healthz`.
4. **Smoke check** (1 minute after rollout):
   - `curl https://api.pandasolve.app/healthz` → `{"status":"ok"}`.
   - `curl https://api.pandasolve.app/openapi.json | jq '.info.version'` → new version string (we bump on every deploy via CI).
   - Open `/docs` in a browser, click through one endpoint.
5. **Verify the bot** is still responsive: send `/start` to `@PandaSolveBot` from a test account.

## Schema-change deploy

A schema change is a 2-stage deploy:

1. **Stage 1 — additive migration.** Apply the SQL (additive only — new columns, new tables, new indexes; no drops). Code in production keeps running on the old schema; the new columns are unused.
2. **Stage 2 — code rollout.** Deploy the code that uses the new columns. Old pods drain; new pods serve.
3. **(Later, separate deploy) — destructive cleanup.** Drop old columns / triggers. Only after the new code has been stable for ≥7 days.

Never combine stages. Never deploy code that *requires* a not-yet-applied migration. Never drop columns in the same deploy that introduces a new code path.

## Worker deploys

The arq workers (`bot/tasks/`) run in a separate process group. Their deploy is the same flow, but:

- Workers drain in-flight jobs before stopping (arq SIGTERM handling).
- Drain timeout: 90 seconds (max solve time + buffer).
- New workers pick up the queue immediately on startup.

If you change job signatures (rename, args), version the job: register both `solve_image_task_v1` and `solve_image_task_v2` for a transition period. arq does not handle renames automatically.

## Rollback

```
fly releases list -a pandasolve-api
fly deploy --image registry/pandasolve-api:<previous_sha> -a pandasolve-api
```

(Or your platform's equivalent. The image tag of the previous deploy is in the platform's release log.)

Rollback constraints:

- **Same schema.** If the new deploy applied an additive migration, rollback to the previous image is safe (it just doesn't use the new columns). If the new deploy applied a destructive migration, rollback also needs a database restore — bad day.
- **Cache invalidation.** If the new code introduced a Redis key shape, rollback may leave stale keys; either let TTLs expire or `redis-cli FLUSHDB` (only on rollback, never on a normal deploy).

## Things that break the deploy

| Symptom | Cause | Fix |
|---|---|---|
| Health check failing | Migration not applied | Apply migration; redeploy |
| 500s right after rollout | Env var missing | Add to platform secrets; restart |
| `/openapi.json` 500 | Pydantic schema error in a new model | Look at logs; fix the model |
| Bot still hitting `/tasker/api/` and getting 404 | Removed shim too early | Restore shim; release a bot update |

## Secrets to set on first deploy

| Secret | Where it comes from |
|---|---|
| `SUPABASE_URL` | Supabase project settings |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase project settings → API |
| `SUPABASE_ANON_KEY` | same |
| `SUPABASE_JWT_SECRET` | same |
| `OPENAI_API_KEY` | OpenAI dashboard |
| `GOOGLE_API_KEY` | Google AI Studio |
| `INTERNAL_AUTH_SECRET` | `openssl rand -hex 32` |
| `TELEGRAM_BOT_TOKEN` | BotFather |
| `REDIS_URL` | your Redis provider |
| `APNS_*` | Apple Developer |
| `FCM_SERVICE_ACCOUNT_JSON_BASE64` | Firebase console |
| `SENTRY_DSN` | Sentry project |

After setting secrets, redeploy. The app crashes loudly on startup if a required secret is missing.

## On-call escalation

If a deploy fails and you can't roll back in 10 minutes, ping the on-call (see [`on-call-incident.md`](on-call-incident.md)) and put up the maintenance page (`MAINTENANCE_MODE=true` env var causes `/v1/*` to return 503 and the mobile app to show a banner).
