#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
PIPELINE = OPS_DIR / "candidate_pipeline.csv"

FIELDNAMES = [
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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def normalize(value: str) -> str:
    return (value or "").strip().lower()


def find_matches(rows: list[dict[str, str]], candidate_id: str, candidate_name: str) -> list[dict[str, str]]:
    id_key = normalize(candidate_id)
    name_key = normalize(candidate_name)
    matches: list[dict[str, str]] = []
    for row in rows:
        row_id = normalize(row.get("candidate_id", ""))
        row_name = normalize(row.get("candidate_name", ""))
        if id_key and row_id == id_key:
            matches.append(row)
            continue
        if name_key and row_name == name_key:
            matches.append(row)
    return matches


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Advance one candidate safely inside the Sunday pipeline.")
    parser.add_argument("--candidate-id", default="", help="Candidate identifier from candidate_pipeline.csv.")
    parser.add_argument("--candidate-name", default="", help="Fallback match by candidate name.")
    parser.add_argument("--status", default="", help="New pipeline status.")
    parser.add_argument("--fit-decision", default="", help="Updated fit decision.")
    parser.add_argument("--screening-score", default="", help="Updated screening score.")
    parser.add_argument("--next-action", default="", help="Next action to record.")
    parser.add_argument("--owner", default="", help="Current owner.")
    parser.add_argument("--append-note", default="", help="Note to append to the current notes field.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.candidate_id and not args.candidate_name:
        raise SystemExit("Provide --candidate-id or --candidate-name.")

    rows = read_rows(PIPELINE)
    matches = find_matches(rows, args.candidate_id, args.candidate_name)
    if not matches:
        raise SystemExit("No matching candidate found in candidate_pipeline.csv.")
    if len(matches) > 1:
        raise SystemExit("Multiple candidates matched. Use --candidate-id for an exact row.")

    row = matches[0]
    if args.status:
        row["current_status"] = args.status
    if args.fit_decision:
        row["fit_decision"] = args.fit_decision
    if args.screening_score:
        row["screening_score"] = args.screening_score
    if args.next_action:
        row["next_action"] = args.next_action
    if args.owner:
        row["owner"] = args.owner
    if args.append_note:
        existing = (row.get("notes") or "").strip()
        row["notes"] = f"{existing} | {args.append_note}" if existing else args.append_note
    row["last_updated_at"] = utc_now()

    write_rows(PIPELINE, rows)
    print(str(PIPELINE))
    print(f"updated_candidate={row.get('candidate_name', '') or row.get('candidate_id', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
