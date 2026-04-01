# FB Safe Workflow UI Status

## Built In This Pass
- Added a vacancy entrypoint into the Facebook workflow from the existing vacancy list.
- Added the first clickable Post Generator UI.
- Added the first clickable Group Selector UI.
- Added the first clickable Posting Queue UI.
- Added minimal client-side wiring to the existing `/api/fb/*` backend endpoints.

## Clickable Flow Now
1. Open [Vacancies](/Users/alexey/Desktop/recruit-autopilot-core/app/templates/vacancies.html) in the web app.
2. Click `Facebook Flow` on a vacancy.
3. Generate one or more draft variants and approve one.
4. Land in Group Selector, load/filter/select groups.
5. Create a posting run.
6. Land in Posting Queue, copy post text, open group, mark posted or skipped, and save a result snapshot.

## What Works Now
- Vacancy-driven entry into the FB workflow
- Draft generation and draft list in UI
- Editable selected variant with approve action
- Group loading and multi-select
- Posting run creation
- Queue display and queue item actions
- Result snapshot save from queue UI
- UI smoke path is scriptable through `python -m scripts.fb_safe_workflow_ui_smoke`

## Validation Snapshot
- Vacancy list route loaded and exposed the `Facebook Flow` entrypoint.
- Post Generator page loaded and called the generation endpoint successfully.
- Approved variant flow worked from UI route context.
- Group Selector page loaded and posting run creation returned `201`.
- Posting Queue page loaded and queue item actions returned `200`.
- Result snapshot save returned `200`.
- No Facebook automation was added; the UI only supports copy/open/manual-status workflow.

## Stubbed / Rough
- Variant history is page-session oriented; there is no dedicated saved-variants browser yet.
- Group filtering is practical but still basic.
- Queue does not yet have pause/resume affordances beyond reopening the queue URL.
- No dedicated results screen or vacancy badges yet.
- No visual Facebook feed mock beyond text preview.

## Next Recommended UI Work
1. Add vacancy-level FB status badges and recent run links on the vacancy list.
2. Add a saved approved variants list per vacancy.
3. Improve queue row warnings for `last_posted_at` and approval-required groups.
4. Add a simple vacancy results view.
5. Polish copy/feedback states for smoother demo handling.

## Changed Files And Why
- [app/routes/fb_ui.py](/Users/alexey/Desktop/recruit-autopilot-core/app/routes/fb_ui.py): new UI blueprint for Post Generator, Group Selector, Posting Queue pages.
- [app/routes/__init__.py](/Users/alexey/Desktop/recruit-autopilot-core/app/routes/__init__.py): registered the new UI blueprint.
- [app/templates/vacancies.html](/Users/alexey/Desktop/recruit-autopilot-core/app/templates/vacancies.html): added `Facebook Flow` entrypoint.
- [app/templates/_layout.html](/Users/alexey/Desktop/recruit-autopilot-core/app/templates/_layout.html): added a scripts block for page-level JS.
- [app/templates/fb_post_generator.html](/Users/alexey/Desktop/recruit-autopilot-core/app/templates/fb_post_generator.html): first generator UI.
- [app/templates/fb_group_selector.html](/Users/alexey/Desktop/recruit-autopilot-core/app/templates/fb_group_selector.html): first group selector UI.
- [app/templates/fb_posting_queue.html](/Users/alexey/Desktop/recruit-autopilot-core/app/templates/fb_posting_queue.html): first posting queue UI.
- [app/static/fb_safe_workflow.js](/Users/alexey/Desktop/recruit-autopilot-core/app/static/fb_safe_workflow.js): minimal API wiring and page behavior.
- [app/static/app.css](/Users/alexey/Desktop/recruit-autopilot-core/app/static/app.css): workflow layout and state styling.
- [scripts/fb_safe_workflow_ui_smoke.py](/Users/alexey/Desktop/recruit-autopilot-core/scripts/fb_safe_workflow_ui_smoke.py): repeatable UI route + workflow smoke validation.
