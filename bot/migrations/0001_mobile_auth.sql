-- Migration 0001 — Mobile auth linkage (ADDITIVE, safe for the live bot)
--
-- The live schema keys everything on `user_id text` (Telegram id for bot users).
-- Mobile users reuse the same column: user_id = the Supabase auth UUID stored
-- as text. We only add a nullable `auth_user_id` so the backend can look a
-- mobile user up by their JWT `sub`. No PK or type changes — the bot is
-- untouched.

BEGIN;

ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_user_id text;
DO $$ BEGIN
  CREATE UNIQUE INDEX users_auth_user_id_key ON users (auth_user_id) WHERE auth_user_id IS NOT NULL;
EXCEPTION WHEN duplicate_table THEN NULL; WHEN duplicate_object THEN NULL; END $$;

-- 6-digit Telegram-link codes (user_id is the text key, no FK needed).
CREATE TABLE IF NOT EXISTS account_links (
  code_hash    bytea PRIMARY KEY,
  user_id      text NOT NULL,
  expires_at   timestamptz NOT NULL,
  consumed_at  timestamptz,
  created_at   timestamptz NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS account_links_expires_idx
  ON account_links (expires_at) WHERE consumed_at IS NULL;

COMMIT;
