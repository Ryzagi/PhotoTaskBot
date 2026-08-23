# 09 — Security

## Threat model

Adversaries we are designing against, ordered by likelihood:

1. **Curious user**: tampers with their own JWT or request bodies trying to get a free solve.
2. **Bot scraper**: scripts the API to mass-solve homework. Goal: rate-limit cost on us.
3. **Account thief**: steals a JWT (XSS on a future web app, MITM on a misconfigured network) and tries to spend someone else's balance.
4. **Internal-endpoint hunter**: finds the bot endpoints exposed somehow (proxy misconfig, port leak) and drains balances or broadcasts spam.
5. **Insider with DB access**: misuses the service-role key. Lower likelihood, severe blast radius.

Not in scope: nation-state, supply-chain attacks on Supabase/OpenAI, physical device theft.

## Authentication boundaries

| Boundary | Mechanism | Failure mode |
|---|---|---|
| `/v1/*` ← mobile | Supabase JWT (HS256) | Drops to 401 |
| `/internal/*` ← bot | HMAC-SHA256 signed header | Drops to 403 |
| FastAPI ↔ Postgres | Service-role key | RLS bypassed; backend must validate |
| FastAPI ↔ Supabase Storage | Service-role key | Same |
| Mobile ↔ Supabase Storage | Signed URL, ≤24h TTL | URL expires |
| Mobile ↔ Supabase Auth | Anon key | Auth is gated by Supabase |

### JWT verification — non-negotiables

- Verify locally with `SUPABASE_JWT_SECRET` (HS256).
- Check `exp`. Reject expired.
- Check `aud = "authenticated"`.
- Use `sub` (auth user UUID) — never trust `email` or `role` for authorization decisions if they can be set by the user (Supabase metadata is editable from the client unless restricted).
- Cache nothing user-specific from the JWT beyond the request scope.

### HMAC verification — non-negotiables

```
X-Internal-Auth: t=<unix_ts>;sig=<hex>
sig = hmac_sha256(INTERNAL_AUTH_SECRET, f"{ts}.{method}.{path}.{sha256(body)}")
```

- Reject if `|now - ts| > 60` (replay window).
- Constant-time compare: `hmac.compare_digest`.
- One secret per environment (prod / staging / dev). Rotate without downtime by accepting two for a 24h window.

## Secrets management

`.env` files are dev-only. In production:

| Secret | Stored in | Rotated by |
|---|---|---|
| `SUPABASE_JWT_SECRET` | Cloud secret manager (1Password, AWS SM, GCP SM) | Supabase project settings; backend reload |
| `SUPABASE_SERVICE_ROLE_KEY` | Same | Supabase project settings; immediate redeploy |
| `OPENAI_API_KEY` | Same | OpenAI dashboard; redeploy |
| `GOOGLE_API_KEY` | Same | GCP console; redeploy |
| `INTERNAL_AUTH_SECRET` | Same | Manual; documented in runbook |
| `APNS_AUTH_KEY_BASE64` | Same | Apple Developer; redeploy |
| `FCM_SERVICE_ACCOUNT_JSON_BASE64` | Same | Firebase console; redeploy |
| `TELEGRAM_BOT_TOKEN` | Same | BotFather; redeploy |
| `SENTRY_DSN` | Same | Sentry settings; redeploy |

The repo's `.env` file is gitignored. `.env.example` is committed with placeholder keys. Pre-commit hook scans staged diffs for `sk-`, `eyJ`, and other secret prefixes.

## RLS audit

Backend uses the service-role key, so RLS is **not** the gate — backend authorization is. RLS is the second layer for any future direct-from-client read.

Audit checklist:

- [ ] `users`: SELECT policy = `auth_user_id = auth.uid()`. No UPDATE/INSERT/DELETE from clients.
- [ ] `users_status`: SELECT policy = `user_id IN (SELECT id FROM users WHERE auth_user_id = auth.uid())`. Backend-only writes.
- [ ] `tasks`: SELECT policy = same. Backend-only writes.
- [ ] `user_devices`: SELECT, INSERT, DELETE policies via auth_uid. Used for the "manage devices" screen if we add one.
- [ ] `account_links`: no client access. Server only.
- [ ] `auth.users`: managed by Supabase Auth; do not touch.

Run `pgaudit` or a custom check in CI that diffs the RLS configuration against the committed `.sql`.

## Input validation

All request bodies are pydantic models. No bare dict access. No string-formatted SQL. No `eval`/`exec` on user input. No subprocess on user input (the LaTeX renderer accepts user text → into a file → into `pdflatex`; review for command injection at every change, even though `pdflatex` itself is the renderer not a shell).

Image upload validations:

1. `Content-Length` ≤ 10 MiB (middleware, before reading).
2. MIME type in allowlist.
3. Pillow can decode + within max megapixels.
4. EXIF stripped before storage (`PIL.ImageOps.exif_transpose` + save without metadata) — orientation is preserved, GPS and camera info is dropped.

Text input validations:

1. Length ≤ 10,000 characters.
2. Decoded as UTF-8; reject other encodings.

## Sign-up and abuse prevention

- Email verification required before solving (Supabase Auth feature; turn it on).
- Apple/Google sign-in is already verified by the provider.
- New accounts: first solve is allowed; after that, rate-limited harder for the first 24h.
- Email domain disposable-list block (e.g., `disposable-email-domains` Python package) on registration.

## Telegram link code

Already covered in `02-identity-and-auth.md`. Recap:

- 6 digits, hashed at rest (SHA-256), 5-minute TTL, single-use.
- 3 codes per hour per `auth_user_id`, 10 per hour per IP.
- Bot's confirm endpoint is on `/internal/*` (HMAC-protected).
- Failed code attempts logged; alert at >100/hour.

## Data privacy

- We collect: email (Supabase Auth), Telegram profile basics, image of the problem, text of the problem, language, device token.
- We do not collect: precise location, contacts, microphone, persistent advertising IDs.
- Deletion: `DELETE /v1/me` endpoint that cascades to `users` (FK ON DELETE CASCADE on dependents). Storage objects are deleted in a background job (Supabase Storage has no direct cascade from Postgres).
- Retention: tasks kept indefinitely today. Add a 1-year auto-delete cron when GDPR/Russian PD law compliance becomes a priority.

App Store privacy nutrition labels and Google Play data safety form: update before submission. See [`../clients/ios.md`](../clients/ios.md) and [`../clients/android.md`](../clients/android.md).

## Dependency scanning

GitHub Dependabot on the repo. Weekly automated PRs for security updates. Manual review for major-version bumps.

`pip-audit` in CI. Block merges with known CVEs in direct deps unless explicitly waived.

## Penetration test

Before public launch, run a focused pen test (paid external firm or a thorough security review by a knowledgeable engineer) targeting:

- Authentication bypass on `/v1/*`.
- Internal endpoint exposure.
- RLS gaps.
- Image upload abuse (zip bombs, polyglot files).
- Telegram link code brute force.

Capture findings in `docs/security/<date>-pentest.md`. Fix `high` and `critical` before launch; document risk acceptance for `medium` and below.
