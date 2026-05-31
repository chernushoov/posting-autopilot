# Posting Autopilot Source Discovery

Date: 2026-03-30

Update: 2026-04-25

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

### Local repo lineage is now partially pinned

The controlled local repo is linked to:

- GitHub: `https://github.com/chernushoov/posting-autopilot.git`

So this repo is part of the Posting Autopilot lineage.

### Vercel production is real, but the current live snapshot is CLI-deployed

Production metadata for `posting-autopilot-next` now confirms:

- Vercel project exists and is reachable from the local machine
- framework preset: `Flask`
- current production deployment id: `dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo`
- deployment source: `cli`

This matters because it means the current production build was uploaded from a local CLI snapshot, not cleanly pinned to the current Git-tracked tree.

### Exact live deployment source has now been recovered from Vercel

Using the Vercel deployment file API, the exact production file tree for deployment `dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo` was recovered into:

- `ops/prelaunch_artifacts/recovered_live_source/dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo/`

Recovered live snapshot structure includes:

- `src/app/routes.py`
- `src/app/models.py`
- `src/app/auth.py`
- `src/app/templates/settings.html`
- `src/app/templates/facebook_connect.html`
- `src/requirements.txt`

This proves the live Flask app is a smaller, separate source tree than the current `recruit-autopilot-core` working tree.

### No exact local git-linked source match found for the live app

Even after recovery, no separate local repo in the scanned workspace was found that clearly contains the same git-linked source tree as the live deployment. The recovered source came from Vercel deployment files, not from a local `.vercel/project.json` or matching tracked repo.

The old unique strings from the live deploy were only found in probe artifacts and launch docs until the deployment file recovery step.

The current controlled workspace still does not contain a git-tracked tree that clearly contains:

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
- `POST /settings` persists values but currently returns `500`

### Exact live `/settings` root cause is now known

Fresh Vercel production logs show the failing path precisely:

- route: `/settings`
- method: `POST`
- status: `500`
- file: `/var/task/app/routes.py`
- line: `331`
- failing statement: `session["user_name"] = user.full_name`
- exception: `sqlalchemy.orm.exc.DetachedInstanceError`

Practical interpretation:

- the settings write is succeeding
- the response path crashes afterwards while reading `user.full_name` from a detached SQLAlchemy instance
- the bug is no longer a vague “save failed”; it is a post-save session/ORM lifecycle bug in the live deploy snapshot

## Practical Meaning

This workspace contains a controlled hardening lane for Recruit Autopilot, and we now know it belongs to the right GitHub lineage.

We also now have the exact production code snapshot recovered locally from Vercel deployment files.

But the deployment is still not pinned to a trustworthy git-linked source of truth, because the live deployment source is `cli` and the recovered tree does not map cleanly onto the current tracked repo layout.

Until that mapping is pinned:

- local fixes remain valid as controlled hardening work
- live deploy fixes can now be prepared against the recovered snapshot
- production ownership is still fragile until a reviewed tree replaces the ad hoc CLI snapshot
- launch gate must stay red if live smoke is red

## Recommended Next Action

Before launch, do one of these deliberately:

1. Apply the recovered hotfix to the recovered snapshot and redeploy it intentionally.
2. Promote a reviewed source tree to become the new authoritative production source, then port the recovered live behavior into that source and deploy it explicitly.

Current recovered hotfix artifact:

- `ops/prelaunch_artifacts/recovered_live_source/dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo/LIVE_SETTINGS_HOTFIX_2026-04-25.patch`

After that, re-run:

```bash
bash scripts/run_prelaunch_front.sh
python3 scripts/final_launch_gate.py
```
