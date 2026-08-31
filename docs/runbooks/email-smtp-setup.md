# Runbook — Custom SMTP for Supabase Auth (signup confirmation emails)

When to use:

- First-time production setup (this doc's main purpose).
- Signup confirmations stop arriving, or arrive late/in spam.
- Rotating the Resend API key.
- Moving to a different sending domain.

## Why this is required, not optional

`Authentication → Email → "Confirm email"` is **ON** — that is our only anti-abuse
measure for email signups (see the auth decisions in the agent memory). Every
signup therefore sends an email.

Supabase's built-in email service is rate-limited to **2 messages per hour** per
project and is documented as best-effort, non-production only. With it, the third
person to sign up in an hour silently never gets a confirmation link and cannot
use the app. Custom SMTP raises this to **30/hour** by default, adjustable.

## What we chose and why

| Decision | Value | Reason |
| --- | --- | --- |
| Provider | **Resend** | Free tier: 3,000/month, 100/day, SMTP relay included, 3 domains. Verifies a domain by **DNS records only** — `upword.live` has no MX, so providers that verify by emailing the sender address (Brevo) can't be used. No branding footer on the free plan (Brevo stamps its logo unless you pay $11/mo extra). |
| Sending domain | **`mail.upword.live`** | `pandasolve.app` is not registered (no NS/A/DMARC as of 2026-08-28). A subdomain keeps sending reputation separate from the root domain that serves the API. |
| From address | `noreply@mail.upword.live`, sender name `PandaSolve` | — |
| Templates | Bilingual RU + EN, in [`docs/email-templates/`](../email-templates/) | Supabase templates are single-language; there is no per-user locale without an auth hook. |

If `pandasolve.app` is ever registered, redo steps 1–3 against `mail.pandasolve.app`
and change only the From address in step 5. Nothing in the app or backend hardcodes
the sending domain.

## 1. Resend account and domain

1. Sign up at [resend.com](https://resend.com) with the project email.
2. **Domains → Add Domain** → `mail.upword.live`.
3. Pick a region and keep it — the MX value in step 2 embeds it.
4. Leave the page open; it lists the three DNS records you need.

## 2. DNS records in GoDaddy

`upword.live` is on GoDaddy DNS (`ns35/ns36.domaincontrol.com`). GoDaddy's
**Name** field is relative to the zone root, so for the `mail` subdomain the
names are:

| Type | Name | Value | Priority |
| --- | --- | --- | --- |
| MX | `send.mail` | `feedback-smtp.<region>.amazonses.com` (copy exact value from Resend) | 10 |
| TXT | `send.mail` | `v=spf1 include:amazonses.com ~all` | — |
| TXT | `resend._domainkey.mail` | `p=…` (the long DKIM key from Resend) | — |

Resend's dashboard shows the names with the domain appended
(`send.mail.upword.live`). **Do not paste that into GoDaddy** — GoDaddy appends the
zone itself, so pasting the full name creates `send.mail.upword.live.upword.live`.
Strip the `.upword.live` suffix.

Then hit **Verify DNS Records** in Resend. Propagation is usually minutes.

Verify from the shell:

```bash
dig +short TXT resend._domainkey.mail.upword.live
dig +short TXT send.mail.upword.live
dig +short MX  send.mail.upword.live
```

## 3. DMARC — already set, do not break it

`_dmarc.upword.live` exists and is **`p=quarantine; adkim=r; aspf=r`** (GoDaddy's
default). There is no `sp=` tag, so **`mail.upword.live` inherits `p=quarantine`**.

This is fine *because* alignment is relaxed (`adkim=r`, `aspf=r`):

- DKIM signs as `d=mail.upword.live` → organizational domain `upword.live` → aligns with the `From:` domain.
- SPF envelope sender is `send.mail.upword.live` → same organizational domain → aligns.

Both pass, so DMARC passes. But it also means that **if step 2 is incomplete, mail
doesn't just look unauthenticated — it gets quarantined.** Don't send real signups
through until Resend reports the domain verified.

The root `upword.live` has **no SPF record at all**. That is only a problem if you
later send from `@upword.live` directly; leave it alone for this setup.

## 4. Resend API key

**API Keys → Create API Key**, permission **Sending access**, restricted to the
`mail.upword.live` domain. Copy it once (`re_…`) — it is not shown again.

This is a secret. It goes in the Supabase dashboard only; never in the repo,
`local.properties`, or a commit.

## 5. Supabase SMTP settings

`Authentication → Emails → SMTP Settings` (older projects: `Project Settings →
Auth → SMTP Settings`). Enable custom SMTP and fill in:

| Field | Value |
| --- | --- |
| Host | `smtp.resend.com` |
| Port | `465` (implicit TLS; `587` STARTTLS also works) |
| Username | `resend` — the literal string, not an email |
| Password | the `re_…` API key from step 4 |
| Sender email | `noreply@mail.upword.live` |
| Sender name | `PandaSolve` |

## 6. Raise the auth rate limit

`Authentication → Rate Limits` → **Rate limit for sending emails**. Attaching
custom SMTP sets it to 30/hour; raise it toward the provider ceiling. Resend's
free tier is **100/day**, so anything above ~4/hour sustained is theoretical —
set it to 100/hour to absorb bursts and let Resend's daily cap be the real limit.

Know what the ceiling means: past 100 emails in a day Resend rejects, Supabase
returns an error on signup, and the user sees a failure. If signups ever approach
that, move to a paid tier before it bites.

## 7. Site URL and redirect

The backend already serves the landing page the confirmation link returns to —
`GET /auth/confirmed` in `bot/app/main.py`, bilingual, brand-styled.

In `Authentication → URL Configuration`:

- **Site URL**: `https://panda-api.upword.live/auth/confirmed`
- **Redirect URLs**: add the same URL, **and** `https://panda-api.upword.live/auth/reset`
  (the password-recovery page). The app builds that second URL from
  `BuildConfig.API_BASE_URL`, so allow-list one entry per API base a build can point
  at — a URL that isn't listed makes Supabase silently fall back to the Site URL and
  the reset link lands on the wrong page.

Both paths are allow-listed in the `Caddyfile`'s `@public` matcher, so no proxy
change is needed — but if you add a third auth page, it must go in that matcher
or Caddy answers 404.

## 8. Email templates

`Authentication → Emails → Templates`:

- **Confirm signup** ← [`docs/email-templates/confirm-signup.html`](../email-templates/confirm-signup.html). Subject: `PandaSolve — подтверди почту / confirm your email`
- **Reset password** ← [`docs/email-templates/reset-password.html`](../email-templates/reset-password.html). Subject: `PandaSolve — сброс пароля / password reset`

Leave **Magic Link**, **Invite** and **Change Email Address** on defaults; no code
path triggers them today.

Edit the files in the repo and re-paste, so the dashboard never becomes the only
copy.

## 9. Verify

1. Sign up in the app with a real address you control. Do it three times in a row
   with different addresses — under the old built-in service the third would have
   been dropped.
2. **Resend → Logs** should show three `delivered` rows.
3. Open the raw headers of a received message and confirm all three pass:

   ```
   Authentication-Results: ... spf=pass ... dkim=pass ... dmarc=pass
   ```

   A `dmarc=fail` here means step 2 is incomplete — with `p=quarantine` the mail is
   heading for spam.
4. Test **one address per major provider your users actually use**: Gmail,
   `mail.ru`, `yandex.ru`. A new sending domain has no reputation, and the Russian
   providers are the strict ones. If mail lands in spam there, register the domain
   in [Mail.ru Postmaster](https://postmaster.mail.ru) and
   [Yandex Postmaster](https://postmaster.yandex.ru) and watch the reputation
   panels rather than guessing.
5. Click the link and confirm you land on the 🐼✅ page and can then sign in.

## Gotchas

- **Link scanners burn the token.** Corporate/AV scanners (Outlook Safe Links and
  friends) pre-fetch URLs, which consumes Supabase's one-time confirmation token —
  the user then clicks a dead link. The fix is an OTP code (`{{ .Token }}`) plus an
  in-app entry screen; the app has no such screen, so this is a known limitation,
  not something the templates can solve.
- **Free-tier log retention is 30 days.** Debugging a delivery complaint older
  than that is not possible.
- **Password recovery goes through the web, not the app.** The sign-in screen's
  "Забыл пароль?" calls `resetPasswordForEmail` with `redirectUrl =
  <API_BASE_URL>/auth/reset`; that backend page takes the new password. It is
  deliberately not an in-app deep link — the user who needs it usually reads mail on
  another device, where `com.pandasolve.app://` is a dead end.
- **`SupabaseAuth.kt` pins `flowType = IMPLICIT`.** The reset page reads the recovery
  token from the URL fragment. Switching to PKCE puts a `?code=` there instead, whose
  verifier only exists on the phone that asked — cross-device reset breaks. If you
  ever need PKCE for something else, the reset page has to change with it.
- **Supabase never says whether an address is registered.** `resetPasswordForEmail`
  succeeds either way, by design. The UI copy says "if that address has an account",
  so don't "fix" it into a confirmation.
- **Google sign-in sends no email**, so it is unaffected by all of this — an
  account created via Credential Manager arrives pre-verified.

## Rollback

Turn off custom SMTP in step 5. Auth immediately falls back to the built-in
service at 2/hour — acceptable for an hour of debugging, not for a day. The DNS
records are harmless to leave in place.
