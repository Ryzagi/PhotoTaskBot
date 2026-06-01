-- Migration 0006 — user-chosen display name (R3-6). Additive, nullable.

BEGIN;

ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name text;

COMMIT;
