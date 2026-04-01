# Candidate Pipeline Guide

Use `candidate_pipeline.csv` when responses start coming in, especially if the full bot apply path is still blocked.

## Purpose
- keep every candidate visible
- avoid losing manual replies from Telegram or Facebook
- keep status and next action clear
- create proof for the first pilot case study

## One row per candidate
Create one row when a person responds or is forwarded by a source owner.

## Update rules
- update the same row as the candidate moves forward
- do not create duplicate rows for the same person unless it is clearly a separate vacancy
- always keep `current_status`, `fit_decision`, and `next_action` filled

## Suggested current_status values
- `new`
- `contacted`
- `screening_started`
- `screening_completed`
- `qualified`
- `interview_requested`
- `interview_scheduled`
- `rejected`
- `hired`

## Suggested fit_decision values
- `pending`
- `fit`
- `unclear`
- `not_fit`

## Minimum fields to keep live
- source
- candidate name or handle
- contact path
- language
- current status
- fit decision
- next action
- owner
- notes
