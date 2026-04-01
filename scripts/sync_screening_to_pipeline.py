#!/usr/bin/env python3
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
SCREENING = OPS_DIR / "manual_screening_answers.csv"
PIPELINE = OPS_DIR / "candidate_pipeline.csv"


FIT_TO_STATUS = {
    "fit": ("qualified", "8"),
    "unclear": ("screening_completed", "5"),
    "not_fit": ("rejected", "2"),
}


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
    screening_rows = read_csv(SCREENING)
    pipeline_rows = read_csv(PIPELINE)
    pipeline_fields = [
        "candidate_id",
        "client_name",
        "vacancy_title",
        "source_name",
        "platform",
        "candidate_name",
        "telegram_handle",
        "phone_or_contact",
        "language",
        "current_status",
        "fit_decision",
        "screening_score",
        "next_action",
        "owner",
        "last_updated_at",
        "notes",
    ]

    updated = 0
    for answer in screening_rows:
        name = (answer.get("candidate_name") or "").strip().lower()
        vacancy = (answer.get("vacancy_title") or "").strip().lower()
        fit = (answer.get("fit_decision") or "").strip().lower()
        if not name or not fit:
            continue
        current_status, score = FIT_TO_STATUS.get(fit, ("screening_completed", ""))
        for row in pipeline_rows:
            same_name = (row.get("candidate_name") or "").strip().lower() == name
            vacancy_match = not vacancy or (row.get("vacancy_title") or "").strip().lower() == vacancy or not (row.get("vacancy_title") or "").strip()
            if same_name and vacancy_match:
                row["current_status"] = current_status
                row["fit_decision"] = fit
                if score:
                    row["screening_score"] = score
                row["next_action"] = answer.get("next_action", "") or row.get("next_action", "")
                row["owner"] = answer.get("owner", "") or row.get("owner", "")
                row["last_updated_at"] = answer.get("updated_at", "") or utc_now()
                notes = " | ".join(
                    part for part in [
                        (answer.get("location_answer") or "").strip(),
                        (answer.get("experience_answer") or "").strip(),
                        (answer.get("legal_answer") or "").strip(),
                        (answer.get("schedule_answer") or "").strip(),
                    ] if part
                )
                if notes:
                    row["notes"] = notes
                updated += 1
                break

    write_csv(PIPELINE, pipeline_fields, pipeline_rows)
    print(str(PIPELINE))
    print(f"updated={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
