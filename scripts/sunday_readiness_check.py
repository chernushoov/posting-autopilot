#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from build_live_vacancy_pack import INTAKE_PATH, OUT_DIR, missing_fields


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
DEFAULT_BASE_URL = "https://posting-autopilot-next.vercel.app"
LAUNCH_GATE_PATH = ROOT / "ops" / "prelaunch_artifacts" / "launch_gate" / "latest.json"
LAUNCH_GATE_MAX_AGE = timedelta(hours=24)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_text() -> str:
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def tail(text: str, limit: int = 10) -> str:
    lines = [line for line in (text or "").splitlines() if line.strip()]
    if len(lines) <= limit:
        return "\n".join(lines)
    return "\n".join(lines[-limit:])


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


def extract_launch_gate_blockers(data: dict) -> list[str]:
    blockers: list[str] = []

    def add(value: str | None) -> None:
        if value and value not in blockers:
            blockers.append(value)

    live_smoke = data.get("live_smoke", {}) or {}
    vercel_production = data.get("vercel_production", {}) or {}

    add(live_smoke.get("message"))
    add(vercel_production.get("message"))

    for item in data.get("environment_blockers", []) or []:
        lowered = item.lower()
        if "deployment_disabled" in lowered or "payment required" in lowered or "vercel" in lowered:
            add(item)

    for item in data.get("blockers", []) or []:
        lowered = item.lower()
        if "deployment_disabled" in lowered or "payment required" in lowered or "vercel" in lowered:
            add(item)

    return blockers


def load_cached_launch_gate() -> dict | None:
    if not LAUNCH_GATE_PATH.exists():
        return None
    try:
        data = load_json(LAUNCH_GATE_PATH)
    except (OSError, json.JSONDecodeError):
        return None

    checked_at = parse_timestamp(data.get("checked_at"))
    fresh = checked_at is not None and utc_now() - checked_at <= LAUNCH_GATE_MAX_AGE
    blockers = extract_launch_gate_blockers(data)
    live_smoke = data.get("live_smoke", {}) or {}
    vercel_production = data.get("vercel_production", {}) or {}

    return {
        "source": "launch_gate_snapshot",
        "checked_at": data.get("checked_at"),
        "fresh": fresh,
        "status": live_smoke.get("status") or vercel_production.get("status") or data.get("overall_status") or "unknown",
        "message": live_smoke.get("message") or vercel_production.get("message"),
        "blockers": blockers,
    }


def probe_live_launch_gate() -> dict:
    base_url = os.environ.get("POSTING_AUTOPILOT_BASE_URL", DEFAULT_BASE_URL)
    try:
        proc = subprocess.run(
            ["bash", str(ROOT / "scripts" / "live_deploy_smoke.sh"), base_url],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return {
            "source": "live_deploy_smoke",
            "checked_at": utc_now_text(),
            "fresh": True,
            "status": "red",
            "message": f"live deploy smoke could not run: {exc}",
            "blockers": [],
        }

    output = "\n".join(part for part in [proc.stdout, proc.stderr] if part).strip()
    output_tail = tail(output)
    deployment_disabled = "DEPLOYMENT_DISABLED" in output or "x-vercel-error DEPLOYMENT_DISABLED" in output
    settings_persisted_with_500 = "WARN settings save persisted despite 500 response" in output

    message = None
    blockers: list[str] = []
    if deployment_disabled:
        message = "RecruitBot production deployment disabled on Vercel (DEPLOYMENT_DISABLED / Payment required)"
        blockers.append(message)
        status = "blocked"
    elif proc.returncode == 0:
        status = "green"
    elif proc.returncode == 2 or settings_persisted_with_500:
        status = "yellow"
        message = "settings save persists values but returns 500 after save"
    else:
        status = "red"
        match = re.search(r"FAIL (.+)", output)
        message = match.group(1) if match else "live deploy smoke failed"

    return {
        "source": "live_deploy_smoke",
        "checked_at": utc_now_text(),
        "fresh": True,
        "status": status,
        "message": message,
        "blockers": blockers,
        "output_tail": output_tail,
        "base_url": base_url,
    }


def get_launch_gate_status() -> dict:
    cached = load_cached_launch_gate()
    if cached and cached.get("fresh"):
        return cached
    return probe_live_launch_gate()


def write_report(report: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "launch_readiness.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_report() -> dict:
    intake = load_json(INTAKE_PATH)
    missing = missing_fields(intake)
    generated_files = []
    if OUT_DIR.exists():
        generated_files = sorted(p.name for p in OUT_DIR.iterdir() if p.is_file())

    token_status = get_token_status()
    telegram = token_status.get("telegram", {})
    token_valid = bool(telegram.get("valid_format")) and not bool(telegram.get("reserved_for_other_runtime"))
    launch_gate = get_launch_gate_status()

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
    for item in launch_gate.get("blockers", []):
        if item not in blocked:
            blocked.append(item)

    if blocked:
        status = "blocked"
    elif missing:
        status = "needs_input"
    else:
        status = "ready_for_manual_launch"

    return {
        "status": status,
        "ready_now": ready_now,
        "needs_quick_input": needs_input,
        "missing_fields": needs_input,
        "blocked": blocked,
        "generated_files": generated_files,
        "telegram": telegram,
        "launch_gate": launch_gate,
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
    launch_gate = report.get("launch_gate", {})
    print("\nLAUNCH GATE")
    print(f"- source={launch_gate.get('source')}")
    print(f"- status={launch_gate.get('status')}")
    print(f"- checked_at={launch_gate.get('checked_at')}")
    print(f"- fresh={launch_gate.get('fresh')}")
    print(f"- message={launch_gate.get('message') or 'none'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Sunday launch readiness for RecruitBot live vacancy prep")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = build_report()
    write_report(report)
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
