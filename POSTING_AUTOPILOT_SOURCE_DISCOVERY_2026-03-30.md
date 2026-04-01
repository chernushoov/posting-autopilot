# Posting Autopilot Source Discovery

Date: 2026-03-30

## Goal

Find a trustworthy local source-of-truth for `https://posting-autopilot-next.vercel.app`.

## Workspace Search Executed

### 1. Search by unique live strings

Searched across `/Users/agentmachine/Desktop` and `/Users/agentmachine/Work` for:

- `Seeded demo account`
- `demo@postingautopilot.local`
- `facebook-connect`
- `default_cta`
- `posting_window`
- `notifications_enabled`
- `Step 1 of 5`
- `Ad and destinations`
- `Facebook and Telegram`

### 2. Search for Vercel linkage metadata

Searched for:

- `.vercel/project.json`
- `vercel.json`
- `posting-autopilot-next`
- `posting-autopilot`

## Findings

### No exact local source match found for the live app

The unique strings from the live deploy were only found in the smoke script and launch docs added during this audit.

No separate local repo in the scanned workspace was found that clearly contains:

- the demo login copy
- the `/facebook-connect` flow
- the `/settings` form fields used by the live app

### No local Vercel linkage metadata for Posting Autopilot

Known Vercel-linked repos found in the workspace belong to other projects:

- `moltbot-dashboard`
- `connector-web`
- `ai-video-studio`
- `site` (FloorDSGN prototype)

No `.vercel/project.json` or `vercel.json` in the scanned workspace maps to `posting-autopilot-next`.

### Controlled local app and live app still differ structurally

Controlled local route evidence from the Flask app:

- `/ai/settings`
- no plain `/settings`

Live operator evidence:

- `/settings` is part of the visible operator flow
- `POST /settings` currently fails with `500`

## Practical Meaning

This workspace contains a controlled hardening lane for Recruit Autopilot, but it does not yet prove that this exact repo is the one currently deployed to `posting-autopilot-next.vercel.app`.

Until that mapping is pinned:

- local fixes remain valid as controlled hardening work
- live deploy fixes remain unproven
- launch gate must stay red if live smoke is red

## Recommended Next Action

Before launch, identify the actual repo/branch connected to the Vercel project `posting-autopilot-next`, then port or deploy the reviewed guardrails there and re-run:

```bash
bash scripts/run_prelaunch_front.sh
python3 scripts/final_launch_gate.py
```
