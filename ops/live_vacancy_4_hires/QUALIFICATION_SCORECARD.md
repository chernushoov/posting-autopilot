# Qualification Scorecard

Use this when a candidate replies manually and you need a fast fit decision.

## Scoring rule
Score each block from `0` to `2`.

### 1. Location / commute
- `2` can reliably reach the work location
- `1` maybe possible but needs confirmation
- `0` cannot realistically reach the location

### 2. Relevant experience
- `2` clearly has relevant experience
- `1` partial or adjacent experience
- `0` no useful experience for this role

### 3. Legal / documents
- `2` clearly eligible to work
- `1` unclear, needs proof or clarification
- `0` not eligible if legal status is mandatory

### 4. Start timing
- `2` can start in the needed window
- `1` small delay but maybe acceptable
- `0` cannot start in time

### 5. Schedule fit
- `2` fully available for the required schedule
- `1` partial fit, needs discussion
- `0` schedule does not fit

## Decision bands
- `8-10` => strong fit
- `5-7` => maybe fit, clarify one or two points
- `0-4` => not fit for this vacancy

## Fast decision rule
- if any critical block is a clear `0` on legal status, commute, or schedule, reject fast even if the total score is not terrible
- use the score to support judgment, not to hide obvious blockers

## Logging rule
- write the total into `candidate_pipeline.csv` field `screening_score`
- set `fit_decision` to `fit`, `unclear`, or `not_fit`
- always set a concrete `next_action`
