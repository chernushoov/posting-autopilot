# Ecosystem Repo Map

## Scope And Method
- Date of inspection: 2026-03-30
- GitHub app returned no repositories in this Codex session.
- This map was built from:
- local workspace inspection on the iMac
- `gh repo list chernushoov`
- `gh repo view` and `gh api` for root structure and stack hints
- Vercel deployment metadata that exposed linked repo names
- Confidence labels:
- `High` = directly confirmed by GitHub/Vercel/local files
- `Medium` = strong inference from matching names, structure, and deployment metadata
- `Low` = partial evidence only

## Confirmed GitHub Repositories

| Repo | Family | Purpose | Status | Surface | Main Stack | Key Files / Docs | Likely Lane | Likely Next Value | Recommendation | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `recruitment-bot` | Recruit Autopilot Bot | Core recruiting bot/runtime with pilot and QA assets; appears to be the main commercial repo for recruiting operations | Active as of 2026-03-27 | Production-facing app + operator docs | Python, FastAPI, Telegram bot, Redis/RQ, SQLAlchemy, Jinja | `README.md`, `SELL_PACKAGE.md`, `PILOT_SMOKE_SEQUENCE.md`, `QA_GO_NO_GO.md`, `TOMORROW_PILOT_RUNBOOK.md`, `requirements.txt` | Product + QA + commercial | Pilot hardening, operator validation, demo/runbook packaging | Keep as primary source of truth for Recruit | High |
| `floordsgn-site` | FloorDSGN | Public marketing/lead-gen site for Floor.DSGN | Active as of 2026-03-27 | Production-facing website | Static site, HTML/CSS/JS, some Vercel/serverless glue | Vercel-linked homepage, public repo, deployment history on `main` | Product + commercial + QA | Lead funnel QA, conversion tracking, contact flow validation | Keep as primary source of truth for FloorDSGN | High |
| `connector-pro` | Connector Pro | PWA-style job marketplace product, older simpler branch of Connector family | Likely stale-active; last GitHub update 2026-02-19, local commit 2026-01-21 | Prototype / product-facing demo | Plain HTML/CSS/JS, PWA, service worker | `README.md` | Product | Clarify whether it still matters or is superseded by Next.js Connector repos | Monitor, do not default to it | High |
| `moltbot-dashboard` | MeltBot / local-core / dashboard | Internal monitoring and control dashboard for bot/runtime ecosystem | Active; repo updated 2026-02-21 and Vercel production redeployed 2026-03-27 | Internal tooling, production-like ops surface | Node/Vercel serverless, static dashboard UI, API | `SYSTEM_STATE.md`, `LAUNCH_READINESS_REPORT.md`, `ALL_PROJECTS_AUDIT_2026-02-19.md`, `vercel.json`, `api/` | Infra + ops + monitoring | Observability, dashboard QA, safe control-plane docs | Keep and monitor; do not refactor casually | High |
| `ai-video-platform` | AI Video Platform | Broader multi-service AI video system; likely backend/platform repo behind studio UI | Active-ish but not current default focus; last update 2026-02-19 | Internal platform / experimental product | Docker Compose, Python API, Node web, Redis, workers | `docker-compose.yml`, `RUNPOD_SETUP.md`, `SYSTEM/`, `api/`, `worker/`, `web/` | Infra + product | Validation of end-to-end generation path and RunPod reliability | Keep, but only touch when explicitly assigned | High |
| `connector-web-test` | Connector Pro | Next.js Connector web app with most complete documented web product surface | Active but unstable; GitHub updated 2026-02-18, Vercel project `connector-web` historically linked here | Prototype / product-facing demo | Next.js 14, React, Tailwind, Supabase, Stripe, Vercel | `STATUS.md`, `QA_SUMMARY.md`, `QA_TESTING_REPORT.md`, `ARCHITECTURE_LOGIC_FLOWS.md`, `package.json`, `vercel.json` | Product + QA | Source-of-truth cleanup, demo QA, commercial packaging | Keep and monitor; not safe as sole source of truth until repo/deploy alignment is cleaned up | High |
| `connector-free-mvp` | Connector Pro | Free-tier or simplified Connector MVP branch | Stale duplicate; last update 2026-02-07 | Prototype / duplicate product | Next.js 14, Prisma/Postgres, Stripe, Twilio, Sentry | `IMPLEMENTATION_PLAN.md`, `README.txt`, `docs/`, `package.json`, `vercel.json` | Product | Decide whether any unique logic still matters before archiving | Archive candidate after extraction check | High |
| `ai-video-studio` | AI Video Platform | Vercel-facing UI for prompt/image-to-video generation | Stale-active; repo updated 2026-01-27, deployment updated 2026-02-23 | Product-facing UI / experimental | Next.js, Vercel UI, RunPod-connected workflow inferred | Vercel-linked repo and deployment metadata | Product | Smoke test generation flow and define monetization or pause | Monitor only | High |
| `connectorwebtest` | Connector Pro | Initial throwaway Connector test repo created from Vercel | Stale test; last update 2026-01-22 | Test / abandoned | Next.js | `package.json`, `STATUS.md`, `QA_SUMMARY.md` | Archive | None unless a hidden dependency is found | Archive / ignore | High |
| `chernushoov.github.io` | Other | Generic GitHub Pages repo, not part of current priority families | Stale as of 2025-07-23 | Public static site | Static web | GitHub Pages homepage | Archive / ignore | None for current strategy | Ignore | High |

## Local Workspaces On This Machine Worth Knowing

These are not all confirmed GitHub repositories, but they materially affect execution on this iMac.

| Local Path | Family | Purpose | Status | Evidence | Recommendation | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| `../recruit-autopilot-core` | Recruit Autopilot Bot | Local execution copy of Recruit Autopilot core with Flask admin, bot, worker, scheduler | Active local workspace on 2026-03-30 | `README.md`, `docker-compose.yml`, bot/worker/app structure, recent local edits | Keep; safest local lane is stability + QA + runbooks | High |
| `../strategist` | MeltBot / local-core precursor | HR/recruiting multi-agent system with orchestrator, copywriter, outreach, scheduler, analytics | Active local-only workspace, modified 2026-03-26 | `README.md`, `.env.example`, `requirements.txt`, no git metadata | Monitor only; treat as infra-heavy and avoid casual edits | Medium |
| `../финал/orchestrator` | MeltBot / orchestration docs | OpenClaw/Claude orchestration setup docs and launch scripts, originally centered on Connector workflows | Likely stale setup pack, modified 2026-02-18 | `docs/SETUP_IMAC.md`, launch scripts, agent markdown files | Do not use as source of truth; keep as reference only | High |
| `../connector-web` | Connector Pro | Local backup copy of Connector web app | High-confusion backup, modified 2026-02-18 | `README.txt` says “РЕЗЕРВНАЯ КОПИЯ”, `.vercel/project.json` points to `backup_rezerv` | Do not treat as source of truth without explicit reconciliation | High |
| `../финал/FloorDSGN` | FloorDSGN | Local scratch workspace for site and strategy docs | Active scratch workspace, modified 2026-03-26, but no commits yet | many staged files, no commit history, local docs/prototypes | Keep for drafts, but source of truth is GitHub `floordsgn-site` | High |
| `../TELEGRAM BOT` | Recruit / unknown legacy bot | Ad hoc Telegram bot folder with local DB, env files, and no commit history | Risky legacy | `.env`, `.env.save`, `bot.db`, no commits | Ignore unless specifically needed; secret/PII risk | High |
| `../MiroFish` | Other / unrelated | External swarm-intelligence project from `666ghj/MiroFish` | Active but unrelated | own remote, unrelated README and stack | Ignore for this founder ecosystem | High |

## Key Read On Source Of Truth

| Family | Current Best Source Of Truth | Notes |
| --- | --- | --- |
| Recruit Autopilot Bot | `recruitment-bot` on GitHub | Current local `recruit-autopilot-core` looks like a working execution copy, but it is not git-linked here |
| FloorDSGN | `floordsgn-site` on GitHub + Vercel project `floordsgn-site` | Local `../финал/FloorDSGN` is a scratch workspace, not the canonical repo |
| Connector Pro | No clean single source right now | `connector-web-test` is the clearest repo history, but local `../connector-web` and multiple Vercel projects create ambiguity |
| MeltBot / local-core | `moltbot-dashboard` for dashboard surface; local `strategist` for runtime ideas | No clean single git-linked local-core repo was found on this machine |
| AI Video Platform | `ai-video-platform` for system-level work; `ai-video-studio` for Vercel UI | Split-stack product, not default focus |
