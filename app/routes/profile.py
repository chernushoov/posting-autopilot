"""Company/Individual profile — view and edit current account."""
import secrets
import string

from flask import Blueprint, render_template, request, redirect, url_for, session

from ..auth import require_company
from ..db import db_session
from ..models import Company, User, UserRole
from .registration import _make_password_hash, _valid_email
from ..tenant import current_company_id

bp = Blueprint("profile", __name__, url_prefix="/profile")
settings_bp = Blueprint("settings", __name__)


def _current_user(db):
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()


def _can_manage_team(user) -> bool:
    if not user:
        return bool(session.get("is_admin") and not session.get("user_id"))
    return user.role in {UserRole.owner, UserRole.admin}


def _temporary_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _render_profile(db, company, **context):
    user = _current_user(db)
    team_users = (
        db.query(User)
        .filter(User.company_id == company.id)
        .order_by(User.role.asc(), User.created_at.asc(), User.id.asc())
        .all()
    )
    from common.email_notify import is_email_configured
    return render_template(
        "profile.html",
        c=company,
        current_user=user,
        team_users=team_users,
        can_manage_team=_can_manage_team(user),
        email_configured=is_email_configured(),
        **context,
    )


def _save_company_profile(company) -> None:
    company.name = request.form.get("name", "").strip() or company.name
    company.description = request.form.get("description", "").strip() or None
    company.business_type = request.form.get("business_type", "company").strip()
    company.contact_person = request.form.get("contact_person", "").strip() or None
    company.phone = request.form.get("phone", "").strip() or None
    company.email = request.form.get("email", "").strip() or None
    company.website = request.form.get("website", "").strip() or None
    company.logo_emoji = request.form.get("logo_emoji", "").strip() or None

    notify_chat = request.form.get("notify_telegram_chat_id", "").strip()
    company.notify_telegram_chat_id = notify_chat if notify_chat.lstrip("-").isdigit() else None
    notify_email = request.form.get("notify_email", "").strip().lower()
    company.notify_email = notify_email if _valid_email(notify_email) else None


@bp.get("/")
@require_company
def view_profile():
    db = db_session()
    company = db.query(Company).filter(Company.id == current_company_id()).first()
    if not company:
        db.close()
        return redirect(url_for("auth.dashboard"))
    response = _render_profile(db, company)
    db.close()
    return response


@bp.post("/")
@require_company
def update_profile():
    db = db_session()
    company = db.query(Company).filter(Company.id == current_company_id()).first()
    if not company:
        db.close()
        return redirect(url_for("auth.dashboard"))

    _save_company_profile(company)

    db.commit()
    response = _render_profile(db, company, saved=True)
    db.close()
    return response


@settings_bp.get("/settings")
@require_company
def settings_alias():
    return redirect(url_for("profile.view_profile"))


@settings_bp.post("/settings")
@require_company
def settings_alias_post():
    db = db_session()
    company = db.query(Company).filter(Company.id == current_company_id()).first()
    if not company:
        db.close()
        return redirect(url_for("auth.dashboard"))
    _save_company_profile(company)
    db.commit()
    db.close()
    return redirect(url_for("profile.view_profile") + "?message=saved")


@bp.post("/team/invite")
@require_company
def invite_teammate():
    db = db_session()
    company = db.query(Company).filter(Company.id == current_company_id()).first()
    if not company:
        db.close()
        return redirect(url_for("auth.dashboard"))

    user = _current_user(db)
    if not _can_manage_team(user):
        response = _render_profile(db, company, team_error="Only an owner can add users.")
        db.close()
        return response

    email = request.form.get("email", "").strip().lower()
    role_raw = request.form.get("role", UserRole.member.value).strip()
    password = request.form.get("password", "").strip() or _temporary_password()

    if not _valid_email(email):
        response = _render_profile(db, company, team_error="Enter a valid work email.")
        db.close()
        return response
    if len(password) < 8:
        response = _render_profile(db, company, team_error="Temporary password must be at least 8 characters.")
        db.close()
        return response

    role = UserRole.owner if role_raw == UserRole.owner.value else UserRole.member
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        if existing.company_id == company.id:
            response = _render_profile(db, company, team_error="This user already belongs to this workspace.")
        else:
            response = _render_profile(db, company, team_error="This email is already used in another workspace.")
        db.close()
        return response

    teammate = User(
        email=email,
        password_hash=_make_password_hash(password),
        company_id=company.id,
        role=role,
        trial_expires_at=None,
        is_active=True,
    )
    db.add(teammate)
    db.commit()
    response = _render_profile(
        db,
        company,
        team_message="User added. Share this one-time temporary password privately.",
        invite_email=email,
        invite_password=password,
    )
    db.close()
    return response


@bp.post("/team/<int:user_id>/deactivate")
@require_company
def deactivate_teammate(user_id: int):
    db = db_session()
    company = db.query(Company).filter(Company.id == current_company_id()).first()
    if not company:
        db.close()
        return redirect(url_for("auth.dashboard"))

    user = _current_user(db)
    if not _can_manage_team(user):
        response = _render_profile(db, company, team_error="Only an owner can deactivate users.")
        db.close()
        return response
    if user and user.id == user_id:
        response = _render_profile(db, company, team_error="You cannot deactivate your own login.")
        db.close()
        return response

    teammate = db.query(User).filter(User.id == user_id, User.company_id == company.id).first()
    if teammate:
        teammate.is_active = False
        db.commit()
    response = _render_profile(db, company, team_message="User access deactivated.")
    db.close()
    return response
