#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
ROSTER = OPS_DIR / "first_wave_source_roster.csv"
EVIDENCE = OPS_DIR / "posting_evidence_log.csv"
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
    parser = argparse.ArgumentParser(description="Mark a source as posted and log proof for Sunday execution.")
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--owner", default="recruiter")
    parser.add_argument("--post-reference", default="")
    parser.add_argument("--screenshot-or-path", default="")
    parser.add_argument("--result", default="posted")
    parser.add_argument("--notes", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    fieldnames, rows = read_csv(ROSTER)
    if not rows:
        raise SystemExit("first_wave_source_roster.csv is empty.")

    matched = None
    for row in rows:
        if (row.get("source_name") or "").strip().lower() == args.source_name.strip().lower():
            matched = row
            break
    if matched is None:
        raise SystemExit("Source not found in first_wave_source_roster.csv.")

    now = utc_now()
    matched["posted_at"] = now
    matched["result"] = args.result
    if args.owner:
        matched["owner"] = args.owner
    write_csv(ROSTER, fieldnames, rows)

    append_csv(
        EVIDENCE,
        [
            "logged_at",
            "source_name",
            "platform",
            "owner",
            "post_reference",
            "screenshot_or_path",
            "result",
            "notes",
        ],
        {
            "logged_at": now,
            "source_name": matched.get("source_name", ""),
            "platform": matched.get("platform", ""),
            "owner": args.owner,
            "post_reference": args.post_reference,
            "screenshot_or_path": args.screenshot_or_path,
            "result": args.result,
            "notes": args.notes,
        },
    )

    intake = load_intake()
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
            "source_name": matched.get("source_name", ""),
            "platform": matched.get("platform", ""),
            "posting_mode": matched.get("posting_mode", ""),
            "activity_type": "posting",
            "posts_sent": "1",
            "responses_received": "0",
            "screenings_started": "0",
            "screenings_completed": "0",
            "qualified_candidates": "0",
            "interviews_arranged": "0",
            "hires_made": "0",
            "estimated_recruiter_minutes_saved": "0",
            "owner": args.owner,
            "notes": args.notes,
        },
    )

    print(str(ROSTER))
    print(str(EVIDENCE))
    print(str(PILOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
