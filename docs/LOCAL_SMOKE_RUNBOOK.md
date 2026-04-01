# Recruit Autopilot Core Local Smoke Runbook

## Purpose
- Bring up the local stack fast
- Validate the admin panel with seeded data
- Confirm the repo is usable for demo, QA, and handoff on the execution machine

## Scope
- In scope:
- Docker boot
- DB seed
- Web login
- Core admin routes
- Seeded company / vacancy / source visibility
- Out of scope:
- auth/security remediation
- real Telegram posting
- AI provider integration
- secrets handling changes

## Prerequisites
- Docker is running
- `.env` exists
- Port `8000` is free for the web panel
- Port `5432` and `6379` are free for Postgres and Redis

## Boot Commands
```bash
cp .env.example .env
docker compose up --build -d
docker compose exec web python -m scripts.seed
python3 scripts/smoke_web.py
```

## Expected Smoke Result
- Script exits with code `0`
- Login page loads on `http://localhost:8000/login`
- Authenticated session reaches `/companies/`
- Seed data is visible:
- `Default Company`
- `Concrete worker`
- `@example_group`
- Protected pages open successfully:
- `/vacancies/`
- `/sources/`
- `/campaigns/`
- `/candidates/`
- `/ai/settings`

## Manual 5-Minute Operator Check
1. Open `http://localhost:8000/login`.
2. Sign in with `admin / admin123`.
3. Confirm company list loads and `Default Company` is present.
4. Open Vacancies and confirm `Concrete worker` exists.
5. Open Sources and confirm `@example_group` exists.
6. Open Campaigns and confirm the create form is reachable.
7. Open AI Settings and confirm the form renders.
8. Open Candidates and confirm the page loads even if candidate list is empty.

## Failure Triage
- Login page does not open:
- check `docker compose ps`
- inspect `docker compose logs web --tail=100`
- Seed failed:
- inspect `docker compose logs web --tail=100`
- confirm Postgres container is healthy
- Smoke script fails after login:
- confirm seed completed
- inspect route response shown by the script
- Worker or bot not relevant to smoke:
- keep the web validation result and treat runtime integrations as a separate lane

## Shutdown
```bash
docker compose down
```
