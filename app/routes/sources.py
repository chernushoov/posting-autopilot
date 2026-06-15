import time
from flask import Blueprint, redirect, render_template, request, url_for

from ..auth import require_company
from ..db import db_session
from ..models import Company, Source, SourceType
from ..plans import UPGRADE_HINT, source_slots_left
from ..tenant import current_company_id, scoped
from worker.queue import enqueue_check_source, enqueue_test_message

bp = Blueprint("sources", __name__, url_prefix="/sources")

TELEGRAM_DESTINATION_KINDS = ("group", "channel", "chat")
FACEBOOK_DESTINATION_KINDS = ("group", "page", "marketplace")
ALL_DESTINATION_KINDS = TELEGRAM_DESTINATION_KINDS + tuple(
    kind for kind in FACEBOOK_DESTINATION_KINDS if kind not in TELEGRAM_DESTINATION_KINDS
)


def _valid_tg_ref(value: str, destination_kind: str = "group") -> bool:
    if value.startswith("@") and len(value) > 1:
        return True
    if value.startswith("-100") and value[4:].isdigit():
        return True
    if destination_kind == "chat" and value.isdigit() and len(value) >= 6:
        return True
    return False


def _is_facebook_destination_ready(source: Source) -> bool:
    return bool(source.is_active and source.destination_url and (source.posting_mode or "assisted_manual") == "assisted_manual")


def _is_telegram_destination_ready(source: Source) -> bool:
    return bool(source.is_active and source.last_check_ok)


@bp.get("/")
@require_company
def list_sources():
    db = db_session()
    sources = scoped(db, Source).order_by(Source.id.desc()).all()
    source_summary = {
        "telegram_total": 0,
        "telegram_ready": 0,
        "telegram_needs_check": 0,
        "facebook_total": 0,
        "facebook_manual": 0,
        "facebook_ready": 0,
        "facebook_missing_url": 0,
    }
    for source in sources:
        platform = (source.platform or "telegram").strip() or "telegram"
        if platform == "facebook":
            source_summary["facebook_total"] += 1
            source_summary["facebook_manual"] += 1
            if _is_facebook_destination_ready(source):
                source_summary["facebook_ready"] += 1
            else:
                source_summary["facebook_missing_url"] += 1
        else:
            source_summary["telegram_total"] += 1
            if _is_telegram_destination_ready(source):
                source_summary["telegram_ready"] += 1
            else:
                source_summary["telegram_needs_check"] += 1
    db.close()
    return render_template(
        "sources.html",
        sources=sources,
        source_summary=source_summary,
        destination_kind_options=ALL_DESTINATION_KINDS,
        platforms=["telegram", "facebook"],
        posting_modes=["auto", "assisted_manual"],
        error=request.args.get("error"),
        message=request.args.get("message"),
    )


@bp.post("/new")
@require_company
def new_source():
    destination_ref = request.form.get("tg_ref", "").strip()
    label = request.form.get("label", "").strip() or None
    destination_kind = request.form.get("destination_kind") or request.form.get("source_type", "group")
    platform = request.form.get("platform", "telegram").strip() or "telegram"
    posting_mode = request.form.get("posting_mode", "auto").strip() or "auto"
    destination_url = request.form.get("destination_url", "").strip() or None

    # Facebook sources don't need a telegram ref — auto-generate a unique one
    if platform == "facebook" and not destination_ref:
        destination_ref = f"fb-{int(time.time())}-{id(destination_url) % 10000}"
    if not destination_ref:
        return redirect(url_for("sources.list_sources", error="Destination ref is required."))
    if platform == "telegram" and not _valid_tg_ref(destination_ref, destination_kind):
        return redirect(url_for("sources.list_sources", error="Telegram ref must look like @username, -1001234567890, or a numeric chat id (chat-kind only)."))
    if platform not in {"telegram", "facebook"}:
        return redirect(url_for("sources.list_sources", error="Choose a valid platform."))
    allowed_destination_kinds = TELEGRAM_DESTINATION_KINDS if platform == "telegram" else FACEBOOK_DESTINATION_KINDS
    if destination_kind not in allowed_destination_kinds:
        return redirect(url_for("sources.list_sources", error="Choose a valid destination kind for this platform."))
    if platform == "facebook":
        posting_mode = "assisted_manual"
        if not destination_url:
            return redirect(url_for("sources.list_sources", error="Facebook pilot destinations require a direct destination URL."))
    if posting_mode not in {"auto", "assisted_manual"}:
        return redirect(url_for("sources.list_sources", error="Choose a valid posting mode."))

    db = db_session()
    company = db.query(Company).filter(Company.id == current_company_id()).first()
    slots = source_slots_left(db, company) if company else 0
    if slots is not None and slots <= 0:
        db.close()
        return redirect(url_for(
            "sources.list_sources",
            error=f"Your plan's destination limit is reached. {UPGRADE_HINT}",
        ))
    folder = request.form.get("folder", "").strip() or None
    source_type = SourceType(destination_kind) if platform == "telegram" else SourceType.group
    source = Source(
        company_id=current_company_id(),
        tg_ref=destination_ref,
        label=label,
        source_type=source_type,
        platform=platform,
        destination_kind=destination_kind,
        posting_mode=posting_mode,
        destination_url=destination_url,
        folder=folder,
        last_check_ok=(True if platform == "facebook" and destination_url else False),
        last_check_message=("Facebook manual destination saved." if platform == "facebook" and destination_url else None),
    )
    db.add(source)
    try:
        db.commit()
    except Exception:
        db.rollback()
        db.close()
        ref = request.referrer
        if ref:
            return redirect(ref + ("&" if "?" in ref else "?") + "error=already_exists")
        return redirect(url_for("sources.list_sources", error="This destination already exists."))
    db.close()
    # Return to referrer (Facebook/Telegram page) instead of sources list
    ref = request.referrer
    if ref:
        return redirect(ref + ("&" if "?" in ref else "?") + "message=added")
    return redirect(url_for("sources.list_sources", message="Destination added."))


@bp.post("/check-all")
@require_company
def check_all_sources():
    """Bulk-enqueue Telethon access checks for every Telegram source in the
    current company that isn't already marked ready. Useful right after a
    fresh sync_dialogs / curated import so the operator doesn't click 5+
    individual Check buttons.

    Facebook destinations are not queued — they're verified differently
    (URL presence) via the per-source check_source path.
    """
    db = db_session()
    sources = scoped(db, Source).filter(
        Source.platform == "telegram",
        Source.is_active == True,
        Source.last_check_ok == False,
    ).all()
    queued = 0
    for s in sources:
        try:
            enqueue_check_source(s.id)
            queued += 1
        except Exception:
            continue
    db.close()
    return redirect(url_for(
        "sources.list_sources",
        message=f"Queued Telethon access checks for {queued} pending Telegram destinations.",
    ))


@bp.post("/check/<int:source_id>")
@require_company
def check_source(source_id: int):
    db = db_session()
    source = scoped(db, Source).filter(Source.id == source_id).first()
    if not source:
        db.close()
        return redirect(url_for("sources.list_sources", error="Destination not found."))
    if (source.platform or "telegram") == "facebook":
        source.last_check_ok = True
        source.last_check_message = "Manual Facebook destination confirmed by operator."
        db.commit()
        db.close()
        return redirect(url_for("sources.list_sources", message="Facebook destination marked ready for assisted/manual pilot posting."))
    db.close()
    enqueue_check_source(source_id)
    return redirect(url_for("sources.list_sources", message="Destination check queued."))


@bp.post("/test/<int:source_id>")
@require_company
def test_source(source_id: int):
    if request.form.get("confirm_live_send") != "yes":
        return redirect(url_for("sources.list_sources", error="Confirm live send before testing a destination."))

    db = db_session()
    # Read the fields we need WHILE the session is open (don't touch a detached
    # instance after close — that can re-query on a closed session or see stale state).
    source = scoped(db, Source).filter(Source.id == source_id).first()
    if not source:
        db.close()
        return redirect(url_for("sources.list_sources", error="Destination not found."))
    platform = source.platform or "telegram"
    last_check_ok = source.last_check_ok
    db.close()

    if platform == "facebook":
        return redirect(url_for("sources.list_sources", error="Facebook destinations use assisted/manual posting in pilot mode. Use Pilot Runs to prepare the post and log the manual result."))
    if not last_check_ok:
        return redirect(url_for("sources.list_sources", error="Run Check first and confirm the destination looks ready before sending a live test message."))

    enqueue_test_message(source_id, "Test message from Posting Autopilot")
    return redirect(url_for("sources.list_sources", message="Live Telegram test message queued."))


@bp.post("/delete/<int:source_id>")
@require_company
def delete_source(source_id: int):
    db = db_session()
    source = scoped(db, Source).filter(Source.id == source_id).first()
    if source:
        # Remove dependent rows first — campaign links and posting history both
        # carry a NOT NULL source_id, so a bare delete would hit a FK violation
        # once enforcement is on. Delete children, then the source.
        from ..models import CampaignSource, PostingAttempt
        db.query(CampaignSource).filter(CampaignSource.source_id == source.id).delete(synchronize_session=False)
        db.query(PostingAttempt).filter(PostingAttempt.source_id == source.id).delete(synchronize_session=False)
        db.delete(source)
        db.commit()
    db.close()
    # Return to referrer (connect/telegram or sources page)
    ref = request.referrer or url_for("sources.list_sources")
    return redirect(ref)


@bp.post("/folder/<int:source_id>")
@require_company
def set_folder(source_id: int):
    folder = request.form.get("folder", "").strip() or None
    db = db_session()
    source = scoped(db, Source).filter(Source.id == source_id).first()
    if source:
        source.folder = folder
        db.commit()
    db.close()
    ref = request.referrer or url_for("sources.list_sources")
    return redirect(ref)
