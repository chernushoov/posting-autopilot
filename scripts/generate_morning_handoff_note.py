#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
GENERATED = OPS_DIR / "generated"
READINESS = GENERATED / "launch_readiness.json"
OUT = GENERATED / "morning_handoff_note.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    readiness = load_json(READINESS)
    missing = readiness.get("missing_fields", []) or []
    generated_files = readiness.get("generated_files", []) or []
    blocked = readiness.get("blocked", []) or []
    launch_gate = readiness.get("launch_gate", {}) or {}

    note = [
        "# Morning Handoff Note",
        "",
        f"Generated at: {utc_now()}",
        "",
        "## Current state",
        f"- Launch readiness status: {readiness.get('status', 'unknown')}",
        f"- Live launch gate: {launch_gate.get('status', 'unknown')}",
        f"- Generated files: {', '.join(generated_files) if generated_files else 'none'}",
        "",
        "## Still needed before clean launch",
    ]
    if missing:
        note.extend(f"- {item}" for item in missing)
    else:
        note.append("- none")
    note.extend([
        "",
        "## Current blockers",
    ])
    if blocked:
        note.extend(f"- {item}" for item in blocked)
    else:
        note.append("- none")
    note.extend([
        "",
        "## First actions this morning",
        "- get the missing vacancy facts from the client",
        "- rerun build_live_vacancy_pack.py",
        "- rerun sunday_launch_control.sh",
        "- post first-wave ready sources if the pack is clean enough",
        "",
    ])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(note), encoding="utf-8")
    print(str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
