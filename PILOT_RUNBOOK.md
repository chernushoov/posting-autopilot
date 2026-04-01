# RecruitBot — Pilot Runbook

## Quick Start

```bash
cd ~/Desktop/recruit-autopilot-core
docker compose up -d
docker compose logs bot --tail 5  # should show "Connected as @AutopillotRecruit_bot"
```

Dashboard: http://localhost:8080
Login: operator / HBIKEGMS5nd7GNXP

## Step 1: Create or Verify Vacancy

1. Dashboard → Vacancies
2. Click "+ New" or verify existing vacancy is active
3. Required fields: title, city, language, body (description), screening questions
4. Questions are JSON array of strings in the vacancy's language
5. Click save → vacancy appears in bot's list

## Step 2: Add Telegram Sources (Channels)

1. Dashboard → Sources → add new
2. Enter channel handle (e.g. `@BROOTTO_Jobs`) or group ID
3. **Critical**: Add `@AutopillotRecruit_bot` as admin to the channel first
4. Click "Check" to verify bot access
5. Click "Test" to send a test message

## Step 3: Create Campaign

1. Dashboard → Campaigns → "+ New"
2. Select vacancy, posting interval (minutes), sources
3. Toggle "Run" to start
4. Scheduler checks every 60 seconds; posts at configured interval

## Step 4: Monitor Candidates

1. Dashboard → Candidates
2. Filter by status: new / qualifying / passed / rejected
3. Click candidate to see:
   - Full chat log (all Q&A)
   - AI score (0-100)
   - AI summary (1-2 sentences)
   - Status and vacancy
4. Manually change status if needed (e.g. move to "interviewing")

## Step 5: Verify Scoring

Strong candidate indicators (score 70+):
- Relevant experience mentioned
- Lives near job location
- Has work authorization
- Available soon
- Flexible on shifts

Weak candidate indicators (score <40):
- No relevant experience
- Far from location
- Limited availability
- Restrictions on shifts

Threshold: 40 (configurable in `bot/run_bot.py:PASS_SCORE_THRESHOLD`)

## Identifying Failures

| Symptom | Check | Fix |
|---------|-------|-----|
| Bot not responding | `docker compose logs bot --tail 20` | Restart: `docker compose restart bot` |
| 409 conflict | Another process polling same token | Stop other bot instances |
| AI scoring returns rule-based | `docker compose exec web python -c "from common.runtime_env import get_ai_provider; print(get_ai_provider())"` | Check AI_API_KEY in .env |
| Campaign not posting | `docker compose logs scheduler` | Verify campaign is_running=True, sources are active |
| 403 on channel post | Bot not admin in channel | Add bot as channel admin in Telegram |
| Dashboard 500 error | `docker compose logs web --tail 20` | Check for Python traceback |
| Candidate score=None | AI call failed silently | Check worker logs, API key validity |

## Common Recovery

```bash
# Restart everything
docker compose down && docker compose up -d

# Restart just the bot
docker compose restart bot

# Check all container health
docker compose ps

# View recent logs
docker compose logs --tail 20

# Force rebuild after code change
docker compose up -d --build

# Access database directly
docker compose exec postgres psql -U postgres -d ra
```
