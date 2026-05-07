from __future__ import annotations
from datetime import datetime, timedelta
import json
import logging
from app.db import db_session
from app.models import Source, Campaign, CampaignSource, Vacancy, Company, Candidate, CandidateStatus, PostingAttempt
from common.ai import build_system_prompt
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
        if vacancy.apply_url:
            parts.append(f"Apply: {vacancy.apply_url}")
        # Task 2.3: WhatsApp click-to-chat
        if getattr(vacancy, 'whatsapp_number', None):
            wa_num = vacancy.whatsapp_number.lstrip('+')
            parts.append(f"WhatsApp: https://wa.me/{wa_num}")
        body = "\n".join([part for part in parts if part])
    return title, body


def _blocked_status_from_message(message: str) -> str:
    lowered = (message or "").lower()
    risky_markers = ["429", "too many requests", "blocked", "spam", "forbidden", "retry after", "flood"]
    if any(marker in lowered for marker in risky_markers):
        return "blocked_or_suspected"
    return "failed"

def check_source_access(source_id: int):
    # MVP: stub. In real world: use Telegram Bot API getChat/getChatMember.
    db = db_session()
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        db.close(); return
    # naive rule: if starts with @ or -100 -> assume ok
    ok = s.tg_ref.startswith("@") or s.tg_ref.startswith("-100")
    s.last_check_ok = bool(ok)
    s.last_check_message = "format looks valid only (stub, not real membership proof)" if ok else "invalid tg_ref format"
    db.commit()
    db.close()

def send_test_message(source_id: int, text: str):
    db = db_session()
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        db.close(); return
    ok, msg = tg_send_message_safe(s.tg_ref, text)
    s.last_check_ok = ok
    s.last_check_message = msg
    db.commit()
    db.close()

def campaign_tick(campaign_id: int, run_key: str | None = None, trigger: str = "scheduler_interval"):
    # MVP: post vacancy text to each source once. Scheduler will call periodically.
    db = db_session()
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c or not c.is_running:
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
        if s and s.last_post_at and s.last_post_at.date() == now.date():
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
            attempt.operator_notes = "Open the saved destination URL or destination ref, paste the prepared content, publish manually, then mark the result."
            s.last_check_message = "Manual Facebook action required."
            continue

        attempt.action_taken = "telegram_post_attempt"
        if not s.last_check_ok:
            attempt.result_status = "failed"
            attempt.error_message = "Telegram destination is not marked ready. Run Check first."
            s.last_check_message = attempt.error_message
            continue

        post_text = f"{asset_title}\n\n{asset_body}".strip()

        # Try Telethon (user account) first — this can post to any group the user is in
        company = db.query(Company).filter(Company.id == c.company_id).first()
        telethon_ok = False
        if company and company.tg_api_id and company.tg_api_hash:
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
        else:
            # Fallback to Bot API (only works if bot is admin in the group)
            ok, msg = tg_send_message_safe(s.tg_ref, post_text)
            logger.info(f"[campaign_tick] Bot API post to {s.tg_ref}: ok={ok}, msg={msg}")

        s.last_check_ok = ok
        s.last_check_message = msg
        if ok:
            s.last_post_at = datetime.utcnow()
            attempt.result_status = "posted"
            attempt.operator_notes = f"Telegram post sent via {'Telethon' if telethon_ok else 'Bot API'}."
            remaining_posts -= 1
        else:
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
