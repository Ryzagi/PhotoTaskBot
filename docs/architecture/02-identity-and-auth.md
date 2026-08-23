# 02 — Identity and Authentication

This is the most consequential change in the project. Get it wrong and you either lock existing Telegram users out or hand attackers a balance API. Read carefully.

## Three identities, one domain user

A real person can sign into the product through up to three different identities:

| Identity | Source | Stable ID | Optional? |
|---|---|---|---|
| Telegram user | Telegram | `telegram_user_id BIGINT` | yes |
| Supabase Auth user | Supabase Auth (email / Google / Apple) | `auth_user_id UUID` | yes |
| Domain user | Our `users` table | `id UUID` | no |

The domain user is the canonical record. The other two are foreign keys that may or may not be set. A user could have:

- Telegram only (existing bot users who never download the app).
- Auth only (new mobile signups who never bind Telegram).
- Both (existing users who download the app and link their Telegram).

All balance, history, and limits hang off the domain `users.id`.

## Schema (post-migration)

```sql
CREATE TABLE users (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_user_id  BIGINT UNIQUE,                           -- nullable
  auth_user_id      UUID UNIQUE REFERENCES auth.users(id),   -- nullable
  username          TEXT,
  first_name        TEXT,
  last_name         TEXT,
  language_code     TEXT,
  is_premium        BOOLEAN DEFAULT false,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT users_at_least_one_identity
    CHECK (telegram_user_id IS NOT NULL OR auth_user_id IS NOT NULL)
);
```

Why `BIGINT` for `telegram_user_id`: Telegram already issues IDs above 2^31. `INTEGER` would silently overflow. The current `users.user_id` column is `INTEGER` and will overflow for newly-created Telegram users sometime in 2026–2027 — fixing this is part of the migration even before mobile work.

## Row-level security (RLS)

After the migration, RLS is trivial:

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users see self" ON users
  FOR SELECT USING (auth_user_id = auth.uid());

ALTER TABLE users_status ENABLE ROW LEVEL SECURITY;
CREATE POLICY "status see self" ON users_status
  FOR SELECT USING (user_id IN (SELECT id FROM users WHERE auth_user_id = auth.uid()));

ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "tasks see self" ON tasks
  FOR SELECT USING (user_id IN (SELECT id FROM users WHERE auth_user_id = auth.uid()));
```

Mobile clients use Supabase's anon key plus the user's JWT; RLS does the rest. The backend uses the service-role key for write paths and bypasses RLS — see `09-security.md` for the operational implications.

## JWT verification

Supabase issues HS256 JWTs signed with the project's JWT secret (different from the service-role and anon keys). Verify locally — **do not** round-trip to `/auth/v1/user` per request.

```python
# bot/auth/jwt.py
import jwt
from datetime import datetime, timezone

JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]
JWT_ALGORITHMS = ["HS256"]

def verify(token: str) -> dict:
    payload = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=JWT_ALGORITHMS,
        audience="authenticated",
    )
    if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
        raise ExpiredSignatureError
    return payload  # sub = auth_user_id, email, role, ...
```

Wrapped in a FastAPI dependency:

```python
# bot/auth/dependencies.py
async def current_user(
    request: Request,
    user_service: UserService = Depends(...),
) -> User:
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401)
    payload = jwt.verify(auth.removeprefix("Bearer "))
    user = await user_service.get_by_auth_id(payload["sub"])
    if not user:
        user = await user_service.create_from_auth(payload)
    return user
```

Every `/v1/*` route depends on `current_user`. The user object is **derived from the JWT**, never accepted as a request parameter.

## Internal bot endpoints

The bot does not have a Supabase Auth identity. It calls `/internal/*` with an HMAC-signed header:

```
X-Internal-Auth: t=<unix_ts>;sig=<hex(hmac_sha256(SECRET, f"{ts}.{method}.{path}.{body_sha256}"))>
```

The signature includes timestamp (reject >60s skew), method, path, and body hash. A constant-time comparison verifies it. The bot loads `INTERNAL_AUTH_SECRET` from the same `.env`.

This is non-negotiable. The current backend listens on `http://app:8000` inside Docker, but if that port ever gets exposed (a misconfigured proxy, a kubectl port-forward left running, a stray `EXPOSE` in a Dockerfile) it's a public balance API. Ship the HMAC before the mobile work, not after.

## Account linking flow

Existing Telegram users download the mobile app. They should not lose their balance or history.

```
┌─────────┐                ┌────────┐                ┌─────────┐                ┌─────┐
│ Mobile  │                │  API   │                │  Bot    │                │ DB  │
└────┬────┘                └───┬────┘                └────┬────┘                └──┬──┘
     │ POST /v1/auth/link/start (JWT)                    │                         │
     ├──────────────────────────►                        │                         │
     │                            INSERT account_links   │                         │
     │                            (code, user_id, ttl=5m)│                         │
     │                            ────────────────────────────────────────────────►│
     │ 200 {code: "ABCDEF"}                              │                         │
     │ ◄──────────────────────────                       │                         │
     │                                                   │                         │
     │ User pastes code in @PandaSolveBot                │                         │
     │ "ABCDEF"                                          │                         │
     │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ►│                         │
     │                                                   │ POST /internal/link/confirm
     │                                                   │ {code, telegram_user_id}
     │                                                   ├────────────────────────►│
     │                                                   │              MERGE      │
     │                                                   │ 200 {merged_user_id}    │
     │                                                   │ ◄────────────────────── │
     │                                                   │                         │
     │                            Bot replies: "Linked." │                         │
     │                                                   │                         │
     │ Push (or next GET /v1/me): linked=true            │                         │
     │ ◄──────────────────────────                       │                         │
```

### Code generation rules

- 6 digits, generated from `secrets.choice("0123456789", k=6)`. (Six is enough for human use; longer feels punitive.)
- Single-use. `consumed_at TIMESTAMPTZ` on the `account_links` row. Confirm endpoint sets it inside a transaction.
- 5-minute TTL.
- Rate limit: 3 codes per hour per `auth_user_id`, 10 per hour per source IP.
- Codes are stored hashed (SHA-256). When the bot calls confirm with the plaintext, we hash and look up.

### Merge policy (canonical)

When linking attaches a mobile-only `users` row (call it `M`) to an existing Telegram-only row (call it `T`), exactly one row survives. The policy is documented and tested. Without this, linking will silently lose money.

```
KEEP T.id  (the older row, the one with history)
ASSIGN M.auth_user_id → T.auth_user_id
SUM:     T.subscription_limit += M.subscription_limit
MAX:     T.daily_limit = MAX(T.daily_limit, M.daily_limit)
REASSIGN tasks      SET user_id = T.id WHERE user_id = M.id
REASSIGN users_status: keep T's row, discard M's
DELETE  M
INSERT  account_links.consumed_at = NOW()
```

The opposite case (auth user exists, then they try to link a Telegram ID that has no `users` row): just set `T.telegram_user_id`. No merge needed.

Edge case to test: a malicious user with their own Telegram ID tries to enter someone else's code. The 5-minute TTL plus 6-digit space (1,000,000) plus 3/hour rate limit makes brute force impractical, but write the rate-limit test anyway.

## What the migration does in practice

Spelled out fully in [`../migrations/0001-uuid-users.md`](../migrations/0001-uuid-users.md). Short version:

1. Add the new columns to `users`, backfill `telegram_user_id = user_id`.
2. Switch the PK to `id UUID`.
3. Add `user_uuid` to `users_status` and `tasks`, backfill.
4. Deploy the new backend that reads/writes `id` everywhere. Old code path that joins on `user_id` continues to work because the column still exists.
5. Cut the bot over to `/internal/*` (still synchronous, still resolves users by `telegram_user_id`).
6. Drop the legacy `user_id INTEGER` column in a follow-up migration once nothing references it.

Total downtime budget: zero. Every step is additive until the legacy column drop.
