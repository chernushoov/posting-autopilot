# Launch Precheck

Before Sunday posting, confirm these 4 things:

1. Intake complete
- `vacancy_intake_template.json` filled
- no critical missing fields

2. Copy generated
- run `python3 scripts/build_live_vacancy_pack.py`
- confirm files exist in `ops/live_vacancy_4_hires/generated/`

3. Source wave selected
- first-wave sources are marked in `source_execution_plan.csv`
- blocked sources are not counted as launch-ready

4. Runtime reality understood
- if the bot token is still invalid, use manual/assisted posting and manual candidate tracking
- do not wait for perfect automation to start manual proof collection
