from flask import Blueprint, render_template, session
from ..auth import login_required, require_company
from ..tenant import current_company_id
from ..db import db_session
from ..models import Candidate, CandidateStatus, Vacancy, Campaign, Source
from sqlalchemy import func
from datetime import datetime, timedelta

bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@bp.route("/")
@require_company
def dashboard():
    db = db_session()
    cid = current_company_id()

    # Funnel counts
    total = db.query(func.count(Candidate.id)).filter(Candidate.company_id == cid).scalar() or 0
    by_status = dict(
        db.query(Candidate.status, func.count(Candidate.id))
        .filter(Candidate.company_id == cid)
        .group_by(Candidate.status)
        .all()
    )

    new = by_status.get(CandidateStatus.new, 0)
    qualifying = by_status.get(CandidateStatus.qualifying, 0)
    interviewing = by_status.get(CandidateStatus.interviewing, 0)
    passed = by_status.get(CandidateStatus.passed, 0)
    rejected = by_status.get(CandidateStatus.rejected, 0)
    hired = by_status.get(CandidateStatus.hired, 0)

    # Funnel stages (cumulative)
    started = total  # everyone who hit /start
    in_screening = qualifying + interviewing + passed + rejected + hired
    completed = passed + rejected + hired
    approved = passed + hired

    funnel = [
        {"stage": "Clicked /start", "count": started, "pct": 100},
        {"stage": "Started screening", "count": in_screening, "pct": round(in_screening / max(started, 1) * 100)},
        {"stage": "Completed screening", "count": completed, "pct": round(completed / max(started, 1) * 100)},
        {"stage": "Passed (score ≥ 40)", "count": approved, "pct": round(approved / max(started, 1) * 100)},
        {"stage": "Hired", "count": hired, "pct": round(hired / max(started, 1) * 100)},
    ]

    # Language breakdown
    lang_stats = dict(
        db.query(Candidate.language, func.count(Candidate.id))
        .filter(Candidate.company_id == cid)
        .group_by(Candidate.language)
        .all()
    )

    # Vacancy stats
    vacancies = (
        db.query(
            Vacancy.title,
            func.count(Candidate.id).label("applicants"),
            func.avg(Candidate.score).label("avg_score"),
        )
        .outerjoin(Candidate, Candidate.vacancy_id == Vacancy.id)
        .filter(Vacancy.company_id == cid)
        .group_by(Vacancy.id)
        .all()
    )

    # Recent 7 days — daily candidate counts
    week_ago = datetime.utcnow() - timedelta(days=7)
    daily = (
        db.query(
            func.date(Candidate.created_at).label("day"),
            func.count(Candidate.id).label("cnt"),
        )
        .filter(Candidate.company_id == cid, Candidate.created_at >= week_ago)
        .group_by(func.date(Candidate.created_at))
        .order_by(func.date(Candidate.created_at))
        .all()
    )

    # Active campaigns & sources
    active_campaigns = db.query(func.count(Campaign.id)).filter(
        Campaign.company_id == cid, Campaign.is_running == True
    ).scalar() or 0
    active_sources = db.query(func.count(Source.id)).filter(
        Source.company_id == cid, Source.is_active == True
    ).scalar() or 0
    active_vacancies = db.query(func.count(Vacancy.id)).filter(
        Vacancy.company_id == cid, Vacancy.is_active == True
    ).scalar() or 0

    db.close()

    return render_template(
        "analytics.html",
        title="Analytics",
        funnel=funnel,
        total=total,
        lang_stats=lang_stats,
        vacancies=vacancies,
        daily=daily,
        active_campaigns=active_campaigns,
        active_sources=active_sources,
        active_vacancies=active_vacancies,
        passed=approved,
        rejected=rejected,
        hired=hired,
    )
