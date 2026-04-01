# Ecosystem Vercel Map

## Scope And Method
- Team inspected: `chernushoov's projects` (`team_3KWcFv5zUVHA6wb5CROURGTW`)
- Project and deployment state inspected on 2026-03-30
- `web_fetch_vercel_url` was used to confirm what several live surfaces actually render

## Vercel Projects

| Vercel Project | Linked Repo | Likely Role | Status | Latest Evidence | Why It Matters / Does Not Matter | Recommendation | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `moltbot-dashboard` | `moltbot-dashboard` | Internal control plane / bot monitoring dashboard | Production-active | Latest production deployment: 2026-03-27 16:09 UTC; renders full “MoltBot Dashboard” UI | Matters because it is the current ops dashboard for runtime visibility and control | Keep + monitor | High |
| `floordsgn-site` | `floordsgn-site` | Public FloorDSGN marketing site | Production-active | Latest production deployment: 2026-03-27 07:00 UTC; renders full public flooring site | High commercial relevance; clearly current public surface | Keep + monitor | High |
| `connector-web` | Historically `connector-web-test`; most recent deploys came from dirty local PR branches (`pr4/live-wiring-telemetry`) | Connector web demo/app surface | Active but unstable | Latest production deployment: 2026-02-23 23:54 UTC; renders Connector app shell; deployment history mixes GitHub-linked and dirty local branch deploys | Matters because it is the newest Connector web surface, but it is not safe as a clean source of truth | Keep + monitor; do not treat as stable production | High |
| `ai-video-studio` | `ai-video-studio` | Public/private AI video generation UI | Stale-active | Latest production deployment: 2026-02-23 13:17 UTC; renders a video generation UI with prompt, image upload, quality modes, model selector | Still functional-looking, but not on current default business path | Monitor only | High |
| `workspace` | Unknown | Unknown experiment / placeholder | Abandoned or broken | Latest deployment 2026-02-18 19:25 UTC; root URL returns `404 NOT_FOUND` | High confusion, no visible product value | Archive / ignore | High |
| `backup_rezerv` | `connector-free-mvp` | Connector duplicate/backup deployment | Duplicate | Latest production deployment: 2026-02-14 00:04 UTC; renders same Connector shell | It matters only as confusion risk because it appears to be another live Connector surface | Archive after confirming no dependencies | High |
| `site` | `floordsgn-site` | Older duplicate FloorDSGN deployment | Duplicate legacy | Latest production deployment: 2026-02-07 18:47 UTC; renders older FloorDSGN variant | Confusing because it is still live and points to the same product family as `floordsgn-site` | Archive / ignore after link check | High |
| `connector-free-mvp` | `connector-free-mvp` | Early Connector MVP deployment | Duplicate / stale | Only deployment on 2026-01-28 10:56 UTC; renders Connector shell | Adds naming confusion with `backup_rezerv` and `connector-web` | Archive candidate | High |
| `connector_deploy` | Unknown | Empty placeholder | Abandoned | No deployments found | No current operational value | Archive / ignore | High |
| `connectorwebtest` | `connectorwebtest` | Initial Vercel-generated test project | Abandoned test | Latest deployment 2026-01-22 08:32 UTC; renders Connector shell; repo says “Initial commit” from Vercel | Pure noise relative to current business priorities | Archive / ignore | High |

## What The Live Surfaces Actually Show

| Surface | Rendered Result | Read |
| --- | --- | --- |
| `https://moltbot-dashboard-lac.vercel.app` | Full “MoltBot Dashboard” control panel with projects, services, approvals, logs | Active internal ops surface |
| `https://floordsgn-site.vercel.app` | Full Floor.DSGN site with market split, contact CTA, SEO content | Current public site |
| `https://connector-web-six.vercel.app` | Next.js Connector shell with loading state and Connector metadata | Live Connector web surface |
| `https://ai-video-studio-theta.vercel.app` | AI Video Studio generation interface | Live but not current focus |
| `https://workspace-jade-pi.vercel.app` | 404 | Likely abandoned |
| `https://backuprezerv.vercel.app` | Connector shell | Duplicate Connector surface |
| `https://site-mu-six-10.vercel.app` | Older FloorDSGN variant | Duplicate legacy FloorDSGN surface |
| `https://connector-free-mvp.vercel.app` | Connector shell | Duplicate legacy Connector surface |
| `https://connectorwebtest.vercel.app` | Connector shell | Throwaway test surface |

## Keep / Archive Decisions

### Keep And Actively Monitor
- `floordsgn-site`
- `moltbot-dashboard`
- `connector-web`

### Keep But Low-Focus
- `ai-video-studio`

### Archive Candidates
- `backup_rezerv`
- `site`
- `connector-free-mvp`
- `connector_deploy`
- `connectorwebtest`
- `workspace`

## Main Confusion Risks On Vercel
- Connector has three clearly duplicate public-facing shells: `connector-web`, `backup_rezerv`, and `connector-free-mvp`, plus the test project `connectorwebtest`.
- FloorDSGN has one current project (`floordsgn-site`) and one older still-live duplicate (`site`).
- `connector-web` production deployments are not cleanly tied to one GitHub repo; recent deploys came from dirty local PR branches, not a stable branch alias.
