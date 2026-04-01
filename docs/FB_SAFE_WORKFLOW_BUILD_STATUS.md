# FB Safe Workflow Build Status

## Implemented In This Pass
- Added SQLAlchemy models for:
- `fb_group_sources`
- `fb_groups`
- `fb_post_variants`
- `fb_posting_runs`
- `fb_posting_queue_items`
- `fb_posting_results`
- Added migration/init command: `python -m scripts.migrate`
- Added seed import command: `python -m scripts.fb_group_import scripts/sample_fb_groups.csv`
- Added JSON API backbone under `/api/fb/*`
- Added reusable smoke test: `python -m scripts.fb_safe_workflow_smoke`

## Working Now
- New Facebook workflow tables can be created on a clean DB.
- CSV or JSON group seed files can be imported with dedupe and import reporting.
- Vacancy input can generate structured Hebrew post output for:
- `professional`
- `casual`
- `urgent`
- Generation supports:
- `short`
- `medium`
- `long`
- Generated variants can be saved as `draft` or `approved`.
- Approved variants can be used to create posting runs and ordered queue items.
- Queue items can be moved through:
- `opened`
- `posted`
- `skipped`
- `failed`
- Latest result snapshot can be stored per queue item.

## Validation Snapshot
- `python -m scripts.migrate` creates all 6 FB tables cleanly.
- `python -m scripts.fb_group_import scripts/sample_fb_groups.csv --source-label sample_seed` imported `2/2` rows with `0` errors on validation DB.
- `python -m scripts.fb_safe_workflow_smoke` completed:
- generate post `200`
- approve variant `200`
- create posting run `201`
- mark posted `200`
- upsert result `200`
- smoke result state: `approved` variant, run `in_progress`, result `got_cvs`

## Stubbed / Lean By Design
- AI provider remains stub-backed inside the repo; prompt pack is implemented but no external provider call is wired.
- No Facebook automation or browser posting logic was added.
- No UI screens were added in this pass.
- No advanced vacancy analytics or summary badges were added yet.

## Recommended Next
1. Build the Post Generator UI on top of `POST /api/fb/post-variants/generate`.
2. Build Group Selector UI on top of `GET /api/fb/groups` and `POST /api/fb/posting-runs`.
3. Build Posting Queue UI on top of `GET /api/fb/posting-runs/:id` and queue item actions.
4. Add small vacancy-level FB status badges derived from posting runs/results.
5. Replace stub generation with a real Hebrew-capable provider only when founder is ready for provider wiring.
