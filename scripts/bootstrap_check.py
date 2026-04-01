#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.runtime_env import is_placeholder_secret, looks_like_bot_token  # noqa: E402

ENV_PATH = ROOT / ".env"
RUNTIME_ENV_PATH = ROOT / ".env.runtime"
COMPOSE_PATH = ROOT / "docker-compose.yml"
REQUIRED_PATHS = [
    ROOT / "app",
    ROOT / "bot",
    ROOT / "worker",
    ROOT / "common",
    ROOT / "scripts",
]
PROMPT_FILES = []
REQUIRED_ENV_KEYS = [
    "FLASK_SECRET_KEY",
    "ADMIN_LOGIN",
    "ADMIN_PASSWORD",
    "DATABASE_URL",
    "REDIS_URL",
]


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text("utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


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


def run(cmd: list[str]) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except Exception as exc:
        return False, str(exc)
    output = (proc.stdout or proc.stderr or "").strip()
    return proc.returncode == 0, output


def check() -> dict:
    issues = []
    env = parse_env_file(ENV_PATH)
    runtime_env = parse_env_file(RUNTIME_ENV_PATH)

    for path in REQUIRED_PATHS:
        if not path.exists():
            issues.append({
                "severity": "critical",
                "code": "path_missing",
                "message": f"Missing required path: {path.name}",
            })

    if not COMPOSE_PATH.exists():
        issues.append({
            "severity": "critical",
            "code": "compose_missing",
            "message": "docker-compose.yml is missing.",
        })

    if not ENV_PATH.exists():
        issues.append({
            "severity": "critical",
            "code": "env_missing",
            "message": ".env is missing. Copy .env.example first.",
        })

    for key in REQUIRED_ENV_KEYS:
        if not (env.get(key) or "").strip():
            issues.append({
                "severity": "critical",
                "code": f"{key.lower()}_missing",
                "message": f"{key} is missing in .env.",
            })

    token, token_source = get_env_value(env, runtime_env, "RECRUITBOT_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN")
    if not token:
        issues.append({
            "severity": "critical",
            "code": "telegram_token_missing",
            "message": "Recruit bot token is missing.",
        })
    elif is_placeholder_secret(token) or not looks_like_bot_token(token):
        issues.append({
            "severity": "critical",
            "code": "telegram_token_invalid",
            "message": f"Recruit bot token from {token_source or 'none'} is placeholder or invalid.",
        })

    ai_provider, ai_provider_source = get_env_value(env, runtime_env, "RECRUITBOT_AI_PROVIDER", "AI_PROVIDER")
    ai_provider = (ai_provider or "stub").strip() or "stub"
    ai_key, ai_key_source = get_env_value(env, runtime_env, "RECRUITBOT_AI_API_KEY", "AI_API_KEY")
    if ai_provider not in {"", "stub"} and not ai_key:
        issues.append({
            "severity": "warning",
            "code": "ai_key_missing",
            "message": f"AI provider '{ai_provider}' from {ai_provider_source or 'none'} is configured without API key.",
        })

    docker_ok, docker_out = run(["docker", "--version"])
    if not docker_ok:
        issues.append({
            "severity": "critical",
            "code": "docker_unavailable",
            "message": docker_out or "docker is not available.",
        })

    compose_ok, compose_out = run(["docker", "compose", "config", "--services"])
    services = compose_out.splitlines() if compose_ok and compose_out else []
    if not compose_ok:
        issues.append({
            "severity": "critical",
            "code": "compose_invalid",
            "message": compose_out or "docker compose config failed.",
        })

    summary = {
        "status": "ready" if not any(i["severity"] == "critical" for i in issues) else "blocked",
        "project_root": str(ROOT),
        "env_file_exists": ENV_PATH.exists(),
        "runtime_env_file_exists": RUNTIME_ENV_PATH.exists(),
        "compose_file_exists": COMPOSE_PATH.exists(),
        "docker_ok": docker_ok,
        "compose_services": services,
        "issues": issues,
        "commands": {
            "runtime_check": "bash scripts/runtime_check_with_env.sh",
            "compose_ps": "bash scripts/compose_with_runtime.sh ps -a",
            "compose_up_core": "bash scripts/compose_with_runtime.sh up -d postgres redis web",
            "compose_up_async": "bash scripts/compose_with_runtime.sh up -d worker scheduler",
            "compose_up_full": "bash scripts/compose_with_runtime.sh up -d postgres redis web worker scheduler bot",
        },
    }
    return summary


def print_human(result: dict) -> None:
    print(f"[{result['status']}] recruit bootstrap")
    print(f"root: {result['project_root']}")
    print(f"env: {'ok' if result['env_file_exists'] else 'missing'} | runtime-env: {'ok' if result.get('runtime_env_file_exists') else 'missing'} | compose: {'ok' if result['compose_file_exists'] else 'missing'} | docker: {'ok' if result['docker_ok'] else 'missing'}")
    print("services:", ", ".join(result.get("compose_services") or []) or "—")
    issues = result.get("issues") or []
    if issues:
      print("issues:")
      for issue in issues:
          print(f"- [{issue['severity']}] {issue['message']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Recruit Autopilot bootstrap readiness check")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print JSON")
    args = parser.parse_args()
    result = check()
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print_human(result)
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
