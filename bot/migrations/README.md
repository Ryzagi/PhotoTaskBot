# Migrations

Numbered, append-only SQL files. Applied by `bot/migrate.py` in order. Never edit a migration that has already shipped — write a new one.

## Applying

```
python -m bot.migrate up   # apply all pending
python -m bot.migrate up 0001  # apply up to (and including) 0001
python -m bot.migrate status   # which have been applied
```

The runner stores applied versions in a `schema_migrations` table (created on first run).

## Writing a new migration

1. Name: `NNNN_short_description.sql`. NNNN is the next integer, zero-padded to four.
2. Wrap in `BEGIN; … COMMIT;`.
3. Use `IF NOT EXISTS` / `IF EXISTS` and `DO $$ … EXCEPTION WHEN duplicate_object THEN NULL; END $$;` for idempotency so reruns are safe.
4. Add a companion `docs/migrations/NNNN-short-description.md` documenting the change, rollout, and rollback.
