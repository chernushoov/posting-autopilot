from __future__ import annotations

from flask import Blueprint, jsonify, request, session

from ..auth import require_company
from ..db import db_session
from ..models import (
    Company,
    FacebookPostVariant,
    FacebookPostVariantStatus,
    FacebookPostingRun,
    Vacancy,
)
from common.fb_safe_workflow import (
    approve_post_variant,
    create_posting_run,
    generate_hebrew_post,
    list_groups,
    save_post_variant,
    serialize_post_variant,
    serialize_posting_result,
    serialize_posting_run,
    upsert_posting_result,
    update_queue_item_action,
)

bp = Blueprint("fb_safe_workflow", __name__, url_prefix="/api/fb")


def _json_payload() -> dict:
    return request.get_json(silent=True) or {}


def _company_context(db):
    company_id = session["current_company_id"]
    owner_id = session["owner_id"]
    company = db.query(Company).filter(Company.id == company_id, Company.owner_id == owner_id).first()
    return company_id, owner_id, company


def _queue_action_response(queue_item_id: int, forced_action: str | None = None):
    payload = _json_payload()
    action = forced_action or payload.get("action")
    if not action:
        return jsonify({"error": "action is required"}), 400
    db = db_session()
    company_id, owner_id, _company = _company_context(db)
    try:
        queue_item = update_queue_item_action(
            db,
            company_id=company_id,
            queue_item_id=queue_item_id,
            action=action,
            actor_id=owner_id,
            payload=payload,
        )
        db.commit()
        run = db.query(FacebookPostingRun).filter(FacebookPostingRun.id == queue_item.run_id).first()
        data = serialize_posting_run(run)
    except Exception as exc:
        db.rollback()
        db.close()
        return jsonify({"error": str(exc)}), 400
    db.close()
    return jsonify(data)


@bp.post("/post-variants/generate")
@require_company
def generate_post_variant():
    payload = _json_payload()
    db = db_session()
    company_id, owner_id, company = _company_context(db)
    vacancy_id = payload.get("vacancy_id")
    if not vacancy_id:
        db.close()
        return jsonify({"error": "vacancy_id is required"}), 400

    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id, Vacancy.company_id == company_id).first()
    if not vacancy:
        db.close()
        return jsonify({"error": "vacancy not found"}), 404

    try:
        generated = generate_hebrew_post(company=company, vacancy=vacancy, payload=payload)
        saved_variant = None
        if payload.get("save"):
            status = FacebookPostVariantStatus(payload.get("save_status", FacebookPostVariantStatus.draft.value))
            variant = save_post_variant(
                db,
                company_id=company_id,
                vacancy_id=vacancy.id,
                actor_id=owner_id,
                generation_payload=generated["prompt_payload"],
                generated_output=generated["output"],
                status=status,
                notes=payload.get("notes"),
            )
            db.commit()
            db.refresh(variant)
            saved_variant = serialize_post_variant(variant)
    except Exception as exc:
        db.rollback()
        db.close()
        return jsonify({"error": str(exc)}), 400
    db.close()
    return jsonify(
        {
            "vacancy_id": vacancy_id,
            "prompt_version": generated["prompt_version"],
            "provider": generated["provider"],
            "prompt_payload": generated["prompt_payload"],
            "prompt_bundle": generated["prompt_bundle"],
            "output": generated["output"],
            "saved_variant": saved_variant,
        }
    )


@bp.post("/post-variants/<int:variant_id>/approve")
@require_company
def approve_variant(variant_id: int):
    payload = _json_payload()
    db = db_session()
    company_id, owner_id, _company = _company_context(db)
    variant = (
        db.query(FacebookPostVariant)
        .filter(FacebookPostVariant.id == variant_id, FacebookPostVariant.company_id == company_id)
        .first()
    )
    if not variant:
        db.close()
        return jsonify({"error": "post variant not found"}), 404

    approve_post_variant(
        variant,
        actor_id=owner_id,
        full_text=payload.get("full_text"),
        headline=payload.get("headline"),
        cta_text=payload.get("cta_text"),
        notes=payload.get("notes"),
    )
    db.commit()
    db.refresh(variant)
    data = serialize_post_variant(variant)
    db.close()
    return jsonify(data)


@bp.get("/groups")
@require_company
def get_groups():
    filters = dict(request.args)
    db = db_session()
    company_id, _owner_id, _company = _company_context(db)
    try:
        groups = list_groups(db=db, company_id=company_id, filters=filters)
    except Exception as exc:
        db.close()
        return jsonify({"error": str(exc)}), 400
    db.close()
    return jsonify({"groups": groups, "count": len(groups)})


@bp.post("/posting-runs/<int:run_id>/smoke")
@require_company
def smoke_session_endpoint(run_id: int):
    """
    Open facebook.com headless with the saved session, screenshot, return state.
    No posting happens. Use to verify the captured FB session is still valid
    before triggering an auto-fire run.
    """
    db = db_session()
    company_id, _owner_id, _company = _company_context(db)
    run = (
        db.query(FacebookPostingRun)
        .filter(FacebookPostingRun.id == run_id, FacebookPostingRun.company_id == company_id)
        .first()
    )
    db.close()
    if not run:
        return jsonify({"error": "run not found or not in current company"}), 404

    try:
        from common.fb_browser_poster import smoke_session, session_exists
    except Exception as exc:
        return jsonify({"error": f"browser poster unavailable: {exc!r}"}), 500

    from common.fb_browser_poster import company_session_name
    # Per-company session ONLY — status/smoke must never reflect another tenant's session.
    session_name = company_session_name(company_id)
    if not session_exists(session_name):
        return jsonify({
            "ok": False,
            "error": "session_missing",
            "session_name": session_name,
            "remediation": "Run scripts/fb_capture_session.py on operator's Mac to capture the FB session.",
        }), 400

    result = smoke_session(session_name)
    return jsonify({"session_name": session_name, **result})


@bp.post("/posting-runs/<int:run_id>/auto-fire")
@require_company
def auto_fire_run(run_id: int):
    """Trigger browser-automation auto-poster for the whole queue with staggered delays."""
    payload = _json_payload()
    db = db_session()
    company_id, _owner_id, _company = _company_context(db)
    run = (
        db.query(FacebookPostingRun)
        .filter(FacebookPostingRun.id == run_id, FacebookPostingRun.company_id == company_id)
        .first()
    )
    db.close()
    if not run:
        return jsonify({"error": "run not found or not in current company"}), 404

    try:
        from worker.fb_auto_post import fire_run_staggered
    except Exception as exc:
        return jsonify({"error": f"auto-poster unavailable: {exc!r}"}), 500

    min_delay = int(payload.get("min_delay_seconds", 300))
    max_delay = int(payload.get("max_delay_seconds", 600))
    first_delay = int(payload.get("first_delay_seconds", 5))
    if min_delay < 60:
        return jsonify({"error": "min_delay_seconds must be >= 60 (anti-spam protection)"}), 400
    if max_delay < min_delay:
        return jsonify({"error": "max_delay_seconds must be >= min_delay_seconds"}), 400

    result = fire_run_staggered(
        run_id,
        min_delay_seconds=min_delay,
        max_delay_seconds=max_delay,
        first_delay_seconds=first_delay,
    )
    return jsonify(result), 200 if result.get("ok") else 400


@bp.post("/posting-runs")
@require_company
def create_run():
    payload = _json_payload()
    db = db_session()
    company_id, owner_id, _company = _company_context(db)
    try:
        run = create_posting_run(
            db,
            company_id=company_id,
            vacancy_id=int(payload.get("vacancy_id")),
            post_variant_id=int(payload.get("post_variant_id")),
            group_ids=[int(group_id) for group_id in payload.get("group_ids", [])],
            created_by=owner_id,
            name=payload.get("name"),
            notes=payload.get("notes"),
        )
        db.commit()
        db.refresh(run)
        data = serialize_posting_run(
            db.query(FacebookPostingRun).filter(FacebookPostingRun.id == run.id).first()
        )
    except Exception as exc:
        db.rollback()
        db.close()
        return jsonify({"error": str(exc)}), 400
    db.close()
    return jsonify(data), 201


@bp.get("/posting-runs/<int:run_id>")
@require_company
def get_run(run_id: int):
    db = db_session()
    company_id, _owner_id, _company = _company_context(db)
    run = db.query(FacebookPostingRun).filter(FacebookPostingRun.id == run_id, FacebookPostingRun.company_id == company_id).first()
    if not run:
        db.close()
        return jsonify({"error": "posting run not found"}), 404
    data = serialize_posting_run(run)
    db.close()
    return jsonify(data)


@bp.post("/queue-items/<int:queue_item_id>/action")
@require_company
def queue_item_action(queue_item_id: int):
    return _queue_action_response(queue_item_id)


@bp.post("/queue-items/<int:queue_item_id>/mark-posted")
@require_company
def queue_item_mark_posted(queue_item_id: int):
    return _queue_action_response(queue_item_id, forced_action="posted")


@bp.post("/queue-items/<int:queue_item_id>/skip")
@require_company
def queue_item_skip(queue_item_id: int):
    return _queue_action_response(queue_item_id, forced_action="skipped")


@bp.post("/results/<int:queue_item_id>")
@require_company
def upsert_result(queue_item_id: int):
    payload = _json_payload()
    db = db_session()
    company_id, owner_id, _company = _company_context(db)
    try:
        result = upsert_posting_result(
            db,
            company_id=company_id,
            queue_item_id=queue_item_id,
            actor_id=owner_id,
            payload=payload,
        )
        db.commit()
        data = serialize_posting_result(result)
    except Exception as exc:
        db.rollback()
        db.close()
        return jsonify({"error": str(exc)}), 400
    db.close()
    return jsonify(data)
