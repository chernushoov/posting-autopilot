# posting-autopilot — Production Readiness Plan
_Grounded in a real code recon 2026-06-15. Goal: a full-grade SaaS that won't bite us later. P0 = before/at launch, P1 = first 2–4 weeks, P2 = scale. Owner = needs your account/money; Eng = I build._

## What we already have (don't rebuild)
Multi-tenant isolation (no IDOR), auth + CSRF + login rate-limit, cabinet SPA (11 screens, RU/EN/HE+RTL, 0 console err, mobile 0px), TG+FB posting engine (headless, cloud), FB server-capture (noVNC, proxy-ready), billing scaffold (Stripe-ready, cancellation revokes), analytics scaffold (CF + Clarity, env-driven), encryption active on prod, landing (3 langs, apps-soon, 2025), a `tests/` dir.

## Recon gaps (verified MISSING)
❌ password reset · ❌ any email sending (SMTP vars exist, no code) · ❌ DB migrations/Alembic (uses create_all → schema changes are manual) · ❌ error tracking (Sentry) · ❌ GDPR data export / account delete · ❌ CI · ❌ off-box backups · ❌ uptime/failure alerts.

---

## P0 — before / at launch (don't launch a real service without these)
| # | Item | Owner/Eng | Why it bites later |
|---|---|---|---|
| P0-1 | **Backups + PROVEN restore** (pg + `data/fb_sessions`+`data/tg_sessions`) | Eng (+Owner O5 off-box) | one disk, one node → data loss = company-ending |
| P0-2 | **Email infra + password reset** | Eng builds; Owner gives email provider creds | users WILL forget passwords → locked out, support hell, churn |
| P0-3 | **ToS + Privacy (HE/EN)** incl. Clarity session-recording + data terms | Eng draft; Owner gives legal entity+email | legal predicate for paid contracts in IL; Clarity needs disclosure |
| P0-4 | **Stripe live** (keys + 3 price-ids) + receipts | Owner account; Eng wires | can't take money |
| P0-5 | **Error tracking (Sentry)** env-driven | Eng wires; Owner DSN (free tier) | blind to prod crashes |
| P0-6 | **Posting-failure + uptime alerts** (TG/email on ban/captcha/session-dead; UptimeRobot on /health) | Eng | bans/outages found days late = pilot sees zero results |
| P0-7 | **FB proxy live + secondary FB acct** | Owner buys proxy; Eng done (env) | personal FB ban from datacenter IP |

## P1 — first 2–4 weeks (full-grade hygiene)
| # | Item | Owner/Eng |
|---|---|---|
| P1-1 | **Alembic migrations** (baseline current schema, future changes safe) | Eng |
| P1-2 | **GDPR: data export + account deletion** (self-serve) | Eng |
| P1-3 | **Dunning** (failed-payment retries/grace) + invoices | Eng |
| P1-4 | **Plan-limit enforcement** (worker-paywall + ad/channel caps per tier) | Eng |
| P1-5 | **Encrypt at rest**: Telethon `.session` files + `Candidate.phone/chat_log_json` | Eng |
| P1-6 | **Onboarding questionnaire** (segment → funnel → upsell; small biz → ₪299 nurture) | Eng (with you, flow change) |
| P1-7 | **Auto-folder TG/FB groups by theme** + post→matching-folder routing | Eng |
| P1-8 | **Lifecycle emails** (welcome, trial-ending day-3/1, receipt, ban-alert) | Eng |
| P1-9 | **RAM mem_limits + swap** (chromium+Xvfb on 2vCPU/4GB) | Eng |
| P1-10 | **Help/FAQ + support contact** (in-app + email) | Eng; Owner support email |

## P2 — scale & sustainability (so we don't get stuck)
| # | Item |
|---|---|
| P2-1 | **CI + test suite** on push (regression guard before every deploy) |
| P2-2 | **Staging environment** (verify before prod; we deploy straight to prod today) |
| P2-3 | **PostHog product funnel** (register→connect→post→pay), conversion dashboards |
| P2-4 | Per-tenant proxies + ban-recovery runbook; multi-account FB/TG |
| P2-5 | Caching + DB indices review; horizontal scale path (separate web/worker hosts) |
| P2-6 | Referral/affiliate; annual plans; VAT/tax (IL) |
| P2-7 | Admin console (tenant health, usage, impersonate-for-support, audit log) |
| P2-8 | Secrets manager (off .env), dependency vuln scanning, 2FA for accounts |

---

## Execution order (recommended)
1. **P0-1 backups** ← starting now (Eng-only, critical).
2. P0-5 Sentry + P0-6 alerts (Eng; you create free Sentry+UptimeRobot).
3. P0-2 email+password-reset (Eng; you pick email provider).
4. P0-3 ToS/Privacy (you give entity name) + P0-4 Stripe (you do KYB) + P0-7 proxy (you buy).
5. P1 in listed order. P2 after first paying customers prove the model.

## Owner accounts to create (batch them in the morning)
Stripe · email provider (Resend/SendGrid/your SMTP) · Sentry (free) · UptimeRobot (free) · residential proxy · Cloudflare Web Analytics token · Clarity project id · object storage (backups) · legal entity name+support email.
