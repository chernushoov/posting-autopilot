# RecruitBot Sunday Prep

This folder is the working pack for one live client vacancy with a target of 4 hires.

## Files
- `vacancy_intake_client.md`
  Copy-paste this to the client to collect the vacancy facts fast.
- `CLIENT_MESSAGE_TEMPLATES.md`
  Ready messages for client intake, missing fields, and launch confirmation.
- `CLIENT_APPROVAL_TEMPLATE.md`
  Fast approval message for the final vacancy text before posting.
- `scripts/generate_client_approval_packet.py`
  Builds a ready approval packet from the current vacancy intake.
- `vacancy_intake_template.json`
  Operator version of the intake. Fill this after the client replies.
- `candidate_pipeline.csv`
  Manual candidate pipeline for Sunday if responses come in before the full bot flow is healthy.
- `CANDIDATE_PIPELINE_GUIDE.md`
  Rules for using the manual candidate pipeline without losing people.
- `raw_response_intake.csv`
  First landing sheet for manual inbound responses.
- `RAW_RESPONSE_INTAKE_GUIDE.md`
  Rules for logging raw inbound candidate responses.
- `scripts/ingest_raw_responses.py`
  Moves raw inbound responses into the candidate pipeline.
- `scripts/log_candidate_response.py`
  One-command logger for a fresh candidate response before the refresh cycle.
- `manual_screening_answers.csv`
  Structured answers for manual or assisted screening.
- `MANUAL_SCREENING_ANSWERS_GUIDE.md`
  How to use the manual screening answer sheet.
- `scripts/sync_screening_to_pipeline.py`
  Syncs manual screening outcomes back into the candidate pipeline.
- `scripts/log_screening_result.py`
  One-command logger for a completed screening result.
- `scripts/advance_candidate_pipeline.py`
  Safe CLI helper for moving one candidate through the manual pipeline without opening the CSV by hand.
- `CANDIDATE_MESSAGE_TEMPLATES.md`
  Short manual messages for first reply, screening, pass, reject, and handoff.
- `CANDIDATE_FOLLOWUP_TEMPLATES.md`
  Short reminders and follow-up messages for incomplete or stalled candidates.
- `qualified_candidates_shortlist.csv`
  Recruiter-facing shortlist of strong candidates.
- `QUALIFIED_CANDIDATE_SHORTLIST_GUIDE.md`
  Rules for moving candidates from pipeline to shortlist.
- `scripts/promote_shortlist_from_pipeline.py`
  Moves strong candidates from pipeline into the shortlist file.
- `scripts/generate_recruiter_handoff_batch.py`
  Builds one ready handoff batch from the shortlist.
- `QUALIFICATION_SCORECARD.md`
  Fast scoring rule for deciding fit without long debates.
- `candidate_scorecard_template.json`
  Optional per-candidate scorecard if the case needs clearer fit notes.
- `RECRUITER_HANDOFF_TEMPLATE.md`
  Short handoff text for moving a qualified candidate to the recruiter.
- `interview_followup_log.csv`
  One simple place to track interviews and follow-ups.
- `POSTING_COPY_PACK.md`
  Ready templates for Telegram, Facebook, and Facebook groups.
- `SCREENING_PACK.md`
  Final short screening questions and fast-reject rules.
- `source_execution_plan.csv`
  Sunday source sheet with honest readiness status.
- `first_wave_source_roster.csv`
  Operational roster for the exact first posting wave.
- `SOURCE_OWNER_MESSAGE_TEMPLATES.md`
  Short outreach messages for group owners or source admins.
- `SOURCE_EXECUTION_SHEET.md`
  How to classify and use sources on Sunday.
- `scripts/build_posting_batch_sheet.py`
  Builds a posting batch sheet from the first-wave roster.
- `scripts/generate_client_progress_update.py`
  Builds a short client-facing progress update from current launch data.
- `generated/missing_fields_message.txt`
  Auto-generated client message for the exact intake gaps that still block a clean launch.
- `generated/operator_start_brief.md`
  One-page operator brief with gaps and first-wave source preview.
- `generated/final_launch_packet.md`
  Combined launch packet with vacancy card, copy pack, screening excerpt, and source preview.
- `OPERATOR_TRIAGE_MAP.md`
  Fast operator map for source and candidate handling.
- `pilot_metrics.csv`
  Live tracking sheet for posts, responses, screenings, and hires.
- `PILOT_TRACKING_GUIDE.md`
  Short logging rules for the pilot sheet.
- `posting_evidence_log.csv`
  Proof log for each real posting action.
- `POSTING_EVIDENCE_GUIDE.md`
  How to keep posting proof for the pilot.
- `scripts/generate_posting_evidence_summary.py`
  Builds a summary of posting proof coverage.
- `case_study_capture.json`
  Proof structure for the first case study.
- `CASE_STUDY_CAPTURE_GUIDE.md`
  How to update proof without writing fake marketing copy.
- `scripts/update_case_study_from_tracking.py`
  Fast rollup from live tracking into the case-study file.
- `scripts/validate_sunday_bundle.py`
  One-command validation of the Sunday bundle before launch.
- `END_OF_DAY_REPORT_TEMPLATE.md`
  Manual end-of-day reporting template.
- `scripts/generate_sunday_ops_report.py`
  Fast markdown ops report from current Sunday tracking files.
- `scripts/generate_end_of_day_report.py`
  Builds a simple end-of-day report from Sunday tracking data.
- `scripts/generate_launch_status_snapshot.py`
  Builds a one-file launch status snapshot from Sunday tracking and readiness.
- `scripts/generate_execution_board.py`
  Builds a compact execution board from current Sunday files.
- `scripts/generate_day_close_packet.py`
  Bundles the launch snapshot, evidence summary, ops report, and end-of-day report into one close packet.
- `CLIENT_PROGRESS_UPDATE_TEMPLATE.md`
  Short client-facing progress update for launch day.
- `BLOCKER_ESCALATION_TEMPLATE.md`
  Short escalation template for operational blockers.
- `scripts/prepare_first_wave_roster.py`
  Auto-fill the first-wave roster from ready-now sources.
- `scripts/mark_source_posted.py`
  Marks one source as posted and writes proof plus pilot metrics in one step.
- `scripts/sunday_launch_control.sh`
  One-command Sunday launch control sequence.
- `scripts/run_ops_refresh.sh`
  Fast mid-day refresh after new posts, responses, or screenings.
- `scripts/generate_morning_handoff_note.py`
  Builds the morning handoff note from current launch readiness.
- `SUNDAY_EXECUTION_CHECKLIST.md`
  Launch-day operating checklist.
- `SUNDAY_LAUNCH_TIMELINE.md`
  Short block-by-block launch sequence for Sunday.
- `READINESS_MATRIX.md`
  Clear split between ready, quick-input, blocked, and ignore.
- `OPS_COMMAND_CHEATSHEET.md`
  Short command reference for posting, response logging, screening, and refresh.
- `CANDIDATE_STATUS_RULES.md`
  Exact meaning of candidate statuses and the recommended next action for each.
- `NIGHT_TO_MORNING_PLAN_2026-03-27.md`
  Current overnight execution order until morning.
- `LAUNCH_PRECHECK.md`
  Final manual precheck before posting.
- `PILOT_DEBRIEF_TEMPLATE.md`
  Short debrief template for the first live pilot.

## Sunday usage
1. Send the client intake.
2. Fill the operator intake.
3. Run `python3 scripts/build_live_vacancy_pack.py`.
4. Run `python3 scripts/sunday_readiness_check.py`.
5. Or use `bash scripts/sunday_launch_prep.sh`.
6. Finalize vacancy copy.
7. Pick first-wave sources.
8. Launch manual/assisted posting.
9. Track every action.
10. Close the day with proof notes.
11. Run `python3 scripts/update_case_study_from_tracking.py`.
12. Run `python3 scripts/generate_sunday_ops_report.py`.
13. Run `python3 scripts/validate_sunday_bundle.py`.
14. Run `python3 scripts/prepare_first_wave_roster.py`.
15. Or run `bash scripts/sunday_launch_control.sh`.
16. Run `python3 scripts/generate_client_approval_packet.py`.
17. Run `python3 scripts/build_posting_batch_sheet.py`.
18. Run `python3 scripts/promote_shortlist_from_pipeline.py`.
19. Run `python3 scripts/generate_end_of_day_report.py`.
20. Run `python3 scripts/generate_morning_handoff_note.py`.
21. Run `python3 scripts/generate_launch_status_snapshot.py`.
22. Run `python3 scripts/ingest_raw_responses.py`.
23. Run `python3 scripts/sync_screening_to_pipeline.py`.
24. Run `python3 scripts/generate_posting_evidence_summary.py`.
25. Run `python3 scripts/generate_execution_board.py`.
26. Run `python3 scripts/generate_client_progress_update.py`.
27. Run `python3 scripts/generate_recruiter_handoff_batch.py`.
28. Run `python3 scripts/generate_day_close_packet.py`.
29. Use `python3 scripts/mark_source_posted.py --source-name "..."` after each real post.
30. Use `python3 scripts/log_candidate_response.py --source-name "..." --platform "..." --candidate-name "..."` for each inbound lead.
31. Use `python3 scripts/log_screening_result.py --candidate-name "..." --fit-decision fit|no_fit` after each screening.
32. Use `python3 scripts/advance_candidate_pipeline.py --candidate-name "..." --status qualified --next-action "..."` for manual status moves.
33. Run `bash scripts/run_ops_refresh.sh` during the day to refresh proof, shortlist, and client update files.
34. Run `python3 scripts/validate_ops_contracts.py` before launch if any CSV layout was edited by hand.
