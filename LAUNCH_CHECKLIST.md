# RecruitBot — Launch Checklist

## Preflight

- [ ] Exact source repo/branch for `posting-autopilot-next` is pinned and matches the reviewed code
- [ ] All 6 containers running: `docker compose ps` (postgres, redis, web, worker, scheduler, bot)
- [ ] Bot log shows: `[bot] Connected as @AutopillotRecruit_bot`
- [ ] No 409 conflict in bot logs
- [ ] `bash scripts/runtime_check_with_env.sh --json`
- [ ] `bash scripts/compose_with_runtime.sh exec -T web python scripts/launch_guardrail_check.py`
- [ ] `bash scripts/live_deploy_smoke.sh https://posting-autopilot-next.vercel.app`
- [ ] `python3 scripts/multilingual_pilot_check.py`
- [ ] `python3 scripts/final_launch_gate.py`
- [ ] `bash scripts/run_launch_release_pack.sh`

## Environment

- [ ] `FLASK_SECRET_KEY` is NOT `change-me`
- [ ] `ADMIN_PASSWORD` is NOT `admin123`
- [ ] `RECRUITBOT_TELEGRAM_BOT_TOKEN` is set and valid format
- [ ] `RECRUITBOT_AI_PROVIDER=openai`
- [ ] `RECRUITBOT_AI_API_KEY` is set (starts with `sk-`)
- [ ] Verify: `docker compose exec web python -c "from common.runtime_env import *; print(get_ai_provider(), bool(get_ai_api_key()), bool(get_recruitbot_token()))"`
- [ ] Expected output: `openai True True`

## Telegram Bot

- [ ] Owner has sent `/start` to `@AutopillotRecruit_bot`
- [ ] Bot responds with language selection
- [ ] Vacancy list appears after language selection
- [ ] Bot responds to screening answers
- [ ] Pass/fail result delivered after all questions

## Dashboard / Operator UI

- [ ] Login works with the currently configured `ADMIN_LOGIN` / `ADMIN_PASSWORD`
- [ ] `SMOKE_BASE_URL=http://localhost:8080 python3 scripts/smoke_web.py`
- [ ] Old/default credentials rejected after hardening
- [ ] Company switched to TopStaff Israel
- [ ] Vacancies visible (Warehouse Worker, Cleaning)
- [ ] Candidates visible with scores
- [ ] Sources listed (5 Telegram channels)
- [ ] Campaigns listed (2 campaigns)
- [ ] Campaign form rejects unsafe config
- [ ] Source test requires explicit confirmation

## AI Scoring

- [ ] Strong candidate scores 70+
- [ ] Weak candidate scores below 40
- [ ] Hebrew candidate scored correctly
- [ ] Verify: `docker compose exec web python -c "from common.ai import score_candidate; r=score_candidate('Test',['Q?'],['Yes'],'en'); print(r['provider'])"`
- [ ] Expected: `openai`

## Channel Posting

- [ ] Bot added as admin to target Telegram channels
- [ ] Test post via Sources page → "Test" button
- [ ] Campaign started (toggle "Run" on campaign)
- [ ] Verify post appears in channel within interval

## Security

- [ ] Flask secret key is random hex (not default)
- [ ] Admin password is strong (not `admin123`)
- [ ] No placeholder tokens in `.env`
- [ ] `.env` not committed to git (check `.gitignore`)
- [ ] Bot token is dedicated (not shared with other bots)

## Rollback

If critical failure after launch:
1. `docker compose stop bot` — stops Telegram polling
2. `docker compose stop scheduler` — stops campaign posting
3. Candidates and data preserved in postgres
4. `docker compose up -d` — full restart
5. `docker compose logs bot --tail 50` — diagnose

## Canonical Final Check

Run:

```bash
bash scripts/run_prelaunch_front.sh
python3 scripts/final_launch_gate.py
```

If this is not green, do not call the app launch-ready.

Current launch gate reference:

- [POSTING_AUTOPILOT_LAUNCH_GATE_STATUS_2026-03-30.md](./POSTING_AUTOPILOT_LAUNCH_GATE_STATUS_2026-03-30.md)
