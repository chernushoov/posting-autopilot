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
    metrics = read_csv(OPS / "pilot_metrics.csv")
    pipeline = read_csv(OPS / "candidate_pipeline.csv")

    ready_sources = [row for row in roster if (row.get("source_name") or "").strip()]
    posted_sources = [row for row in roster if (row.get("posted_at") or "").strip()]
    active_candidates = [
        row for row in pipeline
        if (row.get("current_status") or "").strip().lower() not in {"", "rejected", "hired"}
    ]

    posts_sent = sum(int(float((row.get("posts_sent") or "0") or 0)) for row in metrics if (row.get("posts_sent") or "").strip())
    responses = sum(int(float((row.get("responses_received") or "0") or 0)) for row in metrics if (row.get("responses_received") or "").strip())

    telegram = runtime.get("telegram", {})
    blocked = readiness.get("blocked", []) or []
    launch_gate = readiness.get("launch_gate", {}) or {}
    snapshot = (
        "# Launch Status Snapshot\n\n"
        f"Generated at: {utc_now()}\n\n"
        f"- Launch readiness status: {readiness.get('status', 'unknown')}\n"
        f"- Missing intake fields: {len(readiness.get('missing_fields', []) or [])}\n"
        f"- Launch blockers: {len(blocked)}\n"
        f"- Live launch gate: {launch_gate.get('status', 'unknown')}\n"
        f"- First-wave sources selected: {len(ready_sources)}\n"
        f"- First-wave sources posted: {len(posted_sources)}\n"
        f"- Posts sent logged: {posts_sent}\n"
        f"- Responses logged: {responses}\n"
        f"- Active candidates in pipeline: {len(active_candidates)}\n"
        f"- Telegram token valid: {telegram.get('valid_format')}\n"
        f"- Telegram reserved for other runtime: {telegram.get('reserved_for_other_runtime')}\n"
        f"- Telegram username: {(telegram.get('bot_identity') or {}).get('username') if telegram else None}\n"
    )
    if blocked:
        snapshot += f"- Top blocker: {blocked[0]}\n"
    GENERATED.mkdir(parents=True, exist_ok=True)
    out_path = GENERATED / "launch_status_snapshot.md"
    out_path.write_text(snapshot, encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
