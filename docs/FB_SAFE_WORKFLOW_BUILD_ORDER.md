# Facebook Safe Workflow Build Order

## Build Goal
- Reach a demoable and pilot-usable workflow with the fewest moving parts:
- existing vacancy -> Hebrew post -> selected groups -> queue -> posted/result status

## Screens To Build First

### 1. Post Generator
- Must do:
- load one existing vacancy
- choose tone and length
- generate Hebrew text
- allow manual edit
- approve and save one variant
- Can be stubbed:
- Facebook feed preview can be simple text card
- regenerate history can be omitted

### 2. Group Selector
- Must do:
- load active groups
- filter by category, city, activity
- select groups
- create run + queue items
- warn on recent posting to same group
- Can be stubbed:
- recommendation ranking can start as simple sort by `activity_rating desc, last_posted_at asc`
- bulk import button can be hidden

### 3. Posting Queue
- Must do:
- show approved text
- copy to clipboard
- open current group link
- mark posted
- skip with reason
- persist progress
- Can be stubbed:
- keyboard shortcuts
- per-group post variant override

## Existing Screens To Reuse First
- Reuse current vacancy list as the vacancy picker.
- Do not block MVP on a custom Dashboard.
- Do not block MVP on the full Results screen.

## First-Version Screen Order

| Order | Screen | Why |
| --- | --- | --- |
| 1 | Post Generator | unlocks AI output and approved post persistence |
| 2 | Group Selector | unlocks queue creation |
| 3 | Posting Queue | unlocks the real operator loop |
| 4 | Results View | unlocks business outcome tracking |
| 5 | Group Directory admin | improve maintenance and seed operations |
| 6 | Dashboard | useful only after workflow data exists |

## v1 Exclusions
- Custom Dashboard
- Group detail drill-down
- team management
- advanced analytics
- billing
- automated recommendations beyond simple heuristics

## Engineering Order

### Milestone 0: Foundation
1. Add new ORM models and migrations for Facebook workflow tables.
2. Add seed import path for `fb_group_sources` and `fb_groups`.
3. Add backend service that maps existing `Vacancy` -> generation input payload.

### Milestone 1: Backend Core
1. `POST /api/fb/post-variants/generate`
2. `POST /api/fb/post-variants/:id/approve`
3. `GET /api/fb/groups`
4. `POST /api/fb/posting-runs`
5. `GET /api/fb/posting-runs/:id`
6. `POST /api/fb/queue-items/:id/mark-posted`
7. `POST /api/fb/queue-items/:id/skip`
8. `POST /api/fb/results/:queue_item_id`

### Milestone 2: First UI
1. Add `Distribute -> Facebook Groups` action from vacancy list/detail.
2. Build Post Generator screen.
3. Build Group Selector screen.
4. Build Posting Queue screen.

### Milestone 3: Basic Tracking
1. Build simple Results table by vacancy.
2. Show FB posting state on vacancy rows.
3. Update `fb_groups.last_posted_at` and simple `performance_score` hooks.

### Milestone 4: Operator Polish
1. Resume unfinished queue.
2. CSV seed import UI or admin command.
3. Minimal dashboard cards.

## Recommended Backend First Tasks
- Model classes + migration
- normalized group URL helper
- Hebrew generation service wrapper
- queue creation service
- queue status transition service
- result upsert service

## Recommended Frontend First Tasks
- vacancy action entrypoint
- post generation form
- group selection table
- queue runner page
- results table

## Integration Order
1. Existing vacancy -> generation endpoint
2. Generation endpoint -> approved post variant save
3. Approved post variant -> selected groups -> posting run
4. Posting run -> queue item transitions
5. Queue item -> result upsert
6. Result upsert -> vacancy/group summary badges

## First Manual Test Flow
1. Use an existing vacancy from the current vacancy list.
2. Generate a Hebrew `medium` `professional` post.
3. Edit and approve the post.
4. Select 5 seeded groups.
5. Create queue.
6. Copy/open/mark first 2 groups as posted.
7. Skip 1 group with reason.
8. Re-open queue and verify progress persisted.
9. Record result snapshot for one posted item: `got_cvs`, `cv_count=2`.

## Demoable Output By Milestone

| Milestone | Demo Result |
| --- | --- |
| M0 | Seeded groups exist, models exist |
| M1 | API-only end-to-end workflow works via curl/Postman |
| M2 | Recruiter can run the core posting workflow in UI |
| M3 | Recruiter can see tracked outcome and vacancy FB status |
| M4 | Pilot operator can use system daily with less friction |
