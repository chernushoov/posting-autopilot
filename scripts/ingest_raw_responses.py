#!/usr/bin/env python3
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
RAW_RESPONSES = OPS_DIR / "raw_response_intake.csv"
PIPELINE = OPS_DIR / "candidate_pipeline.csv"


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


def candidate_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        (row.get("candidate_name") or "").strip().lower(),
        (row.get("telegram_handle") or row.get("phone_or_contact") or "").strip().lower(),
        (row.get("vacancy_title") or "").strip().lower(),
    )


def main() -> int:
    raw_rows = read_csv(RAW_RESPONSES)
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
    raw_fields = [
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
    ]

    existing = {candidate_key(row) for row in pipeline_rows}
    imported = 0
    for idx, raw in enumerate(raw_rows, start=1):
        status = (raw.get("status") or "").strip().lower()
        if status and status in {"imported", "moved_to_pipeline", "ignored"}:
            continue
        key = (
            (raw.get("candidate_name") or "").strip().lower(),
            (raw.get("telegram_handle") or raw.get("phone_or_contact") or "").strip().lower(),
            "",
        )
        if not key[0] and not key[1]:
            continue
        pipeline_key = (key[0], key[1], "")
        if pipeline_key in existing:
            raw["status"] = "moved_to_pipeline"
            continue

        pipeline_rows.append(
            {
                "candidate_id": raw.get("logged_at", "") or f"raw_{idx}",
                "client_name": "",
                "vacancy_title": "",
                "source_name": raw.get("source_name", ""),
                "platform": raw.get("platform", ""),
                "candidate_name": raw.get("candidate_name", ""),
                "telegram_handle": raw.get("telegram_handle", ""),
                "phone_or_contact": raw.get("phone_or_contact", ""),
                "language": raw.get("language", ""),
                "current_status": "new",
                "fit_decision": "pending",
                "screening_score": "",
                "next_action": raw.get("next_action", "") or "start screening",
                "owner": raw.get("owner", ""),
                "last_updated_at": raw.get("logged_at", "") or utc_now(),
                "notes": raw.get("raw_message_summary", ""),
            }
        )
        raw["status"] = "moved_to_pipeline"
        imported += 1
        existing.add(pipeline_key)

    write_csv(PIPELINE, pipeline_fields, pipeline_rows)
    write_csv(RAW_RESPONSES, raw_fields, raw_rows)
    print(str(PIPELINE))
    print(f"imported={imported}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
