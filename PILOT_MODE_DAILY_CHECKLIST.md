# Pilot Mode Daily Checklist

Run this in the same order every day.

Quick validation command before opening the UI:

```bash
SMOKE_BASE_URL=http://localhost:8080 python3 scripts/smoke_web.py
```

1. Confirm one active vacancy exists and the final posting asset text is correct.
2. Confirm Telegram destinations show `READY`.
3. Confirm Facebook destinations are saved with direct destination URLs and are treated as `assisted/manual`.
4. Open `Pilot Runs` and run the posting cycle.
5. Confirm Telegram attempts move to `posted` or a visible failure status.
6. Resolve every `manual_action_required` Facebook row:
   - open the destination
   - paste/post the prepared content
   - save the final result as `posted`, `failed`, or `blocked_or_suspected`
7. Review the destination log for:
   - missing attempts
   - repeated failures
   - blocked or suspected platform outcomes
8. Record operator notes on every failed or blocked manual step.
9. Pause the run if repeated `blocked_or_suspected` outcomes appear.
10. At the end of the day, confirm the log tells the full story without needing chat memory.
