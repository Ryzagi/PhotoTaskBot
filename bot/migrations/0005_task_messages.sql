-- Migration 0005 — follow-up chat messages per task (R2-2). Additive.

BEGIN;

CREATE TABLE IF NOT EXISTS task_messages (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id     bigint NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  user_id     text NOT NULL,
  role        text NOT NULL CHECK (role IN ('user', 'assistant')),
  content     text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS task_messages_task_idx ON task_messages (task_id, created_at);

COMMIT;
