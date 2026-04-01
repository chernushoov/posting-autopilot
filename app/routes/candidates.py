import csv
import io
import json

from flask import Blueprint, render_template, request, redirect, url_for, Response
from ..auth import require_company
from ..db import db_session
from ..models import Candidate, CandidateStatus, Vacancy
from ..tenant import scoped

bp = Blueprint("candidates", __name__, url_prefix="/candidates")

@bp.get("/")
@require_company
def list_candidates():
    status = request.args.get("status","")
    db = db_session()
    q = scoped(db, Candidate).order_by(Candidate.id.desc())
    if status:
        try:
            q = q.filter(Candidate.status == CandidateStatus(status))
        except Exception:
            pass
    candidates = q.limit(200).all()
    db.close()
    return render_template("candidates.html", candidates=candidates, statuses=[s.value for s in CandidateStatus], current=status)

@bp.get("/<int:candidate_id>")
@require_company
def view_candidate(candidate_id: int):
    db = db_session()
    c = scoped(db, Candidate).filter(Candidate.id == candidate_id).first()
    v = None
    if c and c.vacancy_id:
        v = scoped(db, Vacancy).filter(Vacancy.id == c.vacancy_id).first()
    chat = []
    if c:
        try:
            chat = json.loads(c.chat_log_json or "[]")
        except Exception:
            chat = []
    db.close()
    if not c:
        return redirect(url_for("candidates.list_candidates"))
    return render_template("candidate_view.html", c=c, v=v, chat=chat)

@bp.get("/export")
@require_company
def export_csv():
    """Task 2.5: Export candidates as CSV."""
    db = db_session()
    candidates = scoped(db, Candidate).order_by(Candidate.id.desc()).limit(5000).all()

    # Prefetch vacancy titles
    vacancy_ids = {c.vacancy_id for c in candidates if c.vacancy_id}
    vacancies = {}
    if vacancy_ids:
        for v in db.query(Vacancy).filter(Vacancy.id.in_(vacancy_ids)).all():
            vacancies[v.id] = v.title

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Phone", "Telegram", "Status", "Classification", "Score", "Summary", "Listing", "Language", "Created"])

    for c in candidates:
        writer.writerow([
            c.id,
            c.full_name or "",
            getattr(c, 'phone', '') or "",
            c.tg_username or "",
            c.status.value if c.status else "",
            getattr(c, 'classification', '') or "",
            c.score or "",
            c.summary or "",
            vacancies.get(c.vacancy_id, ""),
            c.language or "",
            c.created_at.isoformat() if c.created_at else "",
        ])

    db.close()
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=candidates_export.csv"},
    )


@bp.post("/set_status/<int:candidate_id>")
@require_company
def set_status(candidate_id: int):
    new_status = request.form.get("status","")
    db = db_session()
    c = scoped(db, Candidate).filter(Candidate.id == candidate_id).first()
    if c:
        try:
            c.status = CandidateStatus(new_status)
            db.commit()
        except Exception:
            db.rollback()
    db.close()
    return redirect(url_for("candidates.view_candidate", candidate_id=candidate_id))
