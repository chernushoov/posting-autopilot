from flask import session
from .db import db_session

def current_owner_id():
    return session.get("owner_id")

def current_company_id():
    return session.get("current_company_id")

def scoped(db, Model):
    cid = current_company_id()
    return db.query(Model).filter(getattr(Model, "company_id") == cid)
