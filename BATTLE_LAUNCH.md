# posting-autopilot — BATTLE LAUNCH (master doc)
_2026-06-15. Single source of truth for go-live. Detail lives in: `LAUNCH_ROADMAP.md` (holds+burndown), `PRODUCTION_READINESS.md` (P0/P1/P2), `DO_NOT.md` (anti-patterns), `CLAUDE_PROJECT_BRIEF.md` (architecture)._

## 1. Concept & strategy
**Telegram-first recruitment automation for Israeli staffing agencies.** One vacancy → auto-posted to 50+ Telegram groups + Facebook groups/Marketplace → an AI bot screens replies in HE/RU/EN, scores, collects phones → the recruiter gets only hot leads, in a multi-tenant web cabinet. Pricing ₪299 / ₪899 / ₪1999.
- **Wedge:** TG-only pilot (cheapest, safest, works today) → expand to FB once proxy is in.
- **Funnel strategy:** post-login questionnaire segments the client → small biz nurtured on ₪299, bigger ones up-sold (planned F2).
- **Moat (data/reputation):** per-tenant leads + chat history + posting performance compounding over time.

## 2. Competitor positioning
Direct IL competitors (auto-posting tools): **fbzipper, Postify, FaceBoost** (FB/TG mass-posters), **EZPost** (browser-session FB groups).
- **They are POSTERS. We are a posting → AI-screening → qualified-lead pipeline.** They blast; we blast *and* filter, score, collect phones, and hand the recruiter a shortlist.
- **Our edges:** trilingual HE/RU/EN + RTL · AI screening bot (the others have none) · TG + FB groups + Marketplace from the **cloud** (no operator's PC needed, our server-side capture) · leads funnel/CRM + analytics · strict per-tenant isolation · anti-ban (proxy + caps + jitter + night pause).
- **Where they beat us today:** they're live/known; we're pre-revenue. → win first design-partners on the *screening* value they can't match.

## 3. Security — VERIFIED this session ✅
Every user is protected and isolated:
- Code audit: 0 unguarded non-public routes (decorator or inline auth on all).
- `app/tenant.py scoped()` = every tenant query filtered by **company_id from the server session, never request input** → IDOR-proof by construction. Company switch checks `owner_id`.
- Live 2-tenant attack: A sees only own company, can't switch to B, can't read B's vacancy/candidate, POST-only routes reject GET, unauth bounced to login everywhere. FB capture cross-tenant = 403. Encryption active on prod.

## 4. DONE (verified, on prod, main + etalon `dfa9b5e`)
Cabinet SPA (11 screens, RU/EN/HE+RTL, 0 console err, mobile 0px) · tenant isolation · TG+FB posting engine (headless cloud) · **FB server-capture (noVNC, proxy-ready, tenant-isolated)** · billing scaffold + cancellation-revoke · **analytics scaffold (CF + Clarity, env-driven)** · landing 3-lang + apps-coming-soon + © 2025 + mobile-overflow fixed · **backups + PROVEN restore + daily cron** · FB anti-ban proxy-readiness · friendly TG connect errors · 19/19 e2e green.

## 5. NOT done — gates to real launch
**Owner holds** (see ROADMAP): Stripe KYB · TG phone+code · proxy + secondary FB acct · object storage (off-box backup) · email provider · Sentry/UptimeRobot accounts · legal entity · social links · CF API token (biggest unlock).
**Engineering queue** (P0→P1, see READINESS): email+password-reset · ToS/Privacy · Sentry+alerts wiring · GDPR export/delete · Alembic · dunning · plan-limit/worker-paywall · session/PII encryption · onboarding questionnaire · auto-folder groups.

## 6. Go-live sequence (the battle plan)
1. **T-0 now:** Owner starts Stripe KYB (longest timer) + creates the free accounts (CF token, email, Sentry, UptimeRobot) + buys proxy.
2. **Engine arm:** TG connect (owner phone+code) → first real TG-group post verified → pilot can run TG-only, billed manually.
3. **I wire (on accounts):** email+password-reset, Sentry+alerts, analytics ids, Stripe keys+products, proxy → then FB login on a **secondary** account, first FB post verified.
4. **Legal:** ToS/Privacy live (entity name) before first paid contract.
5. **Pilot:** 1–3 design partners, hand-onboarded, 2–4 weeks; success = sessions survive, real leads in funnel, zero cross-tenant leaks, ban behavior observed.
6. **GA:** payments live + ToS + alerts + backups-proven + onboarding + i18n-of-server-labels done.

## 7. Etalon reserve (на всякий)
- **Code:** git tag `etalon-prelaunch-2026-06-15` (@ `dfa9b5e`), pushed to GitHub — restore anytime.
- **Data:** daily DB+sessions backup with proven restore (off-box one env away).
- Treat this tag as the known-good rollback point.
