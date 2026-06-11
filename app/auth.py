from functools import wraps
from flask import session, redirect, url_for, request
from .config import Config
from .db import db_session
from .models import Company, User

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
