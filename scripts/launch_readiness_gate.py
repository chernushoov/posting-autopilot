#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_READINESS = ROOT / "ops" / "live_vacancy_4_hires" / "generated" / "launch_readiness.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def summarize(readiness: dict) -> list[str]:
    blocked = readiness.get("blocked", []) or []
    launch_gate = readiness.get("launch_gate", {}) or {}
    lines = [
        f"readiness_status={readiness.get('status', 'unknown')}",
        f"launch_gate_status={launch_gate.get('status', 'unknown')}",
    ]
    if blocked:
        lines.append(f"top_blocker={blocked[0]}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail when generated launch readiness is blocked.")
    parser.add_argument("--path", default=str(DEFAULT_READINESS), help="Path to launch_readiness.json")
    parser.add_argument("--quiet", action="store_true", help="Suppress summary output")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        if not args.quiet:
            print(f"launch_readiness_missing={path}")
        return 1

    try:
        readiness = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        if not args.quiet:
            print(f"launch_readiness_invalid={exc}")
        return 1

    if not args.quiet:
        for line in summarize(readiness):
            print(line)

    status = str(readiness.get("status", "unknown")).strip().lower()
    return 2 if status == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
