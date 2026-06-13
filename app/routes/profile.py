"""Company/Individual profile — view and edit current account."""
from flask import Blueprint, render_template, request, redirect, url_for, session
import re
from pathlib import Path
from uuid import uuid4

from werkzeug.utils import secure_filename

from ..auth import require_company
from ..db import db_session
from ..models import Company
from ..tenant import current_company_id

bp = Blueprint("profile", __name__, url_prefix="/profile")

CHAT_ID_RE = re.compile(r"^-?\d+$")

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads"
_ALLOWED_IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def _save_logo(file_storage) -> str | None:
    """Save an uploaded company logo and return its filesystem path (or None).

    Mirrors the vacancy image upload: validates the extension, gives the file a
    random name, and drops it in data/uploads (served via /uploads/<basename>).
    """
    if not file_storage or not (file_storage.filename or "").strip():
        return None
    ext = Path(secure_filename(file_storage.filename or "")).suffix.lower()
    if ext not in _ALLOWED_IMG_EXT:
        raise ValueError("Only JPG, PNG, and WebP logo uploads are allowed.")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    save_path = UPLOAD_DIR / f"logo_{uuid4().hex}{ext}"
    file_storage.save(save_path)
    return str(save_path)


@bp.get("/")
@require_company
def view_profile():
    import os
    db = db_session()
    company = db.query(Company).filter(Company.id == current_company_id()).first()
    db.close()
    if not company:
        return redirect(url_for("auth.dashboard"))
    bot_username = os.getenv("RECRUITBOT_BOT_USERNAME", "AutopillotRecruit_bot").lstrip("@")
    return render_template("profile.html", c=company, bot_username=bot_username)


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

    # Company logo: upload a new image, or tick "remove" to clear it.
    if request.form.get("remove_logo"):
        company.logo_path = None
    else:
        try:
            saved_logo = _save_logo(request.files.get("logo"))
        except ValueError as exc:
            return render_template("profile.html", c=company, error=str(exc))
        if saved_logo:
            company.logo_path = saved_logo

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

    from common.notify_targets import normalize_chat_id, sample_hot_lead_message

    # Send to the operator's OWN configured Telegram only — NOT the deployment-wide
    # RECRUIT_OPERATOR_NOTIFY_CHAT fallback. Otherwise a successful send to the shared
    # fallback would report a false "Sent!" while the user's own chat got nothing.
    target = normalize_chat_id(getattr(company, "owner_telegram_id", None))
    if not target:
        return redirect(url_for("profile.view_profile") + "?error=hotlead_no_target")

    lang = session.get("ui_lang", "ru")
    text = sample_hot_lead_message(company, lang)
    try:
        from bot.tg import tg_send_message_safe
        ok, msg = tg_send_message_safe(target, text)
    except Exception as exc:  # pragma: no cover - best-effort send
        ok, msg = False, str(exc)

    if ok:
        return redirect(url_for("profile.view_profile") + "?message=hotlead_sent")
    # Telegram bots cannot DM a user who never pressed Start → "chat not found".
    low = (msg or "").lower()
    if "not found" in low or "chat not found" in low or "blocked" in low or "can't initiate" in low or "bad request" in low:
        return redirect(url_for("profile.view_profile") + "?error=hotlead_need_start")
    return redirect(url_for("profile.view_profile") + "?error=hotlead_fail")
