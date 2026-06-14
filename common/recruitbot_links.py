from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

from .runtime_env import get_recruitbot_token, is_placeholder_secret, looks_like_bot_token

ROOT = Path(__file__).resolve().parents[1]


def _parse_env_file(path: Path) -> dict[str, str]:
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


def _env_username() -> str | None:
    for key in ("RECRUITBOT_BOT_USERNAME", "TELEGRAM_BOT_USERNAME"):
        raw = (os.getenv(key) or "").strip()
        if raw:
            return raw.lstrip("@")
    for filename in (".env.runtime", ".env"):
        values = _parse_env_file(ROOT / filename)
        for key in ("RECRUITBOT_BOT_USERNAME", "TELEGRAM_BOT_USERNAME"):
            raw = (values.get(key) or "").strip()
            if raw:
                return raw.lstrip("@")
    return None


def _resolve_token() -> str:
    token = (get_recruitbot_token() or "").strip()
    if token:
        return token
    for filename in (".env.runtime", ".env"):
        values = _parse_env_file(ROOT / filename)
        token = (values.get("RECRUITBOT_TELEGRAM_BOT_TOKEN") or values.get("TELEGRAM_BOT_TOKEN") or "").strip()
        if token:
            return token
    return ""


@lru_cache(maxsize=1)
def get_recruitbot_username() -> str | None:
    env_username = _env_username()
    if env_username:
        return env_username

    token = _resolve_token()
    if not token or is_placeholder_secret(token) or not looks_like_bot_token(token):
        return None

    try:
        # Verified TLS (default context). NEVER disable cert validation here: the bot
        # token is embedded in the URL, so an unverified context = a MITM can steal the
        # bot token and forge the response.
        with urllib.request.urlopen(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=10,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None

    result = payload.get("result") or {}
    username = (result.get("username") or "").strip().lstrip("@")
    return username or None


def build_recruitbot_apply_link(vacancy_id: int | None) -> str | None:
    if not vacancy_id:
        return None
    username = get_recruitbot_username()
    if not username:
        return None
    return f"https://t.me/{username}?start=apply_{vacancy_id}"
