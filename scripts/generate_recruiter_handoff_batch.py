#!/usr/bin/env python3
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
SHORTLIST = OPS_DIR / "qualified_candidates_shortlist.csv"
OUT = OPS_DIR / "generated" / "recruiter_handoff_batch.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    rows = read_csv(SHORTLIST)
    lines = [
        "# Recruiter Handoff Batch",
        "",
        f"Generated at: {utc_now()}",
        "",
    ]

    if not rows:
        lines.extend(
            [
                "No qualified candidates are in the shortlist yet.",
                "",
                "Next action: keep logging screening outcomes and rerun `python3 scripts/promote_shortlist_from_pipeline.py`.",
            ]
        )
    else:
        lines.append(f"Qualified candidates ready for handoff: {len(rows)}")
        lines.append("")
        for index, row in enumerate(rows, start=1):
            lines.extend(
                [
                    f"## Candidate {index}",
                    f"- Name: {row.get('candidate_name', '')}",
                    f"- Vacancy: {row.get('vacancy_title', '')}",
                    f"- Source: {row.get('source_name', '')}",
                    f"- Contact: {row.get('contact', '')}",
                    f"- Language: {row.get('language', '')}",
                    f"- Screening score: {row.get('screening_score', '')}",
                    f"- Fit summary: {row.get('fit_summary', '')}",
                    f"- Key risk: {row.get('key_risk', '')}",
                    f"- Next step: {row.get('next_step', '')}",
                    f"- Owner: {row.get('owner', '')}",
                    "",
                ]
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
