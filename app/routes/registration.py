"""Task 2.1: Self-Service Signup — registration, login, trial."""
from datetime import datetime, timedelta
import os
import re
import secrets
import hashlib

from flask import Blueprint, render_template, request, redirect, url_for, session

from ..config import Config
from ..db import db_session
from ..models import User, UserRole, Company, PasswordResetToken
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
    from .auth_routes import _check_rate_limit, _record_attempt
    invite_required = bool(_signup_invite_code())
    if not _check_rate_limit():
        return render_template("register.html", invite_required=invite_required,
                               error="Слишком много попыток. Подождите 5 минут и попробуйте снова.")
    _record_attempt()
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

    # Welcome email (best-effort; no-op until an email provider is configured).
    try:
        from ..mailer import send_email
        base = request.host_url.rstrip("/")
        send_email(
            email, "Добро пожаловать в Posting Autopilot",
            f"<p>Привет! Аккаунт «{company_name}» создан — у вас {TRIAL_DAYS} дней пробного периода.</p>"
            f'<p>Кабинет: <a href="{base}/cabinet">{base}/cabinet</a></p>'
            f"<p>Подключите Telegram и запустите первую кампанию — AI-бот начнёт собирать и фильтровать лидов.</p>",
            text=f"Добро пожаловать! Кабинет: {base}/cabinet",
        )
    except Exception:
        pass

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


# ── Password reset (self-service) ─────────────────────────────────────────────
@bp.get("/forgot-password")
def forgot_password():
    return render_template("forgot_password.html")


@bp.post("/forgot-password")
def forgot_password_post():
    email = request.form.get("email", "").strip().lower()
    db = db_session()
    try:
        user = db.query(User).filter(User.email == email, User.is_active == True).first() if email else None
        if user:
            raw = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw.encode()).hexdigest()
            db.add(PasswordResetToken(
                user_id=user.id, token_hash=token_hash,
                expires_at=datetime.utcnow() + timedelta(hours=1),
            ))
            db.commit()
            link = request.host_url.rstrip("/") + "/reset-password?token=" + raw
            try:
                from ..mailer import send_email
                send_email(
                    email, "Сброс пароля — Posting Autopilot",
                    f"<p>Вы запросили сброс пароля. Ссылка действует 1 час:</p>"
                    f'<p><a href="{link}">{link}</a></p>'
                    f"<p>Если это были не вы — просто проигнорируйте письмо.</p>",
                    text=f"Сбросить пароль (1 час): {link}",
                )
            except Exception:
                pass
    finally:
        db.close()
    # Never reveal whether the email exists (no user enumeration).
    return render_template("forgot_password.html", sent=True)


@bp.get("/reset-password")
def reset_password():
    return render_template("reset_password.html", token=request.args.get("token", ""))


@bp.post("/reset-password")
def reset_password_post():
    token = request.form.get("token", "").strip()
    password = request.form.get("password", "").strip()
    if len(password) < 6:
        return render_template("reset_password.html", token=token,
                               error="Пароль должен быть не короче 6 символов.")
    token_hash = hashlib.sha256(token.encode()).hexdigest() if token else ""
    db = db_session()
    try:
        rec = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.token_hash == token_hash, PasswordResetToken.used == False)
            .first()
        ) if token_hash else None
        if not rec or rec.expires_at < datetime.utcnow():
            return render_template("reset_password.html", token=token,
                                   error="Ссылка недействительна или истекла. Запросите новую.")
        user = db.query(User).filter(User.id == rec.user_id).first()
        if not user:
            return render_template("reset_password.html", token=token, error="Пользователь не найден.")
        user.password_hash = _hash_password(password)
        rec.used = True
        # Invalidate any other outstanding tokens for this user.
        for other in db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id, PasswordResetToken.used == False
        ).all():
            other.used = True
        db.commit()
    finally:
        db.close()
    return redirect("/login?reset=1")
