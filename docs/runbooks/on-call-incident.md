# Runbook — On-call incident response

Use this when something is on fire. Skim once before you're on call so you know it exists.

## Severity

| Sev | Definition | Response |
|---|---|---|
| **SEV-1** | Backend down, all users affected. | Page immediately. Aim to restore in <30 min. |
| **SEV-2** | Significant degradation (solve P95 >2× normal, push <50% delivery, error rate >5%). | Acknowledge within 15 min, restore within 2h. |
| **SEV-3** | Localized issue (one route, one cohort, one platform). | Triage same business day. |
| **SEV-4** | Quality issue, no immediate user impact. | File a ticket. |

## First five minutes

1. **Acknowledge** the alert (PagerDuty / Telegram admin chat).
2. **Open the dashboard**: Grafana → Backend Overview. Look at request rate, error rate, P95 latency over the last 30 minutes.
3. **Check `/healthz`** from outside: `curl https://api.pandasolve.app/healthz`. Failed? Move to "backend down" below. Passed? Move to "degraded" below.
4. **Set the status**: post in #incidents (Telegram or Slack) — "Incident: [SEV-X] [summary]. Investigating."

Do not start fixing before you've classified. A wrong fix is worse than no fix.

## Backend down

### Symptoms

- `/healthz` returns 5xx or times out.
- All mobile and bot users get errors.

### First checks

```
fly status -a pandasolve-api       # are pods running?
fly logs -a pandasolve-api         # recent logs
```

- All pods `Running`? Look at logs for crashes.
- Pods restarting in a loop? It's likely a bad deploy or missing env var. Roll back: `fly deploy --image <previous_sha>`.
- No pods? Scale up: `fly scale count 2`.

### If it's the DB

- Supabase status page: https://status.supabase.com — check for incidents.
- Supabase project dashboard → Database → connection pool usage. Maxed out? Reduce backend pool size temporarily or scale up the Supabase compute.
- Migration in progress that's holding locks? `SELECT * FROM pg_stat_activity WHERE wait_event_type = 'Lock';`.

### If it's Redis

- Symptom: `arq` workers stuck, queue depth growing, push delays.
- `redis-cli -u $REDIS_URL ping` — does it answer?
- If Redis is down, push and async solves stop; **the bot's sync solves still work** (they bypass the queue). Communicate this.

### Mitigations

- **Maintenance mode**: set `MAINTENANCE_MODE=true`. `/v1/*` returns `503` with a localized "we'll be back" message. Mobile app shows a banner.
- **Disable mobile**: set `MOBILE_DISABLED=true`. Only `/internal/*` (bot) keeps working.
- **Force the bot offline**: stop the `telegram_bot` service. Users see "bot not responding" and the rest of the system remains stable.

## Degraded — high error rate

### Symptoms

- `task.failed` rate >5%.
- Or `rate_limit_hits_total` rising sharply.

### Checks

1. **Are we under abuse?**: filter logs by `event=rate_limited`. Cluster by IP. If a few IPs dominate, block them at Cloudflare.
2. **Are the solvers down?**: Grafana → Solver Health. OpenAI errors spiking? Gemini still working?
3. **Is the bot misbehaving?**: a bug in `routers.py` causing retries.

### Fixes

- OpenAI is broken: temporarily flip the order so Gemini is primary (`SOLVER_PRIMARY=gemini` env var). Redeploy.
- Both solvers degraded: lower the worker concurrency (`ARQ_WORKERS=2`) to slow the failure rate; tell on-call to wake providers up.
- A bug in production: identify the bad commit, revert, redeploy.

## Degraded — high latency

### Symptoms

- P95 of `POST /v1/tasks` >5s (target <1s; the solve itself happens async).
- Solve duration P95 >60s.

### Checks

1. **DB slow queries**: Supabase → Database → Query performance. Slow query log will show the offender.
2. **Storage upload slow**: Supabase Storage status, or our upload size has crept up.
3. **OpenAI throttling**: Look at `solver_errors_total{error_type="rate_limit"}`.
4. **Worker pool exhausted**: Grafana → Queue → workers metric.

### Fixes

- DB hot spot: add the missing index. Check `pg_stat_user_indexes`.
- Storage slow: nothing we can do; communicate.
- OpenAI throttling: lower concurrency or contact OpenAI for higher tier.
- Worker pool: scale up workers.

## Push delivery low

### Symptoms

- `push_sent_total{status="ok"}` drops well below normal.
- Users complain they don't get notifications.

### Checks

1. **APNs side** (iOS): logs for `aioapns` errors. Common: `BadDeviceToken` (token expired — normal; 410 cleanup runs). `BadCollapseId`, `TooManyProviderTokenUpdates`.
2. **FCM side** (Android): `UnregisteredError` is normal; `InvalidArgumentError` means we're sending a malformed payload.
3. **Backend not even trying**: worker errored before reaching the push call. Look at `task.solved` vs `push.sent` counter ratios.

### Fixes

- APNs token expired (you'll see a flood of `InvalidProviderToken`): rotate the APNs key (see [`rotate-supabase-keys.md`](rotate-supabase-keys.md#apns-p8-key)).
- FCM credentials expired: rotate.
- Worker bug: check Sentry.

## DB corruption / loss

Worst case. Steps:

1. **Stop writes**: set `MAINTENANCE_MODE=true`.
2. **Snapshot current state**: Supabase → Backups → Take backup.
3. **Restore from last good backup**: Supabase has automatic PITR. Pick a point before the corruption.
4. **Replay any reconstructable state**: if Telegram users sent solves during the gap, they may have to redo them.
5. **Post-mortem** before unsetting maintenance mode.

## Communication

- **Internal (within 5 min of confirmation)**: post in #incidents.
- **External**: if SEV-1 or SEV-2 for >10 minutes, post on `status.pandasolve.app` (or pin a message in the Telegram bot via admin command).
- **Updates**: every 30 minutes during an incident, even if no progress. "Still investigating, no ETA."
- **Resolution**: post when it's resolved. Include a one-line summary of the cause.

## Postmortem

For every SEV-1, every SEV-2, and any SEV-3 that surprised someone:

- Within 48 hours of resolution.
- Blameless.
- Sections: timeline, impact, root cause, what went well, what went wrong, action items with owners and dates.
- File in `docs/postmortems/YYYY-MM-DD-<short-name>.md`.
- Schedule a 30-min review for everyone affected.

## Useful one-liners

```bash
# Top 10 erroring endpoints in the last hour
curl -s "https://grafana.../.../top_errors?range=1h" | jq

# Stuck pending tasks
psql "$DATABASE_URL" -c "SELECT id, user_id, created_at FROM tasks WHERE status='pending' AND created_at < NOW() - INTERVAL '10 minutes';"

# Force-cleanup of one user's stuck task
psql "$DATABASE_URL" -c "UPDATE tasks SET status='failed', error_code='manual_cleanup' WHERE id = '<task_id>';"

# Manually refund a user
psql "$DATABASE_URL" -c "SELECT refund_solve('<user_uuid>'::uuid, 'daily');"

# Tail backend logs filtered by user
fly logs -a pandasolve-api | grep '<user_uuid>'
```

## Who to wake up

| Role | Hours | How |
|---|---|---|
| Backend on-call | 24/7 | PagerDuty primary |
| Mobile on-call | business hours | Telegram |
| Supabase support | 24/7 (paid plans) | Support ticket |
| OpenAI support | business hours | api.openai.com → help |

Do not wake the founder unless SEV-1 lasts >30 min.
