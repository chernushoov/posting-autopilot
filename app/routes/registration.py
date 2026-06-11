"""Task 2.1: Self-Service Signup — registration, login, trial."""
from datetime import datetime, timedelta
from hashlib import sha256
import re

from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import db_session
from ..models import User, UserRole, Company

bp = Blueprint("registration", __name__)

TRIAL_DAYS = 14


def _hash_password(password: str) -> str:
    """Legacy SHA-256 hash kept for existing seeded/demo users."""
    return sha256(password.encode()).hexdigest()


def _make_password_hash(password: str) -> str:
    return generate_password_hash(password)


def _verify_password(stored_hash: str, password: str) -> bool:
    if not stored_hash:
        return False
    if stored_hash == _hash_password(password):
        return True
    try:
        return check_password_hash(stored_hash, password)
    except Exception:
        return False


def _valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def _login_user(user: User, db) -> None:
    company = db.query(Company).filter(Company.id == user.company_id).first() if user.company_id else None
    session["user_id"] = user.id
    session["is_admin"] = True
    session["owner_id"] = company.owner_id if company else user.email
    if company:
        session["current_company_id"] = company.id


@bp.get("/register")
def register():
    if session.get("is_admin") or session.get("user_id"):
        return redirect(url_for("auth.dashboard"))
    return render_template("register.html")


@bp.post("/register")
def register_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()
    company_name = request.form.get("company_name", "").strip()

    if not email or not password or not company_name:
        return render_template("register.html", error="All fields are required.")
    if not _valid_email(email):
        return render_template("register.html", error="Invalid email address.")
    if len(password) < 6:
        return render_template("register.html", error="Password must be at least 6 characters.")

    db = db_session()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        db.close()
        return render_template("register.html", error="Email already registered.")

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
        password_hash=_make_password_hash(password),
        company_id=company.id,
        role=UserRole.owner,
        trial_expires_at=datetime.utcnow() + timedelta(days=TRIAL_DAYS),
    )
    db.add(user)
    db.commit()

    # Auto-login
    _login_user(user, db)
    db.close()

    return redirect(url_for("auth.dashboard"))


@bp.get("/user-login")
def user_login():
    if session.get("is_admin") or session.get("user_id"):
        return redirect(url_for("auth.dashboard"))
    return render_template("user_login.html")


@bp.post("/user-login")
def user_login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    if not email or not password:
        return render_template("user_login.html", error="Email and password required.")

    db = db_session()
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user or not _verify_password(user.password_hash, password):
        db.close()
        return render_template("user_login.html", error="Invalid email or password.")

    # Check trial expiration
    if user.trial_expires_at and datetime.utcnow() > user.trial_expires_at:
        db.close()
        return redirect(url_for("pricing.pricing_page"))

    _login_user(user, db)
    next_url = request.args.get("next") or request.form.get("next") or url_for("auth.dashboard")
    db.close()

    return redirect(next_url)
