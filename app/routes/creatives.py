"""Creatives — a per-company media library of banners/posters/logos.

Upload your visual assets once; reuse them across Telegram/Facebook posts. Files
live in data/uploads and are served to the owning tenant via /uploads/<basename>.
"""
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, render_template, request, redirect, url_for

from werkzeug.utils import secure_filename

from ..auth import require_company
from ..db import db_session
from ..models import Creative
from ..tenant import current_company_id

bp = Blueprint("creatives", __name__, url_prefix="/creatives")

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads"
_ALLOWED_IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_KINDS = {"banner", "poster", "logo", "photo"}


@bp.get("/")
@require_company
def list_creatives():
    db = db_session()
    items = (
        db.query(Creative)
        .filter(Creative.company_id == current_company_id())
        .order_by(Creative.created_at.desc())
        .all()
    )
    creatives = [
        {"id": c.id, "kind": c.kind, "title": c.title, "url": f"/uploads/{Path(c.file_path).name}"}
        for c in items
    ]
    db.close()
    return render_template("creatives.html", creatives=creatives)


@bp.post("/")
@require_company
def upload_creative():
    kind = request.form.get("kind", "banner").strip()
    if kind not in _KINDS:
        kind = "banner"
    title = request.form.get("title", "").strip() or None
    file = request.files.get("file")
    if not file or not (file.filename or "").strip():
        return redirect(url_for("creatives.list_creatives") + "?error=nofile")
    ext = Path(secure_filename(file.filename or "")).suffix.lower()
    if ext not in _ALLOWED_IMG_EXT:
        return redirect(url_for("creatives.list_creatives") + "?error=badtype")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    save_path = UPLOAD_DIR / f"creative_{uuid4().hex}{ext}"
    file.save(save_path)
    db = db_session()
    db.add(Creative(company_id=current_company_id(), kind=kind, title=title, file_path=str(save_path)))
    db.commit()
    db.close()
    return redirect(url_for("creatives.list_creatives") + "?message=added")


@bp.post("/<int:creative_id>/delete")
@require_company
def delete_creative(creative_id: int):
    db = db_session()
    item = (
        db.query(Creative)
        .filter(Creative.id == creative_id, Creative.company_id == current_company_id())
        .first()
    )
    if item:
        try:
            fpath = Path(item.file_path)
            if fpath.exists():
                fpath.unlink()
        except Exception:
            pass  # DB row is the source of truth; a stray file is harmless
        db.delete(item)
        db.commit()
    db.close()
    return redirect(url_for("creatives.list_creatives") + "?message=deleted")
