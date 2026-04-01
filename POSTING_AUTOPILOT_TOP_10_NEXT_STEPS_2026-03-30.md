# Posting Autopilot Top 10 Next Steps

Date: 2026-03-30

This is the ordered work front from now until launch.

## 1. Pin the real deploy source

Status: blocked outside this repo

Find the exact repo/branch connected to `posting-autopilot-next.vercel.app`.

Why it matters:

- without this, reviewed fixes cannot be claimed as live fixes
- launch remains red even if the controlled repo is green

## 2. Fix live `/settings` save on the real deploy

Status: blocked until source-of-truth is pinned

Current live blocker:

- `POST /settings` returns `500`

Use:

- `bash scripts/live_settings_probe.sh`

## 3. Align route families between controlled code and live app

Status: blocked until source-of-truth is pinned

Current mismatch:

- controlled repo uses `/ai/settings`
- live app uses `/settings`

## 4. Move the reviewed guardrails into the real deploy source

Status: ready after steps 1-3

Port or deploy the already-reviewed local changes for:

- campaign creation
- source validation
- source test confirmation
- scheduler active window safety
- daily cap safety

## 5. Keep one canonical launch verdict

Status: completed

Use:

- `python3 scripts/final_launch_gate.py`

This is now the machine-readable launch gate.

## 6. Capture live blocker evidence automatically

Status: completed

Use:

- `bash scripts/live_settings_probe.sh`

This captures the current live `500` failure on `/settings` with headers and body.

## 7. Persist every launch check as an artifact

Status: completed

Use:

- `python3 scripts/write_launch_gate_snapshot.py`
- `bash scripts/run_launch_release_pack.sh`

This prevents drift and “I think it was green” mistakes.

## 8. Keep runtime and local guardrails green while the live fix is pending

Status: in progress

Keep re-running:

- `bash scripts/runtime_check_with_env.sh --json`
- `bash scripts/compose_with_runtime.sh exec -T web python scripts/launch_guardrail_check.py`

## 9. Re-run full live smoke only after the real deploy is updated

Status: pending

Canonical command:

- `bash scripts/run_prelaunch_front.sh`

## 10. Only launch after both fronts are green

Status: pending

Do not call launch-ready until both are true:

- local controlled repo is green
- live deployed app is green

Final required signal:

- `python3 scripts/final_launch_gate.py` returns `overall_status = green`
