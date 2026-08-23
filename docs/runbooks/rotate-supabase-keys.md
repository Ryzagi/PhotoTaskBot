# Runbook — Rotate keys and secrets

When to use:

- Routine annual rotation.
- Suspected leak (committed by accident, posted in Slack/Telegram, employee left).
- Required by compliance.

Each section is independent. Read the section, do the steps in order, verify, move on.

## Supabase JWT secret

**Affects**: every signed-in mobile user.

**Downtime**: zero, but every user is forced to sign in again.

1. In Supabase → Project Settings → API → JWT Settings, click **Generate new JWT secret**.
2. Copy the new value.
3. Update production secret `SUPABASE_JWT_SECRET`.
4. Redeploy backend.
5. Existing mobile sessions immediately fail JWT verification → mobile app catches 401, calls `supabase.refreshSession()`, fails (refresh tokens also invalid), shows sign-in screen.
6. Users sign back in. New sessions issued under the new secret.

Mitigation for forced sign-ins: support a 24-hour grace window by verifying with **either** the old or new secret. Requires code change (`auth/jwt.py` checks both), so plan ahead for non-emergency rotations.

## Supabase service-role key

**Affects**: backend writes (everything).

**Downtime**: a few seconds during deploy.

1. Supabase → Project Settings → API → click **Reset service_role key**.
2. Update production secret `SUPABASE_SERVICE_ROLE_KEY`.
3. Redeploy. Backend reconnects with the new key.
4. The old key is invalid immediately; in-flight Supabase calls fail. The retry loop in `bot/supabase_service.py` will reconnect.

This rotation is more disruptive than the JWT secret rotation because all backend writes break for a few seconds. Prefer to deploy during low traffic.

## Supabase anon key

**Affects**: mobile clients (they ship this key).

**Downtime**: zero, but rotation is essentially impossible without a forced mobile-app update.

Practically: do not rotate the anon key unless it's been leaked **and** the leak enables abuse. The anon key only allows operations gated by RLS. If RLS is correct, the anon key being public is fine — it's designed to be.

If you must rotate:

1. Supabase → Reset anon key.
2. Update mobile app `BuildConfig` / `Info.plist` constants.
3. Ship a new mobile release. Old releases stop working.
4. Force-update mechanism: backend `/v1/config` includes `min_supported_version`. Mobile compares with bundled version on startup; below → show "Please update" full-screen.

## INTERNAL_AUTH_SECRET (bot HMAC)

**Affects**: the Telegram bot ↔ backend channel.

**Downtime**: zero with the dual-secret pattern.

1. Generate new secret: `openssl rand -hex 32`.
2. Add to backend env as `INTERNAL_AUTH_SECRET_NEXT`. Backend code verifies against either secret (when present). Redeploy.
3. Update bot env to `INTERNAL_AUTH_SECRET = <new value>`. Redeploy bot. Bot now signs with the new secret; backend accepts old or new.
4. After 24 hours, remove the old secret from backend env: rename `INTERNAL_AUTH_SECRET_NEXT` → `INTERNAL_AUTH_SECRET`. Redeploy.

## OpenAI / Google API keys

**Affects**: solver workers.

**Downtime**: zero with the dual-key pattern.

OpenAI dashboard → create new key → add as `OPENAI_API_KEY_NEXT`. Backend `bot/gpt_service.py` is wired to prefer `_NEXT` if set. Redeploy. Verify solves still work. Delete old key in OpenAI dashboard. Remove `_NEXT` env, rename, redeploy.

Google AI Studio: similar pattern.

## APNs `.p8` key

**Affects**: iOS push notifications.

**Downtime**: zero.

1. Apple Developer → Keys → create a new APNs Auth Key. Download the `.p8` file. Note the Key ID.
2. Base64-encode: `base64 -i AuthKey_ABCD12345.p8`.
3. Set `APNS_AUTH_KEY_BASE64_NEXT` and `APNS_KEY_ID_NEXT`. Redeploy.
4. Backend `bot/push/apns.py` switches to `_NEXT` if set.
5. Revoke old key in Apple Developer.
6. Rename env, redeploy.

## FCM service account JSON

**Affects**: Android push notifications.

**Downtime**: zero.

1. Firebase console → Project settings → Service accounts → Generate new private key.
2. Download JSON, base64-encode, set as `FCM_SERVICE_ACCOUNT_JSON_BASE64_NEXT`. Redeploy.
3. Verify a push goes out.
4. Delete the old service account key in Firebase. Rename env. Redeploy.

## Telegram bot token

**Affects**: the bot.

**Downtime**: ~minutes (bot reconnects).

1. BotFather → `/revoke` (or `/token` to get a new one). The old token stops working immediately.
2. Update `TELEGRAM_BOT_TOKEN` in bot deployment. Redeploy bot.
3. Bot reconnects to Telegram with the new token.

There's no graceful overlap here; BotFather doesn't support two active tokens.

## After any rotation

- [ ] Update 1Password / secret manager with the new value.
- [ ] Delete the old value from the manager.
- [ ] Check that the leaked source is not still in a logged-in shell history or container env: `kubectl exec ... env`, `docker exec ... env`.
- [ ] If the leak was in git history: rewrite history (`git filter-repo`) and force-push, or accept that the leaked credential is permanently public and rely on the rotation having neutralized it. Notify the team.
- [ ] Open a postmortem doc if the leak was unintentional. Don't blame; document and fix the process.

## Forgot which secrets exist?

```bash
fly secrets list -a pandasolve-api
# or
kubectl get secret pandasolve-api -o jsonpath='{.data}' | jq 'keys'
```

The canonical list lives in [`deploy-backend.md`](deploy-backend.md#secrets-to-set-on-first-deploy).
