# DEPLOY PREP REPORT — 2026-06-10

## Ready now

- production-safe `docker-compose.yml`
- hardened `docker-compose.prod.yml`
- dual-host `Caddyfile`
- parseable `.env.prod.example`
- `deploy-hetzner.sh`
- `scripts/validate_prod_env.py`
- updated `deploy.sh` wrapper
- `DEPLOY_RUNBOOK.md`
- `DEPLOY_CHECKLIST.md`
- production env fail-closed guard
- `/ready` endpoint for app readiness
- internal healthchecks for `web/worker/scheduler/bot/listener`
- dynamic `TRIAL_DAYS`
- explicit `BILLING_ENABLED` gate
- landing/app sign-in links aligned to canonical app URL

## Verified locally

- `python3 -m compileall app bot common worker scripts`
- `docker compose --env-file .env.prod.example -f docker-compose.yml -f docker-compose.prod.yml config`
- `python -m scripts.migrate` on fresh temp SQLite DB
- `python -m scripts.seed_demo` on temp SQLite DB
- `scripts/smoke_web.py` against local Flask fallback
- `scripts/smoke_signup_flow.py` proving:
  - `/register`
  - company + user creation
  - `/vacancies/new`
  - `/sources/new`
  - dashboard auto-creates first campaign
  - `/campaigns/`
- `scripts/test_phase2.py`
- `scripts/test_phase3.py`

## Operator-blocked

- real VPS IP
- DNS records
- production secrets
- Telegram bot token
- AI key
- Stripe keys if billing should go live now

## VPS-first-boot only

- Docker daemon/service health on Linux
- Postgres volume creation
- Redis persistence volume creation
- Telegram bot real network connect from VPS
- Telethon session persistence on shared data volume
- Caddy certificate issuance
- external `https://app.posting-autopilot.com/*` smoke

## Main changes in product behavior

- production startup now fails closed on missing critical config instead of silently degrading
- deploy day now fails before Docker boot if `.env.prod` still contains placeholders or broken URL/domain wiring
- billing is now an explicit gate via `BILLING_ENABLED`, not an accidental half-configured path
- app is routed canonically to `app.posting-autopilot.com`
- marketing root remains `posting-autopilot.com`
- root-domain app routes redirect to `app.`
- web production command uses `gunicorn`, not Flask dev server

## Bottom line

On a fresh Hetzner VPS, once `.env.prod` is filled and DNS is pointed, deploy is:

```bash
./deploy-hetzner.sh --smoke
```

Expected time: about `15–25 minutes` after DNS is already set and the secrets are ready.
