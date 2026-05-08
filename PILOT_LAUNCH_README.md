# Pilot Launch — Operator Quick Reference

**Open this first.** Everything you need to run a pilot demo or actual recruitment session, in order, with the right URLs.

---

## What's loaded in the database right now (demo-ready snapshot)

- **4 active vacancies** for FloorDSGN, all with bot screening configured (RU primary, deep-link `?start=apply_<id>`):
  - id 5 — Эпокси / Микротопинг (специалист)
  - id 6 — Бетонные полы / Установка и затирка
  - id 11 — Помощник на полы (без опыта, обучаем)
  - id 12 — Мастер декоративного бетона / терраццо
- **6 Telegram destinations** all marked READY (Telethon access verified):
  - @haifa_rabota, @rabotaisraelrabota, @izrail_rabota, @israels_jobs_haifa, @batyam_rabota, @rabota_v_izrail
- **5 Facebook groups** imported, manual workflow ready.
- **1 multi-channel TG campaign (paused)** — `Floor.DSGN — Concrete worker (multi-channel pilot)` (id 7), vacancy 6 → all 6 ready TG destinations, 4h interval, 6 max/day, hours 10–19 IL. Hit Run Now from `/campaigns/` to fire one staggered cycle (≈10 min total).
- **4 Facebook posting runs** — one per FloorDSGN vacancy, each with an approved Hebrew variant + 5 FB groups in the queue. View at `/facebook/posting-runs/<id>/queue`. Auto-fire when FB session captured.
- **5 demo candidates** seeded — mix of hot/warm/cold/interviewing in RU and HE, populating the Worker Responses panel.

---

## State as of 2026-05-08

- **Stack**: local docker on operator's Mac (`localhost:8080`), exposed via Cloudflare tunnel `basement-inner-extra-tyler.trycloudflare.com`.
- **Bot**: `@AutopillotRecruit_bot` (id `8786784416`).
- **Operator chat for hot-lead notifications**: `8175553706` (set in `.env` as `RECRUIT_OPERATOR_NOTIFY_CHAT`).
- **Default demo company**: FloorDSGN (id 5). Switch via `/companies/switch/5`.
- **AI scoring**: OpenAI gpt-4o-mini via `AI_API_KEY` env. Falls back to rule-based if API key missing.
- **TG live posting**: working. Last real post 2026-05-08 10:35 to `@haifa_rabota` (msg_id `142353`).
- **FB auto-posting**: code shipped, `data/fb_sessions/floordsgn.json` not captured yet — operator must run `scripts/fb_capture_session.py` once on Mac to enable.

---

## Demo (with observer) — 8 minutes

1. **Open dashboard** → `http://localhost:8080/dashboard` — point at the Operator Copilot strip; this is where the operator lives day-to-day.
2. **Open `/vacancies/`** → 4 active FloorDSGN vacancies. Click one (any) → detail page showing what gets posted + the bot screening setup (greeting, qualifying questions, hot/cold criteria).
3. **Open `/sources/`** → 6 Telegram destinations + 1 Facebook. 1 TG ready (@haifa_rabota), 5 staged for operator's check, 1 FB ready (manual workflow).
4. **Open `https://t.me/haifa_rabota` in a browser** → scroll to today 10:35 → real Floor.DSGN posting visible. Evidence that posting works, not theatre.
5. **Open `/facebook/posting-runs/3/queue`** → FB queue UI with 5 groups + the approved Hebrew variant. Explain: "Meta killed groups Graph API in 2024, so every legit Israeli auto-poster (fbzipper, Postify, FaceBoost) does browser automation. We do too. The operator captures their FB session once, then we cycle through groups with anti-ban delays."
6. **Open `/demo/` in a separate tab** → click Fire ▶ on any FloorDSGN vacancy → wait 3 seconds → 🔥 HOT LEAD message arrives in the operator's Telegram. **This is the wow moment.** AI scored the candidate, classified as hot, fired the notification with a wa.me click-to-chat link.
7. **Open `/candidates/`** → show the 5 seeded candidates + the just-fired demo one. Filter by status to focus on hot.
8. **Optional `/analytics/`** → conversion funnel (clicked /start → started screening → completed → passed → hired).

After the observer leaves, run `/demo/` page's Cleanup button to remove demo candidates so the production state stays clean.

Full annotated walkthrough with failure-mode triage: [PILOT_DEMO_SCRIPT_2026-05-08.md](PILOT_DEMO_SCRIPT_2026-05-08.md).

---

## Daily ops cheatsheet

| Task | URL / command |
| --- | --- |
| Start the stack | `docker compose up -d` from `~/Desktop/recruit-autopilot-core` |
| Switch language | top-right `EN / RU / HE` pills, or `/set-lang/ru` |
| Add a vacancy | `/vacancies/new` (textareas for bot questions one-per-line) |
| View / detail one vacancy | `/vacancies/<id>` |
| Add a TG destination | `/connect/telegram` (sync) → `/sources/` (manual ref) |
| Add an FB destination | `/connect/facebook` for the pages flow, or curated CSV via `python -m scripts.fb_group_import` |
| Run all pending TG checks | `/sources/` → "Check N pending Telegram destinations" button |
| Capture FB browser session | `python scripts/fb_capture_session.py` (on Mac, with venv) |
| FB session smoke (no posting) | `POST /api/fb/posting-runs/<id>/smoke` |
| Auto-fire FB queue with 5–10 min stagger | `POST /api/fb/posting-runs/<id>/auto-fire` |
| Trigger one demo hot lead | `/demo/` → Fire ▶ |
| Wipe demo candidates | `/demo/` → Cleanup, OR `psql -c "DELETE FROM candidates WHERE tg_user_id LIKE 'DEMO_%';"` |
| Recheck live posting | `bash scripts/live_deploy_smoke.sh https://posting-autopilot-next.vercel.app` |

---

## Things to do BEFORE the first paying-customer pilot

1. Capture FB session (`scripts/fb_capture_session.py`) and run smoke + 1 real auto-post to a private test group to validate selectors against current FB UI.
2. Decide the FB account strategy: personal vs burner. Personal is risky long-term — ban kills it. Plan a burner before scaling past 10 groups/day.
3. Set per-vacancy WhatsApp quick-reply templates for hot-lead notifications.
4. Wire the email digest: `send_hot_lead_email` already exists in `common/email_notify.py` but no SMTP creds in `.env`. Add `SMTP_HOST/PORT/USER/PASS` if email channel is wanted.
5. Add a real edit-vacancy flow (currently only create + view). Operator workaround: clone the existing one via `/new` with the same title + tweaks, then archive the old one.
6. Multi-account support for TG when operator wants to post from a 2nd phone number. Today the stack assumes one Telethon session per company.
7. FB Meta App review for Pages auto-posting (separate path from groups). Pages are stable via Graph API; only groups need browser automation.

---

## Risks the operator should watch

- **FB account ban**: any browser automation can trigger this. Anti-spam delays in `worker/fb_auto_post.py` default to 5–10 min between groups. If volume grows, switch to a burner account.
- **TG anti-spam**: existing `common/tg_client.py:POST_DELAY_MIN/MAX` handles this. Don't reduce below 30s.
- **Cookie session expiry**: FB sessions live 7-30 days depending on activity. When auto-fire returns `not_logged_in`, re-run capture.
- **Selector breakage**: FB UI updates can break the `_find_composer_box` / `_find_active_textbox` / `_find_submit_button` chain. Each has Hebrew + English fallbacks. Maintenance is ongoing.
- **AI scoring cost**: gpt-4o-mini is ~$0.02-0.05 per candidate. For 100 candidates/month that's $5. Negligible. Falls back to rule-based for free if `AI_API_KEY` removed.

---

## Repository pointers

- Codebase: `~/Desktop/recruit-autopilot-core` → GitHub `chernushoov/posting-autopilot`
- FB recovered live snapshot (the simpler Vercel-deployed Flask): `ops/prelaunch_artifacts/recovered_live_source/dpl_..._hotfix_candidate/src/`
- Live URL of the Vercel snapshot: `https://posting-autopilot-next.vercel.app` (last redeploy 2026-05-08, smoke + bad-input both GREEN, see `PRODUCTION_PROMOTION_2026-05-08.md`)
- Pilot e2e evidence: `ops/prelaunch_artifacts/pilot_e2e/2026-05-08/`
- Demo script: `PILOT_DEMO_SCRIPT_2026-05-08.md`
