# Recovered Live Source Notes

- deployment: `dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo`
- project: `posting-autopilot-next`
- recovery source: Vercel deployment file API
- recovered files: `25`

## What This Proves

- The live production deploy was a separate Flask app snapshot under `src/`.
- The current `recruit-autopilot-core` working tree is not the same codebase shape as the live deployment.
- The live operator routes really do exist in recovered source:
  - `/login`
  - `/facebook-connect`
  - `/ads/new`
  - `/schedule`
  - `/history`
  - `/settings`

## Root Cause

Recovered `src/app/routes.py` matches the Vercel error:

- `settings()` commits, closes the SQLAlchemy session, and only then reads `user.full_name`
- that value is written into `session["user_name"]`
- after `db.commit()`, the ORM instance is expired; after `db.close()`, it is detached
- the response path therefore crashes with `DetachedInstanceError`

Exact failing line in the recovered snapshot:

- [routes.py](</Users/agentmachine/Desktop/recruit-autopilot-core/ops/prelaunch_artifacts/recovered_live_source/dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo/src/app/routes.py:331>)

## Hotfix Artifact

- minimal patch: [LIVE_SETTINGS_HOTFIX_2026-04-25.patch](</Users/agentmachine/Desktop/recruit-autopilot-core/ops/prelaunch_artifacts/recovered_live_source/dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo/LIVE_SETTINGS_HOTFIX_2026-04-25.patch>)

## Secondary Risk

The same detached-object pattern exists earlier in `login()`:

- query user
- `db.close()`
- then read `user.full_name`

It is not failing in the current smoke run, but it is the same unsafe pattern and the patch artifact hardens that path too.
