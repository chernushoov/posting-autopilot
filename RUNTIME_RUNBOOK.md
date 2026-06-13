# Recruit Autopilot Runtime Runbook

## Goal
Bring `web`, `worker`, `scheduler`, and `bot` to a clean running state without colliding with the main MoltBot/OpenClaw Telegram bot.

## Source of truth
- Runtime health: `bash scripts/runtime_check_with_env.sh`
- Bootstrap readiness: `python3 scripts/bootstrap_check.py`
- Runtime env status: `python3 scripts/runtime_env_status.py --json`
- Live services: `bash scripts/compose_with_runtime.sh ps -a`
- Bot logs: `bash scripts/compose_with_runtime.sh logs --tail=80 bot`

## Safe startup order
1. `python3 scripts/bootstrap_check.py`
2. If needed, store secrets with `bash scripts/bootstrap_runtime_secrets.sh --help`
3. `bash scripts/compose_with_runtime.sh up -d postgres redis web`
4. `bash scripts/compose_with_runtime.sh up -d worker scheduler`
5. `bash scripts/runtime_check_with_env.sh`
6. Only after token is valid: `bash scripts/compose_with_runtime.sh up -d bot`

## Local web-only fallback (no Docker)

Use this only when Docker/Colima is blocked and you still need operator access to
the web panel. This is not full production/runtime truth: it runs `web` only,
without `postgres`, `redis`, `worker`, `scheduler`, or `bot`.

```bash
cd ~/Desktop/recruit-autopilot-core
bash scripts/run_local_web_sqlite.sh
```

Default local URL:

```bash
http://127.0.0.1:8080
```

Notes:
- Sources `.env` and `.env.runtime`
- Overrides `DATABASE_URL` to `sqlite:///ra.db` unless `LOCAL_DATABASE_URL` is set
- Reuses real `ADMIN_LOGIN` / `ADMIN_PASSWORD` from env files
- Good for web/auth/vacancy/source/campaign UI validation, not for Telegram posting truth

## Required secret rules
- Use `RECRUITBOT_TELEGRAM_BOT_TOKEN` for this project.
- Do not reuse the main MoltBot/OpenClaw Telegram token.
- `TELEGRAM_BOT_TOKEN` is fallback only for backward compatibility.
- Runtime secret precedence is: exported env, `.env.runtime`, macOS keychain, `.env`.
- If AI is still `stub`, bot can run, but AI behavior remains placeholder.

## Common failure cases

### Bot exited immediately
Check:
```bash
bash scripts/runtime_check_with_env.sh
bash scripts/compose_with_runtime.sh logs --tail=80 bot
```

Most likely cause:
- placeholder or invalid Telegram token

Fix:
- set a real `RECRUITBOT_TELEGRAM_BOT_TOKEN` in `.env.runtime`, exported env, or keychain
- restart with `bash scripts/compose_with_runtime.sh up -d bot`

### Worker or scheduler not running
Check:
```bash
bash scripts/compose_with_runtime.sh logs --tail=80 worker
bash scripts/compose_with_runtime.sh logs --tail=80 scheduler
```

Most likely causes:
- Redis or Postgres unavailable
- `.env` missing DB/Redis URLs

### Web is up but system is not launch-ready
This usually means:
- `web` is reachable
- async layer is not running
- Telegram bot is not running

Use:
```bash
bash scripts/runtime_check_with_env.sh --json
```

## Dashboard expectation
When the project is healthy, dashboard should show:
- `6/6 containers running`
- no critical diagnostics issues
- no `bot_log_hint`

If dashboard still shows old status:
- refresh local dashboard
- ensure sync-agent is pushing `mirror:200`
- check `runtime_check.py --json` locally first

## Database migration policy (P1 follow-up)

There is no Alembic in this repo. Schema is created/upgraded by
`app/schema.py::bootstrap_schema()` which is called from every Python
service entrypoint (web, worker, scheduler). Column changes are manual
via `init_db.py` or by editing `app/models.py` and letting
`bootstrap_schema()` add new tables on next boot.

Rules until Alembic is adopted:
- **Never alter or drop columns** post-pilot without first taking a
  snapshot: `docker compose exec postgres pg_dump -U postgres ra > backups/ra_$(date +%Y%m%d_%H%M).sql`
- **Adding a table or nullable column** is safe (bootstrap handles it).
- **Renaming** a column requires: dump → manual SQL → redeploy.
- P1 follow-up: add `alembic` to `requirements.txt`, run `alembic init`,
  baseline against current production schema, and switch
  `bootstrap_schema()` to `alembic upgrade head`.
