#!/usr/bin/env python3
import argparse
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.runtime_env import is_placeholder_secret, looks_like_bot_token, mask_secret  # noqa: E402

ENV_PATH = ROOT / ".env"
RUNTIME_ENV_PATH = ROOT / ".env.runtime"


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


def read_keychain_secret(service_name: str) -> str:
    try:
        proc = subprocess.run(
            ["security", "find-generic-password", "-w", "-s", service_name],
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").strip()


def resolve_value(primary: str, fallback: str, keychain_service: str | None = None) -> dict:
    primary_os = (os.getenv(primary) or "").strip()
    if primary_os:
        return {"value": primary_os, "source": primary}

    fallback_os = (os.getenv(fallback) or "").strip()
    if fallback_os:
        return {"value": fallback_os, "source": fallback}

    runtime_env = parse_env_file(RUNTIME_ENV_PATH)
    primary_runtime = (runtime_env.get(primary) or "").strip()
    if primary_runtime:
        return {"value": primary_runtime, "source": f".env.runtime:{primary}"}
    fallback_runtime = (runtime_env.get(fallback) or "").strip()
    if fallback_runtime:
        return {"value": fallback_runtime, "source": f".env.runtime:{fallback}"}

    if keychain_service:
        keychain_value = read_keychain_secret(keychain_service)
        if keychain_value:
            return {"value": keychain_value, "source": f"keychain:{keychain_service}"}

    env_file = parse_env_file(ENV_PATH)
    primary_file = (env_file.get(primary) or "").strip()
    if primary_file:
        return {"value": primary_file, "source": f".env:{primary}"}
    fallback_file = (env_file.get(fallback) or "").strip()
    if fallback_file:
        return {"value": fallback_file, "source": f".env:{fallback}"}

    return {"value": "", "source": None}


def build_status() -> dict:
    token = resolve_value("RECRUITBOT_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN", "recruitbot_telegram_bot_token")
    ai_provider = resolve_value("RECRUITBOT_AI_PROVIDER", "AI_PROVIDER", "recruitbot_ai_provider")
    ai_key = resolve_value("RECRUITBOT_AI_API_KEY", "AI_API_KEY", "recruitbot_ai_api_key")

    token_value = token["value"]
    token_present = bool(token_value)
    token_placeholder = is_placeholder_secret(token_value)
    token_valid = looks_like_bot_token(token_value)
    bot_identity = fetch_bot_identity(token_value) if token_valid and not token_placeholder else None
    wrong_identity = is_wrong_recruit_identity(bot_identity)

    issues = []
    if not token_present:
        issues.append("Recruit bot token is missing.")
    elif token_placeholder or not token_valid:
        issues.append("Recruit bot token is placeholder or invalid.")
    elif wrong_identity:
        issues.append("Recruit bot token currently belongs to the main MoltBot bot, not a dedicated RecruitBot bot.")

    ai_provider_value = (ai_provider["value"] or "stub").strip() or "stub"
    if ai_provider_value not in {"", "stub"} and not ai_key["value"]:
        issues.append(f"AI provider '{ai_provider_value}' is configured without API key.")

    next_step = (
        "Set a dedicated RECRUITBOT_TELEGRAM_BOT_TOKEN via keychain or .env.runtime, then run "
        "`bash scripts/runtime_check_with_env.sh --json` and `bash scripts/compose_with_runtime.sh up -d bot`."
        if issues else
        "Runtime secret path looks usable. Run runtime_check_with_env and bring up the bot."
    )

    return {
        "project": "recruitbot",
        "env_file_exists": ENV_PATH.exists(),
        "runtime_env_file_exists": RUNTIME_ENV_PATH.exists(),
        "telegram": {
            "source": token["source"],
            "present": token_present,
            "placeholder": token_placeholder,
            "valid_format": token_valid,
            "masked": mask_secret(token_value),
            "bot_identity": bot_identity,
            "reserved_for_other_runtime": wrong_identity,
        },
        "ai": {
            "provider": ai_provider_value,
            "provider_source": ai_provider["source"],
            "api_key_present": bool(ai_key["value"]),
            "api_key_source": ai_key["source"],
        },
        "issues": issues,
        "next_step": next_step,
    }


def print_human(status: dict) -> None:
    print("[runtime-env] recruitbot")
    print(
        f"env={status['env_file_exists']} runtime-env={status['runtime_env_file_exists']} "
        f"token_source={status['telegram']['source'] or 'none'} token_valid={status['telegram']['valid_format']} "
        f"token_masked={status['telegram']['masked'] or '—'}"
    )
    identity = status["telegram"].get("bot_identity") or {}
    if identity:
        print(
            f"telegram_identity=username={identity.get('username') or 'unknown'} "
            f"first_name={identity.get('first_name') or 'unknown'} "
            f"reserved_for_other_runtime={status['telegram'].get('reserved_for_other_runtime')}"
        )
    print(
        f"ai_provider={status['ai']['provider']} ai_key_present={status['ai']['api_key_present']} "
        f"ai_source={status['ai']['provider_source'] or 'none'}"
    )
    if status["issues"]:
        print("issues:")
        for issue in status["issues"]:
            print(f"- {issue}")
    print("next:", status["next_step"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Show Recruit runtime secret source resolution")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print JSON")
    args = parser.parse_args()
    status = build_status()
    if args.as_json:
        print(json.dumps(status, ensure_ascii=False))
    else:
        print_human(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
