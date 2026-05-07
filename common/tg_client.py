"""
Telegram Client API integration via Telethon.
Used for syncing user's groups/channels and posting to communities.
NOT the bot API — this is the user account API.
"""

import os
import asyncio
import json
import random
import time
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

logger = logging.getLogger(__name__)

SESSION_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "tg_sessions")
os.makedirs(SESSION_DIR, exist_ok=True)

TELETHON_CONNECT_TIMEOUT = 20
TELETHON_ENTITY_TIMEOUT = 30
TELETHON_SEND_TIMEOUT = 90


def _session_path(company_id: int) -> str:
    return os.path.join(SESSION_DIR, f"company_{company_id}")


def _get_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


async def _send_code_async(api_id: int, api_hash: str, phone: str, company_id: int):
    from telethon import TelegramClient
    client = TelegramClient(_session_path(company_id), api_id, api_hash)
    await client.connect()
    result = await client.send_code_request(phone)
    phone_code_hash = result.phone_code_hash
    await client.disconnect()
    return phone_code_hash


async def _verify_code_async(api_id: int, api_hash: str, phone: str, code: str, phone_code_hash: str, company_id: int, password: str = None):
    from telethon import TelegramClient
    client = TelegramClient(_session_path(company_id), api_id, api_hash)
    await client.connect()
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
    except Exception as e:
        if "Two-steps verification" in str(e) or "SessionPasswordNeeded" in str(e):
            if password:
                await client.sign_in(password=password)
            else:
                await client.disconnect()
                return {"ok": False, "error": "2FA_REQUIRED"}
        else:
            await client.disconnect()
            return {"ok": False, "error": str(e)}

    me = await client.get_me()
    await client.disconnect()
    return {
        "ok": True,
        "user_id": me.id,
        "username": me.username,
        "first_name": me.first_name,
        "phone": me.phone,
    }


async def _sync_dialogs_async(api_id: int, api_hash: str, company_id: int):
    from telethon import TelegramClient
    from telethon.tl.types import Channel, Chat, ChatForbidden, ChannelForbidden
    client = TelegramClient(_session_path(company_id), api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        await client.disconnect()
        return {"ok": False, "error": "NOT_AUTHORIZED"}

    groups = []
    async for dialog in client.iter_dialogs(limit=300):
        entity = dialog.entity
        if isinstance(entity, (ChatForbidden, ChannelForbidden)):
            continue

        is_group = False
        is_channel = False
        members = 0
        username = None

        if isinstance(entity, Channel):
            is_channel = not entity.megagroup
            is_group = entity.megagroup
            members = getattr(entity, 'participants_count', 0) or 0
            username = entity.username
        elif isinstance(entity, Chat):
            is_group = True
            members = getattr(entity, 'participants_count', 0) or 0

        if not is_group and not is_channel:
            continue

        groups.append({
            "id": dialog.id,
            "name": dialog.name or "",
            "username": username,
            "type": "channel" if is_channel else "group",
            "members": members,
            "is_megagroup": isinstance(entity, Channel) and entity.megagroup,
            "unread": dialog.unread_count,
        })

    await client.disconnect()
    return {"ok": True, "groups": groups, "total": len(groups)}


async def _check_dialog_access_async(api_id: int, api_hash: str, company_id: int, group_id: str) -> dict:
    from telethon import TelegramClient
    from telethon.errors import ChannelPrivateError, UsernameNotOccupiedError

    client = TelegramClient(_session_path(company_id), api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        await client.disconnect()
        return {"ok": False, "error": "NOT_AUTHORIZED"}

    entity_ref = group_id if group_id.startswith("@") else group_id
    try:
        entity = await client.get_entity(entity_ref)
        title = getattr(entity, "title", None) or getattr(entity, "username", None) or group_id
        await client.disconnect()
        return {"ok": True, "title": title, "error": None}
    except UsernameNotOccupiedError:
        await client.disconnect()
        return {"ok": False, "error": "USERNAME_NOT_OCCUPIED"}
    except ChannelPrivateError:
        await client.disconnect()
        return {"ok": False, "error": "CHANNEL_PRIVATE"}
    except Exception as e:
        await client.disconnect()
        return {"ok": False, "error": str(e)}


def send_code(api_id: int, api_hash: str, phone: str, company_id: int) -> str:
    """Send verification code. Returns phone_code_hash."""
    loop = _get_loop()
    return loop.run_until_complete(_send_code_async(api_id, api_hash, phone, company_id))


def verify_code(api_id: int, api_hash: str, phone: str, code: str, phone_code_hash: str, company_id: int, password: str = None) -> dict:
    """Verify code and sign in. Returns user info or error."""
    loop = _get_loop()
    return loop.run_until_complete(_verify_code_async(api_id, api_hash, phone, code, phone_code_hash, company_id, password))


def sync_dialogs(api_id: int, api_hash: str, company_id: int) -> dict:
    """Sync all groups/channels from user account. Returns list of groups."""
    loop = _get_loop()
    return loop.run_until_complete(_sync_dialogs_async(api_id, api_hash, company_id))


def check_dialog_access(api_id: int, api_hash: str, company_id: int, group_id: str) -> dict:
    """Check whether the connected Telegram account can resolve the target group/channel."""
    loop = _get_loop()
    return loop.run_until_complete(_check_dialog_access_async(api_id, api_hash, company_id, group_id))


def is_authorized(api_id: int, api_hash: str, company_id: int) -> bool:
    """Check if session exists and is authorized."""
    session_file = _session_path(company_id) + ".session"
    if not os.path.exists(session_file):
        return False
    try:
        loop = _get_loop()

        async def _check():
            from telethon import TelegramClient
            client = TelegramClient(_session_path(company_id), api_id, api_hash)
            await client.connect()
            authorized = await client.is_user_authorized()
            await client.disconnect()
            return authorized

        return loop.run_until_complete(_check())
    except Exception:
        return False


# ── Anti-spam constants ──────────────────────────────────────────────────────
# Pilot trade-off (2026-05): upper bound lowered from 600s → 120s.
# Reason: RQ default job_timeout was 180s, so any draw above ~150s silently
# expired the job mid-sleep ("Task exceeded maximum timeout value"). Worker
# timeout is now 900s (see worker/run_worker.py + docker-compose.yml), but a
# 10-minute pre-post sleep is also a bad pilot UX — operators expect their
# "Run Now" click to act in human time. Hourly/daily caps + jitter still
# enforce anti-spam. If a customer needs aggressive throttling, override via
# env or raise these constants in a follow-up.
POST_DELAY_MIN = 30    # 30 s minimum between posts (was 180)
POST_DELAY_MAX = 120   # 2 min maximum between posts (was 600)
JITTER_FACTOR = 0.3    # ±30% random jitter
MAX_POSTS_PER_HOUR = 10
MAX_POSTS_PER_DAY = 50
NIGHT_START = 23        # no posting after 23:00
NIGHT_END = 7           # no posting before 07:00
FLOOD_WAIT_PAUSE = 1800 # 30 min pause on FloodWait
MAX_RETRIES = 3

# Track posting rate per company.
# Primary store: Redis (shared across worker restarts and worker replicas).
# Fallback: in-memory dict (degraded — resets on restart, but keeps the
# anti-spam guard online if Redis is unreachable).
_posting_log: dict[int, list[float]] = {}
_RATE_KEY_PREFIX = "posting_log"
# TTL slightly longer than the longest cooldown window (24h) so per-post
# entries auto-expire and we don't grow the sorted set unbounded.
_RATE_TTL_SECONDS = 86400 + 3600


def _redis():
    """Return a redis client or None on failure. Cached on the function object."""
    cached = getattr(_redis, "_cached", None)
    if cached is not None:
        return cached
    try:
        from redis import Redis
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        # Probe so we fall back fast if redis is down.
        client.ping()
        _redis._cached = client
        return client
    except Exception as e:
        logger.warning(f"[tg_client] Redis unavailable, falling back to in-memory rate limit: {e}")
        _redis._cached = False  # negative cache (don't retry every call)
        return None


def _rate_key(company_id: int) -> str:
    return f"{_RATE_KEY_PREFIX}:{company_id}"


def _check_rate_limit(company_id: int) -> tuple[bool, str]:
    """Check if company is within posting rate limits. Returns (ok, reason).

    Uses Redis sorted set keyed by posting_log:{company_id} with score=epoch
    and member=epoch (uuid suffix added on write). Falls back to in-memory
    list if redis is down so behaviour stays observable.
    """
    now = time.time()
    r = _redis()
    if r:
        try:
            key = _rate_key(company_id)
            # Trim entries older than 24h
            r.zremrangebyscore(key, 0, now - 86400)
            daily = r.zcard(key)
            hourly = r.zcount(key, now - 3600, now)
            if hourly >= MAX_POSTS_PER_HOUR:
                return False, f"Hourly limit reached ({hourly}/{MAX_POSTS_PER_HOUR})"
            if daily >= MAX_POSTS_PER_DAY:
                return False, f"Daily limit reached ({daily}/{MAX_POSTS_PER_DAY})"
            return True, ""
        except Exception as e:
            logger.warning(f"[tg_client] Redis rate-check failed, using fallback: {e}")
            # fall through to in-memory

    log = _posting_log.get(company_id, [])
    log = [t for t in log if now - t < 86400]
    _posting_log[company_id] = log
    hourly = sum(1 for t in log if now - t < 3600)
    daily = len(log)
    if hourly >= MAX_POSTS_PER_HOUR:
        return False, f"Hourly limit reached ({hourly}/{MAX_POSTS_PER_HOUR})"
    if daily >= MAX_POSTS_PER_DAY:
        return False, f"Daily limit reached ({daily}/{MAX_POSTS_PER_DAY})"
    return True, ""


def _is_night_hours() -> bool:
    """Check if current Israel time is in the night window (no posting)."""
    if ZoneInfo is not None:
        israel_tz = ZoneInfo("Asia/Jerusalem")
    else:  # pragma: no cover
        israel_tz = timezone(timedelta(hours=3))
    hour = datetime.now(israel_tz).hour
    return hour >= NIGHT_START or hour < NIGHT_END


def _record_post(company_id: int):
    """Record a successful post for rate limiting (Redis-backed, in-mem fallback)."""
    now = time.time()
    r = _redis()
    if r:
        try:
            key = _rate_key(company_id)
            # Member must be unique; epoch+random suffix avoids clobber on rapid posts.
            member = f"{now:.6f}:{random.randint(0, 1_000_000)}"
            r.zadd(key, {member: now})
            r.expire(key, _RATE_TTL_SECONDS)
            return
        except Exception as e:
            logger.warning(f"[tg_client] Redis record-post failed, using fallback: {e}")
    _posting_log.setdefault(company_id, []).append(now)


async def _post_to_group_async(
    api_id: int,
    api_hash: str,
    company_id: int,
    group_id: str,
    text: str,
    file_path: str = None,
) -> dict:
    """
    Post a message to a Telegram group/channel via Telethon user account.
    Returns: {ok: bool, message_id: int|None, error: str|None}
    """
    from telethon import TelegramClient
    from telethon.errors import (
        FloodWaitError,
        ChatWriteForbiddenError,
        ChannelPrivateError,
        UserBannedInChannelError,
    )

    # Parse group_id: could be @username or numeric ID
    if group_id.startswith("@"):
        entity_ref = group_id
    else:
        try:
            entity_ref = int(group_id)
        except ValueError:
            return {"ok": False, "message_id": None, "error": f"Invalid group_id: {group_id}"}

    client = TelegramClient(
        _session_path(company_id),
        api_id,
        api_hash,
        connection_retries=1,
        request_retries=1,
        retry_delay=1,
    )
    await asyncio.wait_for(client.connect(), timeout=TELETHON_CONNECT_TIMEOUT)

    if not await client.is_user_authorized():
        await client.disconnect()
        return {"ok": False, "message_id": None, "error": "NOT_AUTHORIZED"}

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            entity = await asyncio.wait_for(client.get_entity(entity_ref), timeout=TELETHON_ENTITY_TIMEOUT)
            if file_path and os.path.exists(file_path):
                msg = await asyncio.wait_for(
                    client.send_file(entity, file_path, caption=text),
                    timeout=TELETHON_SEND_TIMEOUT,
                )
            else:
                msg = await asyncio.wait_for(
                    client.send_message(entity, text),
                    timeout=TELETHON_SEND_TIMEOUT,
                )
            msg_id = getattr(msg, 'id', None) if msg else None
            await client.disconnect()
            return {"ok": True, "message_id": msg_id, "error": None}

        except FloodWaitError as e:
            last_error = f"FloodWait: {e.seconds}s (attempt {attempt + 1}/{MAX_RETRIES})"
            logger.warning(f"[tg_client] FloodWaitError for company {company_id}, group {group_id}: wait {e.seconds}s")
            # Wait the required time + extra buffer
            wait_time = min(e.seconds + 30, FLOOD_WAIT_PAUSE)
            await asyncio.sleep(wait_time)

        except ChatWriteForbiddenError:
            await client.disconnect()
            return {"ok": False, "message_id": None, "error": "WRITE_FORBIDDEN: no permission to post in this group"}

        except ChannelPrivateError:
            await client.disconnect()
            return {"ok": False, "message_id": None, "error": "CHANNEL_PRIVATE: group is private or account was removed"}

        except UserBannedInChannelError:
            await client.disconnect()
            return {"ok": False, "message_id": None, "error": "USER_BANNED: account is banned in this group"}

        except asyncio.TimeoutError:
            last_error = "TIMEOUT: Telegram request exceeded allowed time"
            logger.error(f"[tg_client] Timeout for company {company_id}, group {group_id}")
            break

        except Exception as e:
            last_error = str(e)
            logger.error(f"[tg_client] Post error for company {company_id}, group {group_id}: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(10)
            else:
                break

    await client.disconnect()
    return {"ok": False, "message_id": None, "error": last_error}


def post_to_group(
    api_id: int,
    api_hash: str,
    company_id: int,
    group_id: str,
    text: str,
    file_path: str = None,
) -> tuple[bool, str]:
    """
    Synchronous wrapper for posting to a group via Telethon.
    Returns: (success: bool, message: str)

    Enforces anti-spam: rate limits, night hours, random delays.
    """
    # Night hours check
    if _is_night_hours():
        return False, "NIGHT_MODE: posting paused (23:00-07:00)"

    # Rate limit check
    ok, reason = _check_rate_limit(company_id)
    if not ok:
        return False, f"RATE_LIMIT: {reason}"

    # Random delay before posting (anti-spam jitter)
    base_delay = random.uniform(POST_DELAY_MIN, POST_DELAY_MAX)
    jitter = base_delay * random.uniform(-JITTER_FACTOR, JITTER_FACTOR)
    delay = max(1, base_delay + jitter)
    logger.info(f"[tg_client] Anti-spam delay: {delay:.0f}s before posting to {group_id}")
    time.sleep(delay)

    loop = _get_loop()
    result = loop.run_until_complete(
        _post_to_group_async(api_id, api_hash, company_id, group_id, text, file_path)
    )

    if result["ok"]:
        _record_post(company_id)
        return True, f"sent (msg_id={result['message_id']})"
    else:
        return False, result["error"] or "unknown error"
