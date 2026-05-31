# OVERNIGHT WORK PLAN — Posting Autopilot → first-money-ready
# Self-spec. Execute top-down. Do NOT deviate. Tick boxes as completed. Commit per phase.
# Owner starts hunting first leads tomorrow; this must be more-finished product by then.
# HARD RULE: never trigger real public posting to live TG/FB groups without explicit owner OK.
# HARD RULE: anything needing owner money/accounts (VPS, Stripe live keys, domain) = prepare + runbook, don't purchase.

repo: ~/Desktop/recruit-autopilot-core   (running, newest work, live .env/data)
commit style: focused commits per task; co-author trailer; do NOT commit secrets; do NOT push until reviewed batch.

## PHASE 0 — SECURITY (do first)
- [ ] S1 rotate+scrub admin password. New strong ADMIN_PASSWORD in .env. Remove literal `HBIKEGMS5nd7GNXP`/`operator` creds from tracked docs (CLAUDE_PROJECT_BRIEF.md, FINAL_READINESS_REPORT.md, PILOT_RUNBOOK.md) → replace with `<see .env>`. AC: `git grep HBIKEGMS5nd7GNXP` == empty.
- [ ] S2 bcrypt customer passwords. registration.py: hash via bcrypt; verify supports legacy sha256 + upgrade-on-login. requirements.txt += bcrypt. AC: new user registers+logs in; hash starts `$2b$`.
- [ ] S3 Stripe webhook must verify signature. billing.py: if STRIPE_WEBHOOK_SECRET unset → reject (400). AC: unsigned webhook → 400, not trusted.
- [ ] S4 .gitignore the junk: ops/**/multilingual_pilot_*.json, data/*.db, data/tg_sessions/, data/fb_sessions/. AC: `git status` clean of those.

## PHASE 1 — ROBUSTNESS (engine must not break)
- [ ] R1 Redis-down graceful. wrap enqueue (sources.py, campaigns.py) → on ConnectionError flash "background queue offline" + return, never 500. AC: Redis down → Run/Check buttons give friendly state.
- [ ] R2 double-post lock. run_campaign_now: refuse 2nd concurrent tick per campaign (active-run guard). AC: rapid double Run now → 1 tick.
- [ ] R3 idempotency. unique index PostingAttempt(run_key, source_id); per-source daily dedup SKIP (not just cap math). AC: scheduler+manual same day → no dup to same source.
- [ ] R4 TZ fix daily cap. last_post_at vs now.date() same tz. AC: cap counts correct across midnight Israel.
- [ ] R5 bot restart policy. docker-compose bot restart: unless-stopped. AC: set.
- [ ] R6 source-ready honesty. tasks.py: don't mark READY when no TG creds connected. AC: source w/o creds != ready.

## PHASE 2 — INBOUND FUNNEL (stop losing leads)
- [ ] I1 Telethon inbound listener. new worker/tg_listener.py: per-company userbot, events.NewMessage on watched sources; reply from non-self → create Lead/Candidate tied to source→campaign→vacancy, store msg, trigger AI handling + hot-lead. AC: a 2nd-account message in a watched test group creates a candidate row.
- [ ] I2 verify apply-link path solid (post→bot DM→screening). AC: deep link works end-to-end on test bot.

## PHASE 3 — MOAT: REAL AI DIALOG (the differentiator)
- [ ] A1 replace FSM on_message (bot/run_bot.py) with real LLM turn-loop: uses build_system_prompt + vacancy.bot_faq_knowledge + screening Qs + bot_hot/cold_criteria; answers candidate questions; asks next qualifier dynamically; multi-turn; stores chat_log; rule-based fallback; prompt-injection hardened. AC: candidate asks "מה השכר?" → bot answers from FAQ; flow is dynamic.
- [ ] A2 genuine conversation summary at handoff (summarize dialogue, not score rationale). AC: summary references actual answers.
- [ ] A3 classify_candidate uses operator hot/cold criteria. AC: criteria change → classification changes.
- [ ] A4 wire same AI engine to I1 inbound leads.

## PHASE 4 — COMMERCIALIZATION PREP (code-side; owner accounts later)
- [ ] C1 Stripe checkout fully wired + .env.example STRIPE_* + tier→price env map + STRIPE_RUNBOOK.md. AC: with test keys, pricing button → real Checkout session (test mode).
- [ ] C2 deploy package: docker-compose.prod.yml + Caddyfile(HTTPS) + DEPLOY_RUNBOOK.md + .env.production.example + deploy.sh. AC: documented clone→env→up path; health check passes locally.
- [ ] C3 positioning copy honest (only claim "AI dialog" once A1 done).

## PHASE 5 — FACEBOOK (lower priority; FB is a swamp)
- [ ] F1 FB post generator uses real LLM when key set (currently always stub). AC: generate_hebrew_post → AI text.
- [ ] F2 guard orphaned browser auto-poster: endpoints 403 unless FB_BROWSER_ENABLED=1. AC: auto-fire blocked by default.

## PROGRESS LOG
- 2026-05-31 49a2a45 — Phase 0 DONE (S1 rotate+scrub admin pw, S2 verified pbkdf2+legacy-upgrade already OK, S3 webhook signature required, S4 gitignore junk).
- 2026-05-31 db2e9b9 — Phase 1 DONE (R1 redis-graceful, R2 double-post lock, R3 unique-constraint, R4 TZ cap fix, R5 bot restart, R6 source-ready honesty).
- next: Phase 4 (deploy pkg + Stripe), then Phase 3 (AI dialog moat), then Phase 2 (inbound listener).
