#!/usr/bin/env python3
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
EVIDENCE = OPS_DIR / "posting_evidence_log.csv"
OUT = OPS_DIR / "generated" / "posting_evidence_summary.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    rows = read_csv(EVIDENCE)
    logged = [row for row in rows if (row.get("source_name") or "").strip()]
    with_proof = [row for row in logged if (row.get("post_reference") or "").strip() or (row.get("screenshot_or_path") or "").strip()]
    without_proof = [row for row in logged if row not in with_proof]

    report = [
        "# Posting Evidence Summary",
        "",
        f"Generated at: {utc_now()}",
        "",
        f"- Logged posting evidence rows: {len(logged)}",
        f"- Rows with proof reference: {len(with_proof)}",
        f"- Rows missing proof reference: {len(without_proof)}",
        "",
        "## Missing proof sources",
    ]
    if without_proof:
        report.extend(f"- {row.get('source_name', '')}" for row in without_proof)
    else:
        report.append("- none")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
