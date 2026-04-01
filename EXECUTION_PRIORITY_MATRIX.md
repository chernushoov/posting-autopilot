# Execution Priority Matrix

## Product Priority Order

| Priority | Product Family | Why This Order |
| --- | --- | --- |
| 1 | Recruit Autopilot Bot | Strongest evidence of immediate commercial readiness: recent repo activity, sell/runbook artifacts, pilot docs, local execution copy available |
| 2 | FloorDSGN | Clear public site, live Vercel production, active recent updates, direct lead-gen use case |
| 3 | Connector Pro | Still commercially interesting, but source-of-truth is fragmented across repos and deployments |
| 4 | AI Video Platform | Real product exists, but it is infra-heavy and not the shortest path to revenue right now |
| 5 | MeltBot / local-core / dashboard | Operationally important, but should support execution rather than become the default work sink |

## Repo Priority Order

| Priority | Repo / Workspace | Default Use |
| --- | --- | --- |
| 1 | `recruitment-bot` | Primary commercial product repo for Recruit |
| 2 | `../recruit-autopilot-core` | Current iMac execution workspace for Recruit QA/runbooks/stability |
| 3 | `floordsgn-site` | Primary marketing and lead-gen repo |
| 4 | `moltbot-dashboard` | Control-plane monitoring and ops visibility |
| 5 | `connector-web-test` | Best available structured Connector repo, but only after lineage caution |
| 6 | `ai-video-platform` | Use only when explicitly working AI Video system-level tasks |
| 7 | `ai-video-studio` | Use for AI Video UI-only work |
| 8 | `connector-pro` | Legacy/simple Connector branch; not default |
| 9 | `connector-free-mvp` | Archive candidate |
| 10 | `connectorwebtest` | Ignore |

## Deployment Priority Order

| Priority | Vercel Project | Default Use |
| --- | --- | --- |
| 1 | `floordsgn-site` | Public lead-gen surface; conversion and QA matter immediately |
| 2 | `moltbot-dashboard` | Ops visibility; useful for internal runtime state |
| 3 | `connector-web` | Monitor-only demo surface until source-of-truth is cleaned |
| 4 | `ai-video-studio` | Monitor only; not default work target |
| 5 | `backup_rezerv` | Cleanup target, not a default work surface |
| 6 | `site` | Cleanup target |
| 7 | `connector-free-mvp` | Cleanup target |
| 8 | `connectorwebtest` | Ignore |
| 9 | `workspace` | Ignore / archive |
| 10 | `connector_deploy` | Ignore / archive |

## Default Focus For Future Codex Work

### Default Yes
- Recruit Autopilot QA, demo prep, pilot docs, runbooks, validation scripts
- FloorDSGN funnel QA, contact flow validation, sales/demo assets, launch polish
- MeltBot dashboard read-only or low-conflict operational support

### Default No
- Connector architecture churn before repo/deployment lineage is cleaned
- local-core infra rebuilds
- security/auth remediation overlap
- deep AI Video platform work unless specifically assigned

## What Should Not Consume Current Cycles

| Area | Why |
| --- | --- |
| `connectorwebtest`, `connector_deploy`, `workspace` | These look like noise, not leverage |
| local `../TELEGRAM BOT` | Legacy folder with env/db risk; not a clean workspace |
| `chernushoov.github.io` | Outside the current commercial/product focus |
| `../финал/orchestrator` rewrites | Setup-doc artifact, not current product leverage |
| Connector repo unification by guesswork | Too much entropy; needs explicit cleanup mandate |

## Revenue-Nearest Execution Path

1. Recruit Autopilot:
- Use `recruitment-bot` as canonical logic and `../recruit-autopilot-core` as current execution workspace.
- Optimize for pilot readiness, smoke validation, offer packaging, and operator handoff.

2. FloorDSGN:
- Treat `floordsgn-site` + Vercel `floordsgn-site` as the commercial surface.
- Optimize for contact capture, proof packaging, and traffic/conversion QA.

3. Connector Pro:
- Before any sales push, first collapse the source-of-truth problem.
- Do not add feature work into the confusion cluster by default.

## Source-Of-Truth Workspace Rules

| Family | Default Workspace Rule |
| --- | --- |
| Recruit | Work locally in `../recruit-autopilot-core` only for low-conflict execution and docs; treat GitHub `recruitment-bot` as canonical |
| FloorDSGN | Prefer GitHub `floordsgn-site`; use local `../финал/FloorDSGN` only as draft scratch |
| Connector | No default write target without explicit repo choice |
| MeltBot | Prefer repo/deployment inspection over editing local infra folders |
| AI Video | Pick `ai-video-platform` for system work and `ai-video-studio` for UI work; do not mix them casually |
