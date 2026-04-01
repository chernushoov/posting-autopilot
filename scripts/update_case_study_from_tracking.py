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
CASE_STUDY = OPS_DIR / "case_study_capture.json"


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


def load_case_study() -> dict:
    with CASE_STUDY.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def unique_nonempty(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = (raw or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def rollup_metrics(rows: list[dict[str, str]]) -> dict:
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
    channels: list[str] = []
    for row in rows:
        for key in totals:
            totals[key] += parse_int(row.get(key, "0"))
        source_name = (row.get("source_name") or "").strip()
        platform = (row.get("platform") or "").strip()
        if source_name and platform:
            channels.append(f"{platform}:{source_name}")
        elif source_name:
            channels.append(source_name)
    return {
        "totals": totals,
        "channels_used": unique_nonempty(channels),
    }


def rollup_candidates(rows: list[dict[str, str]]) -> dict:
    qualified_statuses = {"qualified", "interview_requested", "interview_scheduled", "passed", "hired"}
    interview_statuses = {"interview_requested", "interview_scheduled"}

    totals = {
        "pipeline_candidates": 0,
        "qualified_from_pipeline": 0,
        "interviews_from_pipeline": 0,
        "hires_from_pipeline": 0,
    }
    for row in rows:
        status = (row.get("current_status") or "").strip().lower()
        if not status:
            continue
        totals["pipeline_candidates"] += 1
        if status in qualified_statuses:
            totals["qualified_from_pipeline"] += 1
        if status in interview_statuses:
            totals["interviews_from_pipeline"] += 1
        if status == "hired":
            totals["hires_from_pipeline"] += 1
    return totals


def main() -> int:
    case_study = load_case_study()
    metric_rows = read_csv(PILOT_METRICS)
    pipeline_rows = read_csv(CANDIDATE_PIPELINE)

    metric_rollup = rollup_metrics(metric_rows)
    pipeline_rollup = rollup_candidates(pipeline_rows)

    case_study["channels_used"] = metric_rollup["channels_used"]
    case_study["totals"]["posts_sent"] = metric_rollup["totals"]["posts_sent"]
    case_study["totals"]["responses_received"] = metric_rollup["totals"]["responses_received"]
    case_study["totals"]["screenings_started"] = metric_rollup["totals"]["screenings_started"]
    case_study["totals"]["screenings_completed"] = metric_rollup["totals"]["screenings_completed"]
    case_study["totals"]["qualified_candidates"] = max(
        metric_rollup["totals"]["qualified_candidates"],
        pipeline_rollup["qualified_from_pipeline"],
    )
    case_study["totals"]["interviews_arranged"] = max(
        metric_rollup["totals"]["interviews_arranged"],
        pipeline_rollup["interviews_from_pipeline"],
    )
    case_study["totals"]["hires_made"] = max(
        metric_rollup["totals"]["hires_made"],
        pipeline_rollup["hires_from_pipeline"],
    )
    case_study["totals"]["estimated_recruiter_minutes_saved"] = metric_rollup["totals"]["estimated_recruiter_minutes_saved"]
    case_study["last_updated_at"] = utc_now()

    with CASE_STUDY.open("w", encoding="utf-8") as handle:
        json.dump(case_study, handle, ensure_ascii=False, indent=2)

    print(json.dumps({
        "updated": str(CASE_STUDY),
        "channels_used": len(case_study["channels_used"]),
        "totals": case_study["totals"],
        "last_updated_at": case_study["last_updated_at"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
