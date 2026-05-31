"""Company/Individual profile — view and edit current account."""
from flask import Blueprint, render_template, request, redirect, url_for, session
import re

from ..auth import require_company
from ..db import db_session
from ..models import Company
from ..tenant import current_company_id

bp = Blueprint("profile", __name__, url_prefix="/profile")

CHAT_ID_RE = re.compile(r"^-?\d+$")


@bp.get("/")
@require_company
def view_profile():
    db = db_session()
    company = db.query(Company).filter(Company.id == current_company_id()).first()
    db.close()
    if not company:
        return redirect(url_for("auth.dashboard"))
    return render_template("profile.html", c=company)


@bp.post("/")
@require_company
def update_profile():
    db = db_session()
    company = db.query(Company).filter(Company.id == current_company_id()).first()
    if not company:
        db.close()
        return redirect(url_for("auth.dashboard"))

    raw_owner_telegram_id = request.form.get("owner_telegram_id", "").strip()
    if raw_owner_telegram_id and not CHAT_ID_RE.fullmatch(raw_owner_telegram_id):
        return render_template(
            "profile.html",
            c=company,
            error="Telegram notification ID must be numeric, for example 123456789 or -1001234567890.",
        )

    company.name = request.form.get("name", "").strip() or company.name
    company.description = request.form.get("description", "").strip() or None
    company.business_type = request.form.get("business_type", "company").strip()
    company.contact_person = request.form.get("contact_person", "").strip() or None
    company.phone = request.form.get("phone", "").strip() or None
    company.email = request.form.get("email", "").strip() or None
    company.website = request.form.get("website", "").strip() or None
    company.logo_emoji = request.form.get("logo_emoji", "").strip() or None
    company.owner_telegram_id = raw_owner_telegram_id or None

    db.commit()
    db.close()
    return redirect(url_for("profile.view_profile") + "?message=saved")


@bp.post("/test-hot-lead")
@require_company
def test_hot_lead():
    """Send a realistic 🔥 hot-lead alert to the operator's configured Telegram, so
    they can confirm — before going live — that the headline feature actually reaches
    them. Uses the same target resolution as the live capture path.
    """
    db = db_session()
    company = db.query(Company).filter(Company.id == current_company_id()).first()
    db.close()
    if not company:
        return redirect(url_for("auth.dashboard"))

    from common.notify_targets import resolve_recruit_notify_targets, sample_hot_lead_message

    targets = resolve_recruit_notify_targets(company)
    if not targets:
        return redirect(url_for("profile.view_profile") + "?error=hotlead_no_target")

    lang = session.get("ui_lang", "ru")
    text = sample_hot_lead_message(company, lang)
    sent = 0
    last_err = ""
    try:
        from bot.tg import tg_send_message_safe

        for chat_id in targets:
            ok, msg = tg_send_message_safe(chat_id, text)
            if ok:
                sent += 1
            else:
                last_err = msg or ""
    except Exception as exc:  # pragma: no cover - best-effort send
        last_err = str(exc)

    if sent:
        return redirect(url_for("profile.view_profile") + "?message=hotlead_sent")
    return redirect(url_for("profile.view_profile") + "?error=hotlead_fail")
