from flask import Blueprint, render_template, request, redirect, url_for
from ..auth import require_company
from ..db import db_session
from ..models import Company, Tone, Language
from flask import session
from common.ai import run_ai_test

bp = Blueprint("ai", __name__, url_prefix="/ai")

@bp.get("/settings")
@require_company
def settings():
    db = db_session()
    c = db.query(Company).filter(Company.id == session["current_company_id"], Company.owner_id == session["owner_id"]).first()
    db.close()
    return render_template("ai_settings.html", company=c, tones=[t.value for t in Tone], langs=[l.value for l in Language])

@bp.post("/settings")
@require_company
def save_settings():
    db = db_session()
    c = db.query(Company).filter(Company.id == session["current_company_id"], Company.owner_id == session["owner_id"]).first()
    if c:
        c.ai_positive_prompt = request.form.get("ai_positive_prompt","")
        c.ai_negative_prompt = request.form.get("ai_negative_prompt","")
        c.ai_tone = Tone(request.form.get("ai_tone","professional"))
        c.ai_language = Language(request.form.get("ai_language","ru"))
        c.ai_greeting_template = request.form.get("ai_greeting_template","")
        c.ai_rejection_template = request.form.get("ai_rejection_template","")
        c.ai_success_template = request.form.get("ai_success_template","")
        db.commit()
    db.close()
    return redirect(url_for("ai.settings"))

@bp.post("/test")
@require_company
def test_ai():
    text = request.form.get("test_text","").strip()
    db = db_session()
    c = db.query(Company).filter(Company.id == session["current_company_id"], Company.owner_id == session["owner_id"]).first()
    db.close()
    answer = run_ai_test(company=c, user_text=text)
    return render_template("ai_test_result.html", text=text, answer=answer)
