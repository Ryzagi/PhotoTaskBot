# Runbook — Deploy / update the backend

How the PandaSolve backend is deployed on the production server and how to ship an
update. One process (`bot.app.main:app`) serves three surfaces: `/v1/*` (mobile,
Supabase JWT), `/internal/*` (bot, HMAC), legacy `/tasker/api/*`.

> Deployment is **docker-compose on a single Ubuntu host**. There is no CI/CD yet
> (a GitHub Actions pipeline is a future enhancement — see the bottom). Deploys are
> `git pull` + `docker compose up -d --build` on the box.

## Topology (as deployed)

The server also runs another product (`upword_game`) whose **Caddy owns ports
80/443**. PandaSolve does **not** run its own Caddy — it attaches to that one.

```
Internet ──443──► upword_game-caddy-1 ──┬─ upword.live          → upword frontend
                  (shared Caddy)        └─ panda-api.upword.live → pandasolve-api:8000
                                                                    (phototaskbot "app")
Telegram bot ──http://app:8000 (private)─► same app container
Supabase (Auth + Postgres + Storage) ── shared, hosted off-box
```

- Compose projects: **`upword_game`** (web app + Caddy) and **`phototaskbot`**
  (this repo: `app` + `telegram_bot`, optional `redis` + `worker`).
- The app's `:8000` is **never published to the host**. The bot reaches it on the
  phototaskbot network as `app:8000`; Caddy reaches it on the shared network as
  `pandasolve-api:8000` (a network alias in `docker-compose.yml`).
- Public DNS: `panda-api.upword.live` → server IP (GoDaddy A record).

## One-time wiring (done; recorded for rebuilds / new servers)

1. **DNS** — GoDaddy A record: name `panda-api`, value = server public IP. Verify:
   ```bash
   dig +short panda-api.upword.live      # → server IP
   ```
2. **Find Caddy's docker network:**
   ```bash
   docker inspect -f '{{range $k,$_ := .NetworkSettings.Networks}}{{$k}} {{end}}' upword_game-caddy-1
   # → upword_game_default
   ```
3. **`.env`** (in the phototaskbot repo dir) needs at least:
   ```ini
   API_DOMAIN=panda-api.upword.live
   CADDY_NETWORK=upword_game_default        # from step 2; compose joins app to it
   SUPABASE_JWT_SECRET=<Supabase → Settings → API → JWT Secret>   # or /v1/* all 401
   # plus existing keys: OPENAI_API_KEY, GOOGLE_API_KEY, SUPABASE_*,
   # TELEGRAM_BOT_TOKEN, INTERNAL_AUTH_SECRET, USER_EMAIL/USER_PASSWORD
   ```
4. **Caddy block** — add to the Caddyfile that `upword_game-caddy-1` uses (in
   `~/upword_game`), alongside the upword block. Source: this repo's `./Caddyfile`.
   ```caddyfile
   panda-api.upword.live {
       encode zstd gzip

       @public path /v1 /v1/* /healthz
       handle @public {
           request_body {
               max_size 10MB
           }
           reverse_proxy pandasolve-api:8000
       }

       # legacy /tasker/api/* and /internal/* stay private
       handle {
           respond 404
       }
   }
   ```
   Caddyfile rule: an opening `{` must be the last token on its line — no inline
   `handle { respond 404 }` one-liners (they fail with "Unexpected next token after '{'").
   Reload Caddy (zero downtime):
   ```bash
   cd ~/upword_game
   docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile
   docker compose exec caddy caddy reload   --config /etc/caddy/Caddyfile
   ```

## Two images (since the apt/TeX split)

- **`Dockerfile`** (lean): the FastAPI `app` + arq `worker`. No apt/TeX — serves `/v1`,
  `/internal`, legacy. Builds without touching Debian repos.
- **`Dockerfile.bot`**: the `telegram_bot` only. Installs TeX Live (pdflatex + pdftoppm) for
  `bot/latex_renderer.py` (PNG rendering), which is imported solely by `bot/app/tg_app.py`.
- `.dockerignore` keeps `clients/` (~260 MB) and caches out of the build context.

So **the mobile backend (`app`) rebuilds without TeX** — the recurring
"At least one invalid signature was encountered" apt failure cannot block it. Only a bot
rebuild touches apt.

## Deploy / update (the routine)

From the phototaskbot repo dir on the server:

```bash
# 1. Get the new code
git fetch && git checkout <branch> && git pull        # e.g. master, or feat/mobile-apps-cute-ui

# 2. Apply additive DB migrations (safe for the live bot; idempotent)
make migrate                                           # needs DATABASE_URL; or paste bot/migrations/*.sql in Supabase

# 3. Rebuild + restart the API only (lean image; bot keeps running on its container)
docker compose build app && docker compose up -d app

# 4. (optional) async solving + push: set REDIS_URL=redis://redis:6379 in .env, then
docker compose --profile async up -d --build worker redis

# 5. (rarely) rebuild the bot — needs TeX Live, so the host apt/clock must be healthy first
docker compose build telegram_bot && docker compose up -d telegram_bot
```

The entrypoint is `bot.app.main:app` (NOT `bot.app.app:app`, which 404s on `/v1/*`).
It's baked into the Dockerfile CMD — don't override it.

## Verify

```bash
curl -s https://panda-api.upword.live/healthz                                    # {"status":"ok"}
curl -s -o /dev/null -w '%{http_code}\n' https://panda-api.upword.live/v1/me     # 401 (no token = correct)
curl -s -o /dev/null -w '%{http_code}\n' https://panda-api.upword.live/tasker/api/x  # 404 (legacy blocked)
docker network inspect upword_game_default | grep -E 'pandasolve-api|caddy'      # both present
```

Then confirm the **bot still works** (send it a photo) — `/internal/*` must not regress.

## Schema-change deploy (additive-only policy)

Migrations are **additive and idempotent** — the live bot must keep working
(`IF NOT EXISTS`, never change PKs; see `mobile-identity-key-model`). A schema change
is a 2-stage deploy:

1. **Apply the migration first** (step 2 above). Old code keeps running; new columns unused.
2. **Roll out the code** that uses them (step 3).
3. **(Later, separate deploy)** any destructive cleanup — only after the new code has
   been stable ≥7 days. Never combine stages; never deploy code that *requires* a
   not-yet-applied migration.

## Worker deploys (only if `--profile async` is in use)

- `docker compose --profile async up -d --build worker` recreates the worker; arq
  drains in-flight jobs on SIGTERM (job timeout 120s, see `bot/tasks/worker.py`).
- If you rename a job or change its args, register both old and new names for a
  transition window — arq does not handle renames automatically.

## Rollback

```bash
git checkout <previous-good-sha>
docker compose up -d --build
```
Migrations are additive, so reverting code is safe against the newer schema — no DB
rollback needed. If `--profile async` introduced a new Redis key shape, let TTLs
expire or `docker compose exec redis redis-cli FLUSHDB` (rollback only, never a normal deploy).

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `502 Bad Gateway` from Caddy | app not on `CADDY_NETWORK`. Check it matches the network from one-time-wiring step 2; `docker network inspect upword_game_default` must list `pandasolve-api`. |
| `/healthz` returns `404` | rebuild didn't pick up new code, or running legacy `bot.app.app:app`. Check `git log` on server; Dockerfile CMD must be `bot.app.main:app`. |
| `/v1/*` returns `401` for valid users | `SUPABASE_JWT_SECRET` missing/wrong in `.env`. |
| `500`s right after rebuild | a required env var is missing — the app crashes loudly on startup. Add it to `.env`, `docker compose up -d`. |
| TLS cert fails on first hit | DNS must resolve (it does) and `:80` must reach the server for the ACME challenge — owned by `upword_game-caddy-1`. |
| Tasks stuck `pending` | `REDIS_URL` set but no worker. Start `--profile async`, or unset `REDIS_URL` to solve inline. |
| Bot can't reach API | bot resolves `app:8000` on the phototaskbot network; `NETWORK=app` in `bot/constants.py` must match the service name. |
| Bot 404s on `/tasker/api/` | legacy shim removed too early — restore it and ship a bot update. |

## Secrets to set on first deploy

| Secret | Where it comes from |
|---|---|
| `SUPABASE_URL` | Supabase project settings |
| `SUPABASE_KEY` (anon) | Supabase → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | same |
| `SUPABASE_JWT_SECRET` | same → JWT Secret (verifies mobile JWTs) |
| `OPENAI_API_KEY` | OpenAI dashboard |
| `GOOGLE_API_KEY` | Google AI Studio |
| `INTERNAL_AUTH_SECRET` | `openssl rand -hex 32` |
| `TELEGRAM_BOT_TOKEN` | BotFather |
| `REDIS_URL` | `redis://redis:6379` (only with `--profile async`) |
| `APNS_*` / `FCM_SERVICE_ACCOUNT_JSON_BASE64` | Apple Developer / Firebase — see `docs/clients/push-setup.md` |
| `SENTRY_DSN` | Sentry project (optional) |

## Future: CI/CD

Not built yet. When added (`.github/workflows/backend.yml`): lint (ruff) → tests
(pytest) → build image → push → `ssh` deploy (`git pull && docker compose up -d --build`)
or a registry-based pull. Health gate on `GET /healthz`. Until then, deploys are manual
as above.

See also: `docs/clients/push-setup.md` (FCM/APNs) and `CLAUDE.md` (architecture).
