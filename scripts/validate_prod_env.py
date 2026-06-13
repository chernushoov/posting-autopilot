#!/usr/bin/env python3
"""Validate a production env file before Docker compose boot.

Uses only the Python standard library so it can run on a fresh VPS before the
app image is built. Fails if critical values are empty or still placeholders.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse


PLACEHOLDER_MARKERS = (
    "CHANGE_ME",
    "YOUR_",
    "EXAMPLE.COM",
    "PUT_",
    "TOKEN_HERE",
    "REPLACE",
)
BOT_TOKEN_RE = re.compile(r"^\d{6,}:[A-Za-z0-9_-]{20,}$")


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values


def looks_placeholder(value: str) -> bool:
    normalized = (value or "").strip().upper()
    if not normalized:
        return True
    return any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def require(values: dict[str, str], key: str, errors: list[str]) -> str:
    value = values.get(key, "").strip()
    if not value:
        errors.append(f"{key} is required")
        return ""
    if looks_placeholder(value):
        errors.append(f"{key} still contains a placeholder value")
    return value


def require_url(values: dict[str, str], key: str, expected_host_key: str, errors: list[str]) -> None:
    raw = require(values, key, errors)
    if not raw:
        return
    parsed = urlparse(raw)
    if parsed.scheme != "https" or not parsed.netloc:
        errors.append(f"{key} must be a full https:// URL")
        return
    expected_host = values.get(expected_host_key, "").strip()
    if expected_host and parsed.netloc != expected_host:
        errors.append(f"{key} host ({parsed.netloc}) must match {expected_host_key} ({expected_host})")


def require_int(values: dict[str, str], key: str, minimum: int, errors: list[str]) -> None:
    raw = require(values, key, errors)
    if not raw:
        return
    try:
        value = int(raw)
    except ValueError:
        errors.append(f"{key} must be an integer")
        return
    if value < minimum:
        errors.append(f"{key} must be >= {minimum}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python3 scripts/validate_prod_env.py <env-file>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1]).expanduser().resolve()
    if not path.exists():
        print(f"env file not found: {path}", file=sys.stderr)
        return 2

    values = load_env(path)
    errors: list[str] = []

    if values.get("APP_ENV", "").strip().lower() != "production":
        errors.append("APP_ENV must be set to production")

    for key in (
        "ADMIN_LOGIN",
        "ADMIN_PASSWORD",
        "FLASK_SECRET_KEY",
        "MARKETING_DOMAIN",
        "APP_DOMAIN",
        "LETSENCRYPT_EMAIL",
        "POSTGRES_PASSWORD",
        "DATABASE_URL",
        "REDIS_URL",
        "TRIAL_DAYS",
        "RECRUITBOT_TELEGRAM_BOT_TOKEN",
        "TELEGRAM_BOT_TOKEN",
        "RECRUITBOT_AI_PROVIDER",
        "AI_PROVIDER",
    ):
        require(values, key, errors)

    require_url(values, "PUBLIC_MARKETING_URL", "MARKETING_DOMAIN", errors)
    require_url(values, "PUBLIC_APP_URL", "APP_DOMAIN", errors)
    require_int(values, "TRIAL_DAYS", 1, errors)
    require_int(values, "RQ_WORKER_TIMEOUT", 60, errors)

    flask_secret = values.get("FLASK_SECRET_KEY", "")
    if flask_secret and len(flask_secret) < 32:
        errors.append("FLASK_SECRET_KEY must be at least 32 characters")

    db_url = values.get("DATABASE_URL", "")
    if db_url and not db_url.startswith("postgresql+psycopg2://"):
        errors.append("DATABASE_URL must use the postgres psycopg2 DSN")
    if db_url and values.get("POSTGRES_PASSWORD") and values["POSTGRES_PASSWORD"] not in db_url:
        errors.append("DATABASE_URL must include the same password as POSTGRES_PASSWORD")

    redis_url = values.get("REDIS_URL", "")
    if redis_url and not redis_url.startswith("redis://redis:6379/"):
        errors.append("REDIS_URL should point to the internal redis service (redis://redis:6379/...)")

    bot_token = values.get("RECRUITBOT_TELEGRAM_BOT_TOKEN", "")
    if bot_token and not BOT_TOKEN_RE.match(bot_token):
        errors.append("RECRUITBOT_TELEGRAM_BOT_TOKEN does not look like a BotFather token")
    if values.get("TELEGRAM_BOT_TOKEN") != bot_token:
        errors.append("TELEGRAM_BOT_TOKEN must mirror RECRUITBOT_TELEGRAM_BOT_TOKEN")

    ai_provider = values.get("RECRUITBOT_AI_PROVIDER", "").strip().lower()
    ai_provider_fallback = values.get("AI_PROVIDER", "").strip().lower()
    if ai_provider and ai_provider != "stub" and not values.get("RECRUITBOT_AI_API_KEY", "").strip():
        errors.append("RECRUITBOT_AI_API_KEY is required when RECRUITBOT_AI_PROVIDER is not stub")
    if ai_provider_fallback and ai_provider_fallback != "stub" and not values.get("AI_API_KEY", "").strip():
        errors.append("AI_API_KEY is required when AI_PROVIDER is not stub")

    billing_enabled = values.get("BILLING_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
    if billing_enabled:
        for key in (
            "STRIPE_SECRET_KEY",
            "STRIPE_PUBLISHABLE_KEY",
            "STRIPE_WEBHOOK_SECRET",
            "STRIPE_PRICE_STARTER",
            "STRIPE_PRICE_PRO",
            "STRIPE_PRICE_AGENCY",
        ):
            require(values, key, errors)

    if errors:
        print("Production env validation FAILED:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Production env validation OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
