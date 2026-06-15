from flask import Blueprint, render_template, request, redirect, url_for, session
from ..auth import login_required
from ..db import db_session
from ..models import Company, User, UserRole

bp = Blueprint("companies", __name__, url_prefix="/companies")


def _delete_company_cascade(db, company_id: int) -> None:
    """Delete a company and every row that belongs to it, children first.

    Done explicitly (not relying on DB ON DELETE) so a tenant offboarding /
    GDPR-deletion fully clears candidate PII and posting history on the existing
    SQLite database too — whose tables predate the ondelete= declarations. Order
    matters: leaf tables before the rows they reference.
    """
    from ..models import (
        Vacancy, Source, Campaign, CampaignSource, Candidate, PostingAttempt,
        FacebookGroupSource, FacebookGroup, FacebookPostVariant,
        FacebookPostingRun, FacebookPostingQueueItem, FacebookPostingResult,
        Prospect, OutreachAttempt,
    )
    campaign_ids = [c.id for c in db.query(Campaign.id).filter(Campaign.company_id == company_id).all()]

    # Facebook posting tree (results -> queue items -> runs -> variants -> groups -> sources)
    db.query(FacebookPostingResult).filter(FacebookPostingResult.company_id == company_id).delete(synchronize_session=False)
    db.query(FacebookPostingQueueItem).filter(FacebookPostingQueueItem.company_id == company_id).delete(synchronize_session=False)
    db.query(FacebookPostingRun).filter(FacebookPostingRun.company_id == company_id).delete(synchronize_session=False)
    db.query(FacebookPostVariant).filter(FacebookPostVariant.company_id == company_id).delete(synchronize_session=False)
    db.query(FacebookGroup).filter(FacebookGroup.company_id == company_id).delete(synchronize_session=False)
    db.query(FacebookGroupSource).filter(FacebookGroupSource.company_id == company_id).delete(synchronize_session=False)

    # Prospecting
    db.query(OutreachAttempt).filter(OutreachAttempt.company_id == company_id).delete(synchronize_session=False)
    db.query(Prospect).filter(Prospect.company_id == company_id).delete(synchronize_session=False)

    # Posting + screening
    db.query(PostingAttempt).filter(PostingAttempt.company_id == company_id).delete(synchronize_session=False)
    if campaign_ids:
        db.query(CampaignSource).filter(CampaignSource.campaign_id.in_(campaign_ids)).delete(synchronize_session=False)
    db.query(Candidate).filter(Candidate.company_id == company_id).delete(synchronize_session=False)
    db.query(Campaign).filter(Campaign.company_id == company_id).delete(synchronize_session=False)
    db.query(Source).filter(Source.company_id == company_id).delete(synchronize_session=False)
    db.query(Vacancy).filter(Vacancy.company_id == company_id).delete(synchronize_session=False)

    # Users belonging to the tenant, then the company itself
    db.query(User).filter(User.company_id == company_id).delete(synchronize_session=False)
    db.query(Company).filter(Company.id == company_id).delete(synchronize_session=False)


@bp.get("/")
@login_required
def list_companies():
    db = db_session()
    user_id = session.get("user_id")
    if user_id:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        companies = (
            db.query(Company)
            .filter(Company.id == user.company_id)
            .order_by(Company.is_active.desc(), Company.id.asc())
            .all()
            if user and user.company_id
            else []
        )
    else:
        owner_id = session.get("owner_id")
        companies = db.query(Company).filter(Company.owner_id == owner_id).order_by(Company.is_active.desc(), Company.id.asc()).all()
    db.close()
    # If no companies → redirect to create
    if not companies:
        return redirect(url_for("companies.new_company"))
    # Auto-select if only 1 active company
    active = [c for c in companies if c.is_active]
    if len(active) == 1 and not session.get("current_company_id"):
        session["current_company_id"] = active[0].id
    # If only 1 company total → redirect to profile (no need for list)
    if len(companies) == 1:
        session["current_company_id"] = companies[0].id
        return redirect(url_for("profile.view_profile"))
    return render_template("companies.html", companies=companies, current_company_id=session.get("current_company_id"))


@bp.get("/new")
@login_required
def new_company():
    return render_template("company_new.html")


@bp.post("/new")
@login_required
def new_company_post():
    db = db_session()
    user_id = session.get("user_id")
    if user_id:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if user and user.company_id and user.role != UserRole.admin:
            db.close()
            return redirect(url_for("profile.view_profile") + "?error=company_exists")
    owner_id = session.get("owner_id")
    name = request.form.get("name", "").strip()
    desc = request.form.get("description", "").strip() or None
    business_type = request.form.get("business_type", "company").strip()
    if not name:
        db.close()
        return render_template("company_new.html", error="Name required")
    c = Company(owner_id=owner_id, name=name, description=desc, business_type=business_type)
    db.add(c)
    db.commit()
    session["current_company_id"] = c.id
    db.close()
    return redirect(url_for("profile.view_profile"))


@bp.get("/switch/<int:company_id>")
@login_required
def switch_company(company_id: int):
    db = db_session()
    user_id = session.get("user_id")
    if user_id:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        c = db.query(Company).filter(Company.id == company_id, Company.id == (user.company_id if user else None), Company.is_active == True).first()
    else:
        owner_id = session.get("owner_id")
        c = db.query(Company).filter(Company.id == company_id, Company.owner_id == owner_id, Company.is_active == True).first()
    db.close()
    if c:
        session["current_company_id"] = c.id
    return redirect(request.referrer or url_for("auth.dashboard"))


@bp.post("/disable/<int:company_id>")
@login_required
def disable_company(company_id: int):
    db = db_session()
    owner_id = session.get("owner_id")
    c = db.query(Company).filter(Company.id == company_id, Company.owner_id == owner_id).first()
    if c:
        c.is_active = False
        db.commit()
        if session.get("current_company_id") == company_id:
            session.pop("current_company_id", None)
    db.close()
    return redirect(url_for("companies.list_companies"))


@bp.post("/enable/<int:company_id>")
@login_required
def enable_company(company_id: int):
    db = db_session()
    owner_id = session.get("owner_id")
    c = db.query(Company).filter(Company.id == company_id, Company.owner_id == owner_id).first()
    if c:
        c.is_active = True
        db.commit()
        session["current_company_id"] = c.id
    db.close()
    return redirect(url_for("companies.list_companies"))


@bp.post("/delete/<int:company_id>")
@login_required
def delete_company(company_id: int):
    """Delete a company and all its data. Only for disabled companies."""
    db = db_session()
    owner_id = session.get("owner_id")
    c = db.query(Company).filter(Company.id == company_id, Company.owner_id == owner_id, Company.is_active == False).first()
    if c:
        _delete_company_cascade(db, company_id)
        db.commit()
        if session.get("current_company_id") == company_id:
            session.pop("current_company_id", None)
    db.close()
    return redirect(url_for("companies.list_companies"))
