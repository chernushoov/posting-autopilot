# Posting Autopilot — Project Brief

## What This Is

A **Telegram-first recruitment automation platform** for Israeli staffing agencies. Agencies post job vacancies to Telegram groups/communities and Facebook groups, screen candidates via AI-powered Telegram bot, and manage the hiring pipeline through a web dashboard.

**Live URL:** https://wet-albuquerque-plastics-halloween.trycloudflare.com (Cloudflare tunnel → localhost:8080)
**Login:** `operator` / `<REDACTED — see ADMIN_PASSWORD in .env (not in repo)>`

---

## Tech Stack

- **Backend:** Python 3.11, Flask, SQLAlchemy ORM
- **Database:** PostgreSQL 16
- **Queue:** Redis + RQ (job queue) + APScheduler
- **Telegram Bot:** aiogram 3.4 (candidate screening)
- **Telegram Client:** Telethon (user account — posting to communities)
- **AI:** OpenAI gpt-4o-mini (candidate scoring) + rule-based fallback
- **Deploy:** Docker Compose (6 services: web, bot, worker, scheduler, postgres, redis)
- **Design:** Apple-style white premium CSS, 3 languages (HE/RU/EN), RTL support

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Web (Flask) │     │  Bot (aiogram)│     │ Worker (RQ)  │
│  port 8080   │     │  Telegram Bot │     │ Async tasks  │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────┬───────┴────────────────────┘
                    │
              ┌─────▼──────┐     ┌───────────┐
              │ PostgreSQL  │     │   Redis    │
              │  port 5432  │     │  (broker)  │
              └────────────┘     └───────────┘
```

**Docker Compose services:**
- `web` — Flask HTTP server (dashboard UI + API)
- `bot` — aiogram Telegram bot (candidate screening via long-polling)
- `worker` — RQ worker (posting tasks, digests)
- `scheduler` — APScheduler (campaign ticks every N minutes)
- `postgres` — Database
- `redis` — Task queue broker

---

## Database Models (app/models.py)

| Entity | Purpose |
|--------|---------|
| **Company** | Multi-tenant: agency profile, AI config (tone, prompts, templates) |
| **Vacancy** | Job posting: title, body, city, salary, schedule, posting asset |
| **Source** | Posting destination: Telegram group/channel or Facebook group |
| **Campaign** | Scheduled posting: interval, active hours, weekdays, max posts/day |
| **CampaignSource** | Many-to-many: campaign ↔ destinations |
| **Candidate** | Applicant: tg_user_id, status, score, summary, chat_log_json |
| **PostingAttempt** | Audit log: every posting action with status and result |
| **FacebookGroup** | FB group directory: category, city, activity rating |
| **FacebookPostVariant** | AI-generated post variants: tone, length, headline, CTA |
| **FacebookPostingRun** | Batch posting session: operator workflow |
| **FacebookPostingQueueItem** | Per-group manual posting action: copy→paste→mark done |
| **FacebookPostingResult** | Outcome: responses, CVs, interviews, hires |
| **Prospect** | B2B lead (scraped from Google Maps) |
| **OutreachAttempt** | Cold email log |

---

## Core User Flow

```
1. Landing page → Login → Dashboard (6-step guided setup)
2. Create Company profile
3. Connect Telegram (API ID + Hash + Phone → verify → sync groups)
4. Connect Facebook (add group name + URL → assisted manual posting)
5. Create Vacancy (title, city, salary, schedule, posting asset text)
6. Create Campaign (select vacancy + destinations + schedule)
7. Run Campaign → Telegram auto-posts, Facebook manual queue
8. Bot screens candidates in HE/RU/EN → AI scores → recruiter sees shortlist
9. Analytics dashboard shows funnel, language breakdown, performance
```

---

## File Structure

```
recruit-autopilot-core/
├── app/
│   ├── factory.py          — Flask app creation, i18n, context processors
│   ├── models.py           — All SQLAlchemy models (461 lines)
│   ├── schema.py           — Auto-migration (ALTER TABLE for new columns)
│   ├── auth.py             — Login, session, require_company decorators
│   ├── config.py           — Environment config
│   ├── db.py               — Database session
│   ├── tenant.py           — Multi-tenant scoping
│   ├── static/app.css      — White premium design system (Apple-style)
│   ├── templates/          — 23 Jinja2 templates
│   │   ├── _layout.html    — Base layout: topbar, nav, lang switcher, RTL
│   │   ├── landing.html    — Public landing page (standalone, i18n)
│   │   ├── login.html      — Login form (standalone, i18n, RTL)
│   │   ├── dashboard.html  — 6-step guided setup with progress bar
│   │   ├── connect_telegram.html — Telegram Client auth + sync groups
│   │   ├── connect_facebook.html — Facebook group add + assisted mode
│   │   ├── vacancies.html / vacancy_new.html
│   │   ├── sources.html    — Destinations management
│   │   ├── campaigns.html / campaign_new.html
│   │   ├── candidates.html / candidate_view.html
│   │   ├── analytics.html  — Funnel, language, daily charts
│   │   ├── pricing.html    — 3 tiers (₪299/₪899/₪1999)
│   │   ├── companies.html / company_new.html
│   │   ├── ai_settings.html / ai_test_result.html
│   │   ├── prospecting.html — Google Maps scraping + cold email
│   │   └── fb_*.html       — Facebook Safe Workflow (3 pages)
│   └── routes/
│       ├── auth_routes.py   — Landing, login, dashboard, connect TG/FB
│       ├── companies.py     — Company CRUD + enable/disable
│       ├── vacancies.py     — Vacancy CRUD + posting asset builder
│       ├── sources.py       — Destination CRUD + check + test
│       ├── campaigns.py     — Campaign CRUD + run + posting log
│       ├── candidates.py    — Candidate list + view + status change
│       ├── analytics.py     — Dashboard with funnel + language stats
│       ├── pricing.py       — Pricing page with 3-language plan data
│       ├── ai_settings.py   — AI config + test
│       ├── prospecting.py   — Google Maps scraping + email outreach
│       ├── fb_ui.py         — Facebook workflow HTML pages
│       └── fb_safe_workflow.py — Facebook workflow JSON API
├── bot/
│   ├── run_bot.py           — Telegram bot: screening flow (548 lines)
│   └── tg.py                — Telegram API wrapper
├── common/
│   ├── i18n.py              — Translations: 100+ UI keys × 3 languages
│   ├── ai.py                — OpenAI scoring + rule-based fallback
│   ├── tg_client.py         — Telethon: auth, sync dialogs, user API
│   └── fb_safe_workflow.py  — Facebook post AI generation
├── worker/
│   ├── tasks.py             — Posting tasks: campaign_tick, check_source
│   ├── run_scheduler.py     — APScheduler loop
│   ├── run_worker.py        — RQ worker entry
│   └── queue.py             — Redis queue helpers
├── growth/
│   ├── leads-israeli-agencies.json — 50 leads (3 tiers)
│   └── outreach-templates.json     — Cold email/TG/LinkedIn templates (HE+EN)
├── scripts/                 — 56 operational scripts
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env / .env.runtime      — Secrets (bot token, AI key, admin creds)
```

---

## i18n System (common/i18n.py)

- **150+ translation keys** across `MESSAGES` (bot) and `UI` (dashboard)
- **3 languages:** Hebrew (he), Russian (ru), English (en)
- **Default:** Hebrew (Israeli market)
- **RTL:** Full Hebrew RTL support in CSS
- **Language switcher:** On every page (EN/RU/HE pills)
- **Bot auto-detection:** Maps Telegram language_code to our languages

---

## Telegram Integration (TWO systems)

### 1. Bot API (aiogram) — Candidate Screening
- Bot: `@AutopillotRecruit_bot`
- Candidates send `/start` → language selection → vacancy picker → screening questions → AI scoring
- Pass threshold: score ≥ 40
- Chat log saved in JSON per candidate

### 2. Client API (Telethon) — Group Posting
- User authenticates with API ID + Hash + Phone + Code
- Syncs all groups/channels the account is member of (up to 300)
- User selects which communities to post to
- Posts as the user account (not as bot) — works in any public group

---

## Facebook Integration (Assisted Manual)

Facebook doesn't allow automated group posting. Our flow:
1. AI generates Hebrew/Russian post variants (tone, length, CTA)
2. Operator opens posting queue
3. For each group: open → copy text → paste → mark as posted
4. System tracks status per group: posted/skipped/failed
5. Result tracking: responses, CVs, interviews, hires

---

## Pricing (app/routes/pricing.py)

| Plan | Price | Features |
|------|-------|----------|
| Solo Recruiter | ₪299/mo | 1 vacancy, 10 channels, AI screening |
| Agency Team | ₪899/mo | 5 vacancies, 50 channels, campaign scheduler |
| Agency Pro | ₪1,999/mo | Unlimited, API, Google Maps prospecting, white-label |

---

## Current Status

### Working:
- ✅ Dashboard with guided 6-step setup
- ✅ Company management (multi-tenant)
- ✅ Vacancy CRUD with posting asset builder
- ✅ Telegram Client auth + group sync (Telethon)
- ✅ Facebook assisted manual posting queue
- ✅ Campaign scheduling (interval, hours, weekdays, daily cap)
- ✅ AI candidate screening (3 languages, OpenAI + fallback)
- ✅ Analytics (funnel, language breakdown, daily chart)
- ✅ Prospecting (Google Maps scrape + cold email)
- ✅ i18n (HE/RU/EN) with RTL
- ✅ Mobile hamburger menu
- ✅ White premium design (Apple-style)
- ✅ Docker Compose orchestration (6 services)

### Not Yet Built:
- ❌ Self-service signup (currently single admin login)
- ❌ Stripe/payment integration
- ❌ Multi-user per company (roles/permissions)
- ❌ Email notifications on new candidates
- ❌ WhatsApp integration
- ❌ Candidate phone number collection in screening
- ❌ Candidate CSV export
- ❌ Terms of service / privacy policy
- ❌ CSRF protection

---

## Target Market

**Israeli staffing agencies** placing blue-collar workers (construction, cleaning, warehouse, hospitality). Market characteristics:
- Telegram is #1 channel for Russian-speaking worker recruitment
- Facebook groups are #2 for both Russian and Hebrew communities
- Hebrew + Russian + English trilingual requirement
- WhatsApp dominant for employer-worker communication
- Typical agency: 5-30 people, 10-50 active vacancies, posts to 20-100 groups

---

## Growth Assets (growth/)

- **50 Israeli agency leads** segmented into 3 tiers
- **Cold outreach templates** in Hebrew + English (email, Telegram DM, LinkedIn)
- **5-step outreach sequence** (day 1→3→5→8→12)
- **Competitor analysis:** Breezy HR, Workable, Manatal, Zoho Recruit, HireVue

---

## Key Commands

```bash
# Start everything
bash scripts/compose_with_runtime.sh up -d

# Rebuild web after code changes
bash scripts/compose_with_runtime.sh up -d --build web

# View logs
bash scripts/compose_with_runtime.sh logs --tail=80 web bot worker

# Seed demo data
bash scripts/compose_with_runtime.sh exec web python -m scripts.seed_demo

# Runtime check
python3 scripts/runtime_check.py
```

---

## Environment Variables (.env.runtime)

```
DATABASE_URL=postgresql://ra:ra@postgres:5432/ra
REDIS_URL=redis://redis:6379/0
ADMIN_LOGIN=operator
ADMIN_PASSWORD=<REDACTED — see ADMIN_PASSWORD in .env (not in repo)>
FLASK_SECRET_KEY=<random>
RECRUITBOT_TELEGRAM_BOT_TOKEN=<bot token for @AutopillotRecruit_bot>
RECRUITBOT_AI_PROVIDER=openai
RECRUITBOT_AI_API_KEY=<OpenAI API key>
```

---

## What We Need Next (Priority Order)

1. **Telegram posting through synced groups** — post vacancy assets via Telethon Client API
2. **Phone number collection** in bot screening flow
3. **WhatsApp click-to-chat link** in posting assets
4. **Self-service signup** (email + password registration)
5. **Stripe billing** for the 3 pricing tiers
6. **Email notifications** when candidate passes screening
7. **Candidate CSV export**
8. **Demo video** (2 min screen capture)
9. **Hebrew landing page** content polish
10. **First pilot** with 3-5 Israeli agencies
