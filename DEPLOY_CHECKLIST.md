# DEPLOY CHECKLIST — Posting Autopilot

This is the mechanical launch sequence from a blank Hetzner Ubuntu VPS to a live app.

## 1. Provision the server

- Ubuntu `22.04` or `24.04`
- public IPv4
- outbound internet open on `80/443`

## 2. Point DNS before Caddy boot

Create:

- `A posting-autopilot.com -> <VPS_IP>`
- `A app.posting-autopilot.com -> <VPS_IP>`

Verify:

```bash
dig +short posting-autopilot.com
dig +short app.posting-autopilot.com
```

Both must resolve to the new VPS IP before expecting automatic TLS.

## 3. Put the repo on the box

```bash
ssh root@<VPS_IP>
apt-get update -y && apt-get install -y git
git clone <REPO_URL> /opt/posting-autopilot
cd /opt/posting-autopilot
```

## 4. Prepare production env

```bash
cp .env.prod.example .env.prod
nano .env.prod
touch .env.runtime
python3 scripts/validate_prod_env.py .env.prod
```

Required operator-filled values:

- `ADMIN_PASSWORD`
- `FLASK_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `MARKETING_DOMAIN`
- `APP_DOMAIN`
- `PUBLIC_MARKETING_URL`
- `PUBLIC_APP_URL`
- `LETSENCRYPT_EMAIL`
- `RECRUITBOT_TELEGRAM_BOT_TOKEN`
- `RECRUITBOT_AI_PROVIDER`
- `RECRUITBOT_AI_API_KEY`

Explicit operator decisions:

- `TRIAL_DAYS`
- `SIGNUP_INVITE_CODE` blank or invite-only
- `RECRUIT_OPERATOR_NOTIFY_CHAT`
- `RECRUITBOT_TG_API_ID` / `RECRUITBOT_TG_API_HASH`
- `BILLING_ENABLED=0|1`
- `STRIPE_*` if `BILLING_ENABLED=1`
- `SMTP_*` if email digests are wanted

## 5. Deploy

```bash
./deploy-hetzner.sh --smoke
```

Expected behavior:

- Docker installed if missing
- `.env.prod` rejected early if placeholders / broken URLs remain
- compose validated
- `postgres`, `redis`, `web`, `worker`, `scheduler`, `bot`, `listener`, `caddy` started
- migrations executed
- internal smoke passes
- public smoke passes if DNS has propagated

## 6. Hard checks after deploy

Inside the repo:

```bash
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml ps
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml logs --tail=80 web
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml logs --tail=80 bot
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml logs --tail=80 listener
```

Public:

```bash
curl -fsS https://posting-autopilot.com/
curl -fsS https://app.posting-autopilot.com/health
curl -fsS https://app.posting-autopilot.com/login
curl -fsS https://app.posting-autopilot.com/register
```

Expected:

- marketing root returns `200`
- app `/health` returns JSON `ok:true`
- app `/login` returns `200`
- app `/register` returns `200`

## 7. Service-by-service first-boot truth

Postgres:

- healthy
- named volume `ra_pg` exists
- `docker volume inspect posting-autopilot_ra_pg` or compose-scoped equivalent succeeds

Redis:

- healthy
- appendonly enabled
- named volume `ra_redis` exists

Web:

- healthy via `/ready`
- `https://app.posting-autopilot.com/login` renders
- `https://posting-autopilot.com/login` redirects to `app.`

Worker:

- healthy
- no immediate crash loop
- can connect to Redis + DB

Scheduler:

- healthy
- no immediate crash loop
- can connect to Redis + DB

Bot:

- healthy
- `docker compose ... logs bot` shows successful Telegram bot connect

Listener:

- healthy
- if no tenant Telegram sessions exist yet, no-op is acceptable

Caddy:

- healthy
- valid TLS on both domains
- HSTS and CSP headers present

## 8. First real account / onboarding

Operator path:

- `https://app.posting-autopilot.com/login`
- login with `ADMIN_LOGIN` / `ADMIN_PASSWORD`

Customer path:

- `https://app.posting-autopilot.com/register`
- invite code required only if `SIGNUP_INVITE_CODE` is set

Do not run on production unless you explicitly want demo data:

```bash
python -m scripts.seed
python -m scripts.seed_demo
```

## 9. Billing gate

Keep billing off until Stripe is operator-supplied:

- `BILLING_ENABLED=0`

Only flip to `1` after:

- Stripe account exists
- live/test key choice is intentional
- webhook endpoint can receive Stripe events
- all `STRIPE_*` values are filled

## 10. If something fails

Compose validation:

```bash
APP_ENV_FILE=.env.prod APP_RUNTIME_ENV_FILE=.env.runtime docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml config
```

Full status:

```bash
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml ps
```

Targeted logs:

```bash
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml logs --tail=120 web
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml logs --tail=120 bot
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml logs --tail=120 worker
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml logs --tail=120 scheduler
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml logs --tail=120 listener
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml logs --tail=120 caddy
```

## 11. First-boot VPS-only checks that remain blocked locally

- real Postgres boot on empty Docker volume
- Redis health under Docker
- actual Telegram bot connectivity from Linux host
- Telethon session persistence in shared `ra_data`
- Caddy certificate issuance and HTTPS redirect behavior
- public DNS propagation and external smoke
