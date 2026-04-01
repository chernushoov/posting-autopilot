# Posting Autopilot Detailed Pilot Test Report

Date: 2026-03-30

## Scope

This pilot used only safe validation paths:

- local runtime and guardrails
- live operator flow probes against `https://posting-autopilot-next.vercel.app`
- multilingual bot/screening validation for `ru`, `he`, `en`

No risky Facebook posting action was executed from the real page because the current reliable automation path for the Facebook-authenticated browser session is not yet established from this workspace and the goal was to avoid account or page friction.

## What Was Tested

### 1. Launch gate

Command:

```bash
python3 scripts/final_launch_gate.py
```

Result:

- runtime: yellow
- local guardrails: green
- multilingual pilot: green
- live smoke: red
- source alignment: red
- overall launch gate: red

### 2. Live settings save path

Commands:

```bash
bash scripts/live_settings_probe.sh
python3 scripts/live_settings_matrix_probe.py
```

Result:

- simple live probe confirms `POST /settings -> 500`
- granular matrix confirms the same `500` for every tested payload

Tested payload classes:

- full payload
- `full_name` only
- `timezone` only
- `default_cta` only
- `posting_window` only
- `notifications_enabled` only
- small combinations

Conclusion:

- this is not a single bad field
- the live `/settings` save path itself is broken

### 3. Multilingual bot/screening pilot

Command:

```bash
python3 scripts/multilingual_pilot_check.py
```

Result:

- overall: green
- `ru/he/en` translation coverage: complete
- language detection mapping: correct
- default screening questions: present in all 3 languages
- rule-based positive answers score above negative answers in all 3 languages
- prompt builder includes the correct target language context

### 4. Independent agent review

Two separate audit agents reviewed the evidence after the pilot run:

- live operator/frontend audit confirmed that `/settings` is a real live blocker and not a single bad-field case
- runtime/readiness audit confirmed that multilingual synthetic coverage is green, but also forced the launch gate to start surfacing multilingual readiness explicitly

Those audits were used to tighten the final gate and the final report, not to replace the direct evidence.

## Pilot Verdict By Area

### Runtime / local core

Status: green

What is proven:

- local runtime is up
- bot/worker/scheduler/web are running
- launch guardrails are active in the controlled repo

### Live operator path

Status: red

What is proven:

- login page works
- demo login works
- facebook-connect step is reachable
- live settings save is broken

### Multilingual readiness

Status: green

What is proven:

- `ru`, `he`, and `en` screening texts are present
- language fallback logic behaves predictably
- multilingual scoring sanity-check passes

## Errors Found During Testing

### 1. Live deploy `/settings` is broken

Severity: high launch blocker

Evidence:

- `bash scripts/live_settings_probe.sh`
- `python3 scripts/live_settings_matrix_probe.py`

Current behavior:

- any tested `POST /settings` payload returned `500`

### 2. Local test harness bug found and fixed

Severity: low

Issue:

- first version of `live_settings_matrix_probe.py` returned `status_code=0` because Python SSL verification failed in this environment

Fix applied immediately:

- switched the probe to an explicit HTTPS handler for this diagnostic path

After fix:

- matrix probe now returns real HTTP status codes and confirms the repeated live `500`

### 3. Launch gate was too optimistic about warnings and languages

Severity: medium

Issue:

- runtime warnings were still showing as `green`
- multilingual readiness was not included in the machine-readable gate

Fix applied immediately:

- `final_launch_gate.py` now marks runtime with warnings as `yellow`
- `multilingual_pilot_check.py` is now included in the machine-readable gate

### 4. OpenAI scoring prompt did not enforce output language

Severity: medium

Issue:

- the OpenAI scoring path accepted `lang` but did not explicitly require the summary to be returned in that language

Fix applied immediately:

- updated `common/ai.py` so the scoring prompt now instructs the model to return the summary in the requested language

## Current Blockers To Real Launch

1. Exact source repo/branch for `posting-autopilot-next` is still not pinned from this workspace
2. Live `POST /settings` is broken regardless of payload
3. Because of source mismatch, the controlled repo fixes cannot yet be claimed as live deploy fixes

## Current Safe Next Actions

1. Keep the controlled repo as the hardening lane
2. Use `python3 scripts/final_launch_gate.py` as the top-level verdict
3. Use `python3 scripts/live_settings_matrix_probe.py` as the live settings incident proof
4. Port the already-reviewed local guardrails into the real deploy source once identified
5. Re-run the full pilot pack only after the live deploy is updated

## Canonical Commands

```bash
python3 scripts/final_launch_gate.py
bash scripts/live_settings_probe.sh
python3 scripts/live_settings_matrix_probe.py
python3 scripts/multilingual_pilot_check.py
bash scripts/run_detailed_pilot_pack.sh
```
