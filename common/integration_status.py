from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IntegrationStatus:
    ok: bool
    message: str


def _telegram_session_file(company_id: int) -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "tg_sessions" / f"company_{company_id}.session"


def telegram_authorization_status(company) -> IntegrationStatus:
    if not company or not getattr(company, "tg_api_id", None) or not getattr(company, "tg_api_hash", None):
        return IntegrationStatus(False, "Telegram credentials are missing.")

    if not _telegram_session_file(company.id).exists():
        return IntegrationStatus(False, "Telegram session is missing. Reconnect the account.")

    try:
        from common.tg_client import is_authorized

        if is_authorized(int(company.tg_api_id), company.tg_api_hash, company.id):
            return IntegrationStatus(True, "Telegram account authorized.")
    except Exception as exc:
        return IntegrationStatus(False, f"Telegram authorization check failed: {str(exc)[:160]}")

    return IntegrationStatus(False, "Telegram account is not authorized.")


def facebook_connection_status(company) -> IntegrationStatus:
    if company and getattr(company, "fb_access_token", None):
        return IntegrationStatus(True, "Facebook token saved.")
    return IntegrationStatus(False, "Facebook is not connected.")


def queue_status() -> IntegrationStatus:
    try:
        from worker.queue import redis_conn

        redis_conn.ping()
        return IntegrationStatus(True, "Background queue is online.")
    except Exception as exc:
        return IntegrationStatus(False, f"Background queue is offline: {str(exc)[:160]}")


def telegram_destination_ready(source, telegram_status: IntegrationStatus) -> bool:
    message = (getattr(source, "last_check_message", None) or "").lower()
    return bool(telegram_status.ok and getattr(source, "is_active", False) and source.last_check_ok and "stub" not in message)
