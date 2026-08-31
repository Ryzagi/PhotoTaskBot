# PhotoTaskBot — Documentation

This directory holds the durable specification for PhotoTaskBot as it evolves from a Telegram-only product into a multi-client (Telegram + Android + iOS) product on a shared FastAPI + Supabase backend.

## How to navigate

- **Start here** if you are new: [`architecture/01-overview.md`](architecture/01-overview.md) for the system diagram, glossary, and current-vs-target gap.
- **Building the backend?** Read the architecture docs in order. `02-identity-and-auth.md` and `04-async-solving.md` are the highest-impact reads.
- **Building the mobile apps?** Skim `01-overview.md`, then go to [`clients/android.md`](clients/android.md) or [`clients/ios.md`](clients/ios.md). The API contract lives in [`architecture/03-backend-api.md`](architecture/03-backend-api.md) plus the live `openapi.json`.
- **Running a migration?** [`migrations/`](migrations/) has the step-by-step, rollback, and downtime budget per migration.
- **On-call?** Start at [`runbooks/on-call-incident.md`](runbooks/on-call-incident.md).
- **Signup emails not arriving?** [`runbooks/email-smtp-setup.md`](runbooks/email-smtp-setup.md) — Supabase's built-in mailer is capped at 2/hour, so production needs custom SMTP.

## Document map

```
docs/
├── README.md                          ← you are here
├── architecture/
│   ├── 01-overview.md                 System diagram, current vs target, glossary
│   ├── 02-identity-and-auth.md        UUID model, link flow, merge policy, JWT verify
│   ├── 03-backend-api.md              /v1/* endpoint spec + error model
│   ├── 04-async-solving.md            Queue topology, retry, push triggers
│   ├── 05-storage-and-data.md         Schema, RLS, storage paths, signed URLs
│   ├── 06-rate-limiting-abuse.md      Per-tier limits, image caps, CF rules
│   ├── 07-push-notifications.md       APNs/FCM token lifecycle, payload schema
│   ├── 08-observability.md            Logs, metrics, Sentry, alerting
│   └── 09-security.md                 Threat model, secrets, RLS audit, internal auth
├── clients/
│   ├── android.md                     Module structure, libs, build, release
│   └── ios.md                         Project structure, libs, build, release
├── migrations/
│   ├── 0001-uuid-users.md             UUID migration, step-by-step + rollback
│   └── 0002-tasks-history.md          Tasks table history columns
├── email-templates/
│   ├── confirm-signup.html            Supabase "Confirm signup" body (RU + EN)
│   └── reset-password.html            Supabase "Reset password" body (RU + EN)
└── runbooks/
    ├── deploy-backend.md              Push code to prod
    ├── email-smtp-setup.md            Custom SMTP (Resend) for signup emails
    ├── rotate-supabase-keys.md        Rotate service-role and JWT secrets
    └── on-call-incident.md            What to do when something is on fire
```

## Conventions

- All API endpoints are versioned. Mobile clients call `/v1/*`. The Telegram bot calls `/internal/*` over a private network with an HMAC-signed header.
- The source of truth for the public API shape is `openapi.json`, emitted by FastAPI. Mobile clients regenerate from it; if you change a schema, mobile CI breaks until the spec is published.
- The source of truth for the database schema is `bot/migrations/*.sql`, applied in numeric order. Never edit a migration that has already shipped — write a new one.
- Times are stored as `TIMESTAMPTZ` and displayed in the user's local zone on the client. Dates (like `last_processing_date`) are `DATE` in UTC.

## Glossary (one place, used everywhere)

| Term | Meaning |
|---|---|
| `auth_user_id` | UUID issued by Supabase Auth. Identifies a sign-in identity. |
| `user_id` (UUID) | Internal domain user. One per real person. May link to a Telegram account, an Auth user, or both. |
| `telegram_user_id` | The Telegram numeric ID, BIGINT. Optional column on `users`. |
| Daily limit | Free solves per UTC day. Default 3. Resets at 00:00 UTC. |
| Subscription limit | Paid solves remaining. Purchased via Telegram Stars (today) or IAP (future). Spent before daily, never the other way around (see `04-async-solving.md`). |
| Task | One solve job. May be image or text. Lives in the `tasks` table. |
| Link code | 6-digit, single-use, 5-minute TTL code that binds a mobile sign-in to an existing Telegram user. |
