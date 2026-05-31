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
DEFAULT_VERCEL_PROJECT = "posting-autopilot-next"
RECOVERED_SOURCE_ROOT = ROOT_DIR / "ops" / "prelaunch_artifacts" / "recovered_live_source"


def run_shell(
    cmd: str,
    extra_env: dict | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    try:
        return subprocess.run(
            cmd,
            cwd=ROOT_DIR,
            shell=True,
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            cmd,
            124,
            normalize_text(exc.stdout),
            normalize_text(exc.stderr),
        )


def tail(text: str, limit: int = 40) -> str:
    lines = (text or "").strip().splitlines()
    if len(lines) <= limit:
        return "\n".join(lines)
    return "\n".join(lines[-limit:])


def run_vercel(cmd: str, timeout: float | None = None) -> tuple[subprocess.CompletedProcess, bool]:
    proc = run_shell(cmd, timeout=timeout)
    combined = "\n".join(part for part in [proc.stdout, proc.stderr] if part).lower()
    if proc.returncode != 0 and (
        "unable to get local issuer certificate" in combined or proc.returncode == 124
    ):
        retry = run_shell(
            cmd,
            extra_env={"NODE_TLS_REJECT_UNAUTHORIZED": "0"},
            timeout=timeout,
        )
        return retry, True
    return proc, False


def parse_json_lines(text: str) -> list[dict]:
    rows = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            rows.append(json.loads(stripped))
        except json.JSONDecodeError:
            continue
    return rows


def normalize_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def summarize_live_settings_error(message: str) -> dict | None:
    if not message:
        return None

    exception_match = re.search(r"sqlalchemy\.orm\.exc\.([A-Za-z0-9_]+):", message)
    route_match = re.search(
        r'File "([^"]+/app/routes\.py)", line (\d+), in ([^\n]+)\n\s+session\["user_name"\] = user\.full_name',
        message,
    )
    if not exception_match and not route_match:
        return None

    exception_name = exception_match.group(1) if exception_match else None
    route_file = route_match.group(1) if route_match else None
    route_line = int(route_match.group(2)) if route_match else None
    route_func = route_match.group(3) if route_match else None
    summary = None
    if exception_name == "DetachedInstanceError" and route_file and route_line:
        summary = (
            f"{exception_name} in {route_file}:{route_line} after save while reading "
            "user.full_name for session['user_name']"
        )
    elif exception_name:
        summary = exception_name

    return {
        "summary": summary,
        "exception": exception_name,
        "route_file": route_file,
        "route_line": route_line,
        "route_function": route_func,
    }


def load_json_file(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def latest_path(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return sorted(paths)[-1]


def docker_daemon_unavailable(*texts: str) -> bool:
    combined = "\n".join(text for text in texts if text).lower()
    if not combined:
        return False
    return "cannot connect to the docker daemon" in combined or (
        "docker.sock" in combined and "is the docker daemon running?" in combined
    )


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
    environment_blocked = any(
        item.get("code") == "docker_compose_unavailable"
        or docker_daemon_unavailable(item.get("message", ""))
        for item in issues
    )
    has_warnings = any(item.get("severity") == "warning" for item in issues)
    healthy = baseline.get("status") == "healthy" and not hard_issues
    status = "green" if healthy and not has_warnings else "yellow" if healthy else "blocked" if environment_blocked else "red"
    result.update(
        {
            "status": status,
            "ok": healthy,
            "environment_blocked": environment_blocked,
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
    environment_blocked = docker_daemon_unavailable(proc.stderr, proc.stdout)
    result = {
        "status": "blocked" if environment_blocked else "red",
        "ok": False,
        "command": "bash scripts/compose_with_runtime.sh exec -T web python scripts/launch_guardrail_check.py",
        "stderr": tail(proc.stderr),
        "environment_blocked": environment_blocked,
    }
    if proc.returncode != 0 and not proc.stdout.strip():
        result["message"] = "docker runtime unavailable for guardrail check" if environment_blocked else "guardrail check command failed"
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
    environment_blocked = docker_daemon_unavailable(proc.stderr, proc.stdout)
    result = {
        "status": "blocked" if environment_blocked else "red",
        "ok": False,
        "stderr": tail(proc.stderr),
        "command": "route probe via compose web python",
        "environment_blocked": environment_blocked,
    }
    if proc.returncode != 0:
        result["message"] = "docker runtime unavailable for local route probe" if environment_blocked else "local route probe failed"
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
    degraded_settings_response = "WARN settings save persisted despite 500 response" in output
    deployment_disabled = "DEPLOYMENT_DISABLED" in output or "x-vercel-error DEPLOYMENT_DISABLED" in output
    result = {
        "status": "green" if proc.returncode == 0 else "blocked" if deployment_disabled else "yellow" if proc.returncode == 2 or degraded_settings_response else "red",
        "ok": proc.returncode == 0,
        "command": f"bash scripts/live_deploy_smoke.sh {base_url}",
        "output": output,
        "details": {
            "settings_persisted_despite_500": degraded_settings_response,
            "deployment_disabled": deployment_disabled,
        },
    }
    if deployment_disabled:
        result["message"] = "production deployment disabled on Vercel (DEPLOYMENT_DISABLED / Payment required)"
    elif degraded_settings_response:
        result["message"] = "settings save persists values but returns 500 after save"
    elif proc.returncode != 0:
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


def probe_vercel_production(project_name: str = DEFAULT_VERCEL_PROJECT) -> dict:
    result = {
        "status": "red",
        "ok": False,
        "project_name": project_name,
        "details": {},
    }

    whoami_proc, whoami_tls_retry = run_vercel("vercel whoami", timeout=10)
    if whoami_proc.returncode != 0:
        result["message"] = "vercel whoami failed"
        result["stderr"] = tail(whoami_proc.stderr)
        result["stdout"] = tail(whoami_proc.stdout)
        result["details"]["tls_retry_used"] = whoami_tls_retry
        return result

    project_proc, project_tls_retry = run_vercel(
        f"vercel api /v9/projects/{shlex.quote(project_name)}",
        timeout=10,
    )
    if project_proc.returncode != 0:
        result["message"] = f"vercel project lookup failed for {project_name}"
        result["stderr"] = tail(project_proc.stderr)
        result["stdout"] = tail(project_proc.stdout)
        result["details"]["account"] = whoami_proc.stdout.strip()
        result["details"]["tls_retry_used"] = whoami_tls_retry or project_tls_retry
        return result

    try:
        project_data = json.loads(project_proc.stdout)
    except json.JSONDecodeError:
        result["message"] = "vercel project api output was not valid json"
        result["stdout"] = tail(project_proc.stdout)
        result["details"]["account"] = whoami_proc.stdout.strip()
        result["details"]["tls_retry_used"] = whoami_tls_retry or project_tls_retry
        return result

    production_target = (
        project_data.get("targets", {}).get("production")
        or next(
            (
                item
                for item in project_data.get("latestDeployments", [])
                if item.get("target") == "production"
            ),
            None,
        )
        or {}
    )
    deployment_id = production_target.get("id")

    deployment_data = {}
    deployment_tls_retry = False
    if deployment_id:
        deployment_proc, deployment_tls_retry = run_vercel(
            f"vercel api /v13/deployments/{shlex.quote(deployment_id)}",
            timeout=10,
        )
        if deployment_proc.returncode == 0:
            try:
                deployment_data = json.loads(deployment_proc.stdout)
            except json.JSONDecodeError:
                deployment_data = {}

    logs_proc, logs_tls_retry = run_vercel(
        f"vercel logs --project {shlex.quote(project_name)} --environment production --since 15m --status-code 500 --json --no-branch",
        timeout=10,
    )
    deployment_meta = deployment_data.get("meta") or production_target.get("meta") or {}
    settings_logs = []
    if logs_proc.returncode == 0:
        settings_logs = [
            row
            for row in parse_json_lines(logs_proc.stdout)
            if row.get("requestPath") == "/settings"
            and row.get("responseStatusCode") == 500
            and (not deployment_id or row.get("deploymentId") == deployment_id)
        ]
    latest_settings_log = settings_logs[0] if settings_logs else None
    root_cause = summarize_live_settings_error(latest_settings_log.get("message", "")) if latest_settings_log else None

    result.update(
        {
            "status": "green",
            "ok": True,
            "message": None,
            "details": {
                "account": whoami_proc.stdout.strip(),
                "project_id": project_data.get("id"),
                "framework": project_data.get("framework"),
                "production_deployment_id": deployment_id,
                "production_ready_state": production_target.get("readyState"),
                "production_created_at": production_target.get("createdAt"),
                "production_aliases": production_target.get("alias", []),
                "deployment_source": deployment_data.get("source"),
                "deployment_target": deployment_data.get("target"),
                "deployment_status": deployment_data.get("status"),
                "deployment_meta": deployment_meta,
                "source_tag": deployment_meta.get("source"),
                "base_deployment": deployment_meta.get("base_deployment"),
                "fix_tag": deployment_meta.get("fix"),
                "promotion_action": deployment_meta.get("action"),
                "original_deployment_id": deployment_meta.get("originalDeploymentId"),
                "tls_retry_used": whoami_tls_retry or project_tls_retry or deployment_tls_retry or logs_tls_retry,
                "recent_settings_500_count": len(settings_logs),
                "latest_settings_500": {
                    "timestamp": latest_settings_log.get("timestamp"),
                    "deployment_id": latest_settings_log.get("deploymentId"),
                    "summary": root_cause.get("summary") if root_cause else None,
                    "exception": root_cause.get("exception") if root_cause else None,
                    "route_file": root_cause.get("route_file") if root_cause else None,
                    "route_line": root_cause.get("route_line") if root_cause else None,
                    "request_path": latest_settings_log.get("requestPath") if latest_settings_log else None,
                }
                if latest_settings_log
                else None,
                "latest_settings_500_message_tail": tail(latest_settings_log.get("message", ""), limit=16)
                if latest_settings_log
                else None,
            },
        }
    )
    return result


def probe_recovered_hotfix_lineage(vercel_production: dict) -> dict:
    result = {
        "status": "red",
        "ok": False,
        "details": {},
    }
    production_details = vercel_production.get("details", {}) if vercel_production else {}
    base_deployment = production_details.get("base_deployment")
    project_id = production_details.get("project_id")
    if not base_deployment:
        result["message"] = "no base deployment id recorded in current production metadata"
        return result

    base_dir = RECOVERED_SOURCE_ROOT / base_deployment
    candidate_dir = RECOVERED_SOURCE_ROOT / f"{base_deployment}_hotfix_candidate"
    candidate_src = candidate_dir / "src"
    link_path = candidate_src / ".vercel" / "project.json"
    link_data = load_json_file(link_path) if link_path.exists() else None
    preview_note = latest_path(list(candidate_dir.glob("PREVIEW_DEPLOY_*.md")))
    promotion_note = latest_path(list(candidate_dir.glob("PRODUCTION_PROMOTION_*.md")))
    recovery_note = latest_path(list(base_dir.glob("RECOVERY_NOTES_*.md")))
    hotfix_patch = latest_path(list(base_dir.glob("LIVE_SETTINGS_HOTFIX_*.patch")))
    recovered_routes = base_dir / "src" / "app" / "routes.py"

    project_match = bool(link_data) and link_data.get("projectId") == project_id
    ok = all(
        [
            base_dir.exists(),
            candidate_src.exists(),
            recovered_routes.exists(),
            bool(hotfix_patch),
            bool(recovery_note),
            bool(preview_note),
            bool(promotion_note),
            project_match,
        ]
    )

    result.update(
        {
            "status": "green" if ok else "yellow",
            "ok": ok,
            "message": None if ok else "recovered hotfix lineage is incomplete or not linked to current production project",
            "details": {
                "base_deployment": base_deployment,
                "base_dir": str(base_dir),
                "candidate_dir": str(candidate_dir),
                "candidate_src": str(candidate_src),
                "recovered_routes": str(recovered_routes) if recovered_routes.exists() else None,
                "hotfix_patch": str(hotfix_patch) if hotfix_patch else None,
                "recovery_note": str(recovery_note) if recovery_note else None,
                "preview_note": str(preview_note) if preview_note else None,
                "promotion_note": str(promotion_note) if promotion_note else None,
                "project_link_path": str(link_path) if link_path.exists() else None,
                "linked_project_id": link_data.get("projectId") if link_data else None,
                "linked_project_name": link_data.get("projectName") if link_data else None,
                "project_match": project_match,
            },
        }
    )
    return result


def compute_source_alignment(
    local_routes: dict,
    live_smoke: dict,
    vercel_linkage: dict,
    vercel_production: dict,
    recovered_hotfix_lineage: dict,
) -> dict:
    mismatch_reasons = []
    route_details = local_routes.get("details", {})
    production_details = vercel_production.get("details", {}) if vercel_production else {}
    recovered_lineage_ok = bool(recovered_hotfix_lineage.get("ok"))
    recovered_hotfix_promoted = (
        production_details.get("source_tag") == "recovered-live-hotfix"
        and recovered_lineage_ok
    )

    if route_details:
        if (
            not recovered_hotfix_promoted
            and not route_details.get("settings_route_present")
            and route_details.get("ai_settings_route_present")
        ):
            mismatch_reasons.append("local app exposes /ai/settings while live deploy operator flow uses /settings")
    if not vercel_linkage.get("ok") and not recovered_hotfix_promoted:
        mismatch_reasons.append("local repo has no Vercel linkage metadata for posting-autopilot-next")
    if not vercel_production.get("ok"):
        mismatch_reasons.append(vercel_production.get("message") or "could not inspect Vercel production metadata")
    else:
        if production_details.get("deployment_source") == "cli" and not recovered_hotfix_promoted:
            mismatch_reasons.append("production deployment source is cli, so the exact live snapshot is not pinned to the current git tree")
        if production_details.get("source_tag") == "recovered-live-hotfix" and not recovered_lineage_ok:
            mismatch_reasons.append(recovered_hotfix_lineage.get("message") or "recovered hotfix lineage metadata is incomplete")
        latest_settings_500 = production_details.get("latest_settings_500") or {}
        if latest_settings_500.get("summary"):
            mismatch_reasons.append(f"live /settings 500 root cause: {latest_settings_500['summary']}")
    if live_smoke.get("details", {}).get("settings_persisted_despite_500") and not any(
        reason.startswith("live /settings 500 root cause:")
        for reason in mismatch_reasons
    ):
        mismatch_reasons.append("live /settings persists writes but returns 500 after save, so the deploy response path still diverges from this controlled repo")
    elif not live_smoke.get("ok") and "settings save failed with status 500" in (live_smoke.get("output") or ""):
        mismatch_reasons.append("live /settings save fails with 500 while controlled local settings flow is a different route family")

    return {
        "status": "red" if mismatch_reasons else "green",
        "ok": not mismatch_reasons,
        "details": mismatch_reasons,
    }


def compute_overall(runtime: dict, guardrails: dict, local_routes: dict, multilingual_pilot: dict, live_smoke: dict, source_alignment: dict) -> tuple[str, list[str], list[str], list[str]]:
    blockers = []
    warnings = []
    environment_blockers = []
    if runtime.get("environment_blocked"):
        environment_blockers.append("docker runtime unavailable for local compose checks")
    elif runtime["status"] == "red":
        blockers.append("runtime health failed")
    elif runtime["status"] == "yellow":
        warnings.append("runtime health reported warnings")
    if guardrails.get("environment_blocked"):
        if "docker runtime unavailable for local compose checks" not in environment_blockers:
            environment_blockers.append("docker runtime unavailable for local compose checks")
    elif guardrails["status"] != "green":
        blockers.append("local launch guardrails failed")
    if local_routes.get("environment_blocked"):
        if "docker runtime unavailable for local compose checks" not in environment_blockers:
            environment_blockers.append("docker runtime unavailable for local compose checks")
    if multilingual_pilot["status"] != "green":
        blockers.append("multilingual pilot failed")
    if live_smoke["status"] == "blocked":
        environment_blockers.append(live_smoke.get("message") or "live deploy smoke blocked by external environment")
    elif live_smoke["status"] == "red":
        blockers.append(live_smoke.get("message") or "live deploy smoke failed")
    elif live_smoke["status"] == "yellow":
        warnings.append(live_smoke.get("message") or "live deploy smoke reported degraded behavior")
    if source_alignment["status"] != "green":
        blockers.extend(source_alignment.get("details", []))

    if blockers:
        return "red", environment_blockers + blockers, environment_blockers, warnings

    if environment_blockers:
        return "blocked", environment_blockers, environment_blockers, warnings

    if warnings:
        return "yellow", warnings, [], warnings

    return "green", [], [], []


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("POSTING_AUTOPILOT_BASE_URL", DEFAULT_BASE_URL)

    runtime = probe_runtime()
    guardrails = probe_guardrails()
    multilingual_pilot = probe_multilingual_pilot()
    local_routes = probe_local_routes()
    live_smoke = probe_live_smoke(base_url)
    vercel_linkage = probe_vercel_linkage()
    vercel_production = probe_vercel_production()
    recovered_hotfix_lineage = probe_recovered_hotfix_lineage(vercel_production)
    source_alignment = compute_source_alignment(local_routes, live_smoke, vercel_linkage, vercel_production, recovered_hotfix_lineage)
    overall, blockers, environment_blockers, warnings = compute_overall(runtime, guardrails, local_routes, multilingual_pilot, live_smoke, source_alignment)

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
        "vercel_production": vercel_production,
        "recovered_hotfix_lineage": recovered_hotfix_lineage,
        "source_alignment": source_alignment,
        "live_smoke": live_smoke,
        "environment_blockers": environment_blockers,
        "warnings": warnings,
        "blockers": blockers,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if overall == "green" else 1


if __name__ == "__main__":
    raise SystemExit(main())
