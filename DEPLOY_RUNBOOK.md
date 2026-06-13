# DEPLOY RUNBOOK — Posting Autopilot on Hetzner VPS

This repo is now prepared for a native Linux deploy:

- core stack: `postgres`, `redis`, `web`, `worker`, `scheduler`, `bot`, `listener`
- edge: `caddy`
- canonical app host: `app.posting-autopilot.com`
- canonical marketing host: `posting-autopilot.com`

## Routing decision

- `posting-autopilot.com` stays the marketing entry.
- `app.posting-autopilot.com` is the canonical operator/customer app.
- root-domain app routes like `/login`, `/register`, `/dashboard`, `/pricing` are redirected to `app.` by Caddy.
- `https://app.posting-autopilot.com/` redirects to `/login`.

## Files that matter

- prod env template: `.env.prod.example`
- compose base: `docker-compose.yml`
- prod overlay: `docker-compose.prod.yml`
- edge proxy: `Caddyfile`
- deploy script: `deploy-hetzner.sh`
- env preflight: `scripts/validate_prod_env.py`
- deploy day checklist: `DEPLOY_CHECKLIST.md`

## What the operator must provide

Required before `web/bot` can be called production-ready:

- `ADMIN_PASSWORD`
- `FLASK_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `PUBLIC_MARKETING_URL`
- `PUBLIC_APP_URL`
- `MARKETING_DOMAIN`
- `APP_DOMAIN`
- `RECRUITBOT_TELEGRAM_BOT_TOKEN`
- `RECRUITBOT_AI_API_KEY` and provider choice

Optional / explicitly gated:

- `SIGNUP_INVITE_CODE`
- `TRIAL_DAYS`
- `RECRUIT_OPERATOR_NOTIFY_CHAT`
- `RECRUITBOT_TG_API_ID` / `RECRUITBOT_TG_API_HASH`
- `FB_APP_ID` / `FB_APP_SECRET`
- `STRIPE_*` only when `BILLING_ENABLED=1`
- `SMTP_*` for email digests / hot-lead email

## DNS records

Add these on deploy day:

- `A  posting-autopilot.com        -> <VPS_IP>`
- `A  app.posting-autopilot.com    -> <VPS_IP>`

Optional:

- `CNAME www.posting-autopilot.com -> posting-autopilot.com`

## Recommended first boot

Inside the repo on the VPS:

```bash
cp .env.prod.example .env.prod
nano .env.prod
touch .env.runtime
./deploy-hetzner.sh --smoke
```

What the script does:

1. installs Docker + compose plugin if missing
2. validates `.env.prod` with `scripts/validate_prod_env.py`
3. validates compose with the supplied env file
4. builds the images
5. starts `postgres` + `redis` first
6. runs `python -m scripts.migrate`
7. starts `web + worker + scheduler + bot + listener + caddy`
8. waits for all 8 services to become healthy
9. runs internal smoke on `/health`, `/login`, `/register`
10. runs public smoke too if `PUBLIC_APP_URL` already resolves

## Health truth

- `web` healthcheck calls `/ready`, not just `/health`
- `/ready` verifies both Postgres and Redis
- `worker`, `scheduler`, `bot`, `listener` all have explicit healthchecks
- `bot` healthcheck fails if the bot token is malformed
- prod env validation fails closed when critical values are missing

## Billing gate

- default production template sets `BILLING_ENABLED=0`
- this keeps the app honest while Stripe keys are still operator-blocked
- turning billing on requires:
  - `BILLING_ENABLED=1`
  - `STRIPE_SECRET_KEY`
  - `STRIPE_PUBLISHABLE_KEY`
  - `STRIPE_WEBHOOK_SECRET`
  - `STRIPE_PRICE_STARTER`
  - `STRIPE_PRICE_PRO`
  - `STRIPE_PRICE_AGENCY`

## Data layer / first account

- migrations/bootstrap: `docker compose exec -T web python -m scripts.migrate`
- no demo seed on production by default
- operator/admin login uses `ADMIN_LOGIN` + `ADMIN_PASSWORD`
- first real customer account is created via `/register`
- invite-only remains controlled by `SIGNUP_INVITE_CODE`

## Local proof completed before VPS

- `python3 -m compileall app bot common worker scripts`
- `docker compose --env-file .env.prod.example -f docker-compose.yml -f docker-compose.prod.yml config`
- temp SQLite smoke:
  - `scripts/smoke_web.py`
  - `scripts/smoke_signup_flow.py`
- phase regressions:
  - `scripts/test_phase2.py`
  - `scripts/test_phase3.py`

## Bottom line

Once the VPS exists and `.env.prod` is filled, the actual go-live command is:

```bash
./deploy-hetzner.sh --smoke
```
