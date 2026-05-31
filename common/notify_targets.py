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
