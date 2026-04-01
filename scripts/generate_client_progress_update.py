#!/usr/bin/env python3
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
PILOT = OPS_DIR / "pilot_metrics.csv"
PIPELINE = OPS_DIR / "candidate_pipeline.csv"
ROSTER = OPS_DIR / "first_wave_source_roster.csv"
OUT_MD = OPS_DIR / "generated" / "client_progress_update.md"
OUT_TXT = OPS_DIR / "generated" / "client_progress_update.txt"


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
    roster_rows = read_csv(ROSTER)

    totals = {
        "posts_sent": 0,
        "responses_received": 0,
        "screenings_completed": 0,
        "qualified_candidates": 0,
        "interviews_arranged": 0,
    }
    for row in pilot_rows:
        for key in totals:
            totals[key] += parse_int(row.get(key, "0"))

    active_candidates = [
        row for row in pipeline_rows
        if (row.get("current_status") or "").strip().lower() not in {"", "new", "rejected", "hired"}
    ]
    ready_sources = [
        row for row in roster_rows
        if (row.get("status") or "").strip().lower() == "ready_now"
    ]
    posted_sources = [
        row for row in roster_rows
        if (row.get("posted_at") or "").strip()
    ]

    text = (
        "Update on the live vacancy campaign:\n"
        f"- First-wave sources ready: {len(ready_sources)}\n"
        f"- Sources already posted: {len(posted_sources)}\n"
        f"- Responses received: {totals['responses_received']}\n"
        f"- Screenings completed: {totals['screenings_completed']}\n"
        f"- Qualified candidates: {totals['qualified_candidates']}\n"
        f"- Interviews arranged: {totals['interviews_arranged']}\n"
        f"- Candidates currently in motion: {len(active_candidates)}\n"
    )

    markdown = (
        "# Client Progress Update\n\n"
        f"Generated at: {utc_now()}\n\n"
        + "\n".join([f"- {line}" for line in text.strip().splitlines()[1:]])
        + "\n"
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(markdown, encoding="utf-8")
    OUT_TXT.write_text(text, encoding="utf-8")
    print(str(OUT_MD))
    print(str(OUT_TXT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
