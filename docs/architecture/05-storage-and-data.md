# 05 — Storage and Data

Postgres (Supabase) holds the relational data. Supabase Storage holds the binary blobs (problem images, thumbnails). Redis is for the queue and short-lived caches only — never the source of truth.

## Postgres schema (target)

```sql
-- Domain users. One per real person.
CREATE TABLE users (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_user_id  BIGINT UNIQUE,
  auth_user_id      UUID UNIQUE REFERENCES auth.users(id),
  username          TEXT,
  first_name        TEXT,
  last_name         TEXT,
  language_code     TEXT DEFAULT 'ru',
  is_premium        BOOLEAN DEFAULT false,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT users_at_least_one_identity
    CHECK (telegram_user_id IS NOT NULL OR auth_user_id IS NOT NULL)
);

-- Mutable per-user state. Separated from users so reads of the latter are cacheable.
CREATE TABLE users_status (
  user_id                   UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  last_processing_date      DATE,
  daily_limit               INTEGER NOT NULL DEFAULT 3,
  subscription_limit        INTEGER NOT NULL DEFAULT 0,
  last_processing_image_path TEXT,
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- One row per solve job. Pending while the worker runs.
CREATE TABLE tasks (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','done','failed')),
  input_kind      TEXT NOT NULL CHECK (input_kind IN ('image','text','latex')),
  input_text      TEXT,                          -- caption for image, or full text for text/latex
  image_path      TEXT,                          -- /task_images/{user_uuid}/{yyyy}/{mm}/{uuid}.jpg
  thumbnail_path  TEXT,
  solution        JSONB,                         -- shape in 03-backend-api.md
  model_used      TEXT,                          -- 'gpt-5-mini' | 'gemini-2.5-flash'
  spent_from      TEXT CHECK (spent_from IN ('daily','subscription')),
  error_code      TEXT,
  error_detail    TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at    TIMESTAMPTZ
);
CREATE INDEX tasks_user_created_idx ON tasks (user_id, created_at DESC);
CREATE INDEX tasks_pending_idx ON tasks (status) WHERE status = 'pending';

-- Push notification tokens, one per device.
CREATE TABLE user_devices (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  platform      TEXT NOT NULL CHECK (platform IN ('ios','android')),
  token         TEXT NOT NULL UNIQUE,
  app_version   TEXT,
  locale        TEXT,
  last_seen     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX user_devices_user_idx ON user_devices (user_id);

-- Telegram ↔ Auth linking codes.
CREATE TABLE account_links (
  code_hash    BYTEA PRIMARY KEY,                -- SHA-256 of the 6-digit code
  user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at   TIMESTAMPTZ NOT NULL,
  consumed_at  TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Idempotency keys, Redis-backed, but documented here for completeness.
-- Key:   idem:{user_id}:{key}
-- Value: task_id
-- TTL:   86400s
```

## Row-level security

See `02-identity-and-auth.md` for the full policies. Short version:

- `users`, `users_status`, `tasks`: `auth_user_id = auth.uid()`.
- `user_devices`: same.
- `account_links`: server-only (no RLS read for clients).
- The backend uses the **service-role key** for write paths and **bypasses RLS**. The mobile clients use the **anon key + user JWT** and rely on RLS for safety.

The implication: anything the backend writes is not gated by RLS. Validation has to live in the backend. RLS is the safety net, not the gate.

## Indexes and query patterns

| Query | Index used |
|---|---|
| `SELECT * FROM tasks WHERE user_id = $1 ORDER BY created_at DESC LIMIT 20` (history) | `tasks_user_created_idx` |
| `SELECT * FROM tasks WHERE id = $1` (poll) | PK |
| `SELECT * FROM users WHERE auth_user_id = $1` (auth lookup) | unique |
| `SELECT * FROM users WHERE telegram_user_id = $1` (bot lookup) | unique |
| `SELECT * FROM tasks WHERE status = 'pending' AND created_at < NOW() - INTERVAL '10 min'` (stuck-task cleanup) | `tasks_pending_idx` |

No FTS, no JSONB GIN on `solution` — we never search inside it.

## Migrations

All schema changes live in `bot/migrations/NNNN-<name>.sql`, applied via a thin runner (`bot/migrate.py`) on container start. Numeric prefixes, never re-edit a shipped migration. See [`../migrations/0001-uuid-users.md`](../migrations/0001-uuid-users.md) for the migration that actually does the UUID work.

## Supabase Storage layout

Bucket: `tasks` (existing).

Old path format (do not change, do not migrate):

```
/task_images/{telegram_user_id_as_string}/{file_id}_{epoch}.png
```

New path format for uploads after the cutover:

```
/task_images/{user_uuid}/{yyyy}/{mm}/{uuid4}.jpg
/task_thumbs/{user_uuid}/{yyyy}/{mm}/{uuid4}.jpg
```

Why include `yyyy/mm`: makes lifecycle policies and bulk audits per-month feasible without scanning a flat directory of millions of objects.

Why `.jpg` not `.png`: mobile clients compress to JPEG (q=85, max 1920px long edge) before upload. Saves bandwidth and storage. Quality loss is invisible to the solver.

## Thumbnails

Generated server-side at upload time, **before** enqueuing the solve job:

```python
from PIL import Image
img = Image.open(io.BytesIO(image_bytes))
img.thumbnail((256, 256))
buf = io.BytesIO()
img.save(buf, "JPEG", quality=80)
await storage.upload(thumbnail_path, buf.getvalue())
```

256px JPEG at q=80 is ~6-15 KB. Cheap. History lists return thumbnails, not full images.

## Signed URLs

Never return raw storage paths to clients. The backend returns short-lived signed URLs:

```python
url = supabase.storage.from_("tasks").create_signed_url(path, expires_in=3600)
```

TTL: 1 hour for thumbnails (history view), 24 hours for the originals (solution detail). Mobile caches them locally; if a URL expires before display, it re-fetches the task.

## Lifecycle and cleanup

- Old task images (>90 days): keep for now, revisit when storage cost matters.
- Old thumbnails: same.
- Old `account_links` with `consumed_at IS NOT NULL OR expires_at < NOW() - INTERVAL '1 day'`: daily cron deletes.
- Old `user_devices` with `last_seen < NOW() - INTERVAL '60 days'`: daily cron deletes (the token is stale, push would 410 anyway).

## What lives in Redis

- arq job queue (default keyspace).
- Rate-limit counters (`fastapi-limiter`, keys `fastapi-limiter:{ip|uid}:{route}`).
- Idempotency keys (`idem:{user_id}:{key}` → `task_id`, TTL 24h).
- Nothing else. No session storage, no caching of business data (Postgres is fast enough; cache invalidation is the bug we don't want).

Redis persistence: AOF enabled (`appendonly yes`) so the queue survives restarts. Loss of Redis = lost in-flight jobs; the stuck-task janitor (see below) recovers them.

## Stuck-task janitor

A cron (every 5 minutes) finds `tasks.status = 'pending' AND created_at < NOW() - INTERVAL '10 minutes'` and either re-enqueues them (if they were lost during a Redis restart) or marks them `failed` with `error_code='timeout'`. Configurable via `STUCK_TASK_AGE_MIN`.
