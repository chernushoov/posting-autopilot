#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from build_live_vacancy_pack import INTAKE_PATH, OUT_DIR, missing_fields


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_token_status() -> dict:
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "runtime_env_status.py"), "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except Exception as exc:
        return {
            "telegram": {
                "valid_format": False,
                "source": None,
                "masked": None,
            },
            "error": str(exc),
        }


def build_report() -> dict:
    intake = load_json(INTAKE_PATH)
    missing = missing_fields(intake)
    generated_files = []
    if OUT_DIR.exists():
        generated_files = sorted(p.name for p in OUT_DIR.iterdir() if p.is_file())

    token_status = get_token_status()
    telegram = token_status.get("telegram", {})
    token_valid = bool(telegram.get("valid_format")) and not bool(telegram.get("reserved_for_other_runtime"))

    ready_now = [
        "Sunday bundle files",
        "Client intake message",
        "Operator intake structure",
        "Posting templates",
        "Screening pack",
        "Source plan",
        "Pilot tracking",
        "Case-study capture",
        "Manual candidate pipeline",
    ]

    needs_input = missing

    blocked = []
    if not token_valid:
        blocked.append("RecruitBot Telegram bot apply path")

    return {
        "status": "ready_for_manual_launch" if not needs_input else "needs_client_input",
        "ready_now": ready_now,
        "needs_quick_input": needs_input,
        "blocked": blocked,
        "generated_files": generated_files,
        "telegram": telegram,
    }


def print_text(report: dict) -> None:
    print(f"status={report['status']}")
    print("\nREADY NOW")
    for item in report["ready_now"]:
        print(f"- {item}")
    print("\nNEEDS QUICK INPUT")
    if report["needs_quick_input"]:
        for item in report["needs_quick_input"]:
            print(f"- {item}")
    else:
        print("- none")
    print("\nBLOCKED")
    if report["blocked"]:
        for item in report["blocked"]:
            print(f"- {item}")
    else:
        print("- none")
    print("\nGENERATED FILES")
    if report["generated_files"]:
        for item in report["generated_files"]:
            print(f"- {item}")
    else:
        print("- none")
    telegram = report.get("telegram", {})
    print("\nTELEGRAM")
    print(f"- token_valid={telegram.get('valid_format')}")
    if telegram.get("bot_identity"):
        print(f"- username={telegram.get('bot_identity', {}).get('username')}")
        print(f"- reserved_for_other_runtime={telegram.get('reserved_for_other_runtime')}")
    print(f"- source={telegram.get('source')}")
    print(f"- masked={telegram.get('masked')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Sunday launch readiness for RecruitBot live vacancy prep")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = build_report()
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
