# Case Study Capture Guide

Use `case_study_capture.json` as a daily proof file.

## Update rule
- Fill client and vacancy identity once.
- Update totals every day.
- Add only real observations, real friction, and real objections.
- Do not write marketing copy here.

## Minimum daily update
- totals
- speed fields if new milestones happened
- one line in `what_worked` or `what_failed`
- one line in `manual_steps_required` if the process still needed human help

## Fast rollup
Use:

```bash
python3 scripts/update_case_study_from_tracking.py
```

This pulls totals from:
- `pilot_metrics.csv`
- `candidate_pipeline.csv`

Then updates:
- `case_study_capture.json`
