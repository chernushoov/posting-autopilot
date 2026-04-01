#!/usr/bin/env python3
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
PILOT = OPS_DIR / "pilot_metrics.csv"
PIPELINE = OPS_DIR / "candidate_pipeline.csv"
OUT = OPS_DIR / "generated" / "end_of_day_report.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_int(value: str) -> int:
    text = (value or "").strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    pilot_rows = read_csv(PILOT)
    pipeline_rows = read_csv(PIPELINE)

    totals = {
        "posts_sent": 0,
        "responses_received": 0,
        "screenings_started": 0,
        "screenings_completed": 0,
        "qualified_candidates": 0,
        "interviews_arranged": 0,
        "hires_made": 0,
        "estimated_recruiter_minutes_saved": 0,
    }
    for row in pilot_rows:
        for key in totals:
            totals[key] += parse_int(row.get(key, "0"))

    active_candidates = [
        row for row in pipeline_rows
        if (row.get("current_status") or "").strip().lower() not in {"", "rejected", "hired"}
    ]

    report = (
        "# End Of Day Report\n\n"
        f"Generated at: {utc_now()}\n\n"
        f"- Posts sent today: {totals['posts_sent']}\n"
        f"- Responses received: {totals['responses_received']}\n"
        f"- Screenings started: {totals['screenings_started']}\n"
        f"- Screenings completed: {totals['screenings_completed']}\n"
        f"- Qualified candidates: {totals['qualified_candidates']}\n"
        f"- Interviews arranged: {totals['interviews_arranged']}\n"
        f"- Hires made: {totals['hires_made']}\n"
        f"- Estimated recruiter time saved: {totals['estimated_recruiter_minutes_saved']}\n"
        f"- Active candidates still in motion: {len(active_candidates)}\n"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(report, encoding="utf-8")
    print(str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
