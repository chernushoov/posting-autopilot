# Demo Path Status

## What Was Fixed
- Verified the exact customer demo path still works end-to-end:
  1. open vacancy
  2. open Facebook Flow
  3. generate post
  4. select groups
  5. create posting run
  6. update queue status
- Re-ran the UI smoke flow on a clean SQLite demo DB and confirmed:
  - generator route loads
  - group selector route loads
  - posting queue route loads
  - post generation returns `200`
  - approve returns `200`
  - posting run creation returns `201`
  - queue status update returns `200`

## What Still Rough
- UI is demo-safe, not polished.
- Group warnings and continuity badges exist but are not critical to the demo.
- No standalone results screen.
- Best demo path is still one vacancy, one approved variant, a few groups, and one queue update.

## Exact Demo Steps
1. Prepare demo data:
   - `python -m scripts.migrate`
   - `python -m scripts.seed`
   - `python -m scripts.fb_group_import scripts/sample_fb_groups.csv --source-label sample_seed`
2. Open the app and log in as `admin / admin123`.
3. Go to `Vacancies`.
4. Pick one vacancy and click `Start FB` or `Resume FB`.
5. On `Post Generator`, click `Generate Variant`.
6. Click `Approve & Select Groups`.
7. On `Group Selector`, load groups, pick 2-3 groups, click `Create Queue`.
8. On `Posting Queue`, click `Open Group`, then `Mark Posted`.
9. If needed for demo, save one result snapshot.

## Validation Note
- Latest validation used:
  - `DATABASE_URL=sqlite:////tmp/recruit_fb_demo_validation.db /tmp/recruit_fb_workflow_venv312/bin/python -m scripts.fb_safe_workflow_ui_smoke`
- Smoke passed on the full demo path with no blocker on the target flow.
