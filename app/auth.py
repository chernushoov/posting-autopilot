import time
from functools import wraps
from flask import session, redirect, url_for, request
from .config import Config
from .db import db_session
from .models import Company, User

# ---- Login rate limiting (shared across /login, /user-login, /register) ----
# In-memory window; resets on restart. Keyed by client IP *and* (when known) the
# submitted email, so a single spoofed IP cannot also evade the per-account cap.
_login_attempts: dict[str, list[float]] = {}
LOGIN_RATE_LIMIT = 10  # max attempts per key per window
LOGIN_RATE_WINDOW = 300  # seconds


def _client_ip() -> str:
    # Prefer the left-most X-Forwarded-For hop when behind a known reverse proxy
    # (Caddy/nginx on the VPS sets it); fall back to the socket peer. Still
    # best-effort — pair with the per-email key below for real throttling.
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _rate_keys(email: str | None = None) -> list[str]:
    keys = [f"ip:{_client_ip()}"]
    if email:
        keys.append(f"email:{email.strip().lower()}")
    return keys


def check_login_rate_limit(email: str | None = None) -> bool:
    now = time.time()
    for key in _rate_keys(email):
        attempts = [t for t in _login_attempts.get(key, []) if now - t < LOGIN_RATE_WINDOW]
        _login_attempts[key] = attempts
        if len(attempts) >= LOGIN_RATE_LIMIT:
            return False
    return True


def record_login_attempt(email: str | None = None) -> None:
    now = time.time()
    for key in _rate_keys(email):
        _login_attempts.setdefault(key, []).append(now)


def is_logged_in():
    return session.get("is_admin") is True or session.get("user_id") is not None

def _login_redirect():
    """Redirect to the appropriate login page."""
    try:
        return redirect(url_for("registration.user_login", next=request.path))
    except Exception:
        return redirect(url_for("auth.login", next=request.path))

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return _login_redirect()
        return fn(*args, **kwargs)
    return wrapper

def require_company(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return _login_redirect()
        company_id = session.get("current_company_id")
        if not company_id:
            return redirect(url_for("companies.list_companies"))
        db = db_session()
        c = None
        user_id = session.get("user_id")
        if user_id:
            user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
            if user and user.company_id == company_id:
                c = db.query(Company).filter(Company.id == company_id, Company.is_active == True).first()
                if c:
                    session["owner_id"] = c.owner_id
        else:
            owner_id = session.get("owner_id")
            if owner_id:
                c = db.query(Company).filter(
                    Company.id == company_id,
                    Company.owner_id == owner_id,
                    Company.is_active == True,
                ).first()
        db.close()
        if not c:
            session.pop("current_company_id", None)
            return redirect(url_for("companies.list_companies"))
        return fn(*args, **kwargs)
    return wrapper

def admin_login_ok(login: str, password: str) -> bool:
    if not Config.ADMIN_PASSWORD:
        return False
    return login == Config.ADMIN_LOGIN and password == Config.ADMIN_PASSWORD
