# Candidate Status Rules

Use one status at a time in `candidate_pipeline.csv`.

## Statuses
- `new`
  Raw response landed but no screening happened yet.
- `screening_completed`
  Screening happened, but fit is still unclear or needs manual review.
- `qualified`
  Candidate passed screening and is ready for recruiter handoff or interview request.
- `interview_requested`
  Recruiter or client should schedule an interview next.
- `interview_scheduled`
  Interview is on the calendar.
- `passed`
  Candidate cleared interview or next decision gate.
- `hired`
  Candidate accepted and joined.
- `rejected`
  Candidate is out of the process.

## Fast operating rule
- Use `fit_decision=fit` for candidates who should move fast.
- Use `fit_decision=unclear` if manual review is still needed.
- Use `fit_decision=not_fit` only when the candidate should be closed out.

## Recommended next actions
- `new` -> `start screening`
- `screening_completed` -> `manual review`
- `qualified` -> `handoff to recruiter`
- `interview_requested` -> `schedule interview`
- `interview_scheduled` -> `confirm attendance`
- `passed` -> `client decision`
- `hired` -> `close and capture proof`
- `rejected` -> `log reason and close`
