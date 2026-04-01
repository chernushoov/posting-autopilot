# Source Execution Sheet Logic

Use `source_execution_plan.csv` as the live Sunday source sheet.

## Classifications
- `telegram bot-ready`
  RecruitBot can post or support the flow if bot access and apply path are healthy.
- `telegram userbot-only`
  Posting requires a personal Telegram account; RecruitBot does not automate this path.
- `telegram manual-only`
  Posting is manual and source-specific.
- `facebook pages`
  Manual posting from a page.
- `facebook groups assisted/manual`
  Manual or assisted posting into groups.
- `blocked / invalid`
  Do not rely on this source until the blocker is cleared.

## Status values
- `ready_now`
- `needs_quick_setup`
- `blocked`
- `ignore_for_now`

## Sunday rule
Only post to sources marked `ready_now` first.
Then clear `needs_quick_setup`.
Do not treat `blocked` as usable.
