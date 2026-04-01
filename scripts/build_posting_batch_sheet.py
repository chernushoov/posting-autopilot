#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
ROSTER = OPS_DIR / "first_wave_source_roster.csv"
OUT_PATH = OPS_DIR / "generated" / "posting_batch_sheet.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def pick_template(platform: str, posting_mode: str) -> str:
    platform = (platform or "").strip().lower()
    posting_mode = (posting_mode or "").strip().lower()
    if platform == "telegram":
        return "telegram_short.txt"
    if platform == "facebook" and "manual" in posting_mode:
        return "facebook_groups_compact.txt"
    return "facebook_standard.txt"


def main() -> int:
    rows = read_csv(ROSTER)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "wave_order",
        "source_name",
        "platform",
        "posting_mode",
        "template_file",
        "owner",
        "planned_post_time",
        "posted_at",
        "result",
    ]
    batch_rows = []
    for row in rows:
        if not (row.get("source_name") or "").strip():
            continue
        batch_rows.append(
            {
                "wave_order": row.get("wave_order", ""),
                "source_name": row.get("source_name", ""),
                "platform": row.get("platform", ""),
                "posting_mode": row.get("posting_mode", ""),
                "template_file": pick_template(row.get("platform", ""), row.get("posting_mode", "")),
                "owner": row.get("owner", ""),
                "planned_post_time": row.get("planned_post_time", ""),
                "posted_at": row.get("posted_at", ""),
                "result": row.get("result", ""),
            }
        )

    with OUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(batch_rows)

    print(str(OUT_PATH))
    print(f"rows={len(batch_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
