# Pilot Tracking Guide

Use `pilot_metrics.csv` during Sunday execution.

## Logging rule
- Log one row per source action or meaningful update.
- Use `activity_type` to keep the sheet readable.
- Keep metrics as delta updates for that row, not vague notes.

## Suggested activity_type values
- `post_batch`
- `response_update`
- `screening_update`
- `interview_update`
- `daily_rollup`

## Minimum discipline
- Every post must create a row.
- Every meaningful response update must create or update a row.
- End the day with a `daily_rollup` row.
