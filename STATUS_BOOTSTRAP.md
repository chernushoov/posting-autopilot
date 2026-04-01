# STATUS BOOTSTRAP

## Detected Project
- Project: Recruit Autopilot Bot
- Repo: `recruit-autopilot-core`
- Machine role fit: iMac / Factory / execution machine

## Repo Purpose
- Local execution core for Recruit Autopilot
- Working copy status: no local `.git` metadata detected in this directory
- Contains:
- Flask admin panel for multi-company recruiting operations
- PostgreSQL + Redis backed runtime
- RQ worker and scheduler for async campaign tasks
- Telegram bot skeleton for candidate intake and interview flow
- Seeded demo data for local validation

## Likely Active Overlap Risks
- `app/auth.py` and `app/routes/auth_routes.py`: auth/login surface, avoid unless explicitly assigned
- `.env` / API keys / bot token / provider credentials: avoid handling beyond documented setup
- Telegram posting/check internals in worker queue and bot runtime: likely active infra/security-adjacent lane
- AI provider replacement and external integrations: likely active deep implementation lane
- Shared security hardening around session handling, headers, CORS, auth protection: do not overlap
- No local git metadata: treat this workspace as a handoff/export copy and avoid assumptions about branch or merge state

## Recommended Lane For Codex On This Machine
- Lane: stability + QA + operator readiness
- Why this lane:
- additive and low-conflict
- directly useful for launch/demo/pilot prep
- safe to validate locally on execution hardware
- supports merge-readiness without touching security-sensitive files

## Top 3 High-Value Next Actions
1. Create a deterministic local smoke pack for boot, login, and seeded admin flows.
2. Create an operator demo runbook for a first live pilot walkthrough.
3. Add merge-safe validation notes/checklist for web, worker, scheduler, and bot startup behavior.

## Immediate Action Started
- Action 1 in progress: local smoke pack
