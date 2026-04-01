# Facebook Safe Workflow Implementation Status

## What Was Produced
- `FB_SAFE_WORKFLOW_MVP_BUILD.md`
- `FB_SAFE_WORKFLOW_DATA_MODEL.md`
- `FB_SAFE_WORKFLOW_STORAGE_SPEC.md`
- `FB_SAFE_WORKFLOW_BUILD_ORDER.md`
- `FB_HEBREW_POST_PROMPTS.md`
- `FB_GROUP_DIRECTORY_SEED_SPEC.md`
- this status file

## What Is Immediately Build-Ready
- MVP scope cut for phase 1 and phase 2
- additive storage/table plan aligned to existing `Company` and `Vacancy`
- first-screen build order
- backend-first engineering sequence
- Hebrew generation prompt pack with output contract
- seed schema and maintenance rules for 200+ FB groups

## What Still Needs Manual Founder Input
- final CTA defaults by recruiter segment: DM, comment, WhatsApp, link
- whether client company name may ever appear in generated posts by default
- initial owner for group seed curation
- target first 3 vacancy categories for pilot
- preferred user identifier strategy for `created_by` / `approved_by` / `updated_by`

## Top 5 Next Engineering Actions
1. Add SQLAlchemy models and migration for the 6 new Facebook workflow tables.
2. Implement Hebrew post generation endpoint using the prompt pack and save approved variants.
3. Build group seed import command for CSV/JSON into `fb_group_sources` and `fb_groups`.
4. Build the first 3 MVP screens: Post Generator, Group Selector, Posting Queue.
5. Add basic result upsert flow and show Facebook status on existing vacancy rows.

## Build Read
- Product docs are no longer the blocker.
- The remaining blocker is implementation plus founder decisions on a few defaults.
- Safest immediate implementation path is:
- storage first
- generation second
- queue UI third
- results fourth
