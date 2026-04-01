# Sunday Ops Command Cheatsheet

## Full prep / start
- `bash scripts/sunday_launch_control.sh`
  Build pack, validate bundle, refresh sources, refresh reports, and build day-close artifacts.

## Mid-day refresh
- `bash scripts/run_ops_refresh.sh`
  Re-ingest responses, sync screening, refresh shortlist, update client progress, and update proof files.

## Mark a real post
- `python3 scripts/mark_source_posted.py --source-name "Recruiter personal Telegram account list" --post-reference "https://t.me/..." --result posted --notes "wave 1"`

## Log a raw candidate response
- `python3 scripts/log_candidate_response.py --source-name "Recruiter personal Telegram account list" --platform telegram --candidate-name "Candidate Name" --telegram-handle "@candidate" --language ru --summary "Interested and available"`

## Log a screening result
- `python3 scripts/log_screening_result.py --candidate-name "Candidate Name" --fit-decision fit --location-answer "Can reach site" --experience-answer "Relevant experience" --legal-answer "Valid work rights" --start-answer "Can start Monday" --schedule-answer "Schedule works" --language-answer "RU" --next-action "handoff to recruiter"`

## Move a candidate manually in the pipeline
- `python3 scripts/advance_candidate_pipeline.py --candidate-name "Candidate Name" --status qualified --fit-decision fit --next-action "handoff to recruiter" --append-note "manual override"`

## Rebuild shortlist and recruiter handoff
- `python3 scripts/promote_shortlist_from_pipeline.py`
- `python3 scripts/generate_recruiter_handoff_batch.py`

## Refresh client-facing summary
- `python3 scripts/generate_client_progress_update.py`

## Check runtime and bundle before launch
- `python3 scripts/validate_ops_contracts.py`
- `python3 scripts/validate_sunday_bundle.py`
- `python3 scripts/sunday_readiness_check.py`
- `bash scripts/runtime_check_with_env.sh --json`
