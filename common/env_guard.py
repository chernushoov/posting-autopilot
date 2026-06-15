import os
from urllib.parse import urlparse

from common.runtime_env import (
    get_ai_api_key,
    get_ai_provider,
    get_recruitbot_token,
    is_placeholder_secret,
    looks_like_bot_token,
)


FORBIDDEN_SECRET_VALUES = {
    "",
    "dev-secret",
    "change-me",
    "replace-with-64-char-random-secret",
}


def _env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def _truthy(name: str) -> bool:
    return _env(name).lower() in {"1", "true", "yes", "on"}


def is_production_mode() -> bool:
    app_env = (_env("APP_ENV") or _env("FLASK_ENV")).lower()
    return app_env in {"prod", "production", "staging"} or _truthy("REQUIRE_PROD_SECRETS")


def _require(name: str, errors: list[str], *, description: str | None = None) -> None:
    value = _env(name)
    if not value:
        errors.append(f"{name} is required{f' ({description})' if description else ''}")
        return
    if is_placeholder_secret(value):
        errors.append(f"{name} still contains a placeholder value")


def _require_https_url(name: str, errors: list[str]) -> None:
    value = _env(name)
    if not value:
        errors.append(f"{name} is required")
        return
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        errors.append(f"{name} must be a full https:// URL")


def _validate_trial_days(errors: list[str]) -> None:
    raw = _env("TRIAL_DAYS") or "3"
    try:
        days = int(raw)
    except ValueError:
        errors.append("TRIAL_DAYS must be an integer")
        return
    if days <= 0:
        errors.append("TRIAL_DAYS must be greater than 0")


def _validate_flask_secret(errors: list[str]) -> None:
    value = _env("FLASK_SECRET_KEY")
    if value in FORBIDDEN_SECRET_VALUES or len(value) < 32 or is_placeholder_secret(value):
        errors.append("FLASK_SECRET_KEY must be a strong 32+ character secret in production")


def _validate_database(errors: list[str]) -> None:
    value = _env("DATABASE_URL")
    if not value:
        errors.append("DATABASE_URL is required")
        return
    if value.startswith("sqlite:"):
        errors.append("DATABASE_URL must point to Postgres in production, not sqlite")


def _validate_redis(errors: list[str]) -> None:
    value = _env("REDIS_URL")
    if not value:
        errors.append("REDIS_URL is required")
        return
    if "localhost" in value or "127.0.0.1" in value:
        errors.append("REDIS_URL must point at the Redis service in production, not localhost")


def _validate_ai(errors: list[str]) -> None:
    provider = (get_ai_provider() or "").strip().lower()
    allow_stub = _truthy("ALLOW_STUB_AI")
    if not provider:
        errors.append("AI provider is missing; set RECRUITBOT_AI_PROVIDER or AI_PROVIDER")
        return
    if provider == "stub":
        if not allow_stub:
            errors.append("AI provider resolves to stub; set ALLOW_STUB_AI=1 explicitly or configure a real AI provider")
        return
    api_key = get_ai_api_key()
    if not api_key or is_placeholder_secret(api_key):
        errors.append(f"{provider} AI is enabled but AI_API_KEY/RECRUITBOT_AI_API_KEY is missing")


def _validate_bot(errors: list[str]) -> None:
    token = get_recruitbot_token()
    if not token:
        errors.append("RECRUITBOT_TELEGRAM_BOT_TOKEN (or TELEGRAM_BOT_TOKEN) is required for the bot service")
        return
    if is_placeholder_secret(token) or not looks_like_bot_token(token):
        errors.append("RECRUITBOT_TELEGRAM_BOT_TOKEN does not look like a valid BotFather token")


def _validate_billing(errors: list[str]) -> None:
    if not _truthy("BILLING_ENABLED"):
        return
    for name in (
        "PADDLE_API_KEY",
        "PADDLE_CLIENT_TOKEN",
        "PADDLE_WEBHOOK_SECRET",
        "PADDLE_PRICE_STARTER",
        "PADDLE_PRICE_PRO",
        "PADDLE_PRICE_AGENCY",
    ):
        _require(name, errors)


def validate_runtime_environment(service: str) -> None:
    if not is_production_mode():
        return

    errors: list[str] = []
    _validate_flask_secret(errors)
    _validate_database(errors)
    _validate_trial_days(errors)

    if service in {"web", "worker", "scheduler", "bot"}:
        _validate_redis(errors)

    if service == "web":
        _require("ADMIN_LOGIN", errors, description="operator login")
        _require("ADMIN_PASSWORD", errors, description="operator password")
        _require_https_url("PUBLIC_MARKETING_URL", errors)
        _require_https_url("PUBLIC_APP_URL", errors)
        _validate_billing(errors)

    if service == "bot":
        _validate_bot(errors)
        _validate_ai(errors)

    if errors:
        bullet_list = "\n".join(f"- {item}" for item in errors)
        raise RuntimeError(f"Production environment validation failed for {service}:\n{bullet_list}")
