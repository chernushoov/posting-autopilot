# Demo Path Status

## What Was Fixed
- Main sign-in is no longer a dead end: `/login` accepts email/password users and still preserves legacy admin login by username.
- Team access now works for sub-users: owner/admin can add members from Profile, and members can enter the same company workspace safely.
- `/settings` now lands on the company profile settings instead of a missing route.
- New vacancy creation now redirects to the vacancy detail page with clear next actions: add destinations or create the first pilot run.
- Campaign creation now has practical empty states for missing vacancies, missing destinations, and no ready destinations.
- Ready destinations are preselected for the first pilot run to reduce operator guesswork.
- `Run now` no longer crashes the UI when Redis/worker is unavailable; it records failed attempts and shows a clear queue error.

## Still Rough
- Team invite is local password based; email invite, password reset, and magic-link onboarding are not implemented yet.
- Billing/trial copy exists, but full paid checkout/live subscription verification still needs a separate pass.
- Real posting still depends on Redis and worker being healthy; no autoposting or browser automation was added.
- UI is product-safe and demoable, but not yet polished to top-tier SaaS onboarding quality.

## Exact Demo Steps
1. Open `/register`, create an owner account, and land on `/dashboard`.
2. Open `/profile/`, add a teammate if sub-user access needs to be shown.
3. Open `/vacancies/new`, create a vacancy.
4. On the vacancy detail page, click `Add destinations`.
5. Add one Facebook assisted/manual destination with a direct group URL, or a ready Telegram destination.
6. Open `/campaigns/new`; confirm the ready destination is already selected.
7. Create the pilot run.
8. Open `/campaigns/` and click `Run now`.
9. If Redis/worker is running, the posting cycle queues. If not, the app stays alive and shows a clear queue-unavailable message.

## Validation
- `python3 -m py_compile app/auth.py app/routes/registration.py app/routes/auth_routes.py app/routes/companies.py app/routes/profile.py app/routes/__init__.py app/schema.py app/routes/campaigns.py app/routes/vacancies.py worker/queue.py`
- `git diff --check`
- SQLite smoke passed on Python 3.12 with forced unavailable Redis:
  - signup
  - dashboard
  - campaign empty state
  - vacancy creation
  - vacancy next actions
  - destination creation
  - campaign creation
  - graceful queue failure with failed `PostingAttempt`
