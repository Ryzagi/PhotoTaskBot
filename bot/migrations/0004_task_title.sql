-- Migration 0004 — short task title for history labels (additive, nullable).

BEGIN;

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS title text;

COMMIT;
