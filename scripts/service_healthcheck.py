#!/usr/bin/env python3
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

from redis import Redis
from sqlalchemy import text

from app.config import Config
from app.db import engine
from common.env_guard import validate_runtime_environment
from common.runtime_env import get_ai_api_key, get_ai_provider, get_recruitbot_token, looks_like_bot_token


def _check_db() -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def _check_redis() -> None:
    Redis.from_url(Config.REDIS_URL).ping()


def _check_web() -> None:
    with urllib.request.urlopen("http://127.0.0.1:8000/ready", timeout=5) as response:
        status = getattr(response, "status", response.getcode())
        if status != 200:
            raise RuntimeError(f"/ready returned {status}")


def _check_bot_token() -> None:
    token = get_recruitbot_token()
    if not token or not looks_like_bot_token(token):
        raise RuntimeError("bot token missing or malformed")


def _check_ai() -> None:
    provider = (get_ai_provider() or "").strip().lower()
    if provider in {"", "stub"}:
        return
    if not get_ai_api_key():
        raise RuntimeError(f"{provider} configured without API key")


def _check_listener_storage() -> None:
    session_dir = Path(__file__).resolve().parents[1] / "data" / "tg_sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    if not session_dir.is_dir():
        raise RuntimeError("data/tg_sessions is not writable")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/service_healthcheck.py <service>", file=sys.stderr)
        return 2

    service = sys.argv[1].strip().lower()
    validate_runtime_environment(service)

    if service == "web":
        _check_web()
    elif service in {"worker", "scheduler"}:
        _check_db()
        _check_redis()
    elif service == "bot":
        _check_db()
        _check_redis()
        _check_bot_token()
        _check_ai()
    elif service == "listener":
        _check_db()
        _check_listener_storage()
    else:
        raise RuntimeError(f"unknown service: {service}")

    print(f"ok: {service}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
