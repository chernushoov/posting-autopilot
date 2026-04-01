# Posting Autopilot Pre-Launch Plan

Date: 2026-03-30

## Current Launch Verdict

The live deploy is good enough for a guided demo flow, but not ready for a clean production launch.

What is already proven on the live app:

- demo login works
- protected pages redirect to login when unauthenticated
- `Connect -> Create -> Schedule -> History -> Settings` is a real working flow
- ad creation works
- schedule creation works
- history updates work

What is still blocking launch confidence:

1. The exact source-of-truth repo/branch for `posting-autopilot-next` is not yet pinned down from the local workspace.
2. The controlled local codebase had unsafe launch defaults around campaigns and source testing.
3. Runtime/deploy hardening still needs a final pass before a public launch.

## What Was Executed Now

### 1. Campaign guardrails

Implemented in:

- [app/routes/campaigns.py](/Users/agentmachine/Desktop/recruit-autopilot-core/app/routes/campaigns.py)
- [app/templates/campaign_new.html](/Users/agentmachine/Desktop/recruit-autopilot-core/app/templates/campaign_new.html)

Added:

- required active vacancy check
- required active source selection
- safe interval range validation
- active hour inputs
- weekday selection
- max-posts-per-day input
- safer toggle-start validation
- operator feedback messages

### 2. Source guardrails

Implemented in:

- [app/routes/sources.py](/Users/agentmachine/Desktop/recruit-autopilot-core/app/routes/sources.py)
- [app/templates/sources.html](/Users/agentmachine/Desktop/recruit-autopilot-core/app/templates/sources.html)

Added:

- Telegram ref format validation
- duplicate source error path
- explicit message after add/check/test actions
- required confirmation before live test send
- required source check before live test send
- clearer status labels so stub checks do not look fully production-ready

### 3. Scheduler/runtime safety

Implemented in:

- [worker/run_scheduler.py](/Users/agentmachine/Desktop/recruit-autopilot-core/worker/run_scheduler.py)
- [worker/tasks.py](/Users/agentmachine/Desktop/recruit-autopilot-core/worker/tasks.py)

Added:

- ignore invalid `interval_minutes <= 0`
- respect active hours
- respect selected weekdays
- respect max-posts-per-day limit
- clearer source check messages

## Validation Performed

Confirmed live deploy behavior:

- login works
- create ad works
- schedule run works
- history update works

Confirmed local controlled code:

- `python3 -m py_compile app/routes/campaigns.py app/routes/sources.py worker/run_scheduler.py worker/tasks.py`
- container app import works through `create_app()`
- guardrail test in container:
  - bad campaign config now blocked
  - source test now requires explicit confirmation

## Exact Next Actions In Order

### P0 — Pin the real deploy source

Before launch, identify exactly which local repo/branch maps to `posting-autopilot-next.vercel.app`.

Reason:

- right now the live deploy and the controlled local codebase do not fully match
- without this, any fix may land in the wrong place

### P1 — Apply the new guardrails to the real deploy source

If the live deploy source is this repo, deploy these changes next.

If not, port the same changes into the real source repo before any public launch.

### P2 — Re-run the live launch flow on staging or preview

Required smoke path:

1. login
2. connect
3. create ad
4. create schedule
5. update history
6. save settings
7. verify no unsafe live-send path is exposed by accident

### P3 — Tighten runtime/deploy readiness

Before launch:

- confirm `.env.runtime` handling is consistent
- confirm bot health cannot report green while degraded
- move the web service off dev-style serving if this is going beyond pilot/demo use
- confirm restart policy for bot/worker/scheduler is intentional

### P4 — Final launch gate

Only call the app launch-ready when all are true:

- source-of-truth repo is known
- deployed build matches reviewed code
- campaign/source guardrails are live
- runtime health signal is trustworthy
- one full guided smoke pass succeeds on the deployed environment
- `python3 scripts/final_launch_gate.py` returns green

## Short Operator Summary

Right now:

- the product is not broken
- the core demo flow works
- the biggest remaining risk is not “feature missing”
- the biggest remaining risk is launch ambiguity and unsafe operator defaults

That ambiguity is now reduced in the controlled codebase.
The next move is to line up the real deploy source and push the guarded version.

## Update After Final Gate Wiring

The branch now has a machine-readable final gate:

```bash
python3 scripts/final_launch_gate.py
```

Current result is still red because:

- local runtime is green
- local guardrails are green
- live deploy smoke still fails on `POST /settings`
- local repo still does not prove it is the source for the current Vercel deploy
