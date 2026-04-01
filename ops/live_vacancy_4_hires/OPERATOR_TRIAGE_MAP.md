# Operator Triage Map

## Source triage

### ready_now
- can be posted today without waiting for new setup
- operator action: post first

### needs_quick_setup
- useful source, but one small dependency remains
- operator action: clear blocker before posting

### blocked
- not safe to rely on for Sunday launch
- operator action: do not count it in the first wave

### ignore_for_now
- low value or off-path for this live vacancy
- operator action: ignore

## Candidate status map

This matches the current RecruitBot candidate model.

### new
- meaning: response received, not yet processed
- next action: start screening or move into manual review

### qualifying
- meaning: candidate is in screening flow
- next action: finish the core questions

### interviewing
- meaning: candidate passed initial screen and needs recruiter follow-up
- next action: arrange recruiter contact / interview

### passed
- meaning: candidate cleared the initial filter
- next action: hand off to recruiter or client-side interview step

### rejected
- meaning: candidate does not fit the vacancy
- next action: stop active processing, keep note if useful

### hired
- meaning: candidate converted to hire
- next action: record as proof and update metrics

## Sunday operator rule
- do not leave candidates between states without a clear next action
- do not leave sources unclassified
- if unsure, choose the simpler honest status instead of optimistic status
