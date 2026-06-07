-- Migration 0007 — Google Play purchase ledger. One row per consumed purchase
-- token, so a token can never grant credits twice (idempotency). Additive.

BEGIN;

CREATE TABLE IF NOT EXISTS play_purchases (
  purchase_token  text PRIMARY KEY,
  user_id         text NOT NULL,
  product_id      text NOT NULL,
  credits         int  NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS play_purchases_user_idx ON play_purchases (user_id);

COMMIT;
