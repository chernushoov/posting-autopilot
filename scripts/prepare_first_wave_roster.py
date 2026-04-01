#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
SOURCE_PLAN = OPS_DIR / "source_execution_plan.csv"
FIRST_WAVE = OPS_DIR / "first_wave_source_roster.csv"


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
    source_rows = read_csv(SOURCE_PLAN)
    selected = [row for row in source_rows if (row.get("status") or "").strip() == "ready_now"][:5]

    fieldnames = [
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
    ]

    rows = []
    for idx, source in enumerate(selected, start=1):
        rows.append(
            {
                "wave_order": str(idx),
                "source_name": source.get("source_name", ""),
                "platform": source.get("platform", ""),
                "posting_mode": source.get("posting_mode", ""),
                "status": source.get("status", ""),
                "owner": source.get("owner", ""),
                "planned_post_time": "",
                "apply_path": source.get("apply_path_ready", ""),
                "recruiter_note": source.get("notes", ""),
                "posted_at": "",
                "result": "",
            }
        )

    write_csv(FIRST_WAVE, fieldnames, rows)
    print(str(FIRST_WAVE))
    print(f"selected={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
