#!/usr/bin/env python3
import argparse
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.runtime_env import (  # noqa: E402
    is_placeholder_secret,
    looks_like_bot_token,
    mask_secret,
)

ENV_PATH = ROOT / ".env"
RUNTIME_ENV_PATH = ROOT / ".env.runtime"
COMPOSE_PATH = ROOT / "docker-compose.yml"
EXPECTED_SERVICES = ["postgres", "redis", "web", "worker", "scheduler", "bot"]


def fetch_bot_identity(token: str) -> dict | None:
    token = (token or "").strip()
    if not token:
        return None
    try:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=10,
            context=context,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None

    result = payload.get("result")
    if not payload.get("ok") or not isinstance(result, dict):
        return None
    return {
        "id": result.get("id"),
        "username": result.get("username"),
        "first_name": result.get("first_name"),
    }


def is_wrong_recruit_identity(identity: dict | None) -> bool:
    if not identity:
        return False
    username = (identity.get("username") or "").strip().lower()
    first_name = (identity.get("first_name") or "").strip().lower()
    return username == "connectoragent_bot" or first_name == "moltbot"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text("utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value
    return values


def run(cmd: list[str], cwd: Path = ROOT) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except Exception as exc:
        return False, str(exc)
    output = (proc.stdout or proc.stderr or "").strip()
    return proc.returncode == 0, output


def parse_compose_ps(raw: str) -> list[dict]:
    rows: list[dict] = []
    for line in (raw or "").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            rows.append(json.loads(text))
        except json.JSONDecodeError:
            continue
    return rows


def get_env_value(base_values: dict[str, str], runtime_values: dict[str, str], primary: str, fallback: str) -> tuple[str, str | None]:
    primary_os = (os.getenv(primary) or "").strip()
    if primary_os:
        return primary_os, primary
    fallback_os = (os.getenv(fallback) or "").strip()
    if fallback_os:
        return fallback_os, fallback
    primary_value = (runtime_values.get(primary) or "").strip()
    if primary_value:
        return primary_value, primary
    fallback_value = (runtime_values.get(fallback) or "").strip()
    if fallback_value:
        return fallback_value, fallback
    primary_value = (base_values.get(primary) or "").strip()
    if primary_value:
        return primary_value, primary
    fallback_value = (base_values.get(fallback) or "").strip()
    if fallback_value:
        return fallback_value, fallback
    return "", None


def detect_bot_log_issue(text: str) -> tuple[str | None, str | None]:
    if not text:
        return None, None
    lowered = text.lower()
    if "tokenvalidationerror" in lowered or "token is invalid" in lowered:
        return "telegram_token_invalid", "Bot log says Telegram token is invalid."
    if "telegram_bot_token missing" in lowered or "recruitbot_telegram_bot_token/telegram_bot_token missing" in lowered:
        return "telegram_token_missing", "Bot log says Telegram token is missing."
    if "terminated by other getupdates request" in lowered or "409 conflict" in lowered:
        return "telegram_polling_conflict", "Bot log shows Telegram polling conflict with another consumer."
    if "connected as @" in lowered or "polling telegram as @" in lowered:
        return None, None
    return "bot_runtime_error", text.splitlines()[-1][:200]


def build_result() -> dict:
    checked_at = utc_now()
    if not ROOT.exists() or not COMPOSE_PATH.exists():
        return {
            "project": "recruitbot",
            "checked_at": checked_at,
            "baseline": {
                "status": "blocked",
                "summary": "Recruit Autopilot repo or docker-compose.yml is missing locally.",
                "blocker": "Expected project root or docker-compose.yml is not present.",
            },
            "runtime": {
                "type": "docker-compose",
                "root": str(ROOT),
                "available": False,
                "expected_services": EXPECTED_SERVICES,
                "running_services": 0,
                "total_services": len(EXPECTED_SERVICES),
                "services": [],
                "checked_at": checked_at,
            },
            "diagnostics": {
                "issues": [
                    {
                        "severity": "critical",
                        "code": "recruit_repo_missing",
                        "message": "Recruit Autopilot local path is missing.",
                    }
                ]
            },
        }

    env_values = parse_env_file(ENV_PATH)
    runtime_env_values = parse_env_file(RUNTIME_ENV_PATH)
    token_value, token_source = get_env_value(env_values, runtime_env_values, "RECRUITBOT_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN")
    ai_provider, ai_provider_source = get_env_value(env_values, runtime_env_values, "RECRUITBOT_AI_PROVIDER", "AI_PROVIDER")
    ai_key, ai_key_source = get_env_value(env_values, runtime_env_values, "RECRUITBOT_AI_API_KEY", "AI_API_KEY")

    compose_ok, compose_out = run(["docker", "compose", "ps", "-a", "--format", "json"])
    if not compose_ok:
        return {
            "project": "recruitbot",
            "checked_at": checked_at,
            "baseline": {
                "status": "blocked",
                "summary": "Recruit stack exists locally, but docker compose status could not be read.",
                "blocker": compose_out or "docker compose ps failed.",
            },
            "runtime": {
                "type": "docker-compose",
                "root": str(ROOT),
                "available": False,
                "expected_services": EXPECTED_SERVICES,
                "running_services": 0,
                "total_services": len(EXPECTED_SERVICES),
                "services": [],
                "checked_at": checked_at,
                "last_error": compose_out or "docker compose ps failed",
            },
            "diagnostics": {
                "issues": [
                    {
                        "severity": "critical",
                        "code": "docker_compose_unavailable",
                        "message": compose_out or "docker compose ps failed.",
                    }
                ]
            },
        }

    rows = parse_compose_ps(compose_out)
    by_service = {str(row.get("Service", "")).strip(): row for row in rows}
    services = []
    for service in EXPECTED_SERVICES:
        row = by_service.get(service)
        running = bool(row) and str(row.get("State", "")).lower() == "running"
        publishers = row.get("Publishers") if isinstance(row, dict) else []
        published_ports = []
        if isinstance(publishers, list):
            for item in publishers:
                if not isinstance(item, dict):
                    continue
                port = item.get("PublishedPort")
                if isinstance(port, int) and port > 0 and port not in published_ports:
                    published_ports.append(port)
        services.append(
            {
                "service": service,
                "running": running,
                "state": str(row.get("State", "missing")).lower() if row else "missing",
                "status": str(row.get("Status") or row.get("State") or "unknown") if row else "not created",
                "container": row.get("Name") or row.get("Names") if row else None,
                "published_ports": published_ports,
            }
        )

    running_services = [item for item in services if item["running"]]
    non_running_services = [item for item in services if not item["running"]]
    web_service = next((item for item in services if item["service"] == "web"), None)
    web_port = web_service["published_ports"][0] if web_service and web_service["published_ports"] else None
    core_ready = all(item["running"] for item in services if item["service"] in {"postgres", "redis", "web"})

    issues = []
    token_placeholder = is_placeholder_secret(token_value)
    token_valid = looks_like_bot_token(token_value)
    bot_identity = fetch_bot_identity(token_value) if token_valid and not token_placeholder else None
    wrong_identity = is_wrong_recruit_identity(bot_identity)
    ai_provider_value = (ai_provider or "stub").strip() or "stub"

    if not token_value:
        issues.append(
            {
                "severity": "critical",
                "code": "telegram_token_missing",
                "message": "Recruit bot token is missing. Set RECRUITBOT_TELEGRAM_BOT_TOKEN in .env.runtime, exported env, or .env.",
            }
        )
    elif token_placeholder or not token_valid:
        issues.append(
            {
                "severity": "critical",
                "code": "telegram_token_invalid",
                "message": "Recruit bot token is placeholder or invalid. Set a dedicated RECRUITBOT_TELEGRAM_BOT_TOKEN in .env.runtime, exported env, or .env.",
            }
        )
    elif wrong_identity:
        issues.append(
            {
                "severity": "critical",
                "code": "telegram_token_wrong_bot",
                "message": "Recruit bot token currently belongs to the main MoltBot bot, not a dedicated RecruitBot bot.",
            }
        )

    if ai_provider_value not in {"", "stub"} and not ai_key:
        issues.append(
            {
                "severity": "warning",
                "code": "ai_api_key_missing",
                "message": f"AI provider '{ai_provider_value}' is configured without an API key.",
            }
        )
    elif ai_provider_value in {"", "stub"}:
        issues.append(
            {
                "severity": "info",
                "code": "ai_stub_mode",
                "message": "AI provider is still in stub mode. Telegram bot can run, but AI behavior remains placeholder.",
            }
        )

    if non_running_services:
        for item in non_running_services:
            severity = "critical" if item["service"] == "bot" else "warning"
            issues.append(
                {
                    "severity": severity,
                    "code": f"service_{item['service']}_{item['state']}",
                    "message": f"{item['service']} service is {item['state']}.",
                }
            )

    bot_logs_ok, bot_logs_out = run(["docker", "compose", "logs", "--tail=40", "bot"])
    bot_log_code, bot_log_message = detect_bot_log_issue(bot_logs_out if bot_logs_ok else "")
    if bot_log_code and bot_log_code not in {issue["code"] for issue in issues}:
        issues.insert(
            0,
            {
                "severity": "critical" if "telegram_" in bot_log_code else "warning",
                "code": bot_log_code,
                "message": bot_log_message,
            },
        )

    critical_issues = [item for item in issues if item["severity"] == "critical"]
    status = "healthy"
    if not core_ready:
        status = "blocked"
    elif critical_issues or non_running_services:
        status = "mixed"

    summary = (
        f"{len(running_services)}/{len(services)} containers running: "
        f"{', '.join(item['service'] for item in running_services) or 'none'}"
    )
    if web_port:
        summary += f" | web :{web_port}"

    blocker = critical_issues[0]["message"] if critical_issues else None
    if not blocker and non_running_services:
        blocker = "Non-running containers: " + ", ".join(
            f"{item['service']} [{item['state']}]" for item in non_running_services
        ) + "."

    return {
        "project": "recruitbot",
        "checked_at": checked_at,
        "baseline": {
            "status": status,
            "summary": summary,
            "blocker": blocker,
        },
        "runtime": {
            "type": "docker-compose",
            "root": str(ROOT),
            "available": True,
            "expected_services": EXPECTED_SERVICES,
            "running_services": len(running_services),
            "total_services": len(services),
            "services": services,
            "checked_at": checked_at,
            "bot_log_hint": bot_log_message,
        },
        "diagnostics": {
            "env_file_exists": ENV_PATH.exists(),
            "runtime_env_file_exists": RUNTIME_ENV_PATH.exists(),
            "telegram": {
                "source": token_source,
                "present": bool(token_value),
                "placeholder": token_placeholder,
                "valid_format": token_valid,
                "masked": mask_secret(token_value),
                "bot_identity": bot_identity,
                "reserved_for_other_runtime": wrong_identity,
            },
            "ai": {
                "provider": ai_provider_value,
                "provider_source": ai_provider_source,
                "api_key_present": bool(ai_key),
                "api_key_source": ai_key_source,
                "stub_mode": ai_provider_value in {"", "stub"},
            },
            "issues": issues,
        },
        "commands": {
            "runtime_check": "bash scripts/runtime_check_with_env.sh --json",
            "compose_ps": "bash scripts/compose_with_runtime.sh ps -a",
            "compose_up_core": "bash scripts/compose_with_runtime.sh up -d postgres redis web",
            "compose_up_async": "bash scripts/compose_with_runtime.sh up -d worker scheduler",
            "compose_up_full": "bash scripts/compose_with_runtime.sh up -d postgres redis web worker scheduler bot",
            "bot_up": "bash scripts/compose_with_runtime.sh up -d bot",
            "bot_logs": "bash scripts/compose_with_runtime.sh logs -f bot",
            "worker_logs": "bash scripts/compose_with_runtime.sh logs -f worker",
            "scheduler_logs": "bash scripts/compose_with_runtime.sh logs -f scheduler",
        },
    }


def print_human(result: dict) -> None:
    print(f"[{result['baseline']['status']}] {result['baseline']['summary']}")
    if result["baseline"].get("blocker"):
        print(f"blocker: {result['baseline']['blocker']}")
    diagnostics = result.get("diagnostics") or {}
    telegram = diagnostics.get("telegram") or {}
    ai = diagnostics.get("ai") or {}
    print(
        "telegram:",
        f"source={telegram.get('source') or 'none'}",
        f"present={telegram.get('present')}",
        f"placeholder={telegram.get('placeholder')}",
        f"valid={telegram.get('valid_format')}",
        f"masked={telegram.get('masked') or '—'}",
    )
    print(
        "ai:",
        f"provider={ai.get('provider') or 'stub'}",
        f"api_key_present={ai.get('api_key_present')}",
    )
    issues = diagnostics.get("issues") or []
    if issues:
        print("issues:")
        for issue in issues:
            print(f"- [{issue['severity']}] {issue['message']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Recruit Autopilot runtime diagnostics")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print JSON output")
    args = parser.parse_args()
    result = build_result()
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
