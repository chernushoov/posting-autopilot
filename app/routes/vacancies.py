import json

from flask import Blueprint, redirect, render_template, request, url_for, jsonify

from ..auth import require_company
from ..db import db_session
from ..models import Language, Vacancy
from ..tenant import current_company_id, scoped
from ..listing_templates import get_template, get_all_templates
from common.recruitbot_links import build_recruitbot_apply_link

bp = Blueprint("vacancies", __name__, url_prefix="/vacancies")


def _build_post_asset_from_form(form, *, apply_url: str | None = None) -> tuple[str, str]:
    title = form.get("final_post_title", "").strip() or form.get("title", "").strip()
    custom_body = form.get("final_post_body", "").strip()
    if custom_body:
        return title, custom_body

    parts = [form.get("body", "").strip()]
    city = form.get("city", "").strip()
    salary_text = form.get("salary_text", "").strip()
    schedule_text = form.get("schedule_text", "").strip()
    contact_text = form.get("contact_text", "").strip()
    apply_url = apply_url if apply_url is not None else form.get("apply_url", "").strip()
    if city:
        parts.append(f"City: {city}")
    if salary_text:
        parts.append(f"Pay: {salary_text}")
    if schedule_text:
        parts.append(f"Schedule: {schedule_text}")
    if contact_text:
        parts.append(f"Contact: {contact_text}")
    if apply_url:
        parts.append(f"Apply: {apply_url}")
    return title, "\n".join([part for part in parts if part])


@bp.get("/")
@require_company
def list_vacancies():
    db = db_session()
    vacancies = scoped(db, Vacancy).order_by(Vacancy.id.desc()).all()
    db.close()
    generated_apply_links = {
        vacancy.id: build_recruitbot_apply_link(vacancy.id) for vacancy in vacancies
    }
    return render_template(
        "vacancies.html",
        vacancies=vacancies,
        generated_apply_links=generated_apply_links,
        error=request.args.get("error"),
        message=request.args.get("message"),
    )


@bp.get("/<int:vacancy_id>")
@require_company
def view_vacancy(vacancy_id: int):
    """Read-only detail view for one vacancy.

    Useful for the demo walkthrough: opens a clean page with the full
    vacancy state — body, post title/body, apply link, bot screening
    questions parsed back into a list, hot/cold criteria, image.
    No edit form yet (would need a /new-template UPDATE refactor); use
    SQL or recreate via /new for now.
    """
    from ..models import Candidate
    db = db_session()
    vacancy = scoped(db, Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        db.close()
        return redirect(url_for("vacancies.list_vacancies", error="Vacancy not found in this company."))

    bot_questions_list = []
    if vacancy.bot_qualifying_questions:
        try:
            parsed = json.loads(vacancy.bot_qualifying_questions)
            if isinstance(parsed, list):
                bot_questions_list = [str(q) for q in parsed if str(q).strip()]
        except Exception:
            pass
    interview_questions_list = []
    if vacancy.interview_questions_json:
        try:
            parsed = json.loads(vacancy.interview_questions_json)
            if isinstance(parsed, list):
                interview_questions_list = [str(q) for q in parsed if str(q).strip()]
        except Exception:
            pass

    # Per-vacancy candidate funnel — primary daily-ops view
    candidates_for_vac = (
        scoped(db, Candidate)
        .filter(Candidate.vacancy_id == vacancy_id)
        .order_by(Candidate.id.desc())
        .all()
    )
    scored = [c for c in candidates_for_vac if c.score]
    funnel = {
        "total": len(candidates_for_vac),
        "hot": sum(1 for c in candidates_for_vac if c.classification == "hot"),
        "warm": sum(1 for c in candidates_for_vac if c.classification == "warm"),
        "cold": sum(1 for c in candidates_for_vac if c.classification == "cold"),
        "duplicate": sum(1 for c in candidates_for_vac if c.classification == "duplicate"),
        "avg_score": (round(sum(c.score for c in scored) / len(scored), 1) if scored else None),
        "last_at": candidates_for_vac[0].created_at if candidates_for_vac else None,
    }
    recent_candidates = candidates_for_vac[:8]

    apply_link = vacancy.apply_url or build_recruitbot_apply_link(vacancy.id)
    db.close()
    return render_template(
        "vacancy_detail.html",
        vacancy=vacancy,
        bot_questions_list=bot_questions_list,
        interview_questions_list=interview_questions_list,
        apply_link=apply_link,
        funnel=funnel,
        recent_candidates=recent_candidates,
    )


@bp.get("/new")
@require_company
def new_vacancy():
    return render_template(
        "vacancy_new.html",
        languages=[l.value for l in Language],
        form_values={},
        templates=get_all_templates(),
        edit_id=None,
    )


@bp.get("/<int:vacancy_id>/edit")
@require_company
def edit_vacancy(vacancy_id: int):
    """Reuse the new-vacancy form template, pre-filled from the existing
    Vacancy row. POST goes to /vacancies/<id>/edit, which UPDATEs in place.
    """
    db = db_session()
    v = scoped(db, Vacancy).filter(Vacancy.id == vacancy_id).first()
    db.close()
    if not v:
        return redirect(url_for("vacancies.list_vacancies", error="Vacancy not found in this company."))

    bot_qq_text = ""
    if v.bot_qualifying_questions:
        try:
            parsed = json.loads(v.bot_qualifying_questions)
            if isinstance(parsed, list):
                bot_qq_text = "\n".join(str(q) for q in parsed if str(q).strip())
        except Exception:
            bot_qq_text = v.bot_qualifying_questions
    interview_qs_text = ""
    if v.interview_questions_json:
        try:
            parsed = json.loads(v.interview_questions_json)
            if isinstance(parsed, list):
                interview_qs_text = "\n".join(str(q) for q in parsed if str(q).strip())
        except Exception:
            interview_qs_text = v.interview_questions_json

    form_values = {
        "title": v.title or "",
        "body": v.body or "",
        "city": v.city or "",
        "language": v.language.value if v.language else "ru",
        "salary_text": v.salary_text or "",
        "schedule_text": v.schedule_text or "",
        "contact_text": v.contact_text or "",
        "apply_url": v.apply_url or "",
        "final_post_title": v.final_post_title or "",
        "final_post_body": v.final_post_body or "",
        "questions": interview_qs_text,
        "listing_type": v.listing_type or "recruitment",
        "bot_introduction": v.bot_introduction or "",
        "bot_faq_knowledge": v.bot_faq_knowledge or "",
        "bot_qualifying_questions": bot_qq_text,
        "bot_hot_criteria": v.bot_hot_criteria or "",
        "bot_cold_criteria": v.bot_cold_criteria or "",
        "whatsapp_number": v.whatsapp_number or "",
    }
    return render_template(
        "vacancy_new.html",
        languages=[l.value for l in Language],
        form_values=form_values,
        templates=get_all_templates(),
        edit_id=v.id,
        existing_image=v.image_path,
    )


@bp.post("/<int:vacancy_id>/edit")
@require_company
def edit_vacancy_post(vacancy_id: int):
    db = db_session()
    v = scoped(db, Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not v:
        db.close()
        return redirect(url_for("vacancies.list_vacancies", error="Vacancy not found."))

    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    if not title or not body:
        db.close()
        return redirect(url_for("vacancies.edit_vacancy", vacancy_id=vacancy_id, error="Title and body are required."))

    v.title = title
    v.body = body
    v.city = request.form.get("city", "").strip() or None
    lang_raw = request.form.get("language", "ru")
    try:
        v.language = Language(lang_raw)
    except Exception:
        pass
    v.salary_text = request.form.get("salary_text", "").strip() or None
    v.schedule_text = request.form.get("schedule_text", "").strip() or None
    v.contact_text = request.form.get("contact_text", "").strip() or None
    apply_url_raw = request.form.get("apply_url", "").strip() or None
    v.apply_url = apply_url_raw or build_recruitbot_apply_link(v.id)
    v.listing_type = request.form.get("listing_type", "recruitment").strip() or "recruitment"
    v.bot_introduction = request.form.get("bot_introduction", "").strip() or None
    v.bot_faq_knowledge = request.form.get("bot_faq_knowledge", "").strip() or None
    bot_qq_raw = request.form.get("bot_qualifying_questions", "").strip()
    v.bot_qualifying_questions = (
        json.dumps([line.strip() for line in bot_qq_raw.split("\n") if line.strip()], ensure_ascii=False)
        if bot_qq_raw
        else None
    )
    v.bot_hot_criteria = request.form.get("bot_hot_criteria", "").strip() or None
    v.bot_cold_criteria = request.form.get("bot_cold_criteria", "").strip() or None
    v.whatsapp_number = request.form.get("whatsapp_number", "").strip() or None
    questions_raw = request.form.get("questions", "").strip()
    v.interview_questions_json = json.dumps(
        [line.strip() for line in questions_raw.split("\n") if line.strip()],
        ensure_ascii=False,
    )

    final_post_title, final_post_body = _build_post_asset_from_form(request.form, apply_url=v.apply_url)
    if final_post_title:
        v.final_post_title = final_post_title
    if final_post_body.strip():
        v.final_post_body = final_post_body

    if 'image' in request.files:
        img = request.files['image']
        if img and img.filename:
            import os, time as _time
            upload_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            safe_name = f"{int(_time.time())}_{img.filename.replace(' ', '_')}"
            save_path = os.path.join(upload_dir, safe_name)
            img.save(save_path)
            v.image_path = save_path

    db.commit()
    db.close()
    return redirect(url_for("vacancies.view_vacancy", vacancy_id=vacancy_id, message="saved"))


@bp.get("/api/template/<key>")
@require_company
def get_template_data(key: str):
    """API: return template pre-fill data as JSON."""
    tpl = get_template(key)
    return jsonify(tpl)


@bp.post("/new")
@require_company
def new_vacancy_post():
    db = db_session()
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    city = request.form.get("city", "").strip() or None
    lang = request.form.get("language", "ru")
    questions = request.form.get("questions", "").strip()
    salary_text = request.form.get("salary_text", "").strip() or None
    schedule_text = request.form.get("schedule_text", "").strip() or None
    contact_text = request.form.get("contact_text", "").strip() or None
    apply_url = request.form.get("apply_url", "").strip() or None

    if not title or not body:
        db.close()
        return render_template(
            "vacancy_new.html",
            error="Title and body are required.",
            languages=[l.value for l in Language],
            form_values=request.form,
            templates=get_all_templates(),
        )
    try:
        q = [line.strip() for line in questions.split("\n") if line.strip()]
    except Exception:
        q = []
    # Bot settings (Task 1.2)
    listing_type = request.form.get("listing_type", "recruitment").strip() or "recruitment"
    bot_introduction = request.form.get("bot_introduction", "").strip() or None
    bot_faq_knowledge = request.form.get("bot_faq_knowledge", "").strip() or None
    bot_qualifying_questions_raw = request.form.get("bot_qualifying_questions", "").strip()
    bot_hot_criteria = request.form.get("bot_hot_criteria", "").strip() or None
    bot_cold_criteria = request.form.get("bot_cold_criteria", "").strip() or None
    whatsapp_number = request.form.get("whatsapp_number", "").strip() or None

    # Image upload
    image_path = None
    if 'image' in request.files:
        img = request.files['image']
        if img and img.filename:
            import os
            upload_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            import time as _time
            safe_name = f"{int(_time.time())}_{img.filename.replace(' ', '_')}"
            save_path = os.path.join(upload_dir, safe_name)
            img.save(save_path)
            image_path = save_path

    # Parse bot qualifying questions as JSON array
    bot_qq = None
    if bot_qualifying_questions_raw:
        bot_qq = json.dumps(
            [line.strip() for line in bot_qualifying_questions_raw.split("\n") if line.strip()],
            ensure_ascii=False,
        )

    vacancy = Vacancy(
        company_id=current_company_id(),
        title=title,
        body=body,
        city=city,
        language=Language(lang),
        salary_text=salary_text,
        schedule_text=schedule_text,
        contact_text=contact_text,
        apply_url=apply_url,
        final_post_title=request.form.get("final_post_title", "").strip() or title,
        final_post_body=request.form.get("final_post_body", "").strip() or None,
        interview_questions_json=json.dumps(q, ensure_ascii=False),
        listing_type=listing_type,
        bot_introduction=bot_introduction,
        bot_faq_knowledge=bot_faq_knowledge,
        bot_qualifying_questions=bot_qq,
        bot_hot_criteria=bot_hot_criteria,
        bot_cold_criteria=bot_cold_criteria,
        whatsapp_number=whatsapp_number,
        image_path=image_path,
    )
    db.add(vacancy)
    db.flush()  # get vacancy.id

    effective_apply_url = apply_url or build_recruitbot_apply_link(vacancy.id)
    vacancy.apply_url = effective_apply_url
    final_post_title, final_post_body = _build_post_asset_from_form(request.form, apply_url=effective_apply_url)
    if not final_post_body.strip():
        db.rollback()
        db.close()
        return render_template(
            "vacancy_new.html",
            error="Final post content could not be built. Add body text or final post body.",
            languages=[l.value for l in Language],
            form_values=request.form,
            templates=get_all_templates(),
        )
    vacancy.final_post_title = final_post_title
    vacancy.final_post_body = final_post_body

    # Auto-create campaign if coming from quick-post modal (has interval_minutes)
    interval_minutes = request.form.get("interval_minutes", "").strip()
    if interval_minutes:
        from ..models import Campaign, CampaignSource, Source
        cid = current_company_id()

        # Parse schedule params
        try:
            interval = int(interval_minutes)
        except ValueError:
            interval = 180
        active_start = request.form.get("active_start", "9")
        active_end = request.form.get("active_end", "19")
        days = request.form.getlist("days") or ["0", "1", "2", "3", "4"]

        hours_json = json.dumps({"start": int(active_start), "end": int(active_end)})
        days_json = json.dumps([int(d) for d in days])

        campaign = Campaign(
            company_id=cid,
            vacancy_id=vacancy.id,
            name=f"Auto: {title[:40]}",
            interval_minutes=interval,
            active_hours_json=hours_json,
            days_of_week_json=days_json,
            max_posts_per_day=10,
            is_running=True,
        )
        db.add(campaign)
        db.flush()

        # Attach all active Telegram sources
        tg_sources = db.query(Source).filter(
            Source.company_id == cid,
            Source.platform == "telegram",
            Source.is_active == True,
        ).all()
        for src in tg_sources:
            link = CampaignSource(campaign_id=campaign.id, source_id=src.id)
            db.add(link)

        db.commit()

        # Trigger first post immediately
        try:
            from worker.queue import enqueue_campaign_tick
            enqueue_campaign_tick(campaign.id)
        except Exception:
            pass

        db.close()
        return redirect(url_for("auth.connect_telegram", message=f"Listing created + campaign started with {len(tg_sources)} destinations"))

    db.commit()
    db.close()
    return redirect(url_for("vacancies.list_vacancies", message="Listing created."))


@bp.post("/toggle/<int:vacancy_id>")
@require_company
def toggle_vacancy(vacancy_id: int):
    db = db_session()
    vacancy = scoped(db, Vacancy).filter(Vacancy.id == vacancy_id).first()
    if vacancy:
        vacancy.is_active = not vacancy.is_active
        db.commit()
    db.close()
    return redirect(url_for("vacancies.list_vacancies"))
