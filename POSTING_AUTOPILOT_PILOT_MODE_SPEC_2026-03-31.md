# Posting Autopilot Pilot Mode Spec

## 1. Exact Interpretation Of The Pilot Mission

Deliver one real pilot workflow for daily operator use over several weeks:

1. create one live vacancy
2. prepare one final posting asset from that vacancy
3. choose destinations for:
   - Telegram
   - Facebook
4. execute the safest practical posting path:
   - Telegram = actual working posting path
   - Facebook = assisted/manual path unless safe real automation already exists
5. log every action and result per destination
6. make status/history understandable from one operator flow
7. remove or hide unfinished paths that distract from this pilot

The pilot is not a redesign and not a general platform build.
The pilot is one reliable operator workflow with one live vacancy.

## 2. Exact List Of Files / Modules To Change

Primary data model and state:
- `app/models.py`

Vacancy flow:
- `app/routes/vacancies.py`
- `app/templates/vacancy_new.html`
- `app/templates/vacancies.html`

Destination/source flow:
- `app/routes/sources.py`
- `app/templates/sources.html`

Pilot execution flow:
- `app/routes/campaigns.py`
- `app/templates/campaign_new.html`
- `app/templates/campaigns.html`

Operator layout / navigation:
- `app/templates/_layout.html`

Posting execution and safety:
- `worker/tasks.py`
- `worker/run_scheduler.py`

Queue entrypoints if needed for explicit pilot actions:
- `worker/queue.py`

Optional but still inside pilot scope if needed for clarity:
- `app/routes/analytics.py`
- `app/templates/analytics.html`

Do not treat these as primary for this pilot:
- `app/routes/ai_settings.py`
- `app/templates/ai_settings.html`
- `app/routes/candidates.py`

## 3. Exact Implementation Order

1. Extend the data model for pilot logging and explicit posting status.
2. Tighten vacancy creation so the live vacancy contains operator-ready posting fields.
3. Convert Sources into a real destination screen for pilot use:
   - Telegram destinations
   - Facebook assisted destinations
4. Convert Campaigns into one pilot execution screen:
   - final posting asset
   - selected destinations
   - publish now / schedule
   - status visibility
5. Update worker posting logic:
   - Telegram actual post path
   - Facebook assisted/manual action path
   - per-destination logging
6. Hide or de-emphasize unfinished/non-pilot routes in the operator UI.
7. Add one short repeated test checklist and one run path.

## 4. Exact UI / API / Logic Changes

### Data model

Add explicit pilot posting entities or fields in `app/models.py`:

- `Vacancy` must gain:
  - `employment_type`
  - `salary_or_pay`
  - `schedule_summary`
  - `apply_path`
  - `contact_name`
  - `contact_phone`
  - `posting_asset_text`
  - `posting_asset_title`
- `Source` must gain:
  - `platform` with values:
    - `telegram`
    - `facebook`
  - `destination_kind` with values:
    - `group`
    - `channel`
    - `page`
    - `marketplace`
  - `destination_ref`
  - `destination_label`
  - `posting_mode` with values:
    - `auto`
    - `assisted_manual`
  - `is_ready`
  - `readiness_note`
- Add a new posting log model, for example `PostingAttempt`, with:
  - `id`
  - `company_id`
  - `vacancy_id`
  - `campaign_id`
  - `source_id`
  - `platform`
  - `destination`
  - `asset_title`
  - `action_taken`
  - `status`
  - `error_message`
  - `operator_notes`
  - `created_at`
  - `updated_at`

### Vacancy UI

In `app/routes/vacancies.py` and `app/templates/vacancy_new.html`:

- turn vacancy creation into a pilot-ready posting asset form
- required fields:
  - title
  - city
  - body
  - salary/pay
  - schedule
  - apply path / contact
- generate/store one final posting asset text
- remove dependence on AI settings for the pilot path

### Sources / destinations UI

In `app/routes/sources.py` and `app/templates/sources.html`:

- rename the screen meaning from “Sources” to practical “Destinations”
- separate destination rows by platform:
  - Telegram
  - Facebook
- allow operator to mark Facebook destinations as:
  - assisted/manual
- explicitly show:
  - platform
  - destination type
  - destination label
  - readiness
  - posting mode
- add clear destination states:
  - ready
  - needs_check
  - manual_only
  - blocked

Important rule:
- Telegram can use the actual working bot path
- Facebook must not pretend to be full automation if that is unsafe
- for Facebook pilot mode, the product must prepare final content, destination context, and logging, then require operator confirmation

### Campaign / pilot execution UI

In `app/routes/campaigns.py`, `app/templates/campaign_new.html`, and `app/templates/campaigns.html`:

- reduce this to one understandable pilot execution flow
- one campaign should represent one live vacancy posting workflow
- show:
  - linked vacancy
  - final posting text
  - selected Telegram destinations
  - selected Facebook destinations
  - mode per destination
  - publish now / schedule
- prevent immediate “start” if:
  - no ready Telegram destination exists
  - no destination is selected
  - vacancy lacks required posting fields
- for Facebook assisted/manual destinations:
  - create log row with `manual_action_required`
  - show exact posting text and destination label
  - allow operator to mark:
    - `posted`
    - `failed`
    - `blocked_or_suspected`
  - require operator note on failure/block

### Worker logic

In `worker/tasks.py` and `worker/run_scheduler.py`:

- Telegram path:
  - only post to Telegram sources where:
    - `platform=telegram`
    - `posting_mode=auto`
    - `is_ready=true`
  - create one `PostingAttempt` per destination
  - log success/failure explicitly
- Facebook path:
  - do not auto-post unless a truly safe implemented path already exists
  - default pilot behavior must be:
    - create a `PostingAttempt`
    - set status to `manual_action_required`
    - store prepared content and destination
    - wait for operator status update
- scheduler must only run pilot-ready destinations
- daily cap logic must be destination-aware and actually enforced
- do not let inactive vacancies continue posting

### Operator clarity

In `app/templates/_layout.html`:

- de-emphasize or hide unfinished paths not needed for pilot:
  - AI
  - analytics-heavy side paths
  - anything that distracts from:
    - vacancy
    - destinations
    - campaign/pilot run
    - history/log
- make the pilot flow obvious in the nav order

## 5. Exact Statuses And Logging Structure

Allowed statuses only:
- `pending`
- `scheduled`
- `manual_action_required`
- `posted`
- `failed`
- `blocked_or_suspected`

Every posting attempt log row must include:
- timestamp
- platform
- destination
- vacancy / posting asset id
- action taken
- result status
- error message
- operator notes

Recommended mapping:
- Telegram queued but not executed yet: `pending`
- Telegram planned for later: `scheduled`
- Facebook operator handoff item: `manual_action_required`
- actual success confirmed: `posted`
- delivery or action failed: `failed`
- destination risky / suspected / platform warning: `blocked_or_suspected`

Action values should stay concrete:
- `telegram_post_attempt`
- `facebook_manual_prepare`
- `facebook_manual_confirm_posted`
- `facebook_manual_confirm_failed`
- `facebook_manual_blocked`

## 6. Exact Acceptance Criteria

The pilot is done only if all of these are true:

1. One real live vacancy can be created in the product with all required posting fields.
2. The operator can prepare one final posting asset from that vacancy.
3. The operator can choose Telegram and Facebook destinations explicitly.
4. Telegram posting is actually usable through the working path.
5. Facebook is handled in the safest realistic way:
   - assisted/manual if full automation is unsafe or unfinished
6. Every posting attempt creates a visible log entry per destination.
7. Every failure is visible in the product.
8. The operator can tell the difference between:
   - pending
   - scheduled
   - manual_action_required
   - posted
   - failed
   - blocked_or_suspected
9. The UI no longer pushes the operator into unfinished side paths.
10. The operator can run this daily for several weeks without confusion.

## 7. Final Command Sequence To Run And Verify The Pilot

Local verification after implementation:

```bash
cd /Users/agentmachine/Desktop/recruit-autopilot-core
python3 -m py_compile app/routes/vacancies.py app/routes/sources.py app/routes/campaigns.py worker/tasks.py worker/run_scheduler.py app/models.py
bash scripts/compose_with_runtime.sh up -d postgres redis web worker scheduler bot
bash scripts/compose_with_runtime.sh logs --tail=80 web worker scheduler bot
```

Operator pilot verification sequence:

1. Open `Vacancies`
2. Create one real construction vacancy with:
   - title
   - city
   - body
   - salary/pay
   - schedule
   - apply path
3. Open `Destinations`
4. Add/select:
   - one Telegram destination marked ready
   - one Facebook destination marked assisted/manual
5. Open `Campaigns`
6. Create one campaign for that vacancy
7. Confirm final posting asset preview
8. Run:
   - Telegram destination through actual post path
   - Facebook destination through assisted/manual path
9. Open campaign/history/log view
10. Verify every destination has a log row and a final visible status

Minimal daily pilot loop:

```bash
cd /Users/agentmachine/Desktop/recruit-autopilot-core
bash scripts/compose_with_runtime.sh logs --tail=50 scheduler worker bot
python3 scripts/runtime_check.py
```
