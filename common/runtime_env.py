import os
import re

TOKEN_PATTERN = re.compile(r"^\d{6,}:[A-Za-z0-9_-]{20,}$")
PLACEHOLDER_MARKERS = (
    "PUT_YOUR_TOKEN_HERE",
    "PUT_YO...HERE",
    "CHANGE_ME",
    "YOUR_TOKEN",
    "TOKEN_HERE",
)


def _get_env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def get_recruitbot_token() -> str:
    return _get_env("RECRUITBOT_TELEGRAM_BOT_TOKEN") or _get_env("TELEGRAM_BOT_TOKEN")


def get_recruitbot_token_source() -> str | None:
    if _get_env("RECRUITBOT_TELEGRAM_BOT_TOKEN"):
        return "RECRUITBOT_TELEGRAM_BOT_TOKEN"
    if _get_env("TELEGRAM_BOT_TOKEN"):
        return "TELEGRAM_BOT_TOKEN"
    return None


def get_ai_provider() -> str:
    return _get_env("RECRUITBOT_AI_PROVIDER") or _get_env("AI_PROVIDER") or "stub"


def get_ai_api_key() -> str:
    return _get_env("RECRUITBOT_AI_API_KEY") or _get_env("AI_API_KEY")


def is_placeholder_secret(value: str) -> bool:
    normalized = (value or "").strip().upper()
    if not normalized:
        return False
    return any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def looks_like_bot_token(value: str) -> bool:
    return bool(TOKEN_PATTERN.match((value or "").strip()))


def mask_secret(value: str, keep: int = 4) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if len(text) <= keep * 2:
        return "*" * len(text)
    return f"{text[:keep]}...{text[-keep:]}"
