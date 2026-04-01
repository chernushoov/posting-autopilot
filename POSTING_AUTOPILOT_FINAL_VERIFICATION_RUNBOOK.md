# Posting Autopilot Final Verification Runbook

## Goal

Run one canonical sequence before launch so the operator can verify:

- runtime health
- local safety guardrails
- live deploy smoke flow

## Canonical Sequence

### 1. Runtime health

```bash
bash scripts/runtime_check_with_env.sh --json
```

Expected:

- all required services up
- no hard runtime blocker

### 2. Local guardrail check

```bash
bash scripts/compose_with_runtime.sh exec -T web python scripts/launch_guardrail_check.py
```

Expected:

- campaigns reject unsafe config
- sources reject invalid refs
- test send requires explicit confirmation

### 3. Live deploy smoke

```bash
bash scripts/live_deploy_smoke.sh https://posting-autopilot-next.vercel.app
```

Expected:

- demo login works
- settings save works
- ad creation works
- schedule creation works
- history update works

### 4. One-command front

```bash
bash scripts/run_prelaunch_front.sh
```

Use this as the final compact launch check.

### 5. Machine-readable launch gate

```bash
python3 scripts/final_launch_gate.py
```

Use this when you need one final verdict that separates:

- local runtime health
- local guardrail health
- multilingual bot readiness
- live deploy smoke
- source-of-truth alignment

### 6. Persisted release-pack artifacts

```bash
bash scripts/run_launch_release_pack.sh
```

This writes machine-readable launch artifacts under:

- `ops/prelaunch_artifacts/launch_gate`
- `ops/prelaunch_artifacts/live_settings_probe`

### 7. Detailed pilot pack

```bash
bash scripts/run_detailed_pilot_pack.sh
```

This extends the release-pack with:

- granular `/settings` payload matrix
- multilingual bot pilot checks for `ru/he/en`

## Interpretation

### Green

- runtime check passes
- local guardrail check passes
- live deploy smoke passes

### Yellow

- runtime is healthy
- local guardrails pass
- live smoke partially passes but source-of-truth or deploy mismatch still exists

### Red

- runtime fails
- guardrail check fails
- live deploy smoke breaks in the main operator flow
- source alignment is still unresolved

## Current Practical Rule

Do not call the app launch-ready until the live deploy source is known and the guarded code path is what is actually deployed.

Current branch-level launch status is tracked in [POSTING_AUTOPILOT_LAUNCH_GATE_STATUS_2026-03-30.md](./POSTING_AUTOPILOT_LAUNCH_GATE_STATUS_2026-03-30.md).
