# Recruit Autopilot — Demo Script for Observer

Date: 2026-05-08
Stack: local docker on operator's Mac (`localhost:8080`) ↔ Cloudflare tunnel `basement-inner-extra-tyler.trycloudflare.com`
Bot: `@AutopillotRecruit_bot`
Estimated runtime: **8–12 minutes** with Q&A

The observer should walk away seeing three things working end-to-end:
1. We post job ads to multiple Telegram and Facebook channels from one place.
2. Candidates who reply land in our bot, get screened by AI, get scored.
3. The operator gets a Telegram notification only for the hot leads, with the candidate's phone + WhatsApp link ready to call.

That's the differentiator vs. fbzipper / Postify / FaceBoost — they only post. We post and qualify.

---

## Pre-flight (do once before the observer arrives, ~2 min)

```bash
# All 6 containers up, last fired post in TG visible in @haifa_rabota
docker ps --filter name=recruit-autopilot-core
docker exec recruit-autopilot-core-postgres-1 psql -U postgres -d ra -c \
  "SELECT id, title FROM vacancies WHERE company_id=5 AND is_active=true ORDER BY id;"
```

Expected: 4 active FloorDSGN vacancies (id 5, 6, 11, 12), all with `bot_qualifying_questions` and `bot_hot_criteria` set.

If the live FB session is captured (operator ran `scripts/fb_capture_session.py`), pre-run a smoke check:
```bash
curl -s -b /tmp/posting-e2e/admin_cookies.txt \
  -H "X-CSRF-Token: ..." \
  -X POST http://localhost:8080/api/fb/posting-runs/3/smoke
```
Should return `ok: true` with a screenshot path.

---

## Slide 1 · Operator dashboard (1 min)

Open `http://localhost:8080/dashboard` (or the Cloudflare tunnel URL).

Walk through the Operator Copilot strip:

> "This is the daily-status panel. It tells the operator at a glance what's
> running, what's stale, what needs attention. Right now Telegram is connected,
> 1 of 1 channels marked ready, 0 of 4 campaigns running because we paused
> them after the last live post earlier today."

Point at the bottom panel:
- **Active vacancies: 4**
- **Telegram channels ready: 1/1**
- **Telegram account auth: yes**
- **Facebook channels: 1**
- **Worker responses: live**
- **Last post attempt status: posted** (TG @haifa_rabota at 10:35)

This is the "is everything alive" view. We deliberately keep it minimal.

---

## Slide 2 · The 4 vacancies (1 min)

Open `/vacancies/`.

> "FloorDSGN has 4 active vacancies. Each one carries the ad copy AND the bot's
> screening setup: the questions the bot asks the candidate, the criteria for
> hot vs cold, and a deep link that takes the candidate from the Facebook /
> Telegram post directly into the bot screening for that specific vacancy."

Click into vacancy 6 (Бетонные полы):
- show `final_post_body` — what gets posted
- show `bot_qualifying_questions` — 4 questions in Russian
- show `bot_hot_criteria` / `bot_cold_criteria` — what the AI looks for

> "When this vacancy is published in Telegram or Facebook, the post links
> candidates to `t.me/AutopillotRecruit_bot?start=apply_6` — the bot then
> knows which vacancy the candidate is applying to and asks the right questions."

---

## Slide 3 · Live Telegram post (1 min)

Open `https://t.me/haifa_rabota` in any browser (no FB needed).

> "This is the Хайфа и Крайот Работа Telegram group, 1.6k members.
> Floor.DSGN's vacancy 6 was posted there at 10:35 today, fully automated.
> The post links to our bot for screening."

Scroll to the post → screenshot it for the demo packet.

If observer asks "how many groups can you post to": pull up `/connect/telegram`:

> "The operator's Telegram account is synced. We see 78 groups they're already
> a member of. Operator picks which to add as destinations, we run a one-time
> safety check, then they're available for any campaign."

---

## Slide 4 · Facebook auto-poster (2 min)

Open `/facebook/posting-runs/3/queue`.

> "Facebook killed group posting via their API in 2024. Every legitimate
> auto-poster in Israel uses browser automation — fbzipper, Postify, FaceBoost
> all do this. We do too. The architecture: operator captures their Facebook
> session once on their Mac, our worker container loads that session into a
> headless Chromium, opens each group, types the Hebrew variant, clicks Post.
> Random delays 5–10 minutes between groups for anti-ban."

Show the queue page: 5 FB groups, 1 current + 4 pending, the approved Hebrew
variant ready to fire.

> "If the operator wants the system to fire the whole queue, they hit one
> button or one curl. The worker handles the staggering and screenshots
> before/after for evidence."

If session is captured, run the smoke endpoint (no posting) to show the bot
can see the operator's FB feed:
```
POST /api/fb/posting-runs/3/smoke
→ ok: true, screenshot: data/fb_screenshots/smoke_floordsgn_*.png
```

If session is not captured, show the capture script and explain the 60-second
one-time setup:
```
python scripts/fb_capture_session.py
```

---

## Slide 5 · The screening — THIS IS THE WOW MOMENT (3 min)

Open Telegram on a phone (operator's), open `@AutopillotRecruit_bot`. Pretend
to be a candidate.

**OR**, if the observer doesn't need to see the bot UI specifically, run the
end-to-end simulation, which is faster and deterministic:

```bash
docker exec recruit-autopilot-core-bot-1 sh -c \
  "cd /app && PYTHONPATH=/app python scripts/simulate_hot_lead.py 6"
```

Within 2 seconds:

```
=== Demo candidate created ===
  candidate_id : 12
  vacancy      : Floor.DSGN — Бетонные полы / Установка и затирка
  score        : 95
  classification: hot
  scoring source: openai
  summary      : Кандидат имеет 5 лет опыта работы с бетоном, готов работать
                 по всей стране и имеет все необходимые документы для работы
                 в Израиле. Он также готов начать работу на следующей неделе.

→ Firing send_hot_lead_notification
[bot] hot lead notification sent → 8175553706
```

The operator's Telegram (their personal chat with `@AutopillotRecruit_bot`)
gets:

```
🔥 HOT LEAD!

📋 Listing: Floor.DSGN — Бетонные полы...
🏢 Company: FloorDSGN
👤 Name: Demo Candidate (E2E simulation)
📞 Phone: +972-50-555-0001
📊 Score: 95
📝 Summary: Кандидат имеет 5 лет опыта работы с бетоном...
💬 Telegram: @demo_hot_candidate
📲 WhatsApp: https://wa.me/972505550001
```

> "This is what the operator sees in their pocket within seconds of a
> candidate finishing the screening conversation in the bot. They click the
> WhatsApp link and they're on the candidate's WhatsApp ready to call. They
> don't read low-scoring candidates — those are filtered out and stored for
> the operator to review later, but no notification is fired."

If the observer asks "how does the AI score?", show `common/ai.py`:
- OpenAI gpt-4o-mini under the hood
- System prompt: "score 0-100 based on relevance, location fit, availability, work authorization, willingness"
- Returns score + 1-2 sentence summary
- Falls back to rule-based heuristics if API key fails

---

## Slide 6 · The aggregate view (1 min)

Open `/candidates/`.

> "All candidates land here, sortable by status. The operator works the hot
> leads first. The cold ones stay archived but not deleted — sometimes the
> right person applies for the wrong vacancy and we want that record."

Show the latest candidates: passed (green), rejected (red), interviewing
(yellow). Filter by status='passed' to focus on hot.

---

## Slide 7 · What's next (closing, 1 min)

> "Today we covered the 80% of the workflow that's in operator's hands.
> What's not in the demo:
> - Hebrew bot screening (already supported, RU shown today since FloorDSGN
>   is RU primary). We can switch any vacancy to HE per ad with one config.
> - Multi-account Facebook rotation (planned).
> - Custom hot/cold criteria per industry (currently free-text in Russian,
>   will become a structured chip selector).
> - Email digest of all leads at end of day (the code path exists, SMTP not
>   wired in this demo)."

---

## Demo cleanup (after the observer leaves)

```bash
# Remove demo candidates
docker exec recruit-autopilot-core-postgres-1 psql -U postgres -d ra -c \
  "DELETE FROM candidates WHERE tg_user_id LIKE 'DEMO_HOT_%' OR full_name = 'Demo Candidate (E2E simulation)';"

# Restart bot to clear any cached state
docker compose -f ~/Desktop/recruit-autopilot-core/docker-compose.yml restart bot
```

---

## Demo failure modes — what to do if something breaks live

| Symptom | What to say | What to do |
| --- | --- | --- |
| `simulate_hot_lead.py` ImportError | "Container hasn't picked up the latest code, one moment." | `docker compose restart bot` and retry — typically resolves in 5s. |
| Telegram notification doesn't arrive | "Let me check the bot's notification target." | Verify `RECRUIT_OPERATOR_NOTIFY_CHAT=<tg_user_id>` is set in `.env` and bot container has it: `docker exec ... bot-1 env \| grep RECRUIT_OPERATOR`. |
| FB queue UI shows "Loading…" forever | "Let me check the API behind it." | Open DevTools network tab, look for `/api/fb/posting-runs/<id>` — should be 200 with queue data. |
| FB smoke endpoint returns `session_missing` | "Operator hasn't captured the FB session yet — that's a one-minute setup." | Walk them through `scripts/fb_capture_session.py` — show the 4 commands, don't actually capture during demo. |
| TG @haifa_rabota post not visible | "Let me show the database evidence instead." | `psql -c "SELECT * FROM posting_attempts WHERE result_status='posted';"` shows the message_id and timestamp. |

---

## Honest caveats to share if asked

- FB account ban risk is real with browser automation. Recommend a burner FB
  account for posting volume above 10/day per account.
- Cookie sessions expire 7-30 days; operator re-runs capture script to refresh.
- FB UI changes break selectors occasionally; we maintain a fallback selector
  chain (Hebrew + English aria-labels) but ongoing maintenance is part of
  what the operator pays for.
- Telegram has an internal rate limiter at 30 messages/sec across the whole
  bot. Not a concern at our volumes.
- AI scoring requires an OpenAI API key. Rule-based fallback works without it
  but is less accurate. We use ~$0.02-0.05 per candidate at gpt-4o-mini rates.
