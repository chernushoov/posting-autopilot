#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "ops" / "live_vacancy_4_hires"
GENERATED = OPS / "generated"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def main() -> int:
    readiness = load_json(GENERATED / "launch_readiness.json")
    runtime = load_json(GENERATED / "runtime_status.json")
    roster = read_csv(OPS / "first_wave_source_roster.csv")
    raw_responses = read_csv(OPS / "raw_response_intake.csv")
    pipeline = read_csv(OPS / "candidate_pipeline.csv")
    shortlist = read_csv(OPS / "qualified_candidates_shortlist.csv")

    roster_selected = [row for row in roster if (row.get("source_name") or "").strip()]
    raw_logged = [row for row in raw_responses if (row.get("candidate_name") or row.get("phone_or_contact") or row.get("telegram_handle") or "").strip()]
    pipeline_live = [row for row in pipeline if (row.get("candidate_name") or "").strip()]
    shortlist_live = [row for row in shortlist if (row.get("candidate_name") or "").strip()]
    telegram = runtime.get("telegram", {})
    blocked = readiness.get("blocked", []) or []
    launch_gate = readiness.get("launch_gate", {}) or {}

    lines = [
        "# Execution Board",
        "",
        f"Generated at: {utc_now()}",
        "",
        f"- Readiness status: {readiness.get('status', 'unknown')}",
        f"- Missing intake fields: {len(readiness.get('missing_fields', []) or [])}",
        f"- Launch blockers: {len(blocked)}",
        f"- First-wave sources selected: {len(roster_selected)}",
        f"- Raw inbound responses logged: {len(raw_logged)}",
        f"- Candidates in pipeline: {len(pipeline_live)}",
        f"- Candidates in shortlist: {len(shortlist_live)}",
        f"- Telegram token valid: {telegram.get('valid_format')}",
        f"- Telegram reserved for other runtime: {telegram.get('reserved_for_other_runtime')}",
        "",
    ]
    if launch_gate:
        lines.append(f"- Live launch gate: {launch_gate.get('status', 'unknown')}")
    if blocked:
        lines.append(f"- Top blocker: {blocked[0]}")
        lines.append("")

    GENERATED.mkdir(parents=True, exist_ok=True)
    out_path = GENERATED / "execution_board.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
