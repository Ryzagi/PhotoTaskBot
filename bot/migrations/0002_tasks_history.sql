-- Migration 0002 — Task history columns + push devices (ADDITIVE)
--
-- Adds the columns the mobile app needs to render history and (later) async
-- solving, plus a device-token table. Keys stay on `user_id text`; the
-- existing `tasks.id bigint` PK is untouched.

BEGIN;

ALTER TABLE tasks
  ADD COLUMN IF NOT EXISTS status text DEFAULT 'done',
  ADD COLUMN IF NOT EXISTS input_kind text,
  ADD COLUMN IF NOT EXISTS input_text text,
  ADD COLUMN IF NOT EXISTS image_path text,
  ADD COLUMN IF NOT EXISTS thumbnail_path text,
  ADD COLUMN IF NOT EXISTS model_used text,
  ADD COLUMN IF NOT EXISTS error_code text,
  ADD COLUMN IF NOT EXISTS completed_at timestamptz,
  ADD COLUMN IF NOT EXISTS album_id uuid;

-- Backfill kind/path for existing bot rows.
UPDATE tasks SET
  input_kind = CASE WHEN file_path IS NULL OR file_path = '' THEN 'text' ELSE 'image' END,
  image_path = NULLIF(file_path, ''),
  status = COALESCE(status, 'done'),
  completed_at = COALESCE(completed_at, created_at)
WHERE input_kind IS NULL;

CREATE INDEX IF NOT EXISTS tasks_user_created_idx ON tasks (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS tasks_album_idx ON tasks (album_id);

CREATE TABLE IF NOT EXISTS user_devices (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       text NOT NULL,
  platform      text NOT NULL CHECK (platform IN ('ios','android')),
  token         text NOT NULL UNIQUE,
  app_version   text,
  locale        text,
  last_seen     timestamptz NOT NULL DEFAULT NOW(),
  created_at    timestamptz NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS user_devices_user_idx ON user_devices (user_id);

COMMIT;
