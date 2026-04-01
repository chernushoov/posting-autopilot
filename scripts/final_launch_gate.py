#!/usr/bin/env python3

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_BASE_URL = "https://posting-autopilot-next.vercel.app"


def run_shell(cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=ROOT_DIR,
        shell=True,
        text=True,
        capture_output=True,
    )


def tail(text: str, limit: int = 40) -> str:
    lines = (text or "").strip().splitlines()
    if len(lines) <= limit:
        return "\n".join(lines)
    return "\n".join(lines[-limit:])


def probe_runtime() -> dict:
    proc = run_shell("bash scripts/runtime_check_with_env.sh --json")
    result = {
        "status": "red",
        "ok": False,
        "command": "bash scripts/runtime_check_with_env.sh --json",
        "summary": None,
        "details": {},
        "stderr": tail(proc.stderr),
    }
    if proc.returncode != 0:
        result["message"] = "runtime check command failed"
        result["stdout"] = tail(proc.stdout)
        return result

    data = json.loads(proc.stdout)
    issues = data.get("diagnostics", {}).get("issues", [])
    hard_issues = [item for item in issues if item.get("severity") == "error"]
    baseline = data.get("baseline", {})
    has_warnings = any(item.get("severity") == "warning" for item in issues)
    healthy = baseline.get("status") == "healthy" and not hard_issues
    status = "green" if healthy and not has_warnings else "yellow" if healthy else "red"
    result.update(
        {
            "status": status,
            "ok": healthy,
            "summary": baseline.get("summary"),
            "details": {
                "baseline_status": baseline.get("status"),
                "running_services": data.get("runtime", {}).get("running_services"),
                "total_services": data.get("runtime", {}).get("total_services"),
                "issues": issues,
            },
        }
    )
    return result


def probe_multilingual_pilot() -> dict:
    proc = run_shell("python3 scripts/multilingual_pilot_check.py")
    result = {
        "status": "red",
        "ok": False,
        "command": "python3 scripts/multilingual_pilot_check.py",
        "stderr": tail(proc.stderr),
    }
    if proc.returncode != 0 and not proc.stdout.strip():
        result["message"] = "multilingual pilot command failed"
        return result

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        result["message"] = "multilingual pilot output was not valid json"
        result["stdout"] = tail(proc.stdout)
        return result

    result.update(
        {
            "status": "green" if data.get("overall_ok") else "red",
            "ok": bool(data.get("overall_ok")),
            "details": data,
        }
    )
    return result


def probe_guardrails() -> dict:
    proc = run_shell("bash scripts/compose_with_runtime.sh exec -T web python scripts/launch_guardrail_check.py")
    result = {
        "status": "red",
        "ok": False,
        "command": "bash scripts/compose_with_runtime.sh exec -T web python scripts/launch_guardrail_check.py",
        "stderr": tail(proc.stderr),
    }
    if proc.returncode != 0 and not proc.stdout.strip():
        result["message"] = "guardrail check command failed"
        return result

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        result["message"] = "guardrail output was not valid json"
        result["stdout"] = tail(proc.stdout)
        return result

    result.update(
        {
            "status": "green" if data.get("ok") else "red",
            "ok": bool(data.get("ok")),
            "details": data.get("checks", []),
        }
    )
    return result


def probe_local_routes() -> dict:
    cmd = """bash scripts/compose_with_runtime.sh exec -T web python - <<'PY'
from app.factory import create_app
import json
app = create_app()
routes = []
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    methods = sorted(rule.methods - {'HEAD', 'OPTIONS'})
    if 'settings' in rule.rule or 'campaign' in rule.rule or 'source' in rule.rule:
        routes.append({'rule': rule.rule, 'methods': methods})
print(json.dumps({'routes': routes}))
PY"""
    proc = run_shell(cmd)
    result = {
        "status": "red",
        "ok": False,
        "stderr": tail(proc.stderr),
        "command": "route probe via compose web python",
    }
    if proc.returncode != 0:
        result["message"] = "local route probe failed"
        result["stdout"] = tail(proc.stdout)
        return result

    data = json.loads(proc.stdout)
    routes = data.get("routes", [])
    rule_set = {item["rule"] for item in routes}
    settings_route_present = "/settings" in rule_set
    ai_settings_route_present = "/ai/settings" in rule_set
    result.update(
        {
            "status": "green",
            "ok": True,
            "details": {
                "settings_route_present": settings_route_present,
                "ai_settings_route_present": ai_settings_route_present,
                "routes": routes,
            },
        }
    )
    return result


def probe_live_smoke(base_url: str) -> dict:
    quoted = shlex.quote(base_url)
    proc = run_shell(f"bash scripts/live_deploy_smoke.sh {quoted}")
    output = tail("\n".join(part for part in [proc.stdout, proc.stderr] if part))
    result = {
        "status": "green" if proc.returncode == 0 else "red",
        "ok": proc.returncode == 0,
        "command": f"bash scripts/live_deploy_smoke.sh {base_url}",
        "output": output,
    }
    if proc.returncode != 0:
        match = re.search(r"FAIL (.+)", output)
        result["message"] = match.group(1) if match else "live smoke failed"
    return result


def probe_vercel_linkage() -> dict:
    proc = run_shell("rg --files -g 'vercel.json' -g '.vercel/**'")
    files = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    linked = bool(files)
    return {
        "status": "green" if linked else "yellow",
        "ok": linked,
        "details": {
            "linked_files": files,
        },
        "message": None if linked else "no local Vercel linkage metadata found in this repo",
    }


def compute_source_alignment(local_routes: dict, live_smoke: dict, vercel_linkage: dict) -> dict:
    mismatch_reasons = []
    route_details = local_routes.get("details", {})
    if route_details:
        if not route_details.get("settings_route_present") and route_details.get("ai_settings_route_present"):
            mismatch_reasons.append("local app exposes /ai/settings while live deploy operator flow uses /settings")
    if not vercel_linkage.get("ok"):
        mismatch_reasons.append("local repo has no Vercel linkage metadata for posting-autopilot-next")
    if not live_smoke.get("ok") and "settings save failed with status 500" in (live_smoke.get("output") or ""):
        mismatch_reasons.append("live /settings save fails with 500 while controlled local settings flow is a different route family")

    return {
        "status": "red" if mismatch_reasons else "green",
        "ok": not mismatch_reasons,
        "details": mismatch_reasons,
    }


def compute_overall(runtime: dict, guardrails: dict, multilingual_pilot: dict, live_smoke: dict, source_alignment: dict) -> tuple[str, list[str]]:
    blockers = []
    if runtime["status"] == "red":
        blockers.append("runtime health failed")
    if guardrails["status"] != "green":
        blockers.append("local launch guardrails failed")
    if multilingual_pilot["status"] != "green":
        blockers.append("multilingual pilot failed")
    if live_smoke["status"] != "green":
        blockers.append(live_smoke.get("message") or "live deploy smoke failed")
    if source_alignment["status"] != "green":
        blockers.extend(source_alignment.get("details", []))

    if blockers:
        return "red", blockers

    if runtime["status"] == "yellow":
        return "yellow", ["runtime health reported warnings"]

    return "green", []


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("POSTING_AUTOPILOT_BASE_URL", DEFAULT_BASE_URL)

    runtime = probe_runtime()
    guardrails = probe_guardrails()
    multilingual_pilot = probe_multilingual_pilot()
    local_routes = probe_local_routes()
    live_smoke = probe_live_smoke(base_url)
    vercel_linkage = probe_vercel_linkage()
    source_alignment = compute_source_alignment(local_routes, live_smoke, vercel_linkage)
    overall, blockers = compute_overall(runtime, guardrails, multilingual_pilot, live_smoke, source_alignment)

    result = {
        "checked_at": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], text=True, capture_output=True).stdout.strip(),
        "base_url": base_url,
        "overall_status": overall,
        "launch_ready": overall == "green",
        "runtime": runtime,
        "local_guardrails": guardrails,
        "multilingual_pilot": multilingual_pilot,
        "local_route_probe": local_routes,
        "vercel_linkage": vercel_linkage,
        "source_alignment": source_alignment,
        "live_smoke": live_smoke,
        "blockers": blockers,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if overall == "green" else 1


if __name__ == "__main__":
    raise SystemExit(main())
