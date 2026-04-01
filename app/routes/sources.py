import time
from flask import Blueprint, redirect, render_template, request, url_for

from ..auth import require_company
from ..db import db_session
from ..models import Source, SourceType
from ..tenant import current_company_id, scoped
from worker.queue import enqueue_check_source, enqueue_test_message

bp = Blueprint("sources", __name__, url_prefix="/sources")


def _valid_tg_ref(value: str) -> bool:
    if value.startswith("@") and len(value) > 1:
        return True
    if value.startswith("-100") and value[4:].isdigit():
        return True
    return False


@bp.get("/")
@require_company
def list_sources():
    db = db_session()
    sources = scoped(db, Source).order_by(Source.id.desc()).all()
    db.close()
    return render_template(
        "sources.html",
        sources=sources,
        types=[t.value for t in SourceType],
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
    if platform == "telegram" and not _valid_tg_ref(destination_ref):
        return redirect(url_for("sources.list_sources", error="Telegram ref must look like @username or -1001234567890."))
    if platform not in {"telegram", "facebook"}:
        return redirect(url_for("sources.list_sources", error="Choose a valid platform."))
    if destination_kind not in {t.value for t in SourceType}:
        return redirect(url_for("sources.list_sources", error="Choose a valid destination kind."))
    if platform == "facebook":
        posting_mode = "assisted_manual"
    if posting_mode not in {"auto", "assisted_manual"}:
        return redirect(url_for("sources.list_sources", error="Choose a valid posting mode."))

    db = db_session()
    folder = request.form.get("folder", "").strip() or None
    source = Source(
        company_id=current_company_id(),
        tg_ref=destination_ref,
        label=label,
        source_type=SourceType(destination_kind),
        platform=platform,
        destination_kind=destination_kind,
        posting_mode=posting_mode,
        destination_url=destination_url,
        folder=folder,
    )
    db.add(source)
    try:
        db.commit()
    except Exception:
        db.rollback()
        db.close()
        return redirect(url_for("sources.list_sources", error="This destination already exists for the current company."))
    db.close()
    return redirect(url_for("sources.list_sources", message="Destination added. Run Check before any live send."))


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
    source = scoped(db, Source).filter(Source.id == source_id).first()
    db.close()
    if not source:
        return redirect(url_for("sources.list_sources", error="Destination not found."))
    if (source.platform or "telegram") == "facebook":
        return redirect(url_for("sources.list_sources", error="Facebook destinations use assisted/manual posting in pilot mode. Use Pilot Runs to prepare the post and log the manual result."))
    if not source.last_check_ok:
        return redirect(url_for("sources.list_sources", error="Run Check first and confirm the destination looks ready before sending a live test message."))

    enqueue_test_message(source_id, "Test message from Posting Autopilot")
    return redirect(url_for("sources.list_sources", message="Live Telegram test message queued."))


@bp.post("/delete/<int:source_id>")
@require_company
def delete_source(source_id: int):
    db = db_session()
    source = scoped(db, Source).filter(Source.id == source_id).first()
    if source:
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
