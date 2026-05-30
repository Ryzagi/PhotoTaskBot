# Migration 0001 — UUID users

Switch the user identity model from "Telegram ID is the PK" to "UUID is the PK; Telegram ID and Auth ID are nullable columns." Background and rationale: [`../architecture/02-identity-and-auth.md`](../architecture/02-identity-and-auth.md).

## Downtime budget

**Zero seconds.** Every step is additive. The bot keeps running against the old PK shape until step 5; the new backend can start in parallel.

## Risk

| Risk | Mitigation |
|---|---|
| Backfill row count is large enough to lock writes | Use `ALTER TABLE … ADD COLUMN … DEFAULT …` (Postgres 11+ writes the default lazily); backfill in batches |
| FK on `auth.users(id)` rejects orphan rows | Set FK with `NOT VALID`, then `VALIDATE CONSTRAINT` after backfill |
| Bot writes that race the migration | Run during a known-quiet window (3am MSK) and keep the old `user_id INTEGER` column populated by a trigger until step 5 |
| Rollback needed | Old columns kept until step 5; until then, the old code path still works |

## Pre-flight

- [ ] Snapshot Supabase Postgres (pgdump or Supabase backup).
- [ ] Tag the current code revision: `git tag -a pre-uuid-migration -m "before 0001"`.
- [ ] Deploy a dev environment with a copy of prod data and rehearse end-to-end.
- [ ] Verify `pgcrypto` extension is enabled (`gen_random_uuid()` needs it). On Supabase it is enabled by default.

## SQL — `bot/migrations/0001_uuid_users.sql`

```sql
BEGIN;

-- 1. Add the new columns. DEFAULT is set lazily on Postgres 11+, so no rewrite.
ALTER TABLE users
  ADD COLUMN id UUID NOT NULL DEFAULT gen_random_uuid(),
  ADD COLUMN telegram_user_id BIGINT,
  ADD COLUMN auth_user_id UUID;

-- 2. Backfill telegram_user_id from the existing PK.
UPDATE users SET telegram_user_id = user_id WHERE telegram_user_id IS NULL;

-- 3. Add uniqueness and FK constraints (NOT VALID first, validate after).
ALTER TABLE users
  ADD CONSTRAINT users_telegram_user_id_key UNIQUE (telegram_user_id);

ALTER TABLE users
  ADD CONSTRAINT users_auth_user_id_fkey
    FOREIGN KEY (auth_user_id) REFERENCES auth.users(id) NOT VALID;

ALTER TABLE users VALIDATE CONSTRAINT users_auth_user_id_fkey;

-- 4. At-least-one-identity check.
ALTER TABLE users
  ADD CONSTRAINT users_at_least_one_identity
    CHECK (telegram_user_id IS NOT NULL OR auth_user_id IS NOT NULL) NOT VALID;

ALTER TABLE users VALIDATE CONSTRAINT users_at_least_one_identity;

-- 5. Switch PK from user_id to id.
ALTER TABLE users DROP CONSTRAINT users_pkey;
ALTER TABLE users ADD PRIMARY KEY (id);

-- 6. Add user_uuid columns to dependents.
ALTER TABLE users_status ADD COLUMN user_uuid UUID;
UPDATE users_status us
  SET user_uuid = u.id
  FROM users u
  WHERE us.user_id = u.telegram_user_id;
ALTER TABLE users_status
  ADD CONSTRAINT users_status_user_uuid_fkey FOREIGN KEY (user_uuid) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE tasks ADD COLUMN user_uuid UUID;
UPDATE tasks t
  SET user_uuid = u.id
  FROM users u
  WHERE t.user_id = u.telegram_user_id;
ALTER TABLE tasks
  ADD CONSTRAINT tasks_user_uuid_fkey FOREIGN KEY (user_uuid) REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX tasks_user_uuid_created_idx ON tasks (user_uuid, created_at DESC);

-- 7. Trigger so the bot's legacy writes continue to populate user_uuid until step 5 of the rollout.
CREATE OR REPLACE FUNCTION sync_user_uuid() RETURNS trigger AS $$
BEGIN
  IF NEW.user_uuid IS NULL THEN
    SELECT id INTO NEW.user_uuid FROM users WHERE telegram_user_id = NEW.user_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_status_sync_uuid BEFORE INSERT OR UPDATE ON users_status
  FOR EACH ROW EXECUTE FUNCTION sync_user_uuid();
CREATE TRIGGER tasks_sync_uuid BEFORE INSERT OR UPDATE ON tasks
  FOR EACH ROW EXECUTE FUNCTION sync_user_uuid();

-- 8. account_links table.
CREATE TABLE account_links (
  code_hash    BYTEA PRIMARY KEY,
  user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at   TIMESTAMPTZ NOT NULL,
  consumed_at  TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX account_links_user_idx ON account_links (user_id);
CREATE INDEX account_links_expires_idx ON account_links (expires_at) WHERE consumed_at IS NULL;

COMMIT;
```

## Rollout

1. **Apply migration.** No code change. The old `user_id INTEGER` PK on `users` is gone, but every dependent still has a `user_id` column populated; the new `id UUID` is also populated. Triggers keep the new `user_uuid` columns in sync for any legacy writes.

2. **Deploy refactored backend.** New code reads/writes by `id UUID` and resolves identity via `auth_user_id` (mobile) or `telegram_user_id` (bot). Old endpoints still work because the legacy columns still exist.

3. **Cut bot to `/internal/*`.** Bot starts calling the new HMAC-protected endpoints. Backend handlers for `/tasker/api/*` become thin shims that forward to `/internal/*` for backward compatibility (in case any old container is still running) and log a deprecation warning.

4. **Wait 7 days, verify no `tasker_api_legacy` logs.** Then remove the shims.

5. **Drop legacy columns** (migration `0003_drop_legacy_user_id.sql`):
   ```sql
   ALTER TABLE users_status DROP COLUMN user_id;
   ALTER TABLE users_status RENAME COLUMN user_uuid TO user_id;
   ALTER TABLE tasks DROP COLUMN user_id;
   ALTER TABLE tasks RENAME COLUMN user_uuid TO user_id;
   ALTER TABLE users DROP COLUMN user_id;
   DROP TRIGGER users_status_sync_uuid ON users_status;
   DROP TRIGGER tasks_sync_uuid ON tasks;
   DROP FUNCTION sync_user_uuid();
   ```

## Rollback (if step 1 or 2 goes wrong)

Until step 5 ships, rollback is a code-only redeploy. The old `user_id INTEGER` PK has been demoted to a regular column, but it still exists, is still unique-by-trigger, and the old code can still operate on it.

If something catastrophic happens at step 5 (legacy columns dropped): restore from the pre-migration snapshot. There is no in-place rollback after step 5.

## Verification

After migration:

```sql
-- Every user has an id.
SELECT COUNT(*) FROM users WHERE id IS NULL;  -- expect 0

-- Every user has at least one identity.
SELECT COUNT(*) FROM users WHERE telegram_user_id IS NULL AND auth_user_id IS NULL;  -- expect 0

-- No orphan tasks.
SELECT COUNT(*) FROM tasks t LEFT JOIN users u ON t.user_uuid = u.id WHERE u.id IS NULL;  -- expect 0

-- No orphan users_status.
SELECT COUNT(*) FROM users_status us LEFT JOIN users u ON us.user_uuid = u.id WHERE u.id IS NULL;  -- expect 0

-- Telegram IDs are unique.
SELECT telegram_user_id, COUNT(*) FROM users GROUP BY telegram_user_id HAVING COUNT(*) > 1;  -- expect empty
```

End-to-end: run the bot's `/start` + photo solve + balance flow against the staging DB. Confirm no regression.
