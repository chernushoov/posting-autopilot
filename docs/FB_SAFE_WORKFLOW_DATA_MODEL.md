# Facebook Safe Workflow Data Model

## Model Principles
- `Company` remains the tenant boundary.
- Existing `Vacancy` remains the vacancy source of truth.
- Facebook workflow data is append-light and mutable enough for MVP.
- Queue execution and result tracking are separate concerns.

## Entity 1: Vacancy

### Purpose
- Existing job record used as the source for AI generation and campaign context.

### Source Of Truth
- Existing `vacancies` table.

### Required Fields
- `id`
- `company_id`
- `title`
- `body`
- `language`
- `is_active`

### Optional Fields
- `city`
- `interview_questions_json`

### Relevant Existing Enums
- `Language`: `ru`, `en`, `auto`

### Facebook Workflow Notes
- MVP should derive missing Facebook-specific content from:
- `title`
- `body`
- `city`
- company AI settings

## Entity 2: FacebookGroup

### Purpose
- Directory record for one Facebook recruitment group.

### Required Fields
- `id`
- `company_id`
- `name`
- `facebook_url`
- `facebook_url_normalized`
- `primary_category`
- `country_code`
- `language_code`
- `status`
- `seed_source_id`
- `is_active`
- `created_at`
- `updated_at`

### Optional Fields
- `facebook_slug`
- `city`
- `region`
- `member_count_estimate`
- `activity_rating`
- `audience_type`
- `secondary_tags_json`
- `posting_rules_summary`
- `requires_membership`
- `requires_admin_approval`
- `last_verified_at`
- `last_posted_at`
- `performance_score`
- `notes`

### Status Enum
- `active`
- `paused`
- `archived`
- `blocked`
- `needs_review`

### Relationship Notes
- Belongs to one `Company`
- Belongs to one `FacebookGroupSource`
- Has many `FacebookPostingQueueItem`

## Entity 3: FacebookGroupSource

### Purpose
- Track where a group record came from and when it was last verified.

### Required Fields
- `id`
- `company_id`
- `source_type`
- `source_label`
- `import_batch_key`
- `created_at`

### Optional Fields
- `collected_by`
- `collected_at`
- `verification_status`
- `last_verified_at`
- `raw_source_url`
- `notes`

### Source Type Enum
- `seed_csv`
- `seed_json`
- `manual_entry`
- `customer_import`
- `ops_review`

### Verification Status Enum
- `unverified`
- `verified`
- `stale`
- `rejected`

### Relationship Notes
- Belongs to one `Company`
- Has many `FacebookGroup`

## Entity 4: FacebookPostVariant

### Purpose
- Store one generated or edited Facebook post for a vacancy.

### Required Fields
- `id`
- `company_id`
- `vacancy_id`
- `variant_label`
- `tone`
- `length_mode`
- `language_code`
- `full_text`
- `status`
- `generation_source`
- `created_at`

### Optional Fields
- `headline`
- `cta_text`
- `prompt_version`
- `input_payload_json`
- `char_count`
- `edited_by_user`
- `approved_at`
- `approved_by`
- `notes`

### Status Enum
- `draft`
- `approved`
- `archived`

### Tone Enum
- `professional`
- `casual`
- `urgent`

### Length Mode Enum
- `short`
- `medium`
- `long`

### Generation Source Enum
- `ai`
- `manual`
- `ai_then_edited`

### Relationship Notes
- Belongs to one `Company`
- Belongs to one `Vacancy`
- Can be used by many `FacebookPostingRun`

## Entity 5: FacebookPostingRun

### Purpose
- One recruiter-intended posting session for one vacancy using one approved post.

### Required Fields
- `id`
- `company_id`
- `vacancy_id`
- `post_variant_id`
- `status`
- `group_count`
- `created_by`
- `created_at`

### Optional Fields
- `name`
- `started_at`
- `completed_at`
- `last_action_at`
- `notes`

### Status Enum
- `draft`
- `ready`
- `in_progress`
- `completed`
- `cancelled`

### Relationship Notes
- Belongs to one `Company`
- Belongs to one `Vacancy`
- Belongs to one `FacebookPostVariant`
- Has many `FacebookPostingQueueItem`

## Entity 6: FacebookPostingQueueItem

### Purpose
- One group inside one posting run.

### Required Fields
- `id`
- `company_id`
- `run_id`
- `group_id`
- `position`
- `status`
- `created_at`

### Optional Fields
- `opened_at`
- `copied_at`
- `posted_at`
- `skipped_at`
- `completed_by`
- `skip_reason`
- `group_note`
- `post_url_manual`

### Status Enum
- `pending`
- `current`
- `opened`
- `posted`
- `skipped`
- `failed`

### Relationship Notes
- Belongs to one `Company`
- Belongs to one `FacebookPostingRun`
- Belongs to one `FacebookGroup`
- Has zero or one `FacebookPostingResult`

## Entity 7: FacebookPostingResult

### Purpose
- Latest tracked business outcome for one queue item.

### Required Fields
- `id`
- `company_id`
- `queue_item_id`
- `result_status`
- `updated_at`

### Optional Fields
- `response_count`
- `cv_count`
- `interview_count`
- `hire_count`
- `quality_score`
- `last_checked_at`
- `owner_note`
- `result_note`
- `updated_by`

### Result Status Enum
- `posted`
- `got_responses`
- `got_cvs`
- `interview_scheduled`
- `hired`
- `rejected_by_group`
- `no_signal`

### Relationship Notes
- Belongs to one `Company`
- Belongs to one `FacebookPostingQueueItem`

## Relationship Summary
- `Company` -> many `Vacancy`
- `Company` -> many `FacebookGroupSource`
- `Company` -> many `FacebookGroup`
- `Vacancy` -> many `FacebookPostVariant`
- `Vacancy` -> many `FacebookPostingRun`
- `FacebookPostVariant` -> many `FacebookPostingRun`
- `FacebookPostingRun` -> many `FacebookPostingQueueItem`
- `FacebookGroup` -> many `FacebookPostingQueueItem`
- `FacebookPostingQueueItem` -> zero/one `FacebookPostingResult`
