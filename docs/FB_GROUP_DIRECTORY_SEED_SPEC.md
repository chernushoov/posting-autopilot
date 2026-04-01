# FB Group Directory Seed Spec

## Goal
- Seed and maintain 200+ Israeli Facebook recruitment groups for safe manual posting workflows.
- Collection must stay manual or desk-research based.
- No scraping bots or Facebook automation should be used in this seed process.

## CSV Schema

### Required Columns

| Column | Type | Notes |
| --- | --- | --- |
| `group_name` | string | visible group name |
| `facebook_url` | string | full group URL |
| `primary_category` | string | one main category |
| `country_code` | string | default `IL` |
| `language_code` | string | default `he` |
| `source_type` | string | `seed_csv`, `manual_entry`, `ops_review` |
| `import_batch_key` | string | e.g. `il_fb_seed_2026_q2` |
| `verification_status` | string | `verified`, `unverified`, `stale` |

### Recommended Columns

| Column | Type | Notes |
| --- | --- | --- |
| `facebook_slug` | string | if visible |
| `city` | string | `Tel Aviv`, `Haifa`, etc. |
| `region` | string | `Center`, `North`, `South`, `Jerusalem`, `Remote`, `All Israel` |
| `member_count_estimate` | integer | approximate is fine |
| `activity_rating` | integer | `1-5` |
| `audience_type` | string | recruiters, job_seekers, mixed |
| `secondary_tags` | json array or pipe-separated string | see tagging model |
| `posting_rules_summary` | string | one-line operator summary |
| `requires_membership` | boolean | true/false |
| `requires_admin_approval` | boolean | true/false |
| `last_verified_at` | date | ISO format |
| `notes` | string | operator notes |

## JSON Schema

```json
{
  "group_name": "משרות הייטק תל אביב",
  "facebook_url": "https://www.facebook.com/groups/example",
  "facebook_slug": "example",
  "primary_category": "tech",
  "country_code": "IL",
  "language_code": "he",
  "city": "Tel Aviv",
  "region": "Center",
  "member_count_estimate": 85000,
  "activity_rating": 5,
  "audience_type": "mixed",
  "secondary_tags": ["java", "startup", "jobs"],
  "posting_rules_summary": "מותר לפרסם משרות, בלי כפילויות יומיות",
  "requires_membership": true,
  "requires_admin_approval": false,
  "source_type": "seed_csv",
  "import_batch_key": "il_fb_seed_2026_q2",
  "verification_status": "verified",
  "last_verified_at": "2026-03-30",
  "notes": "קבוצה פעילה מאוד בימים א-ה"
}
```

## Quality Criteria
- Group is Israel-relevant.
- Group is job/recruitment relevant.
- Group has visible recent activity within the last 30 days.
- Group allows job-related posting or clearly contains job posts already.
- URL resolves to a real Facebook group.
- Category and geography can be assigned with confidence.

## Tagging Model

### Primary Category
- `tech`
- `finance`
- `sales`
- `customer_service`
- `blue_collar`
- `operations`
- `general_jobs`
- `city_jobs`
- `students_juniors`
- `executive`

### Secondary Tags
- `hebrew`
- `russian`
- `english`
- `tel_aviv`
- `jerusalem`
- `haifa`
- `beer_sheva`
- `center`
- `north`
- `south`
- `remote`
- `startup`
- `recruiters`
- `high_volume`
- `approval_required`

## Exclusion Rules
- Not a Facebook group.
- Obviously unrelated to jobs or recruitment.
- No visible activity in the last 60 days.
- Pure spam group.
- Group explicitly forbids vacancy posting.
- Duplicate of an already-seeded group.
- Broken or inaccessible URL.

## Dedupe Rules
- Primary dedupe key: normalized `facebook_url`.
- Secondary dedupe key: `facebook_slug`.
- Fallback dedupe check: same normalized name + same city/region + same category.
- If duplicates conflict, keep the row with:
- most recent `last_verified_at`
- richer rules/notes
- higher confidence on geography/category

## Maintenance Flow

### Initial Seed
1. Collect candidate groups manually from known recruitment communities, agency lists, search results, and recruiter knowledge.
2. Normalize URLs.
3. Assign category, city/region, and basic rules.
4. Verify minimum relevance/activity.
5. Import as one named batch.

### Weekly Maintenance
1. Review groups used in the last 7 days.
2. Update `last_verified_at` and `activity_rating` if needed.
3. Mark broken or irrelevant groups as `stale` or `blocked`.

### Monthly Maintenance
1. Review top 50 high-performing groups.
2. Review bottom 50 inactive or low-quality groups.
3. Add 10-20 new candidate groups manually.
4. Archive dead duplicates.

## Source Tracking Rules
- Every import must carry one `import_batch_key`.
- Every manually added group must have `source_type=manual_entry`.
- Re-verified records should keep the same group row and update provenance notes, not create duplicates.

## Founder / Ops Collection Checklist
- Validate Israel relevance.
- Confirm job-post suitability.
- Capture city/region.
- Estimate member count.
- Add one-line posting rule note.
- Mark whether membership or approval is required.
