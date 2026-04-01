# Posting Autopilot Final Verification Report

Date: 2026-03-30

## Canonical Commands Run

```bash
bash scripts/run_prelaunch_front.sh
python3 scripts/final_launch_gate.py
```

## Actual Results

### 1. Runtime health

- status: green
- summary: `6/6 containers running: postgres, redis, web, worker, scheduler, bot | web :8080`
- note: runtime still reports one bot warning line, but no hard blocker

### 2. Local guardrails

- status: green
- verified:
  - campaigns require at least one active source
  - unsafe interval values are rejected
  - invalid Telegram refs are rejected
  - source test requires explicit confirmation

### 3. Live deploy smoke

- status: red
- live URL: `https://posting-autopilot-next.vercel.app`
- passed:
  - login page available
  - demo login works
  - facebook connect page reachable
- failed:
  - `POST /settings` returns `500`

Observed response:

```text
HTTP/2 500
content-type: text/html; charset=utf-8
server: Vercel
```

### 4. Source alignment

- status: red
- evidence:
  - controlled local Flask app exposes `/ai/settings`
  - controlled local Flask app does not expose plain `/settings`
  - live Vercel deploy operator flow uses `/settings`
  - no Vercel linkage metadata is present in this repo

## Final Gate Output

`python3 scripts/final_launch_gate.py` currently returns:

- `overall_status = red`
- `launch_ready = false`

Current blockers:

1. `settings save failed with status 500`
2. `local app exposes /ai/settings while live deploy operator flow uses /settings`
3. `local repo has no Vercel linkage metadata for posting-autopilot-next`
4. `live /settings save fails with 500 while controlled local settings flow is a different route family`

## Launch Decision

### Allowed now

- guarded local hardening
- runtime validation
- guided demo with caution
- internal review

### Not allowed now

- production launch
- claiming the live deploy has the reviewed fixes
- treating the local repo as proven source-of-truth for the Vercel app

## Required Next Actions

1. Pin the real deploy source repo/branch
2. Move the reviewed guardrails into that real deploy source
3. Fix live `/settings` save path
4. Re-run:
   - `bash scripts/run_prelaunch_front.sh`
   - `python3 scripts/final_launch_gate.py`
5. Only call the app launch-ready after both commands go green
