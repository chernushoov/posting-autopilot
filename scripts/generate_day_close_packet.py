#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
GENERATED = OPS_DIR / "generated"
OUT = GENERATED / "day_close_packet.md"

SECTIONS = [
    ("Launch Status Snapshot", GENERATED / "launch_status_snapshot.md"),
    ("Posting Evidence Summary", GENERATED / "posting_evidence_summary.md"),
    ("Sunday Ops Report", GENERATED / "sunday_ops_report.md"),
    ("End Of Day Report", GENERATED / "end_of_day_report.md"),
]


def main() -> int:
    parts = ["# Day Close Packet", ""]
    for title, path in SECTIONS:
        parts.append(f"## {title}")
        parts.append("")
        if path.exists():
            parts.append(path.read_text(encoding="utf-8").strip())
        else:
            parts.append(f"Missing artifact: {path.name}")
        parts.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    print(str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
