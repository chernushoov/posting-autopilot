from __future__ import annotations
from datetime import datetime, timedelta
import json
import logging
from app.db import db_session
from app.models import Source, Campaign, CampaignSource, Vacancy, Company, Candidate, CandidateStatus, PostingAttempt
from common.ai import build_system_prompt
from common.recruitbot_links import build_recruitbot_apply_link
from bot.tg import tg_send_message_safe

logger = logging.getLogger(__name__)

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
        body = "\n".join([part for part in parts if part])
    return title, body


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


def _source_destination_kind(source: Source) -> str:
    if source.destination_kind:
        return source.destination_kind.lower()
    if getattr(source, "source_type", None):
        source_type = getattr(source.source_type, "value", source.source_type)
        return str(source_type).lower()
    return "group"


def _send_telegram_post(source: Source, company: Company | None, text: str, file_path: str | None = None) -> tuple[bool, str, str]:
    kind = _source_destination_kind(source)
    use_telethon = bool(company and company.tg_api_id and company.tg_api_hash) and kind != "chat"
    if use_telethon:
        from common.tg_client import post_to_group, should_fallback_to_bot_api

        ok, msg = post_to_group(
            api_id=int(company.tg_api_id),
            api_hash=company.tg_api_hash,
            company_id=company.id,
            group_id=source.tg_ref,
            text=text,
            file_path=file_path,
        )
        logger.info(f"[telegram_post] Telethon post to {source.tg_ref}: ok={ok}, msg={msg}")
        if not ok and should_fallback_to_bot_api(msg):
            logger.info(f"[telegram_post] Telethon could not resolve {source.tg_ref}, falling back to Bot API")
            ok, msg = tg_send_message_safe(source.tg_ref, text)
            logger.info(f"[telegram_post] Bot API fallback post to {source.tg_ref}: ok={ok}, msg={msg}")
            return ok, msg, "bot_api"
        return ok, msg, "telethon"

    ok, msg = tg_send_message_safe(source.tg_ref, text)
    logger.info(f"[telegram_post] Bot API post to {source.tg_ref}: ok={ok}, msg={msg}")
    return ok, msg, "bot_api"

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
        # R6: don't green-light a destination we can't actually post to. Without a
        # connected Telegram account the source can't be verified OR posted, so
        # marking it READY was a false green light that fails silently at run time.
        s.last_check_ok = False
        s.last_check_message = "Connect your Telegram account first (Connect Telegram), then re-check this destination."
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
    company = db.query(Company).filter(Company.id == s.company_id).first()
    ok, msg, _delivery_method = _send_telegram_post(s, company, text)
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
    # Use Israel time (UTC+3) for active hours check
    from datetime import timezone, timedelta
    ISRAEL_TZ = timezone(timedelta(hours=3))
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
    asset_title, asset_body = _build_post_asset(v)

    links = db.query(CampaignSource).filter(CampaignSource.campaign_id == c.id).all()
    posted_today = 0
    for link in links:
        s = db.query(Source).filter(Source.id == link.source_id, Source.company_id == c.company_id).first()
        if s and s.last_post_at:
            # R4: last_post_at is stored naive UTC; compare in Israel-local date so
            # the per-day cap doesn't miscount near midnight Israel time.
            last_local_date = s.last_post_at.replace(tzinfo=timezone.utc).astimezone(ISRAEL_TZ).date()
            if last_local_date == now.date():
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

        # Routing rules:
        # - destination_kind == "chat": user-account Telethon CANNOT DM yourself, so use Bot API.
        #   Bot API can DM any user who has /start'd the bot — perfect for pilot DM destinations.
        # - Otherwise: try Telethon (user-account, posts to any group the user is in), Bot API as fallback.
        company = db.query(Company).filter(Company.id == c.company_id).first()
        image = getattr(v, 'image_path', None)
        ok, msg, delivery_method = _send_telegram_post(s, company, post_text, file_path=image)

        s.last_check_message = msg
        if ok:
            s.last_check_ok = True
            s.last_post_at = datetime.utcnow()
            attempt.result_status = "posted"
            attempt.operator_notes = f"Telegram post sent via {'Telethon' if delivery_method == 'telethon' else 'Bot API'}."
            remaining_posts -= 1
        else:
            if _should_clear_source_ready(msg):
                s.last_check_ok = False
            attempt.result_status = _blocked_status_from_message(msg)
            attempt.error_message = msg
    db.commit()
    db.close()

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
    # Send to admin chat (owner_id is typically tg user id or we skip)
    if comp.owner_id and comp.owner_id.isdigit():
        tg_send_message_safe(comp.owner_id, digest)
    db.commit()
    db.close()
