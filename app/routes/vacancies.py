import json

from flask import Blueprint, redirect, render_template, request, url_for, jsonify

from ..auth import require_company
from ..db import db_session
from ..models import Language, Vacancy
from ..tenant import current_company_id, scoped
from ..listing_templates import get_template, get_all_templates

bp = Blueprint("vacancies", __name__, url_prefix="/vacancies")


def _build_post_asset_from_form(form) -> tuple[str, str]:
    title = form.get("final_post_title", "").strip() or form.get("title", "").strip()
    custom_body = form.get("final_post_body", "").strip()
    if custom_body:
        return title, custom_body

    parts = [form.get("body", "").strip()]
    city = form.get("city", "").strip()
    salary_text = form.get("salary_text", "").strip()
    schedule_text = form.get("schedule_text", "").strip()
    contact_text = form.get("contact_text", "").strip()
    apply_url = form.get("apply_url", "").strip()
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
    return render_template(
        "vacancies.html",
        vacancies=vacancies,
        error=request.args.get("error"),
        message=request.args.get("message"),
    )


@bp.get("/new")
@require_company
def new_vacancy():
    return render_template(
        "vacancy_new.html",
        languages=[l.value for l in Language],
        form_values={},
        templates=get_all_templates(),
    )


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
    final_post_title, final_post_body = _build_post_asset_from_form(request.form)

    if not title or not body or not final_post_body.strip():
        db.close()
        return render_template(
            "vacancy_new.html",
            error="Title, body, and final post content are required.",
            languages=[l.value for l in Language],
            form_values=request.form,
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
        final_post_title=final_post_title,
        final_post_body=final_post_body,
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
