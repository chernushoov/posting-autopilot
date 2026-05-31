import json

from flask import Blueprint, redirect, render_template, request, url_for

from ..auth import require_company
from ..db import db_session
from ..models import Campaign, CampaignSource, PostingAttempt, Source, Vacancy
from ..tenant import current_company_id, scoped
from worker.queue import schedule_campaign_tick

bp = Blueprint("campaigns", __name__, url_prefix="/campaigns")

MIN_INTERVAL_MINUTES = 15
MAX_INTERVAL_MINUTES = 24 * 60
MIN_MAX_POSTS_PER_DAY = 1
MAX_MAX_POSTS_PER_DAY = 50
ATTEMPT_STATUSES = [
    "pending",
    "scheduled",
    "manual_action_required",
    "posted",
    "failed",
    "blocked_or_suspected",
]


def _is_source_pilot_ready(source):
    platform = (source.platform or "telegram").strip() or "telegram"
    if platform == "facebook":
        return bool(source.is_active and source.destination_url and (source.posting_mode or "assisted_manual") == "assisted_manual")
    return bool(source.is_active and source.last_check_ok)


def _parse_int(value, fallback=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _build_attempt_summary(attempts):
    summary = {status: 0 for status in ATTEMPT_STATUSES}
    by_platform = {}
    for attempt in attempts:
        status = (attempt.result_status or "pending").strip() or "pending"
        platform = (attempt.platform or "telegram").strip() or "telegram"
        summary[status] = summary.get(status, 0) + 1
        platform_bucket = by_platform.setdefault(platform, {key: 0 for key in ATTEMPT_STATUSES})
        platform_bucket[status] = platform_bucket.get(status, 0) + 1
    return {
        "by_status": summary,
        "by_platform": by_platform,
        "manual_required": summary.get("manual_action_required", 0),
    }


def _build_destination_summary(sources):
    telegram_total = 0
    telegram_ready = 0
    facebook_total = 0
    facebook_ready = 0
    for source in sources:
        platform = (source.platform or "telegram").strip() or "telegram"
        if platform == "facebook":
            facebook_total += 1
            if _is_source_pilot_ready(source):
                facebook_ready += 1
            continue
        telegram_total += 1
        if _is_source_pilot_ready(source):
            telegram_ready += 1
    return {
        "telegram_total": telegram_total,
        "telegram_ready": telegram_ready,
        "telegram_needs_check": max(telegram_total - telegram_ready, 0),
        "facebook_total": facebook_total,
        "facebook_ready": facebook_ready,
        "facebook_manual_only": facebook_total,
    }


def _campaign_form_context(db, *, error=None, message=None, form=None):
    vacancies = scoped(db, Vacancy).filter(Vacancy.is_active == True).order_by(Vacancy.id.desc()).all()
    sources = scoped(db, Source).filter(Source.is_active == True).order_by(Source.id.desc()).all()
    form = form or request.form
    selected_source_ids = {sid for sid in form.getlist("source_ids")} if hasattr(form, "getlist") else set(form.get("source_ids", []))
    selected_days = {day for day in form.getlist("days_of_week")} if hasattr(form, "getlist") else set(form.get("days_of_week", []))
    defaults = {
        "name": form.get("name", ""),
        "vacancy_id": form.get("vacancy_id", str(vacancies[0].id) if vacancies else ""),
        "interval_minutes": form.get("interval_minutes", "180"),
        "active_start_hour": form.get("active_start_hour", "9"),
        "active_end_hour": form.get("active_end_hour", "19"),
        "max_posts_per_day": form.get("max_posts_per_day", "10"),
    }
    if not selected_days:
        selected_days = {"0", "1", "2", "3", "4", "5"}
    return {
        "vacancies": vacancies,
        "sources": sources,
        "error": error,
        "message": message,
        "form_values": defaults,
        "selected_source_ids": selected_source_ids,
        "selected_days": selected_days,
        "interval_min": MIN_INTERVAL_MINUTES,
        "interval_max": MAX_INTERVAL_MINUTES,
        "max_posts_min": MIN_MAX_POSTS_PER_DAY,
        "max_posts_max": MAX_MAX_POSTS_PER_DAY,
        "weekday_options": [
            ("0", "Mon"),
            ("1", "Tue"),
            ("2", "Wed"),
            ("3", "Thu"),
            ("4", "Fri"),
            ("5", "Sat"),
            ("6", "Sun"),
        ],
    }


def _count_eligible_sources(sources):
    return sum(1 for source in sources if _is_source_pilot_ready(source))


@bp.get("/")
@require_company
def list_campaigns():
    db = db_session()
    campaigns = scoped(db, Campaign).order_by(Campaign.id.desc()).all()
    recent_attempts = (
        scoped(db, PostingAttempt)
        .order_by(PostingAttempt.created_at.desc(), PostingAttempt.id.desc())
        .limit(40)
        .all()
    )
    all_active_sources = scoped(db, Source).filter(Source.is_active == True).order_by(Source.id.desc()).all()
    open_manual_attempts = (
        scoped(db, PostingAttempt)
        .filter(PostingAttempt.result_status == "manual_action_required")
        .order_by(PostingAttempt.created_at.desc(), PostingAttempt.id.desc())
        .limit(12)
        .all()
    )
    attempt_summary = _build_attempt_summary(recent_attempts)
    destination_summary = _build_destination_summary(all_active_sources)
    pilot_checklist = [
        "Confirm the vacancy asset text, salary, contact, and apply path.",
        "Use only Telegram destinations marked READY for auto posting.",
        "Use Facebook only through assisted/manual posting with a direct destination URL.",
        "Run the pilot and then resolve every manual_action_required row before leaving the screen.",
        "Record operator notes on every failed or blocked_or_suspected destination.",
    ]
    db.close()
    return render_template(
        "campaigns.html",
        campaigns=campaigns,
        recent_attempts=recent_attempts,
        open_manual_attempts=open_manual_attempts,
        attempt_summary=attempt_summary,
        destination_summary=destination_summary,
        pilot_checklist=pilot_checklist,
        error=request.args.get("error"),
        message=request.args.get("message"),
    )


@bp.get("/new")
@require_company
def new_campaign():
    db = db_session()
    context = _campaign_form_context(db)
    db.close()
    return render_template("campaign_new.html", **context)


@bp.post("/new")
@require_company
def new_campaign_post():
    db = db_session()
    name = request.form.get("name", "").strip() or "Pilot run"
    vacancy_id = _parse_int(request.form.get("vacancy_id", "0"), 0)
    interval = _parse_int(request.form.get("interval_minutes", "180"), 0)
    active_start_hour = _parse_int(request.form.get("active_start_hour", "9"), -1)
    active_end_hour = _parse_int(request.form.get("active_end_hour", "19"), -1)
    max_posts_per_day = _parse_int(request.form.get("max_posts_per_day", "10"), 0)

    source_ids = []
    for raw in request.form.getlist("source_ids"):
        parsed = _parse_int(raw)
        if parsed is not None:
            source_ids.append(parsed)

    selected_days = []
    for raw in request.form.getlist("days_of_week"):
        parsed = _parse_int(raw)
        if parsed is not None:
            selected_days.append(parsed)

    vacancy = scoped(db, Vacancy).filter(Vacancy.id == vacancy_id, Vacancy.is_active == True).first()
    if not vacancy:
        context = _campaign_form_context(db, error="Choose one active vacancy before creating a pilot run.")
        db.close()
        return render_template("campaign_new.html", **context)

    if not source_ids:
        context = _campaign_form_context(db, error="Choose at least one active destination before creating a pilot run.")
        db.close()
        return render_template("campaign_new.html", **context)

    sources = scoped(db, Source).filter(Source.id.in_(source_ids), Source.is_active == True).all()
    if len(sources) != len(set(source_ids)):
        context = _campaign_form_context(db, error="One or more selected destinations are missing or inactive.")
        db.close()
        return render_template("campaign_new.html", **context)

    if _count_eligible_sources(sources) == 0:
        context = _campaign_form_context(
            db,
            error="Choose at least one pilot-ready destination: Telegram must be READY, Facebook must have a direct URL for assisted/manual posting.",
        )
        db.close()
        return render_template("campaign_new.html", **context)

    if interval is None or interval < MIN_INTERVAL_MINUTES or interval > MAX_INTERVAL_MINUTES:
        context = _campaign_form_context(
            db,
            error=f"Interval must be between {MIN_INTERVAL_MINUTES} and {MAX_INTERVAL_MINUTES} minutes.",
        )
        db.close()
        return render_template("campaign_new.html", **context)

    invalid_hours = (
        active_start_hour is None
        or active_end_hour is None
        or active_start_hour < 0
        or active_start_hour > 23
        or active_end_hour < 1
        or active_end_hour > 24
        or active_start_hour >= active_end_hour
    )
    if invalid_hours:
        context = _campaign_form_context(db, error="Active hours must be valid and the end hour must be later than the start hour.")
        db.close()
        return render_template("campaign_new.html", **context)

    if not selected_days:
        context = _campaign_form_context(db, error="Select at least one active weekday for the pilot run.")
        db.close()
        return render_template("campaign_new.html", **context)

    if max_posts_per_day is None or max_posts_per_day < MIN_MAX_POSTS_PER_DAY or max_posts_per_day > MAX_MAX_POSTS_PER_DAY:
        context = _campaign_form_context(
            db,
            error=f"Max posts per day must be between {MIN_MAX_POSTS_PER_DAY} and {MAX_MAX_POSTS_PER_DAY}.",
        )
        db.close()
        return render_template("campaign_new.html", **context)

    campaign = Campaign(
        company_id=current_company_id(),
        vacancy_id=vacancy_id,
        name=name,
        interval_minutes=interval,
        active_hours_json=json.dumps({"start": active_start_hour, "end": active_end_hour}),
        days_of_week_json=json.dumps(sorted(set(selected_days))),
        max_posts_per_day=max_posts_per_day,
        is_running=False,
    )
    db.add(campaign)
    db.commit()

    for source_id in sorted(set(source_ids)):
        db.add(CampaignSource(campaign_id=campaign.id, source_id=source_id))
    db.commit()
    db.close()
    return redirect(url_for("campaigns.list_campaigns", message="Pilot run created. Review the posting preview and start only when the destinations are ready."))


@bp.post("/toggle/<int:campaign_id>")
@require_company
def toggle_campaign(campaign_id: int):
    db = db_session()
    campaign = scoped(db, Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        db.close()
        return redirect(url_for("campaigns.list_campaigns", error="Pilot run not found."))

    if not campaign.is_running:
        vacancy = scoped(db, Vacancy).filter(Vacancy.id == campaign.vacancy_id, Vacancy.is_active == True).first()
        linked_sources = (
            db.query(Source)
            .join(CampaignSource, Source.id == CampaignSource.source_id)
            .filter(CampaignSource.campaign_id == campaign.id, Source.company_id == campaign.company_id, Source.is_active == True)
            .all()
        )
        if not vacancy:
            db.close()
            return redirect(url_for("campaigns.list_campaigns", error="Cannot start pilot run without an active vacancy."))
        if not linked_sources:
            db.close()
            return redirect(url_for("campaigns.list_campaigns", error="Cannot start pilot run without at least one active destination."))
        if _count_eligible_sources(linked_sources) == 0:
            db.close()
            return redirect(url_for("campaigns.list_campaigns", error="Cannot start pilot run until at least one destination is pilot-ready. Telegram must be READY. Facebook must have a direct URL."))
        if campaign.interval_minutes < MIN_INTERVAL_MINUTES or campaign.interval_minutes > MAX_INTERVAL_MINUTES:
            db.close()
            return redirect(url_for("campaigns.list_campaigns", error="Pilot interval is outside the safe operating range."))

    campaign.is_running = not campaign.is_running
    db.commit()
    db.close()

    if campaign.is_running:
        schedule_campaign_tick(campaign.id, "campaign_started")
        message = "Pilot run started and the first posting cycle was queued."
    else:
        message = "Pilot run paused."
    return redirect(url_for("campaigns.list_campaigns", message=message))


@bp.post("/run/<int:campaign_id>")
@require_company
def run_campaign_now(campaign_id: int):
    db = db_session()
    campaign = scoped(db, Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        db.close()
        return redirect(url_for("campaigns.list_campaigns", error="Pilot run not found."))

    vacancy = scoped(db, Vacancy).filter(Vacancy.id == campaign.vacancy_id, Vacancy.is_active == True).first()
    linked_sources = (
        db.query(Source)
        .join(CampaignSource, Source.id == CampaignSource.source_id)
        .filter(CampaignSource.campaign_id == campaign.id, Source.company_id == campaign.company_id, Source.is_active == True)
        .all()
    )
    db.close()
    if not vacancy:
        return redirect(url_for("campaigns.list_campaigns", error="Cannot run without an active vacancy."))
    if not linked_sources:
        return redirect(url_for("campaigns.list_campaigns", error="Cannot run without at least one active destination."))
    if _count_eligible_sources(linked_sources) == 0:
        return redirect(url_for("campaigns.list_campaigns", error="Cannot run until at least one destination is pilot-ready. Telegram must be READY. Facebook must have a direct URL."))

    try:
        job, _run_key = schedule_campaign_tick(campaign_id, "operator_run_now")
    except Exception:
        return redirect(url_for("campaigns.list_campaigns", error="Background queue is offline (Redis/worker not running). Start the stack and try again."))
    if job is None:
        return redirect(url_for("campaigns.list_campaigns", message="A posting cycle is already in progress for this pilot — not starting a duplicate. Watch the log below."))
    return redirect(url_for("campaigns.list_campaigns", message="Posting cycle queued immediately. Watch the destination log below for results."))


@bp.post("/attempt/<int:attempt_id>/retry")
@require_company
def retry_attempt(attempt_id: int):
    """Re-fire a single failed PostingAttempt. The worker treats it as a
    `operator_run_now` trigger limited to the original campaign + source.

    Use case: posting fails (FloodWait, transient network), operator fixes
    something (joins the group / rotates session) and wants ONE retry without
    rebuilding the campaign or waiting for the scheduler tick.
    """
    db = db_session()
    attempt = scoped(db, PostingAttempt).filter(PostingAttempt.id == attempt_id).first()
    if not attempt:
        db.close()
        return redirect(url_for("campaigns.list_campaigns", error="Posting log entry not found."))
    if attempt.result_status not in ("failed", "blocked_or_suspected"):
        db.close()
        return redirect(url_for("campaigns.list_campaigns", error="Only failed entries can be retried."))
    campaign_id = attempt.campaign_id
    db.close()
    try:
        job, _run_key = schedule_campaign_tick(campaign_id, "operator_run_now")
    except Exception:
        return redirect(url_for("campaigns.list_campaigns", error="Background queue is offline (Redis/worker not running). Start the stack and try again."))
    if job is None:
        return redirect(url_for("campaigns.list_campaigns", message="A posting cycle is already in progress — retry not duplicated."))
    return redirect(url_for(
        "campaigns.list_campaigns",
        message="Retry queued. The next posting cycle will reuse the existing campaign + destinations.",
        focus_attempt=attempt_id,
    ))


@bp.post("/attempt/<int:attempt_id>/result")
@require_company
def update_attempt_result(attempt_id: int):
    result_status = (request.form.get("result_status", "") or "").strip()
    operator_notes = request.form.get("operator_notes", "").strip()
    allowed_statuses = {"posted", "failed", "blocked_or_suspected"}
    if result_status not in allowed_statuses:
        return redirect(url_for("campaigns.list_campaigns", error="Choose a valid manual result status."))

    db = db_session()
    attempt = scoped(db, PostingAttempt).filter(PostingAttempt.id == attempt_id).first()
    if not attempt:
        db.close()
        return redirect(url_for("campaigns.list_campaigns", error="Posting log entry not found."))
    if attempt.result_status != "manual_action_required":
        db.close()
        return redirect(url_for("campaigns.list_campaigns", error="Only manual-action entries can be updated from the operator screen."))

    attempt.action_taken = f"facebook_manual_confirm_{result_status}"
    attempt.result_status = result_status
    attempt.operator_notes = operator_notes
    attempt.error_message = None if result_status == "posted" else operator_notes or "Operator marked the assisted/manual Facebook step as unsuccessful."
    db.commit()
    db.close()
    return redirect(url_for("campaigns.list_campaigns", message="Manual destination result saved."))
