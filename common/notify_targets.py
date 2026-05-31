"""Helpers for resolving operator notification targets for RecruitBot."""

from __future__ import annotations

import os
import re
from typing import Iterable


CHAT_ID_RE = re.compile(r"^-?\d+$")


def normalize_chat_id(value: str | None) -> str | None:
    """Return a cleaned Telegram chat/user id string or None if invalid."""
    if value is None:
        return None
    cleaned = str(value).strip()
    if not cleaned or not CHAT_ID_RE.fullmatch(cleaned):
        return None
    return cleaned


def _append_unique(targets: list[str], candidates: Iterable[str | None]) -> None:
    for value in candidates:
        normalized = normalize_chat_id(value)
        if normalized and normalized not in targets:
            targets.append(normalized)


def sample_hot_lead_message(company=None, lang: str = "ru") -> str:
    """A realistic 🔥 hot-lead alert in the live format, clearly marked as a test, so
    the operator can confirm alerts land in the right Telegram chat before going live.
    Mirrors worker/tg_listener._capture_lead's note layout.
    """
    company_name = getattr(company, "name", None) or "RecruitBot"
    wa = "https://wa.me/972501234567"  # 050-1234567 normalised to IL international form
    if lang == "he":
        return (
            "🔥 ליד חם (בדיקה)\n"
            "👤 דני כהן\n"
            "📋 מודעה: נהג משאית C\n"
            "💬 הודעה: זמין להתחיל מיד, יש לי רישיון C ו-3 שנות ניסיון. אפשר לשוחח?\n"
            "📞 050-1234567\n"
            f"📲 WhatsApp: {wa}\n"
            f"— זוהי הודעת בדיקה מ-{company_name}. אם קיבלת אותה, התראות הלידים מחוברות. ✅"
        )
    if lang == "en":
        return (
            "🔥 Hot lead (test)\n"
            "👤 Danny Cohen\n"
            "📋 Listing: Class-C truck driver\n"
            "💬 Message: Available to start now, I have a class-C licence and 3 years' experience. Can we talk?\n"
            "📞 050-1234567\n"
            f"📲 WhatsApp: {wa}\n"
            f"— this is a test alert from {company_name}. If you got it, hot-lead alerts are wired up. ✅"
        )
    return (
        "🔥 Горячий лид (тест)\n"
        "👤 Дани Коэн\n"
        "📋 Объявление: Водитель грузовика кат. C\n"
        "💬 Сообщение: Готов выйти сразу, есть права категории C и 3 года опыта. Можем поговорить?\n"
        "📞 050-1234567\n"
        f"📲 WhatsApp: {wa}\n"
        f"— это тестовое уведомление от {company_name}. Если вы его получили, оповещения о лидах настроены. ✅"
    )


def resolve_recruit_notify_targets(company, env: dict[str, str] | None = None) -> list[str]:
    """Resolve notify targets in deterministic priority order.

    Priority:
      1. Explicit company.owner_telegram_id from the company profile.
      2. Per-company env override RECRUIT_OPERATOR_NOTIFY_CHAT_<company_id>.
      3. Global env fallback RECRUIT_OPERATOR_NOTIFY_CHAT.
      4. Legacy company.owner_id if it already stores a Telegram numeric id.
    """
    env_map = env or os.environ
    company_id = getattr(company, "id", None)

    targets: list[str] = []
    _append_unique(
        targets,
        [
            getattr(company, "owner_telegram_id", None),
            env_map.get(f"RECRUIT_OPERATOR_NOTIFY_CHAT_{company_id}") if company_id is not None else None,
            env_map.get("RECRUIT_OPERATOR_NOTIFY_CHAT"),
            getattr(company, "owner_id", None),
        ],
    )
    return targets
