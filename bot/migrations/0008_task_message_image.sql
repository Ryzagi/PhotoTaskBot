-- Migration 0008 — optional image attachment on a chat message (R: chat attachments).
-- Additive, nullable. image_path points into the same storage bucket as task images.

BEGIN;

ALTER TABLE task_messages ADD COLUMN IF NOT EXISTS image_path text;

COMMIT;
