# Codex Operating Context

## Concise System Understanding
- This ecosystem is a mixed founder stack with one active commercial path, one active marketing site, one useful internal dashboard, and one high-entropy product family.
- The cleanest current pairs are:
- Recruit: GitHub `recruitment-bot` plus local execution copy `../recruit-autopilot-core`
- FloorDSGN: GitHub `floordsgn-site` plus Vercel `floordsgn-site`
- MeltBot dashboard: GitHub `moltbot-dashboard` plus Vercel `moltbot-dashboard`
- The least clean area is Connector: too many repos, dirty-branch deployments, backups, and near-duplicate Vercel projects.

## How Codex Should Behave Going Forward

### Default Behavior
- optimize for revenue-near execution first
- prefer validated source-of-truth repos over local backup folders
- treat local non-git folders as potentially disposable or partial
- produce operator-ready assets, not architecture churn
- separate confirmed facts from inference

### Default Lane Preferences
- 1: Recruit Autopilot pilot readiness, QA, runbooks, validation
- 2: FloorDSGN lead-gen and conversion support
- 3: MeltBot dashboard monitoring or low-conflict ops support
- 4: Connector cleanup only when explicitly assigned
- 5: AI Video only when explicitly assigned

## Overlap Risks To Avoid
- security/auth remediation lanes
- shared auth/login/session logic
- key handling, secret rotation, webhook security, PII cleanup
- local-core / strategist / orchestration surgery
- Connector code changes in a repo that has not been explicitly chosen as canonical

## What To Inspect First On Future Tasks

1. Current repo identity
- Is this a git-linked canonical repo, a backup copy, or a scratch folder?

2. Canonical mapping
- Does this repo cleanly map to a known product and deployment?

3. Operational status docs
- For Recruit: look for runbooks, smoke docs, pilot checklists, sell packages
- For FloorDSGN: check public deployment, contact flow, and recent commits
- For MeltBot: check dashboard/system-state docs before touching code
- For Connector: first determine whether the task belongs in `connector-web-test`, a backup workspace, or nowhere

4. Conflict risk
- If the task touches auth, security, infra internals, or deployment lineage, slow down and confirm evidence first

## What Codex Should Never Do Unless Explicitly Told
- never treat `../connector-web` as authoritative just because it is on disk
- never treat `../финал/FloorDSGN` as canonical over GitHub `floordsgn-site`
- never treat `../TELEGRAM BOT` as a safe working repo
- never deploy from dirty local branches as a default habit
- never spend cycles cleaning Connector duplication unless the task is explicitly about that
- never drift into local-core or orchestration rebuilds because they “look important”

## Default Source-Of-Truth Rules

| Family | Canonical Default |
| --- | --- |
| Recruit Autopilot | GitHub `recruitment-bot` |
| FloorDSGN | GitHub `floordsgn-site` + Vercel `floordsgn-site` |
| MeltBot dashboard | GitHub `moltbot-dashboard` + Vercel `moltbot-dashboard` |
| Connector | No implicit canonical repo; choose explicitly |
| AI Video | `ai-video-platform` for full system, `ai-video-studio` for UI |

## Quick Start Heuristic For Future Tasks

1. Identify product family.
2. Check whether the current folder is canonical or just local working state.
3. Check matching Vercel project if the task is web-facing.
4. Avoid overlap lanes.
5. Pick the smallest high-value deliverable that moves product, validation, or revenue.
