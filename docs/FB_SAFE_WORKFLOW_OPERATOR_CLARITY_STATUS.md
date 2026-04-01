# FB Safe Workflow Operator Clarity Status

## Added In This Pass
- Compact vacancy-level Facebook results block with latest run outcome context.
- Lightweight latest-signal and note visibility on the vacancy list.
- Warning chips in Group Selector and Posting Queue.
- Human-friendly relative time labels for key workflow timestamps.

## What Operators Can See Now
- Whether the latest run is complete or still needs attention.
- Posted / pending / skipped counts from the latest run.
- Latest signal such as `Got CVs` when a result snapshot exists.
- Latest short note from result or operator context when available.
- Group-level warnings like:
- `recently posted here`
- `repost risk`
- `approval likely`
- `low activity`
- `already in unfinished run`

## Human-Friendly Context Added
- Vacancy list now shows the latest run activity in relative time.
- Group Selector shows `last posted` in readable relative form.
- Posting Queue shows run status, last activity, and group `last posted` context.

## What Is Still Rough
- No standalone results page yet.
- Warning chips are intentionally simple and rules-based.
- Time labels are relative but not localized by user timezone yet.
- No richer performance rollups or charts.

## Recommended Next
1. Add a tiny vacancy-level recent results drawer or inline expand block.
2. Show approval-required and repost-risk warnings before queue creation as a small summary.
3. Add a compact results history list for the latest run.

## Changed Files And Why
- [common/fb_safe_workflow.py](/Users/alexey/Desktop/recruit-autopilot-core/common/fb_safe_workflow.py): added run/result summaries, warning-chip derivation, and human-friendly time labels.
- [app/routes/fb_ui.py](/Users/alexey/Desktop/recruit-autopilot-core/app/routes/fb_ui.py): passes existing unfinished-run group ids into Group Selector.
- [app/templates/vacancies.html](/Users/alexey/Desktop/recruit-autopilot-core/app/templates/vacancies.html): shows compact vacancy-level FB results context.
- [app/templates/fb_group_selector.html](/Users/alexey/Desktop/recruit-autopilot-core/app/templates/fb_group_selector.html): hydrates existing-run group ids for warnings.
- [app/templates/fb_posting_queue.html](/Users/alexey/Desktop/recruit-autopilot-core/app/templates/fb_posting_queue.html): added queue context and signal area.
- [app/static/fb_safe_workflow.js](/Users/alexey/Desktop/recruit-autopilot-core/app/static/fb_safe_workflow.js): renders warning chips and human-friendly time/status cues.
- [app/static/app.css](/Users/alexey/Desktop/recruit-autopilot-core/app/static/app.css): styles for chips and notes.
