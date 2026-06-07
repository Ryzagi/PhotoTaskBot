# Google Play Billing — top-ups (consumable packs + subscription)

Sell in-app credit ("bamboo"/solutions) through **Google Play Billing** (required by Play
policy for in-app digital goods; the Telegram top-up stays for *bot* users only). Two product
types: **consumable packs** (buy N solutions) and a **subscription** (recurring, raised/unlimited
daily limit).

## Golden rule
The client never grants credit. Purchase → **purchase token** → **backend verifies with the
Google Play Developer API** → backend credits balance + records the token (dedupe) → client
consumes/acknowledges. All entitlement is server-decided.

## External setup (must be done in consoles — code can't)
1. **Play Console** (dev account, $25): register `com.pandasolve.app`; create products:
   - Consumables: e.g. `bamboo_10`, `bamboo_30`, `bamboo_100` (managed products, consumable).
   - Subscription: `panda_plus` with a base plan (e.g. monthly), defining the entitlement.
2. **Play Developer API:** a Google Cloud service account with the Android Publisher API enabled,
   linked + granted in Play Console (Financial data → view; or appropriate role). Download its
   JSON key → backend env `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON_BASE64`.
3. **Subscriptions only — Real-time Developer Notifications (RTDN):** a Pub/Sub topic in GCP, set
   in Play Console; a push subscription → a backend webhook to track renew/cancel/expire/grace.
   (Polling on app-open is a simpler fallback for v1; RTDN is the robust path.)
4. Upload a signed build to a **closed/internal test track**; add license testers to test
   purchases without being charged.

## Backend (code)
- **Migration `0007_purchases.sql`:** `purchases(id, user_id, platform, product_id, purchase_token UNIQUE,
  kind ['consumable'|'subscription'], state, credited_amount, created_at)` — UNIQUE token prevents
  double-credit.
- **`PlayVerifier`** (`bot/billing/play.py`): given (productId, token), call the Play Developer API
  (`purchases.products.get` for consumables, `purchases.subscriptionsv2.get` for subs) using a
  service-account access token (via `google-auth`). Env-gated: clear error if creds absent.
- **Endpoints (`bot/api/v1/billing.py`):**
  - `POST /v1/billing/google/verify` `{productId, purchaseToken}` — verify a **consumable**; if valid
    & unseen, credit `subscription_limit` by the pack's solution count (a `PRODUCT_CREDITS` map), insert
    the token row, return new balance. Idempotent on token.
  - `POST /v1/billing/google/subscription` `{productId, purchaseToken}` — verify a **subscription**;
    mark active, raise the daily limit / flag premium while active.
  - `POST /internal/billing/rtdn` (or `/v1/...` with a shared secret) — RTDN webhook for sub lifecycle.
- Reuse `BillingService.add_subscription` for crediting; add `set_premium`/daily-limit bump for subs.

## Android (code)
- Dep: `com.android.billingclient:billing-ktx`.
- **`BillingRepository`:** connect `BillingClient`; `queryProductDetails` (INAPP packs + SUBS);
  `launchBillingFlow`; on `PurchasesUpdated` → POST token to backend verify → on success
  `consumeAsync` (consumables) / `acknowledgePurchase` (subs) → refresh `/v1/me`.
- **UI:** a top-up sheet (packs grid + the subscription card) opened from Profile "Пополнить бамбук"
  (replaces the Telegram deep link in the Play build). Localized (ru/en).
- Handle pending/cancelled/already-owned; restore on launch (`queryPurchasesAsync`).

## Decisions still open
- Pack sizes + prices; subscription entitlement (unlimited vs +N/day) + period/price.
- v1 subs: RTDN webhook vs poll-on-open (recommend RTDN, but poll is a fine MVP).

## Build order
1. Backend: migration + `PlayVerifier` interface + consumable verify endpoint + crediting + tests
   (verification stubbed/env-gated until creds exist).
2. Android: `BillingRepository` + consumable packs UI + verify wiring.
3. Subscription: verify endpoint + RTDN webhook + entitlement + UI.
4. Console/GCP setup + closed-track test purchases → iterate.

## Reality check
Steps 1–3 are writable now; **nothing is testable end-to-end until the Play Console products +
Play Developer API service account exist and a signed build is on a test track**. The Play
fee is ~15–30%.
