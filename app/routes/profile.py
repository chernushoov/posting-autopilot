"""Company/Individual profile — view and edit current account."""
import os
import time

from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

from ..auth import require_company
from ..db import db_session
from ..models import Company
from ..tenant import current_company_id

bp = Blueprint("profile", __name__, url_prefix="/profile")


def _upload_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"/uploads/{os.path.basename(path)}"


def _save_profile_logo(file_storage) -> str | None:
    if not file_storage or not file_storage.filename:
        return None
    filename = secure_filename(file_storage.filename)
    if not filename:
        return None
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, f"company_{int(time.time() * 1000)}_{filename}")
    file_storage.save(save_path)
    return save_path


@bp.get("/")
@require_company
def view_profile():
    db = db_session()
    company = db.query(Company).filter(Company.id == current_company_id()).first()
    db.close()
    if not company:
        return redirect(url_for("auth.dashboard"))
    return render_template("profile.html", c=company, logo_url=_upload_url(company.logo_path))


@bp.post("/")
@require_company
def update_profile():
    db = db_session()
    company = db.query(Company).filter(Company.id == current_company_id()).first()
    if not company:
        db.close()
        return redirect(url_for("auth.dashboard"))

    company.name = request.form.get("name", "").strip() or company.name
    company.description = request.form.get("description", "").strip() or None
    company.business_type = request.form.get("business_type", "company").strip()
    company.contact_person = request.form.get("contact_person", "").strip() or None
    company.phone = request.form.get("phone", "").strip() or None
    company.email = request.form.get("email", "").strip() or None
    company.website = request.form.get("website", "").strip() or None
    company.logo_emoji = request.form.get("logo_emoji", "").strip() or None
    company.service_area = request.form.get("service_area", "").strip() or None
    company.specialties = request.form.get("specialties", "").strip() or None
    company.proof_points = request.form.get("proof_points", "").strip() or None
    company.documents_text = request.form.get("documents_text", "").strip() or None
    company.education_text = request.form.get("education_text", "").strip() or None
    company.ai_context = request.form.get("ai_context", "").strip() or None

    logo_path = _save_profile_logo(request.files.get("logo"))
    if logo_path:
        company.logo_path = logo_path

    db.commit()
    db.close()
    return redirect(url_for("profile.view_profile") + "?message=saved")
