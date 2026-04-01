#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "ops" / "live_vacancy_4_hires"

EXPECTED_HEADERS = {
    "raw_response_intake.csv": [
        "logged_at",
        "source_name",
        "platform",
        "candidate_name",
        "telegram_handle",
        "phone_or_contact",
        "language",
        "raw_message_summary",
        "owner",
        "status",
        "next_action",
    ],
    "manual_screening_answers.csv": [
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
    "candidate_pipeline.csv": [
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
    ],
    "qualified_candidates_shortlist.csv": [
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
    ],
    "pilot_metrics.csv": [
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
    "posting_evidence_log.csv": [
        "logged_at",
        "source_name",
        "platform",
        "owner",
        "post_reference",
        "screenshot_or_path",
        "result",
        "notes",
    ],
    "first_wave_source_roster.csv": [
        "wave_order",
        "source_name",
        "platform",
        "posting_mode",
        "status",
        "owner",
        "planned_post_time",
        "apply_path",
        "recruiter_note",
        "posted_at",
        "result",
    ],
}


def read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def main() -> int:
    checks: list[dict[str, object]] = []
    status = "ok"
    for name, expected in EXPECTED_HEADERS.items():
        path = OPS / name
        if not path.exists():
            checks.append({"file": name, "status": "missing", "expected": expected, "actual": []})
            status = "error"
            continue
        actual = read_header(path)
        if actual != expected:
            checks.append({"file": name, "status": "header_mismatch", "expected": expected, "actual": actual})
            status = "error"
        else:
            checks.append({"file": name, "status": "ok", "expected_count": len(expected)})

    print(json.dumps({"ops_dir": str(OPS), "status": status, "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
