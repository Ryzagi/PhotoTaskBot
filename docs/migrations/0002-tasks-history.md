# Migration 0002 — Tasks history columns

Add the columns needed to render a useful history list on mobile and to drive async-solve state. Builds on top of [`0001-uuid-users.md`](0001-uuid-users.md).

## Downtime budget

Zero. All additive.

## SQL — `bot/migrations/0002_tasks_history.sql`

```sql
BEGIN;

-- 1. New task lifecycle columns.
ALTER TABLE tasks
  ADD COLUMN id_v2 UUID NOT NULL DEFAULT gen_random_uuid(),
  ADD COLUMN status TEXT NOT NULL DEFAULT 'done'
    CHECK (status IN ('pending','done','failed')),
  ADD COLUMN input_kind TEXT,
  ADD COLUMN input_text TEXT,
  ADD COLUMN image_path TEXT,
  ADD COLUMN thumbnail_path TEXT,
  ADD COLUMN model_used TEXT,
  ADD COLUMN spent_from TEXT CHECK (spent_from IN ('daily','subscription')),
  ADD COLUMN error_code TEXT,
  ADD COLUMN error_detail TEXT,
  ADD COLUMN completed_at TIMESTAMPTZ;

-- 2. Backfill existing rows.
UPDATE tasks SET
  input_kind = CASE WHEN file_path IS NULL OR file_path = '' THEN 'text' ELSE 'image' END,
  image_path = NULLIF(file_path, ''),
  status = 'done',
  completed_at = created_at;

-- 3. Promote id_v2 to PK. The old composite (user_id, file_path, created_at) was not a true PK.
ALTER TABLE tasks ADD CONSTRAINT tasks_pkey_v2 PRIMARY KEY (id_v2);
ALTER TABLE tasks RENAME COLUMN id_v2 TO id;

-- 4. Indexes.
CREATE INDEX IF NOT EXISTS tasks_user_uuid_created_idx ON tasks (user_uuid, created_at DESC);
CREATE INDEX IF NOT EXISTS tasks_pending_idx ON tasks (status) WHERE status = 'pending';

-- 5. Stuck-task janitor support: a generated column for "age."
-- (Optional; the janitor can compute on the fly.)

COMMIT;
```

## user_devices table (separate but contemporaneous)

```sql
CREATE TABLE user_devices (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  platform      TEXT NOT NULL CHECK (platform IN ('ios','android')),
  token         TEXT NOT NULL UNIQUE,
  app_version   TEXT,
  locale        TEXT,
  notification_prefs SMALLINT NOT NULL DEFAULT 7,  -- bitmask
  last_seen     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX user_devices_user_idx ON user_devices (user_id);
```

## Postgres functions for atomic quota work

```sql
-- Atomic decrement; refunds at the end of failed solves.
CREATE OR REPLACE FUNCTION reserve_solve(uid UUID)
RETURNS TABLE(spent_from TEXT, remaining INTEGER) AS $$
DECLARE r INTEGER;
BEGIN
  UPDATE users_status
     SET daily_limit = daily_limit - 1, updated_at = NOW()
   WHERE user_uuid = uid AND daily_limit > 0
   RETURNING daily_limit INTO r;
  IF FOUND THEN
    spent_from := 'daily'; remaining := r; RETURN NEXT; RETURN;
  END IF;

  UPDATE users_status
     SET subscription_limit = subscription_limit - 1, updated_at = NOW()
   WHERE user_uuid = uid AND subscription_limit > 0
   RETURNING subscription_limit INTO r;
  IF FOUND THEN
    spent_from := 'subscription'; remaining := r; RETURN NEXT; RETURN;
  END IF;

  spent_from := NULL; remaining := -1; RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION refund_solve(uid UUID, bucket TEXT)
RETURNS VOID AS $$
BEGIN
  IF bucket = 'daily' THEN
    UPDATE users_status SET daily_limit = daily_limit + 1 WHERE user_uuid = uid;
  ELSIF bucket = 'subscription' THEN
    UPDATE users_status SET subscription_limit = subscription_limit + 1 WHERE user_uuid = uid;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Persists the daily reset. Replaces the buggy get_current_balance reset-in-memory.
CREATE OR REPLACE FUNCTION get_or_reset_balance(uid UUID, default_daily INTEGER DEFAULT 3)
RETURNS TABLE(daily_limit INTEGER, subscription_limit INTEGER) AS $$
DECLARE d INTEGER; s INTEGER;
BEGIN
  UPDATE users_status
     SET daily_limit = default_daily,
         last_processing_date = CURRENT_DATE,
         updated_at = NOW()
   WHERE user_uuid = uid
     AND (last_processing_date IS NULL OR last_processing_date < CURRENT_DATE)
   RETURNING daily_limit, subscription_limit INTO d, s;

  IF FOUND THEN
    daily_limit := d; subscription_limit := s; RETURN NEXT; RETURN;
  END IF;

  SELECT us.daily_limit, us.subscription_limit INTO d, s
    FROM users_status us WHERE us.user_uuid = uid;
  daily_limit := d; subscription_limit := s; RETURN NEXT;
END;
$$ LANGUAGE plpgsql;
```

These functions fix the two production bugs called out in [`../architecture/01-overview.md`](../architecture/01-overview.md). They are required for the backend refactor.

## Rollout

1. Apply migration.
2. Deploy backend code that uses the new functions and columns.
3. Bot continues working — the existing `tasks` rows are backfilled, the `file_path` column still exists, and the bot can keep writing it (a trigger or the service layer writes both `file_path` and `image_path` during the transition).

## Verification

```sql
-- Every row has a status.
SELECT COUNT(*) FROM tasks WHERE status IS NULL;  -- expect 0

-- input_kind is filled.
SELECT COUNT(*) FROM tasks WHERE input_kind IS NULL;  -- expect 0

-- Atomic decrement under load.
-- (Run in a loop test: 50 concurrent calls to reserve_solve for a user with daily_limit=10,
-- subscription_limit=0. Expect exactly 10 returns of spent_from='daily', then 40 returns
-- of (NULL, -1).)
```
