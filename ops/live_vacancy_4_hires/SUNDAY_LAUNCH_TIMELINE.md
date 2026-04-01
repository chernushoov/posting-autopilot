# Sunday Launch Timeline

## Block 1 — Before first posting
- send the client intake message
- normalize facts into `vacancy_intake_template.json`
- finalize the vacancy body
- confirm the 6 screening questions
- select first-wave sources from `source_execution_plan.csv`

## Block 2 — First launch wave
- post to the fastest Telegram manual sources
- post to recruiter-controlled Telegram sources
- post to Facebook page
- post to the first Facebook groups
- log every post immediately in `pilot_metrics.csv`

## Block 3 — Response handling
- count new responses
- mark candidate status as `new` or `qualifying`
- move strong candidates toward `interviewing` or `passed`
- reject fast if minimum fit is clearly absent

## Block 4 — Midday review
- compare posts sent vs responses received
- identify which sources are working
- identify which sources are dead or blocked
- decide whether to repeat or shift the next posting wave

## Block 5 — End of day
- add a `daily_rollup` row to `pilot_metrics.csv`
- update `case_study_capture.json`
- write one short note for:
  - what worked
  - what failed
  - what is blocked for the next cycle
