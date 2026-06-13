"""Task 2.1: Self-Service Signup — registration, login, trial."""
from datetime import datetime, timedelta
import os
import re

from flask import Blueprint, render_template, request, redirect, url_for, session

from ..config import Config
from ..db import db_session
from ..models import User, UserRole, Company
from common.passwords import hash_password, verify_password
from common.i18n import ui

bp = Blueprint("registration", __name__)

# Early access: the owner personally onboards the first pilot companies and
# converts them by hand, so the unattended trial is short.
TRIAL_DAYS = Config.trial_days()


def _signup_invite_code() -> str:
    """Invite code that gates self-service signup. Set on the live/demo server so
    only hand-picked pilot companies can register; unset in dev/CI = open."""
    return (os.environ.get("SIGNUP_INVITE_CODE") or "").strip()


def _invite_ok(submitted) -> bool:
    required = _signup_invite_code()
    if not required:
        return True
    return (submitted or "").strip() == required


def _hash_password(password: str) -> str:
    return hash_password(password)


def _valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def _start_authenticated_session(user: User):
    session["user_id"] = user.id
    session["is_admin"] = True
    session["owner_id"] = user.email
    if user.company_id:
        session["current_company_id"] = user.company_id
    else:
        session.pop("current_company_id", None)


@bp.get("/register")
def register():
    if session.get("is_admin") or session.get("user_id"):
        return redirect(url_for("auth.dashboard"))
    return render_template("register.html", invite_required=bool(_signup_invite_code()))


@bp.post("/register")
def register_post():
    invite_required = bool(_signup_invite_code())
    lang = session.get("ui_lang", "he")
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()
    company_name = request.form.get("company_name", "").strip()

    if not _invite_ok(request.form.get("invite_code")):
        return render_template("register.html", invite_required=True, error=ui("reg_invite_bad", lang))
    if not email or not password or not company_name:
        return render_template("register.html", invite_required=invite_required, error="All fields are required.")
    if not _valid_email(email):
        return render_template("register.html", invite_required=invite_required, error="Invalid email address.")
    if len(password) < 6:
        return render_template("register.html", invite_required=invite_required, error="Password must be at least 6 characters.")

    db = db_session()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        db.close()
        return render_template("register.html", invite_required=invite_required, error="Email already registered.")

    # Create company
    company = Company(
        owner_id=email,
        name=company_name,
        is_active=True,
    )
    db.add(company)
    db.flush()

    # Create user with trial
    user = User(
        email=email,
        password_hash=_hash_password(password),
        company_id=company.id,
        role=UserRole.owner,
        trial_expires_at=datetime.utcnow() + timedelta(days=TRIAL_DAYS),
    )
    db.add(user)
    db.commit()

    # Auto-login
    _start_authenticated_session(user)
    db.close()

    return redirect(url_for("auth.dashboard"))


@bp.get("/user-login")
def user_login():
    if session.get("is_admin") or session.get("user_id"):
        return redirect(url_for("auth.dashboard"))
    return redirect(url_for("auth.login"))


@bp.post("/user-login")
def user_login_post():
    from .auth_routes import _check_rate_limit, _record_attempt

    if not _check_rate_limit():
        return render_template("user_login.html", error="Too many attempts. Please wait 5 minutes.")
    _record_attempt()

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    if not email or not password:
        return render_template("user_login.html", error="Email and password required.")

    db = db_session()
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    password_ok = False
    should_upgrade_hash = False
    if user:
        password_ok, should_upgrade_hash = verify_password(user.password_hash, password)
    if not user or not password_ok:
        db.close()
        return render_template("user_login.html", error="Invalid email or password.")

    # Check trial expiration
    if user.trial_expires_at and datetime.utcnow() > user.trial_expires_at:
        db.close()
        return redirect(url_for("pricing.pricing_page"))

    if should_upgrade_hash:
        user.password_hash = _hash_password(password)
        db.commit()

    _start_authenticated_session(user)
    db.close()

    return redirect(url_for("auth.dashboard"))
