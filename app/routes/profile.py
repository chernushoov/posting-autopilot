"""Company/Individual profile — view and edit current account."""
from flask import Blueprint, render_template, request, redirect, url_for, session

from ..auth import require_company
from ..db import db_session
from ..models import Company
from ..tenant import current_company_id

bp = Blueprint("profile", __name__, url_prefix="/profile")


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

    company.name = request.form.get("name", "").strip() or company.name
    company.description = request.form.get("description", "").strip() or None
    company.business_type = request.form.get("business_type", "company").strip()
    company.contact_person = request.form.get("contact_person", "").strip() or None
    company.phone = request.form.get("phone", "").strip() or None
    company.email = request.form.get("email", "").strip() or None
    company.website = request.form.get("website", "").strip() or None
    company.logo_emoji = request.form.get("logo_emoji", "").strip() or None

    db.commit()
    db.close()
    return redirect(url_for("profile.view_profile") + "?message=saved")
