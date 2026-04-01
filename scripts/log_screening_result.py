#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
SCREENING = OPS_DIR / "manual_screening_answers.csv"
PILOT = OPS_DIR / "pilot_metrics.csv"
INTAKE = OPS_DIR / "vacancy_intake_template.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def append_csv(path: Path, fieldnames: list[str], row: dict[str, str]) -> None:
    existing_fields, existing_rows = read_csv(path)
    final_fields = existing_fields or fieldnames
    existing_rows.append({key: row.get(key, "") for key in final_fields})
    write_csv(path, final_fields, existing_rows)


def load_intake() -> dict:
    import json

    if not INTAKE.exists():
        return {}
    return json.loads(INTAKE.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Log one manual screening result for Sunday execution.")
    parser.add_argument("--candidate-name", required=True)
    parser.add_argument("--vacancy-title", default="")
    parser.add_argument("--location-answer", default="")
    parser.add_argument("--experience-answer", default="")
    parser.add_argument("--legal-answer", default="")
    parser.add_argument("--start-answer", default="")
    parser.add_argument("--schedule-answer", default="")
    parser.add_argument("--language-answer", default="")
    parser.add_argument("--fit-decision", default="pending")
    parser.add_argument("--next-action", default="")
    parser.add_argument("--owner", default="recruiter")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    now = utc_now()
    intake = load_intake()
    append_csv(
        SCREENING,
        [
            "candidate_name",
            "vacancy_title",
            "location_answer",
            "experience_answer",
            "legal_answer",
            "start_answer",
            "schedule_answer",
            "language_answer",
            "fit_decision",
            "next_action",
            "owner",
            "updated_at",
        ],
        {
            "candidate_name": args.candidate_name,
            "vacancy_title": args.vacancy_title or intake.get("vacancy_title", ""),
            "location_answer": args.location_answer,
            "experience_answer": args.experience_answer,
            "legal_answer": args.legal_answer,
            "start_answer": args.start_answer,
            "schedule_answer": args.schedule_answer,
            "language_answer": args.language_answer,
            "fit_decision": args.fit_decision,
            "next_action": args.next_action,
            "owner": args.owner,
            "updated_at": now,
        },
    )
    append_csv(
        PILOT,
        [
            "log_timestamp",
            "campaign_id",
            "client_name",
            "vacancy_title",
            "hires_needed",
            "source_name",
            "platform",
            "posting_mode",
            "activity_type",
            "posts_sent",
            "responses_received",
            "screenings_started",
            "screenings_completed",
            "qualified_candidates",
            "interviews_arranged",
            "hires_made",
            "estimated_recruiter_minutes_saved",
            "owner",
            "notes",
        ],
        {
            "log_timestamp": now,
            "campaign_id": "live_vacancy_4_hires",
            "client_name": intake.get("client_name", ""),
            "vacancy_title": intake.get("vacancy_title", ""),
            "hires_needed": str(intake.get("hires_needed", "")),
            "source_name": "",
            "platform": "",
            "posting_mode": "",
            "activity_type": "screening",
            "posts_sent": "0",
            "responses_received": "0",
            "screenings_started": "1",
            "screenings_completed": "1",
            "qualified_candidates": "1" if args.fit_decision.strip().lower() == "fit" else "0",
            "interviews_arranged": "0",
            "hires_made": "0",
            "estimated_recruiter_minutes_saved": "0",
            "owner": args.owner,
            "notes": args.candidate_name,
        },
    )
    print(str(SCREENING))
    print(str(PILOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
