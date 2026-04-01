#!/usr/bin/env python3
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
PIPELINE = OPS_DIR / "candidate_pipeline.csv"
SHORTLIST = OPS_DIR / "qualified_candidates_shortlist.csv"


QUALIFIED_STATUSES = {"qualified", "interview_requested", "interview_scheduled", "passed", "hired"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    pipeline_rows = read_csv(PIPELINE)
    fieldnames = [
        "candidate_name",
        "vacancy_title",
        "source_name",
        "contact",
        "city",
        "language",
        "screening_score",
        "fit_summary",
        "key_risk",
        "next_step",
        "owner",
        "last_updated_at",
    ]
    shortlist_rows = []
    for row in pipeline_rows:
        status = (row.get("current_status") or "").strip().lower()
        fit = (row.get("fit_decision") or "").strip().lower()
        if status not in QUALIFIED_STATUSES and fit != "fit":
            continue
        shortlist_rows.append(
            {
                "candidate_name": row.get("candidate_name", ""),
                "vacancy_title": row.get("vacancy_title", ""),
                "source_name": row.get("source_name", ""),
                "contact": row.get("phone_or_contact", "") or row.get("telegram_handle", ""),
                "city": "",
                "language": row.get("language", ""),
                "screening_score": row.get("screening_score", ""),
                "fit_summary": row.get("notes", ""),
                "key_risk": "",
                "next_step": row.get("next_action", ""),
                "owner": row.get("owner", ""),
                "last_updated_at": row.get("last_updated_at", "") or utc_now(),
            }
        )

    write_csv(SHORTLIST, fieldnames, shortlist_rows)
    print(str(SHORTLIST))
    print(f"rows={len(shortlist_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
