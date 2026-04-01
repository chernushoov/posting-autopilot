# FB Safe Workflow Continuity Status

## Added In This Pass
- Vacancy-level Facebook workflow status on the vacancy list.
- Compact latest-run summary on each vacancy row.
- Predictable quick-resume routing from vacancy context.
- Saved-variant continuity on the Post Generator screen.
- Resume queue shortcut from Group Selector when unfinished work already exists.

## Resume Logic Now
- If a vacancy has an unfinished run with status `draft`, `ready`, or `in_progress`, `Resume FB` jumps directly to the posting queue.
- If no unfinished run exists but an approved variant exists, `Resume FB` jumps to Group Selector with that variant preselected.
- If only a draft variant exists, `Resume FB` jumps back to Post Generator with the latest saved variant loaded.
- If no Facebook workflow data exists, `Resume FB` starts at Post Generator.

## What Operators Can See Now
- A simple FB status badge per vacancy.
- Whether an unfinished run exists.
- Latest run summary with posted / pending / skipped counts when available.
- Latest saved variant summary when no run exists yet.
- Direct links to resume the current queue or reopen generator.

## What Is Still Rough
- No dedicated variant browser beyond recent variants on the generator screen.
- No separate vacancy results screen yet.
- No date formatting polish for latest timestamps.
- No advanced warning badges yet for recent reposts or approval-required groups.

## Recommended Next
1. Add a lightweight recent results block per vacancy.
2. Add warning chips for recent posting / approval-required groups.
3. Add a tiny approved-variants list on Group Selector.
4. Add better human-readable time formatting for latest run activity.

## Changed Files And Why
- [common/fb_safe_workflow.py](/Users/alexey/Desktop/recruit-autopilot-core/common/fb_safe_workflow.py): added vacancy continuity summary builder.
- [app/routes/vacancies.py](/Users/alexey/Desktop/recruit-autopilot-core/app/routes/vacancies.py): injects FB continuity data into vacancy list.
- [app/routes/fb_ui.py](/Users/alexey/Desktop/recruit-autopilot-core/app/routes/fb_ui.py): added resume route and continuity-aware generator/selector loading.
- [app/templates/vacancies.html](/Users/alexey/Desktop/recruit-autopilot-core/app/templates/vacancies.html): vacancy-level FB status, latest run summary, and resume actions.
- [app/templates/fb_post_generator.html](/Users/alexey/Desktop/recruit-autopilot-core/app/templates/fb_post_generator.html): recent variants + continue-from-approved continuity.
- [app/templates/fb_group_selector.html](/Users/alexey/Desktop/recruit-autopilot-core/app/templates/fb_group_selector.html): resume queue shortcut when unfinished run exists.
- [app/static/fb_safe_workflow.js](/Users/alexey/Desktop/recruit-autopilot-core/app/static/fb_safe_workflow.js): initial state hydration for saved variants and continue button behavior.
- [app/static/app.css](/Users/alexey/Desktop/recruit-autopilot-core/app/static/app.css): continuity status badge styling.
