# Production Promotion 2026-05-08

- promoted_at: `2026-05-08T23:31Z`
- project: `posting-autopilot-next`
- production_url: `https://posting-autopilot-next.vercel.app`
- production_runtime_url: `https://posting-autopilot-next-qx3zhu7f4-chernushoovs-projects.vercel.app`
- inspect_url: `https://vercel.com/chernushoovs-projects/posting-autopilot-next/DKgMXyh2PTejnwLTj7vSmh8B4Zwo`

## Promotion metadata

- `source=recovered-live-hotfix`
- `base_deployment=dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo`
- `fix=audit-2026-05-08-no-5xx-on-bad-input`
- `audit_session=2026-05-08-claude-opus47`

## Audit motivation

Operator instruction was to crawl the live site as a logged-in user (with the seeded TG/FB profiles), find every UI/logic inconsistency, fix them, and gate the redeploy on tests turning green. The audit was performed with a session-cookie crawl through `/`, `/login`, `/facebook-connect`, `/settings`, `/ads/new`, `/schedule`, `/history`, `/logout`, plus hostile-input POSTs.

Audit captured at `/tmp/posting-audit-2026-05-08/` (`page_*.html`, `extract.py`, `audit.txt`).

## Bugs fixed

| ID | Class | Endpoint | Symptom before | Fix |
| --- | --- | --- | --- | --- |
| B1 | 5xx | `POST /schedule` | `int(request.form.get("ad_id"))` raised `TypeError`/`ValueError` for empty or non-numeric ad_id → 500 | Wrap in try/except, render schedule with inline error "Select an ad first." |
| B2 | 5xx | `POST /schedule` | `datetime.fromisoformat(start_at_raw)` raised `ValueError` for malformed dates → 500 | Wrap in try/except, render with "Start time must be a valid date/time (YYYY-MM-DDTHH:MM)." |
| B10 | 5xx | `POST /ads/new` | `[int(g) for g in getlist("group_ids")]` raised `ValueError` for non-numeric group ids → 500 | Iterate with try/except per id, drop non-numeric values, then re-validate "at least one destination". |
| B6 | UX | `GET /schedule` | Hardcoded `value="2026-03-30T10:00"` in template — past date by default, looked like dead form | Compute `default_start_at = now+1h` rounded to next 5-min slot in route, pass to template. Error-path renders share the same default. |
| B4 | UX | `GET /history?status=…` | Unknown status filter silently returned 0 rows | Validate against `HistoryStatus` enum; on unknown value, drop the filter and flash a warning so the operator knows their input was ignored. |
| B5 | UX | `POST /history/<id>/status` | Non-existent / not-yours item silently 302→/history with success flash | If item not found OR new status not in `HistoryStatus` enum, flash explicit error; legitimate updates flash success as before. |
| — | hardening | `POST /schedule` | `cadence` was free-form text, anything was saved verbatim | Validate against `{daily, weekdays, manual_review}`, fall back to `daily` for unknown values. |

## What was NOT changed

- The seeded demo flow (visible `demo@postingautopilot.local` / `demo123` on /login) is intentional for the MVP demo path; it stays.
- `/` → `/facebook-connect` redirect is intentional for the MVP shape (no separate dashboard yet).
- The Facebook "connect" form is a manual stub (no real OAuth), unchanged.

## Verification

Both suites green against `https://posting-autopilot-next.vercel.app` after this deploy:

- `bash scripts/live_deploy_smoke.sh` → 8/8 PASS — `SMOKE OK`
- `bash scripts/live_bad_input_smoke.sh` → 20/20 PASS, **zero 5xx on hostile input**

Before this deploy, `live_bad_input_smoke.sh` reported 4 of 20 as 5xx (the schedule and ads/new ValueError paths above).

## Files changed in the snapshot

- `src/app/routes.py` (tracked) — 61 insertions, 19 deletions: validation + render_form helper + cadence enum + history filter validation + history status enum guard.
- `src/app/templates/schedule.html` (was untracked, now tracked): replaced hardcoded `2026-03-30T10:00` with `{{ default_start_at or '' }}`.

## Files changed outside the snapshot

- `scripts/live_deploy_smoke.sh` — case-insensitive `grep -iEq "^location: …"` so the suite passes against both Vercel (lowercase) and Werkzeug local (capital `Location:`). Same coverage, no behaviour change against live.
- `scripts/live_bad_input_smoke.sh` (new) — 20-case 5xx-resistance suite. Designed to run against the same `BASE_URL` as `live_deploy_smoke.sh`. Expectation: every case is 2xx (inline error) or 3xx (redirect with flashed error); a 5xx anywhere fails the suite.

## Deploy command used

```
NODE_EXTRA_CA_CERTS=/etc/ssl/cert.pem vercel deploy --prod --yes \
  -m source=recovered-live-hotfix \
  -m base_deployment=dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo \
  -m fix=audit-2026-05-08-no-5xx-on-bad-input \
  -m audit_session=2026-05-08-claude-opus47
```

`NODE_EXTRA_CA_CERTS=/etc/ssl/cert.pem` was needed because the bundled Node 22 in this iMac's vercel CLI v50.18.2 install does not see the macOS keychain CAs by default and otherwise fails with `unable to get local issuer certificate` on `api.vercel.com`. Documented here so future redeploys don't have to rediscover it.
