# Pilot smoke checklist — claude/review-projects-5s4tA

Date: 2026-05-08
Goal: validate the 9 CLAUDE_FIX_ALL blocks land cleanly before tomorrow's
trial launch.

## What this branch changes

| Block | Title | State on `main` | State on this branch |
| --- | --- | --- | --- |
| 1 | Unified auth | two logins (`/login` admin only, `/user-login` self-service); pricing → `/login` only | one `/login` accepts email or username; `/user-login` 302/307 → `/login` |
| 2 | Sidebar guard for guests | already gated in `_layout.html` | verified, no leaks (login.html and register.html now extend the layout) |
| 3 | i18n on public pages | register/login/pricing FAQ/terms hardcoded English | all routed through `ui()` with HE/RU/EN |
| 4 | Universal terminology | mostly via i18n keys, some leaks | `vacancy_detail`, `campaigns`, `fb_post_generator`, `fb_group_selector` no longer leak `Vacancy`/`Candidate` |
| 5 | Demo chat on landing | Hebrew-only | `botScripts.{he,ru,en}`, picked by `ui_lang` |
| 6 | Telethon posting in `campaign_tick` | already wired (`worker/tasks.py` 251–268) | unchanged |
| 7 | Phone collection in bot | already wired (`bot/run_bot.py` 709 contact handler + `extract_phone`) | unchanged |
| 8 | HOT lead notification | already wired (`bot/run_bot.py` 194 `send_hot_lead_notification` + `RECRUIT_OPERATOR_NOTIFY_CHAT`) | unchanged |
| 9 | Misc | no `og:` tags, scattered links | `og:` + Twitter card on landing & pricing, all `/user-login` links rewritten to `/login` |

## Local rebuild after pulling this branch

```bash
cd ~/Desktop/recruit-autopilot-core
git fetch origin claude/review-projects-5s4tA
git checkout claude/review-projects-5s4tA
docker compose down
docker compose up -d --build
docker compose logs -f web | head -40   # confirms factory.create_app boots clean
```

## Hard gates — must pass before pilot

### 1. Self-service registration

1. Open `http://localhost:8080/` (or the Cloudflare tunnel) in incognito.
2. Switch to `RU`; landing copy and demo chat both render in Russian.
3. Click `Начать` → `/register` shows in RU, no sidebar visible.
4. Submit `pilot1@example.com` / `pilot1234` / `Pilot Test`.
5. Should land on `/dashboard` with sidebar showing Панель/Объявления/Лиды… (RU).
6. Click logout → `/` (landing).
7. Click `Войти` → `/login`. Enter `pilot1@example.com` / `pilot1234`.
8. Should land back on `/dashboard`. ✅ This is the previously broken loop.

### 2. Admin still works

1. Logout (or new incognito).
2. `/login` → enter `operator` / `<ADMIN_PASSWORD>`.
3. Should land on `/dashboard` against TopStaff/FloorDSGN companies.

### 3. Locale switch covers public pages

For each of HE / RU / EN, top-right pill switch → verify nothing in
`/`, `/register`, `/login`, `/pricing`, `/terms` is in the wrong language.

### 4. Vacancy detail terminology

1. Logged in as admin, open a FloorDSGN vacancy at `/vacancies/<id>`.
2. Switch UI to RU; section headers should say `Основное / Что публикуется /
   Настройка бота-скрининга / Действия оператора`. **No** "Vacancy core" or
   "Candidate funnel" anywhere in the page.

### 5. Demo chat

1. `/` → scroll to demo phone-frame → chat plays through in current language
   (HE/RU/EN). Final message is the orange `🔥 HOT LEAD` card with name +
   phone + WhatsApp link.

### 6. End-to-end posting (already wired, verify intact)

1. `/campaigns/` → pick the FloorDSGN multi-channel pilot → `Run now`.
2. Watch worker logs:
   ```bash
   docker compose logs --tail 30 worker | grep campaign_tick
   ```
   Should show `Telethon post to @haifa_rabota: ok=True`.
3. `/sources/` → posting attempts row goes `pending → posted` for ready TG
   destinations.

### 7. End-to-end screening + HOT notification (already wired, verify intact)

1. `/demo/` → `Fire ▶` on any FloorDSGN vacancy.
2. Operator's Telegram (`RECRUIT_OPERATOR_NOTIFY_CHAT=8175553706`) gets a
   `🔥 HOT LEAD!` message within 3s with name + phone + WhatsApp deep link.

## Soft gates (nice to have, not blocking)

- Old user_login.html is dead code — file kept (template no longer rendered);
  can delete in a follow-up.
- Password hash is still SHA-256; werkzeug/bcrypt upgrade deferred so
  existing trial users aren't locked out.
- `/static/favicon.ico` 404 fixed for pricing; landing already had it.

## Known unchanged risks

- FB browser session capture is still a one-time operator action
  (`scripts/fb_capture_session.py`). Code untouched.
- Bot restart policy is `restart: no`; flip to `unless-stopped` once tomorrow's
  pilot is stable.
- OpenAI key spend ≈ $0.02–0.05 per scored candidate.

## Rollback

If any gate fails, `git checkout main && docker compose up -d --build`
restores the prior state. No DB migrations were added by this branch — all
changes are template/route/Python code only.
