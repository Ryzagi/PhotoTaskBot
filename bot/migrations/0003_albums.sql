-- Migration 0003 — Albums (theme collections), keyed on user_id text.

BEGIN;

CREATE TABLE IF NOT EXISTS albums (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     text NOT NULL,
  name        text NOT NULL,
  emoji       text,
  color       text,            -- palette key: mint|sky|lav|coral|butter|pink
  created_at  timestamptz NOT NULL DEFAULT NOW(),
  updated_at  timestamptz NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS albums_user_idx ON albums (user_id);

-- tasks.album_id was added in 0002; wire the FK now that albums exists.
DO $$ BEGIN
  ALTER TABLE tasks ADD CONSTRAINT tasks_album_id_fkey
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

COMMIT;
