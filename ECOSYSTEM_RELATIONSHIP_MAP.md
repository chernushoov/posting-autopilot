# Ecosystem Relationship Map

## Repo To Product Mapping

### MeltBot / Local-Core / Dashboard
- Confirmed repo: `moltbot-dashboard`
- Related local workspaces: `../strategist`, `../финал/orchestrator`
- Role split:
- `moltbot-dashboard` = visible control plane and dashboard surface
- `strategist` = local multi-agent runtime / recruiting automation concept stack
- `orchestrator` = older setup and launch docs for autonomous agent workflows

### Recruit Autopilot Bot
- Confirmed repo: `recruitment-bot`
- Related local workspace: `../recruit-autopilot-core`
- Related risky legacy folder: `../TELEGRAM BOT`
- Read:
- GitHub repo is the likely canonical commercial product repo
- current local repo is a working execution copy without `.git` metadata
- legacy `TELEGRAM BOT` folder is not a safe source of truth

### Connector Pro
- Confirmed repos:
- `connector-pro`
- `connector-web-test`
- `connector-free-mvp`
- `connectorwebtest`
- Related local workspace:
- `../connector-web`
- Vercel projects:
- `connector-web`
- `backup_rezerv`
- `connector-free-mvp`
- `connectorwebtest`
- `connector_deploy`
- Read:
- this is the highest-entropy family
- multiple repos and deployments render nearly the same shell
- `connector-web-test` has the clearest structured repo surface
- `../connector-web` is explicitly labeled as a backup copy, not a primary repo

### AI Video Platform
- Confirmed repos:
- `ai-video-platform`
- `ai-video-studio`
- Vercel project:
- `ai-video-studio`
- Read:
- `ai-video-platform` is the broader Docker multi-service stack
- `ai-video-studio` is the Vercel-facing UI layer

### FloorDSGN
- Confirmed repo: `floordsgn-site`
- Related local workspace: `../финал/FloorDSGN`
- Vercel projects:
- `floordsgn-site`
- `site`
- Read:
- `floordsgn-site` is the current public source of truth
- `site` is an older duplicate deployment
- local `../финал/FloorDSGN` is an uncommitted draft workspace, not canonical

## Repo To Deployment Mapping

| Product | Repo | Vercel Project | Mapping Status | Read |
| --- | --- | --- | --- | --- |
| MeltBot | `moltbot-dashboard` | `moltbot-dashboard` | Confirmed | Deployment metadata directly names the repo |
| Recruit Autopilot | `recruitment-bot` | None found | Confirmed no Vercel surface in inspected team | Current execution appears local/runtime-first |
| FloorDSGN | `floordsgn-site` | `floordsgn-site` | Confirmed | Clean `main` branch deploy history |
| FloorDSGN | `floordsgn-site` | `site` | Confirmed duplicate | Older duplicate deployment of same repo |
| Connector | `connector-web-test` | `connector-web` | Partially confirmed | Older deploys directly reference `connector-web-test` |
| Connector | dirty local PR branch | `connector-web` | Confirmed for latest deploys | Recent production deploys came from `pr4/live-wiring-telemetry`, not a clean GitHub branch link |
| Connector | `connector-free-mvp` | `backup_rezerv` | Confirmed | Deployment metadata names `connector-free-mvp` |
| Connector | `connector-free-mvp` | `connector-free-mvp` | Confirmed | Early direct deployment |
| Connector | `connectorwebtest` | `connectorwebtest` | Confirmed | Pure Vercel-generated test project |
| AI Video | `ai-video-studio` | `ai-video-studio` | Confirmed | Deployment metadata directly names the repo |
| AI Video | `ai-video-platform` | none found | Confirmed within inspected Vercel team | Broader system repo does not have a same-name Vercel project here |

## Source Of Truth Candidates

| Family | Best Current Source Of Truth | Why | What Is Not Source Of Truth |
| --- | --- | --- | --- |
| Recruit Autopilot | `recruitment-bot` | Rich operator/runbook/docs surface and recent activity | local `../recruit-autopilot-core` until git linkage is restored; `../TELEGRAM BOT` |
| FloorDSGN | GitHub `floordsgn-site` + Vercel `floordsgn-site` | Cleanest repo-deploy alignment and active public surface | local `../финал/FloorDSGN`; Vercel `site` |
| Connector | None fully clean | Repo and deployment lineage are split across multiple variants | `../connector-web`, `backup_rezerv`, `connectorwebtest`, `connector_deploy` |
| MeltBot | `moltbot-dashboard` for dashboard surface | Only clean repo-to-deploy pair found | `../strategist` and `../финал/orchestrator` as authoritative app repos |
| AI Video | `ai-video-platform` for full stack; `ai-video-studio` for UI | Clean product split between platform and studio UI | assuming the Vercel UI repo alone covers the whole system |

## Duplicate / Stale Confusion Points

### Connector Confusion Cluster
- `connector-web-test` and `connectorwebtest` are different repos with almost the same meaning.
- `connector-web`, `backup_rezerv`, and `connector-free-mvp` all render Connector shells.
- local `../connector-web` is a backup copy linked to `backup_rezerv`, not clearly to `connector-web`.
- Recent `connector-web` production deployments came from dirty local branches, which breaks clean provenance.

### FloorDSGN Duplicate
- `floordsgn-site` is current.
- `site` is an older duplicate still live on Vercel.
- local `../финал/FloorDSGN` has no commit history and should not be treated as canonical.

### Recruit Autopilot Split
- local `../recruit-autopilot-core` is active and usable.
- GitHub source appears to be `recruitment-bot`.
- There is no clean git linkage in the current local folder, so merge-readiness must be handled carefully.

### MeltBot / Local-Core Split
- The dashboard is clearly repo-backed.
- The runtime/orchestration folders on disk are not cleanly repo-backed in the current machine state.

## Active Execution Lanes That Matter

### Lane A: Revenue-Near Product Work
- Recruit Autopilot pilot readiness
- FloorDSGN lead generation and contact funnel conversion

### Lane B: Ops / Control Plane
- MeltBot dashboard monitoring and safe control-plane visibility

### Lane C: Cleanup Before Re-Engagement
- Connector source-of-truth cleanup
- duplicate deployment retirement

### Lanes To Avoid By Default
- deep infra surgery in local-core / strategist / orchestration folders
- security/auth remediation overlap
- Connector rewrites before lineage cleanup
