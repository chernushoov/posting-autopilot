# Posting Autopilot Launch Gate Status

Date: 2026-03-30

## Current Verdict

Launch gate is **RED**.

The controlled local codebase is in much better shape than before launch prep, but the live deploy still fails a core operator action and the deploy source remains unresolved from this workspace.

## What Is Green

### 1. Runtime

- `6/6` containers running
- bot, worker, scheduler, web, redis, postgres all up
- current runtime summary:
  - `6/6 containers running: postgres, redis, web, worker, scheduler, bot | web :8080`

### 2. Local launch guardrails

Verified by:

```bash
bash scripts/compose_with_runtime.sh exec -T web python scripts/launch_guardrail_check.py
```

Current result:

- campaigns reject missing sources
- campaigns reject unsafe interval values
- source creation rejects invalid Telegram refs
- source test requires explicit live-send confirmation

### 3. Scheduler/runtime safety

The controlled code now respects:

- active hours
- selected weekdays
- max posts per day
- safe interval validation

## What Is Red

### 1. Live deploy smoke

Verified by:

```bash
bash scripts/live_deploy_smoke.sh https://posting-autopilot-next.vercel.app
```

Current result:

- login page works
- demo login works
- facebook-connect step works
- `POST /settings` fails with `500`

Exact live failure:

```text
FAIL settings save failed with status 500
```

### 2. Source-of-truth mismatch

The local controlled app does **not** expose the same settings route family as the live deploy.

Local route evidence:

- `/ai/settings`
- no plain `/settings` route in the controlled Flask app

Live deploy evidence:

- operator flow uses `/settings`
- that live settings save currently fails with `500`

This means we still do **not** have a trustworthy one-to-one mapping between the reviewed local code and the app currently deployed at `posting-autopilot-next.vercel.app`.

## Launch Gate Logic

### Green requires all of the following

- runtime health passes
- local guardrail check passes
- live smoke passes
- reviewed local source is confirmed to be the actual deploy source

### Current reality

- runtime: green
- local guardrails: green
- live smoke: red
- source alignment: red

## Exact Blockers

1. `POST /settings` on the live deploy returns `500`
2. exact deploy source repo/branch is still not pinned from this workspace
3. because of that mismatch, local fixes cannot yet be claimed as live deploy fixes

## Practical Launch Stance

### Allowed now

- guided demo
- controlled internal review
- local/runtime verification
- guarded code review in the controlled repo

### Not allowed yet

- clean public launch
- calling the live deploy production-ready
- assuming the reviewed local code is already what Vercel is running

## Next Actions In Order

1. Keep using the controlled repo as the hardening lane
2. Use `python3 scripts/final_launch_gate.py` as the machine-readable launch verdict
3. Identify the exact repo/branch for `posting-autopilot-next`
4. Apply the reviewed guardrails to that real deploy source
5. Re-run:
   - `bash scripts/run_prelaunch_front.sh`
   - `python3 scripts/final_launch_gate.py`
6. Only flip the launch gate when both local and live are green
