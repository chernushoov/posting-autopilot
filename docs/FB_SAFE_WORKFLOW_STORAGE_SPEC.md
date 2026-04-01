# Facebook Safe Workflow Storage Spec

## Persistence Approach
- Use the existing PostgreSQL + SQLAlchemy stack.
- Keep `company_id` on every new Facebook workflow table.
- Reuse current `vacancies` table without altering its core semantics for MVP.
- Prefer simple nullable columns over premature normalization.

## Tables

### 1. Existing: `vacancies`
- Source of truth for job data.
- MVP may optionally add later derived Facebook counters, but not required now.

### 2. New: `fb_group_sources`

#### Columns
- `id` PK
- `company_id` FK -> `companies.id`
- `source_type` varchar(32) not null
- `source_label` varchar(120) not null
- `import_batch_key` varchar(120) not null
- `collected_by` varchar(120) null
- `collected_at` datetime null
- `verification_status` varchar(32) not null default `unverified`
- `last_verified_at` datetime null
- `raw_source_url` text null
- `notes` text null
- `created_at` datetime not null

#### Indexes
- `(company_id, source_type)`
- `(company_id, import_batch_key)`

### 3. New: `fb_groups`

#### Columns
- `id` PK
- `company_id` FK -> `companies.id`
- `seed_source_id` FK -> `fb_group_sources.id`
- `name` varchar(200) not null
- `facebook_url` text not null
- `facebook_url_normalized` varchar(255) not null
- `facebook_slug` varchar(160) null
- `primary_category` varchar(64) not null
- `secondary_tags_json` text not null default `[]`
- `country_code` varchar(8) not null default `IL`
- `language_code` varchar(16) not null default `he`
- `city` varchar(120) null
- `region` varchar(120) null
- `audience_type` varchar(64) null
- `member_count_estimate` integer null
- `activity_rating` integer null
- `posting_rules_summary` text null
- `requires_membership` boolean not null default `false`
- `requires_admin_approval` boolean not null default `false`
- `performance_score` integer null
- `status` varchar(32) not null default `active`
- `is_active` boolean not null default `true`
- `last_verified_at` datetime null
- `last_posted_at` datetime null
- `notes` text null
- `created_at` datetime not null
- `updated_at` datetime not null

#### Indexes
- unique `(company_id, facebook_url_normalized)`
- `(company_id, primary_category, city)`
- `(company_id, status, is_active)`
- `(company_id, activity_rating)`
- `(company_id, last_posted_at)`

#### Minimal Constraints
- `activity_rating` between `1` and `5` when present
- `member_count_estimate >= 0` when present

### 4. New: `fb_post_variants`

#### Columns
- `id` PK
- `company_id` FK -> `companies.id`
- `vacancy_id` FK -> `vacancies.id`
- `variant_label` varchar(80) not null
- `tone` varchar(32) not null
- `length_mode` varchar(16) not null
- `language_code` varchar(16) not null default `he`
- `headline` varchar(160) null
- `cta_text` varchar(160) null
- `full_text` text not null
- `char_count` integer null
- `status` varchar(16) not null default `draft`
- `generation_source` varchar(32) not null
- `prompt_version` varchar(40) null
- `input_payload_json` text null
- `edited_by_user` boolean not null default `false`
- `approved_at` datetime null
- `approved_by` varchar(120) null
- `notes` text null
- `created_at` datetime not null

#### Indexes
- `(company_id, vacancy_id, created_at desc)`
- `(company_id, vacancy_id, status)`
- `(company_id, tone, length_mode)`

### 5. New: `fb_posting_runs`

#### Columns
- `id` PK
- `company_id` FK -> `companies.id`
- `vacancy_id` FK -> `vacancies.id`
- `post_variant_id` FK -> `fb_post_variants.id`
- `name` varchar(160) null
- `status` varchar(24) not null default `draft`
- `group_count` integer not null default `0`
- `created_by` varchar(120) not null
- `started_at` datetime null
- `completed_at` datetime null
- `last_action_at` datetime null
- `notes` text null
- `created_at` datetime not null

#### Indexes
- `(company_id, vacancy_id, created_at desc)`
- `(company_id, status, created_at desc)`

### 6. New: `fb_posting_queue_items`

#### Columns
- `id` PK
- `company_id` FK -> `companies.id`
- `run_id` FK -> `fb_posting_runs.id`
- `group_id` FK -> `fb_groups.id`
- `position` integer not null
- `status` varchar(24) not null default `pending`
- `opened_at` datetime null
- `copied_at` datetime null
- `posted_at` datetime null
- `skipped_at` datetime null
- `completed_by` varchar(120) null
- `skip_reason` varchar(160) null
- `group_note` text null
- `post_url_manual` text null
- `created_at` datetime not null

#### Indexes
- unique `(run_id, group_id)`
- unique `(run_id, position)`
- `(company_id, status)`
- `(group_id, posted_at desc)`

### 7. New: `fb_posting_results`

#### Columns
- `id` PK
- `company_id` FK -> `companies.id`
- `queue_item_id` FK -> `fb_posting_queue_items.id`
- `result_status` varchar(32) not null default `posted`
- `response_count` integer null
- `cv_count` integer null
- `interview_count` integer null
- `hire_count` integer null
- `quality_score` integer null
- `last_checked_at` datetime null
- `owner_note` text null
- `result_note` text null
- `updated_by` varchar(120) null
- `updated_at` datetime not null

#### Indexes
- unique `(queue_item_id)`
- `(company_id, result_status)`
- `(company_id, updated_at desc)`

#### Minimal Constraints
- counts `>= 0` when present
- `quality_score` between `1` and `5` when present

## Source-Of-Truth Notes

| Entity | Source Of Truth |
| --- | --- |
| Vacancy content | `vacancies` |
| Group directory | `fb_groups` |
| Group provenance | `fb_group_sources` |
| Approved AI/manual post text | `fb_post_variants` |
| Active queue execution state | `fb_posting_queue_items` |
| Latest result snapshot | `fb_posting_results` |

## What Can Stay Simple In MVP
- Store tags in `secondary_tags_json` instead of a join table.
- Store one latest result row per queue item instead of full event history.
- Keep `created_by`, `approved_by`, `updated_by` as string IDs for now.
- Keep performance score as nullable manual/derived field, not a materialized analytics pipeline.
- Keep member count and activity rating manually maintained.

## Recommended ORM Order
1. `FacebookGroupSource`
2. `FacebookGroup`
3. `FacebookPostVariant`
4. `FacebookPostingRun`
5. `FacebookPostingQueueItem`
6. `FacebookPostingResult`

## Migration Read
- This is a clean additive set of tables.
- No destructive migration to current vacancy flow is required.
- The only current-model dependency is `company_id` and `vacancy_id`.
