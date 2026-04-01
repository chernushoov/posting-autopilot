from functools import wraps
from flask import session, redirect, url_for, request
from .config import Config
from .db import db_session
from .models import Company

def is_logged_in():
    return session.get("is_admin") is True

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("auth.login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

def require_company(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("auth.login"))
        company_id = session.get("current_company_id")
        owner_id = session.get("owner_id")
        if not company_id or not owner_id:
            return redirect(url_for("companies.list_companies"))
        db = db_session()
        c = db.query(Company).filter(Company.id == company_id, Company.owner_id == owner_id, Company.is_active == True).first()
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
