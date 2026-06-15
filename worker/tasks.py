from __future__ import annotations
from datetime import datetime, timedelta, timezone
import json
import logging
from app.db import db_session
from app.models import Source, Campaign, CampaignSource, Vacancy, Company, Candidate, CandidateStatus, PostingAttempt
from common.ai import build_system_prompt
from common.recruitbot_links import build_recruitbot_apply_link
from bot.tg import tg_send_message_safe

logger = logging.getLogger(__name__)

try:
    from zoneinfo import ZoneInfo
    ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")  # handles IDT/IST transitions
except Exception:
    ISRAEL_TZ = timezone(timedelta(hours=3))


def _israel_date(dt_utc_naive: datetime):
    """DB timestamps are naive UTC; convert to Israel local date for daily-cap math."""
    return dt_utc_naive.replace(tzinfo=timezone.utc).astimezone(ISRAEL_TZ).date()

def _load_campaign_window(campaign: Campaign):
    try:
        hours = json.loads(campaign.active_hours_json or '{"start":9,"end":19}')
    except Exception:
        hours = {"start": 9, "end": 19}
    try:
        days = json.loads(campaign.days_of_week_json or '[0,1,2,3,4,5]')
    except Exception:
        days = [0, 1, 2, 3, 4, 5]
    return hours, days


def _build_post_asset(vacancy: Vacancy):
    title = (vacancy.final_post_title or vacancy.title or "").strip()
    if vacancy.final_post_body and vacancy.final_post_body.strip():
        body = vacancy.final_post_body.strip()
    else:
        parts = [vacancy.body.strip()]
        if vacancy.city:
            parts.append(f"City: {vacancy.city}")
        if vacancy.salary_text:
            parts.append(f"Pay: {vacancy.salary_text}")
        if vacancy.schedule_text:
            parts.append(f"Schedule: {vacancy.schedule_text}")
        if vacancy.contact_text:
            parts.append(f"Contact: {vacancy.contact_text}")
        effective_apply_url = vacancy.apply_url or build_recruitbot_apply_link(vacancy.id)
        if effective_apply_url:
            parts.append(f"Apply: {effective_apply_url}")
        # Task 2.3: WhatsApp click-to-chat
        if getattr(vacancy, 'whatsapp_number', None):
            wa_num = vacancy.whatsapp_number.lstrip('+')
            parts.append(f"WhatsApp: https://wa.me/{wa_num}")
        body = "\n".join([part for part in parts if part])
    return title, body


def _parse_retry_later(message: str):
    """Extract the retry delay (seconds) from a 'RETRY_LATER:<secs>:<reason>' signal
    returned by common.tg_client (FloodWait / night-mode / rate-limit). None otherwise."""
    if not message or not message.startswith("RETRY_LATER:"):
        return None
    try:
        return int(message.split(":", 2)[1])
    except (ValueError, IndexError):
        return 600


def _reschedule_run(campaign_id: int, run_key: str, trigger: str, delay_seconds) -> None:
    """Requeue this run after a cooldown so rescheduled sources (FloodWait/night)
    are retried. Bounded by a counter encoded in the trigger to prevent loops."""
    base, _, cnt = trigger.partition("|resched=")
    n = int(cnt) if cnt.isdigit() else 0
    if n >= 3:
        logger.warning(f"[campaign_tick] run {run_key} hit reschedule cap (3); giving up")
        return
    delay = max(60, min(int(delay_seconds), 3 * 3600))
    try:
        from worker.queue import q_default
        q_default.enqueue_in(timedelta(seconds=delay), campaign_tick, campaign_id, run_key, f"{base}|resched={n + 1}")
        logger.info(f"[campaign_tick] run {run_key} rescheduled in {delay}s (attempt {n + 1})")
    except Exception as exc:
        logger.error(f"[campaign_tick] failed to reschedule run {run_key}: {exc}")


def campaign_tick_on_failure(job, connection, exc_type, exc_value, traceback) -> None:
    """RQ on_failure hook: if a campaign_tick job dies, unstick its attempts so they
    don't sit forever in 'scheduled'/'pending' with no resolution."""
    try:
        run_key = job.args[1] if len(job.args) > 1 else None
    except Exception:
        run_key = None
    if not run_key:
        return
    db = db_session()
    try:
        db.query(PostingAttempt).filter(
            PostingAttempt.run_key == run_key,
            PostingAttempt.result_status.in_(["scheduled", "pending"]),
        ).update(
            {"result_status": "failed", "error_message": "worker job failed before this destination was processed"},
            synchronize_session=False,
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _blocked_status_from_message(message: str) -> str:
    lowered = (message or "").lower()
    risky_markers = ["429", "too many requests", "blocked", "spam", "forbidden", "retry after", "flood"]
    if any(marker in lowered for marker in risky_markers):
        return "blocked_or_suspected"
    return "failed"


def _should_clear_source_ready(message: str) -> bool:
    lowered = (message or "").lower()
    hard_failure_markers = [
        "chat not found",
        "username not occupied",
        "peer_id_invalid",
        "channel_invalid",
        "bot is not a member",
        "user not participant",
        "have no rights",
        "not enough rights",
        "administrator rights",
        "forbidden: bot was kicked",
    ]
    return any(marker in lowered for marker in hard_failure_markers)


def _valid_tg_ref(value: str) -> bool:
    if value.startswith("@") and len(value) > 1:
        return True
    if value.startswith("-100") and value[4:].isdigit():
        return True
    if value.isdigit() and len(value) >= 6:
        return True
    return False

def check_source_access(source_id: int):
    db = db_session()
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        db.close(); return
    if (s.platform or "telegram") == "facebook":
        s.last_check_ok = bool(s.destination_url)
        s.last_check_message = "Manual Facebook destination confirmed by operator." if s.destination_url else "Facebook destination URL is missing."
        db.commit()
        db.close()
        return

    if not _valid_tg_ref(s.tg_ref):
        s.last_check_ok = False
        s.last_check_message = "invalid tg_ref format"
        db.commit()
        db.close()
        return

    company = db.query(Company).filter(Company.id == s.company_id).first()
    if not company or not company.tg_api_id or not company.tg_api_hash:
        s.last_check_ok = True
        s.last_check_message = "format looks valid, but Telegram account is not connected yet"
        db.commit()
        db.close()
        return

    from common.tg_client import check_dialog_access

    result = check_dialog_access(int(company.tg_api_id), company.tg_api_hash, company.id, s.tg_ref)
    s.last_check_ok = bool(result.get("ok"))
    if result.get("ok"):
        resolved_title = result.get("title") or s.label or s.tg_ref
        s.last_check_message = f"Access confirmed via Telegram account: {resolved_title}"
    else:
        s.last_check_message = result.get("error") or "Unable to verify destination access"
    db.commit()
    db.close()

def send_test_message(source_id: int, text: str):
    db = db_session()
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        db.close(); return
    ok, msg = tg_send_message_safe(s.tg_ref, text)
    if ok:
        s.last_check_ok = True
    elif _should_clear_source_ready(msg):
        s.last_check_ok = False
    s.last_check_message = msg
    db.commit()
    db.close()

def campaign_tick(campaign_id: int, run_key: str | None = None, trigger: str = "scheduler_interval"):
    # MVP: post vacancy text to each source once. Scheduler will call periodically.
    db = db_session()
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    allow_paused_run = trigger == "operator_run_now"
    if not c or (not c.is_running and not allow_paused_run):
        db.close(); return
    if c.interval_minutes <= 0:
        db.close(); return

    hours, days = _load_campaign_window(c)
    # Active-hours / daily-cap math runs in Israel local time
    now = datetime.now(ISRAEL_TZ)
    if trigger == "scheduler_interval":
        if now.weekday() not in days:
            db.close(); return
        start_hour = int(hours.get("start", 9))
        end_hour = int(hours.get("end", 19))
        if now.hour < start_hour or now.hour >= end_hour:
            db.close(); return

    v = db.query(Vacancy).filter(Vacancy.id == c.vacancy_id, Vacancy.company_id == c.company_id).first()
    if not v:
        db.close(); return

    # Billing gate: never post for a tenant whose trial expired / subscription lapsed
    # (enforced in the worker, not only in the web before_request gate).
    from app.plans import is_billing_active
    company = db.query(Company).filter(Company.id == c.company_id).first()
    if not is_billing_active(db, company):
        logger.info(f"[campaign_tick] billing inactive for company {c.company_id}; skipping campaign {c.id}")
        db.close(); return

    # Per-campaign lock so two ticks (scheduler + operator_run_now + retry) never run
    # concurrently and double-post. TTL bounded by the RQ job timeout.
    from worker.queue import (
        acquire_lock, release_lock, reserve_daily_slot, release_daily_slot,
    )
    lock_key = f"campaign_tick_lock:{c.id}"
    lock_token = acquire_lock(lock_key, ttl=900)
    if not lock_token:
        logger.info(f"[campaign_tick] campaign {c.id} already running; skipping concurrent tick")
        db.close(); return

    asset_title, asset_body = _build_post_asset(v)

    # Atomic per-(campaign, Israel-day) cap, shared across processes.
    cap_key = f"campaign_postcap:{c.id}:{now.strftime('%Y%m%d')}"
    reschedule_after = None  # set if any source asks to retry later (FloodWait/night/rate)

    links = db.query(CampaignSource).filter(CampaignSource.campaign_id == c.id).all()
    posted_today = 0
    for link in links:
        s = db.query(Source).filter(Source.id == link.source_id, Source.company_id == c.company_id).first()
        if s and s.last_post_at and _israel_date(s.last_post_at) == now.date():
            posted_today += 1
    remaining_posts = max(c.max_posts_per_day - posted_today, 0)

    for link in links:
        s = db.query(Source).filter(Source.id == link.source_id, Source.company_id == c.company_id).first()
        if not s or not s.is_active:
            continue
        attempt = None
        if run_key:
            attempt = (
                db.query(PostingAttempt)
                .filter(
                    PostingAttempt.run_key == run_key,
                    PostingAttempt.source_id == s.id,
                    PostingAttempt.company_id == c.company_id,
                )
                .order_by(PostingAttempt.id.desc())
                .first()
            )
        # Idempotency for rescheduled runs: if this (run_key, source) was already
        # posted, never re-post it.
        if attempt and attempt.result_status == "posted":
            continue
        if not attempt:
            attempt = PostingAttempt(
                company_id=c.company_id,
                campaign_id=c.id,
                vacancy_id=v.id,
                source_id=s.id,
                run_key=run_key or f"direct_{c.id}_{int(now.timestamp())}",
                platform=(s.platform or "telegram"),
                destination=(s.label or s.tg_ref),
                destination_ref=(s.destination_url or s.tg_ref or ""),
                asset_title=asset_title,
                asset_body=asset_body,
                action_taken="campaign_tick_direct",
                result_status="pending",
            )
            db.add(attempt)
        attempt.asset_title = asset_title
        attempt.asset_body = asset_body
        attempt.destination = s.label or s.tg_ref
        attempt.destination_ref = s.destination_url or s.tg_ref or ""
        attempt.platform = s.platform or "telegram"
        attempt.result_status = "pending"
        attempt.error_message = None
        attempt.operator_notes = ""

        if remaining_posts <= 0:
            attempt.action_taken = "daily_cap_reached"
            attempt.result_status = "failed"
            attempt.error_message = "Daily posting cap reached before this destination was processed."
            continue

        if (s.platform or "telegram") == "facebook":
            attempt.action_taken = "facebook_manual_prepare"
            attempt.result_status = "manual_action_required"
            # Operator-facing instruction stored on the attempt row. Keep RU primary
            # for the FloorDSGN pilot since the operator and customers are RU/HE.
            # Tamar feedback 2026-05-08: this string was leaking English into a
            # Russian-locale workspace. RU first, English follow-up for ops mixing.
            attempt.operator_notes = (
                "Открой канал/URL, скопируй подготовленный текст, опубликуй вручную, "
                "затем отметь результат (Posted/Failed). · Open destination, paste content, mark result."
            )
            s.last_check_message = "Manual Facebook action required."
            continue

        attempt.action_taken = "telegram_post_attempt"
        if not s.last_check_ok:
            attempt.result_status = "failed"
            attempt.error_message = "Telegram destination is not marked ready. Run Check first."
            s.last_check_message = attempt.error_message
            continue

        post_text = f"{asset_title}\n\n{asset_body}".strip()

        # Atomically reserve a daily-cap slot (shared across worker processes).
        # FB manual path returns above, so it never consumes the cap. Released
        # below if the post fails or is rescheduled.
        if not reserve_daily_slot(cap_key, c.max_posts_per_day):
            attempt.action_taken = "daily_cap_reached"
            attempt.result_status = "failed"
            attempt.error_message = f"Daily posting cap ({c.max_posts_per_day}) reached."
            continue

        # Routing rules:
        # - destination_kind == "chat": user-account Telethon CANNOT DM yourself, so use Bot API.
        #   Bot API can DM any user who has /start'd the bot — perfect for pilot DM destinations.
        # - Otherwise: try Telethon (user-account, posts to any group the user is in), Bot API as fallback.
        company = db.query(Company).filter(Company.id == c.company_id).first()
        telethon_ok = False
        kind = (s.destination_kind or s.source_type.value if hasattr(s, 'source_type') and s.source_type else 'group').lower()
        use_telethon = bool(company and company.tg_api_id and company.tg_api_hash) and kind != "chat"
        if use_telethon:
            from common.tg_client import post_to_group
            image = getattr(v, 'image_path', None)
            ok, msg = post_to_group(
                api_id=int(company.tg_api_id),
                api_hash=company.tg_api_hash,
                company_id=company.id,
                group_id=s.tg_ref,
                text=post_text,
                file_path=image,
            )
            telethon_ok = True
            logger.info(f"[campaign_tick] Telethon post to {s.tg_ref}: ok={ok}, msg={msg}")
            if not ok and ("Cannot find any entity" in (msg or "") or "PEER_ID_INVALID" in (msg or "")):
                logger.info(f"[campaign_tick] Telethon could not resolve {s.tg_ref}, falling back to Bot API")
                ok, msg = tg_send_message_safe(s.tg_ref, post_text)
                telethon_ok = False
                logger.info(f"[campaign_tick] Bot API fallback post to {s.tg_ref}: ok={ok}, msg={msg}")
        else:
            # Bot API path (only works if bot is admin in the group OR target user has /start'd the bot)
            ok, msg = tg_send_message_safe(s.tg_ref, post_text)
            logger.info(f"[campaign_tick] Bot API post to {s.tg_ref}: ok={ok}, msg={msg}")

        s.last_check_message = msg
        retry_secs = _parse_retry_later(msg)
        if ok:
            s.last_check_ok = True
            s.last_post_at = datetime.utcnow()
            attempt.result_status = "posted"
            attempt.operator_notes = f"Telegram post sent via {'Telethon' if telethon_ok else 'Bot API'}."
            remaining_posts -= 1
        elif retry_secs is not None:
            # FloodWait / night-mode / rate-limit — reschedule the run instead of
            # dropping the post; give the reserved slot back.
            release_daily_slot(cap_key)
            attempt.result_status = "rescheduled"
            attempt.error_message = msg
            reschedule_after = retry_secs if reschedule_after is None else min(reschedule_after, retry_secs)
        else:
            release_daily_slot(cap_key)
            if _should_clear_source_ready(msg):
                s.last_check_ok = False
            attempt.result_status = _blocked_status_from_message(msg)
            attempt.error_message = msg

    db.commit()
    db.close()

    # Reschedule once if any destination asked to retry later (bounded to avoid loops).
    if reschedule_after is not None and run_key:
        _reschedule_run(campaign_id, run_key, trigger, reschedule_after)
    release_lock(lock_key, lock_token)
    return

def daily_digest(company_id: int):
    # MVP: create digest string; sending to owner is out of scope.
    db = db_session()
    comp = db.query(Company).filter(Company.id == company_id).first()
    if not comp:
        db.close(); return
    new_count = db.query(Candidate).filter(Candidate.company_id==company_id, Candidate.created_at >= datetime.utcnow()-timedelta(days=1)).count()
    passed = db.query(Candidate).filter(Candidate.company_id==company_id, Candidate.status==CandidateStatus.passed).count()
    rejected = db.query(Candidate).filter(Candidate.company_id==company_id, Candidate.status==CandidateStatus.rejected).count()
    # Send daily digest via Telegram
    from bot.tg import tg_send_message_safe
    digest = (
        f"📊 Daily Digest — {comp.name}\n"
        f"New candidates (24h): {new_count}\n"
        f"Passed total: {passed}\n"
        f"Rejected total: {rejected}\n"
        f"—\nPosting Autopilot"
    )
    # Resolve a real Telegram chat id: per-company notify setting wins, then a
    # numeric owner_id, then an env fallback. (Self-service tenants store an email
    # in owner_id, so owner_id.isdigit() alone silently skipped them.)
    import os as _os
    chat_id = (getattr(comp, "notify_telegram_chat_id", None) or "").strip()
    if not (chat_id and chat_id.lstrip("-").isdigit()):
        chat_id = comp.owner_id if (comp.owner_id and comp.owner_id.lstrip("-").isdigit()) else ""
    if not chat_id:
        chat_id = (_os.getenv(f"RECRUIT_OPERATOR_NOTIFY_CHAT_{company_id}") or _os.getenv("RECRUIT_OPERATOR_NOTIFY_CHAT") or "").strip()
    if chat_id and chat_id.lstrip("-").isdigit():
        ok, msg = tg_send_message_safe(chat_id, digest)
        if not ok:
            logger.warning(f"[daily_digest] failed to send digest for company {company_id}: {msg}")
    else:
        logger.info(f"[daily_digest] company {company_id}: no Telegram chat configured, digest not sent")
    db.close()
