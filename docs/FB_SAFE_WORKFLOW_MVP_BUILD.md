# Facebook Safe Workflow MVP Build

## Pilot-Critical MVP

### Core Outcome
- Make one recruiter complete this flow safely in one session:
- select existing vacancy
- generate Hebrew post
- approve/edit post
- select Facebook groups
- create posting queue
- copy/open/mark posting steps
- track basic outcome

### Must-Have Now
- Use existing `Company` and `Vacancy` as source of truth.
- Add Facebook group directory with manual seed/import.
- Add Hebrew AI post generation for one vacancy at a time.
- Save approved post variant before queue creation.
- Allow group filtering by category, city, activity, status.
- Create posting queue with ordered queue items.
- Support queue actions: `copy post`, `open group`, `mark posted`, `skip`.
- Persist latest result status per posted group.
- Show basic per-vacancy Facebook status: not posted / queued / posted / got CVs / hired.

### Should-Have Next
- Recommended groups for a vacancy.
- Multiple post variants per vacancy.
- Manual quality score per group.
- Resume unfinished queue.
- Bulk group import from CSV.
- Results table by vacancy and by group.
- Simple daily dashboard cards.

### Later
- Team seats and recruiter ownership.
- Billing and usage limits.
- Advanced analytics and charts.
- A/B testing of post variants.
- Group contribution workflow for agencies.
- Facebook Page posting via official API where compliant.

## Explicit v1 Exclusions
- No automatic Facebook posting.
- No browser automation or scripted interaction with Facebook.
- No scraping-based group discovery inside the product.
- No full analytics dashboard.
- No seat management.
- No billing/paywall.
- No mobile-first optimization beyond workable responsive layout.
- No post scheduling.

## MVP Phase Split

### Phase 1
- Vacancy -> AI post -> group selection -> queue -> mark posted
- Group seed import and basic admin CRUD
- Latest result snapshot per queue item

### Phase 2
- Better results view
- Suggested groups
- Reusable post variants
- Group performance scoring
- Dashboard summary

## MVP Acceptance Criteria
- Recruiter can start from an existing vacancy and produce an approved Hebrew post in under 2 minutes.
- Recruiter can select 10 groups and create a queue in under 1 minute.
- Queue state survives refresh/reopen.
- Every group action is persisted with timestamp and note.
- Recruiter can later record `responses`, `CVs`, and `hired` outcome for each posted group.

## Pilot Scope Boundary

### Included In Pilot
- One company account
- One recruiter operator flow
- Seeded 200+ Israeli FB groups
- Hebrew post generation with 3 tone variants
- Manual posting workflow with copy/open/mark
- Basic result tracking

### Not Required For Pilot Start
- Perfect performance scoring
- Deep historical reporting
- Full permission matrix
- Marketplace-grade onboarding

## Lean MVP Read
- Reuse the current vacancy list and tenant model.
- Build only the screens that unblock the operator path.
- Keep all Facebook interaction outside the app except opening links and recording outcomes.
