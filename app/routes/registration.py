"""Task 2.1: Self-Service Signup — registration, login, trial."""
from datetime import datetime, timedelta
from hashlib import sha256
import re

from flask import Blueprint, render_template, request, redirect, url_for, session

from ..db import db_session
from ..models import User, UserRole, Company

bp = Blueprint("registration", __name__)

TRIAL_DAYS = 14


def _hash_password(password: str) -> str:
    """Simple SHA-256 hash. Replace with bcrypt for production."""
    return sha256(password.encode()).hexdigest()


def _valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


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
        password_hash=_hash_password(password),
        company_id=company.id,
        role=UserRole.owner,
        trial_expires_at=datetime.utcnow() + timedelta(days=TRIAL_DAYS),
    )
    db.add(user)
    db.commit()

    # Auto-login
    session["user_id"] = user.id
    session["is_admin"] = True
    session["owner_id"] = email
    session["current_company_id"] = company.id
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
    if not user or user.password_hash != _hash_password(password):
        db.close()
        return render_template("user_login.html", error="Invalid email or password.")

    # Check trial expiration
    if user.trial_expires_at and datetime.utcnow() > user.trial_expires_at:
        db.close()
        return redirect(url_for("pricing.pricing_page"))

    session["user_id"] = user.id
    session["is_admin"] = True
    session["owner_id"] = user.email
    if user.company_id:
        session["current_company_id"] = user.company_id
    db.close()

    return redirect(url_for("auth.dashboard"))
