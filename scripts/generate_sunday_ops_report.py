#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
PILOT_METRICS = OPS_DIR / "pilot_metrics.csv"
CANDIDATE_PIPELINE = OPS_DIR / "candidate_pipeline.csv"
SOURCE_ROSTER = OPS_DIR / "first_wave_source_roster.csv"
READINESS = OPS_DIR / "generated" / "launch_readiness.json"
OUT_DIR = OPS_DIR / "generated"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_int(value: str) -> int:
    text = (value or "").strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def nonempty(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in values:
        value = (raw or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def build_report() -> str:
    metric_rows = read_csv(PILOT_METRICS)
    candidate_rows = read_csv(CANDIDATE_PIPELINE)
    source_rows = read_csv(SOURCE_ROSTER)
    readiness = load_json(READINESS)

    totals = {
        "posts_sent": 0,
        "responses_received": 0,
        "screenings_started": 0,
        "screenings_completed": 0,
        "qualified_candidates": 0,
        "interviews_arranged": 0,
        "hires_made": 0,
        "estimated_recruiter_minutes_saved": 0,
    }

    for row in metric_rows:
        for key in totals:
            totals[key] += parse_int(row.get(key, "0"))

    sources_used = nonempty([row.get("source_name", "") for row in metric_rows if parse_int(row.get("posts_sent", "0")) > 0])
    planned_sources = [row for row in source_rows if (row.get("source_name") or "").strip()]
    posted_sources = [row for row in source_rows if (row.get("posted_at") or "").strip()]
    qualified_pipeline = [
        row for row in candidate_rows
        if (row.get("current_status") or "").strip().lower() in {"qualified", "interview_requested", "interview_scheduled", "passed", "hired"}
    ]
    blocked = readiness.get("blocked", []) or []
    launch_gate = readiness.get("launch_gate", {}) or {}

    lines = [
        "# Sunday Ops Report",
        "",
        f"Generated at: {utc_now()}",
        "",
        "## Launch Truth",
        f"- Launch readiness status: {readiness.get('status', 'unknown')}",
        f"- Live launch gate: {launch_gate.get('status', 'unknown')}",
        f"- Launch blockers: {len(blocked)}",
        f"- Top blocker: {blocked[0] if blocked else 'none'}",
        "",
        "## Totals",
        f"- Posts sent: {totals['posts_sent']}",
        f"- Responses received: {totals['responses_received']}",
        f"- Screenings started: {totals['screenings_started']}",
        f"- Screenings completed: {totals['screenings_completed']}",
        f"- Qualified candidates: {max(totals['qualified_candidates'], len(qualified_pipeline))}",
        f"- Interviews arranged: {totals['interviews_arranged']}",
        f"- Hires made: {totals['hires_made']}",
        f"- Estimated recruiter minutes saved: {totals['estimated_recruiter_minutes_saved']}",
        "",
        "## Sources",
        f"- Planned first-wave sources: {len(planned_sources)}",
        f"- Posted sources logged: {len(posted_sources)}",
        f"- Sources used in pilot metrics: {', '.join(sources_used) if sources_used else 'none'}",
        "",
        "## Candidate Pipeline",
        f"- Candidates in pipeline: {len(candidate_rows)}",
        f"- Qualified / advanced candidates: {len(qualified_pipeline)}",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report()
    out_path = OUT_DIR / "sunday_ops_report.md"
    out_path.write_text(report, encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
