"""Central posting safety guard — the single chokepoint every autonomous send must pass.

Why this exists (pre-launch audit 2026-06-13):
  - There was NO global kill switch (C4): halting all posting meant toggling each
    campaign by hand, and even then queued/in-flight jobs still fired.
  - The 23:00-07:00 quiet-hours freeze (C2) lived only inside the Telethon
    `post_to_group` path; the Bot-API send (`bot/tg.py`) and the Facebook browser
    poster (`worker/fb_auto_post.py`) had no night guard, so an operator "Run now"
    or a staggered FB job fired at 02:00.

Dependency-light on purpose (stdlib + zoneinfo only): importable from every send
site (worker, bot, telethon client, fb poster) with no circular import, and it keeps
working when Redis is down.

The kill switch is a FILE in the shared data volume (mounted into every service as
/app/data per docker-compose), so one `pause()` is seen by web/worker/scheduler/bot/
listener with no restart and survives a crash. An env var (POSTING_KILL_SWITCH=1) is
honoured too for a static/boot-time stop.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

logger = logging.getLogger(__name__)

# Quiet hours (Israel). Mirrors common/tg_client NIGHT_START/END; override via env.
QUIET_HOURS_START = int(os.getenv("QUIET_HOURS_START", "23"))  # no posting at/after 23:00
QUIET_HOURS_END = int(os.getenv("QUIET_HOURS_END", "7"))       # no posting before 07:00
ISRAEL_TZ_NAME = "Asia/Jerusalem"


def _data_dir() -> str:
    override = os.getenv("RA_DATA_DIR")
    if override:
        return override
    return os.path.join(os.path.dirname(__file__), "..", "data")


def _pause_file() -> str:
    return os.path.join(_data_dir(), "POSTING_PAUSED")


def _israel_now(now: datetime | None = None) -> datetime:
    if now is not None:
        return now
    if ZoneInfo is not None:
        return datetime.now(ZoneInfo(ISRAEL_TZ_NAME))
    # Fallback if zoneinfo is unavailable: fixed UTC+2 (Israel standard time).
    return datetime.now(timezone(timedelta(hours=2)))


def quiet_hours_enabled() -> bool:
    return os.getenv("QUIET_HOURS_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}


def is_night_hours(now: datetime | None = None) -> bool:
    """True when current Israel time is inside the quiet window (no posting).

    `now` may be injected (timezone-aware) for testing.
    """
    if not quiet_hours_enabled():
        return False
    hour = _israel_now(now).hour
    start, end = QUIET_HOURS_START, QUIET_HOURS_END
    if start <= end:
        return start <= hour < end
    # Wrap-around window (e.g. 23 -> 7): night if hour >= start OR hour < end.
    return hour >= start or hour < end


# ── Kill switch ───────────────────────────────────────────────────────────────

def _env_kill() -> bool:
    return os.getenv("POSTING_KILL_SWITCH", "").strip().lower() in {"1", "true", "yes", "on"}


def is_paused() -> bool:
    if _env_kill():
        return True
    try:
        return os.path.exists(_pause_file())
    except Exception:  # pragma: no cover - the guard must never crash a caller
        return False


def pause(reason: str = "", actor: str = "operator") -> str:
    """Engage the global kill switch. Returns the stored marker text."""
    path = _pause_file()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    stamp = _israel_now().isoformat()
    marker = f"{stamp}\tactor={actor}\treason={reason or '(none)'}"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(marker + "\n")
    logger.warning("[posting_guard] POSTING PAUSED — %s", marker)
    return marker


def resume(actor: str = "operator") -> bool:
    """Release the global kill switch. Returns True if it had been engaged."""
    path = _pause_file()
    existed = os.path.exists(path)
    try:
        if existed:
            os.remove(path)
    except FileNotFoundError:
        existed = False
    logger.warning("[posting_guard] POSTING RESUMED by %s (was_paused=%s)", actor, existed)
    return existed


def pause_info() -> str | None:
    if _env_kill():
        return "POSTING_KILL_SWITCH env set"
    try:
        with open(_pause_file(), "r", encoding="utf-8") as fh:
            return fh.read().strip()
    except FileNotFoundError:
        return None
    except Exception:  # pragma: no cover
        return None


# ── The single chokepoint ───────────────────────────────────────────────────

def block_reason(now: datetime | None = None) -> str | None:
    """Return a human reason string if an autonomous post/DM must NOT go out now,
    else None. Call this immediately before every external send.
    """
    if is_paused():
        info = pause_info() or ""
        return f"KILL_SWITCH: posting globally paused ({info})".strip()
    if is_night_hours(now):
        return (
            f"NIGHT_MODE: posting paused ({QUIET_HOURS_START:02d}:00-"
            f"{QUIET_HOURS_END:02d}:00 {ISRAEL_TZ_NAME})"
        )
    return None


def can_post(now: datetime | None = None) -> tuple[bool, str | None]:
    """Convenience wrapper: (ok, reason)."""
    reason = block_reason(now)
    return (reason is None), reason


# ── New-account warm-up ramp (anti-ban) ───────────────────────────────────────

def effective_daily_cap(configured_cap: int, company_age_days: int | None) -> int:
    """Ramp the daily posting cap for young accounts so a fresh account doesn't blast
    at full volume on day one (a classic ban trigger). Linear ramp from
    WARMUP_DAY1_CAP on day 0 to `configured_cap` by WARMUP_RAMP_DAYS, then unchanged.
    """
    try:
        ramp_days = int(os.getenv("WARMUP_RAMP_DAYS", "7"))
        day1_cap = int(os.getenv("WARMUP_DAY1_CAP", "3"))
    except ValueError:
        return configured_cap
    if ramp_days <= 0 or company_age_days is None or company_age_days >= ramp_days:
        return configured_cap
    if company_age_days < 0:
        company_age_days = 0
    span = max(configured_cap - day1_cap, 0)
    ramped = day1_cap + int(round(span * (company_age_days / ramp_days)))
    return max(1, min(configured_cap, ramped))
