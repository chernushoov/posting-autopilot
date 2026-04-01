from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, session, url_for

from ..auth import require_company
from ..db import db_session
from ..models import FacebookPostVariant, FacebookPostVariantStatus, FacebookPostingQueueItem, FacebookPostingRun, FacebookPostingRunStatus, Vacancy
from common.fb_safe_workflow import build_vacancy_fb_continuity_map, serialize_post_variant

bp = Blueprint("fb_ui", __name__, url_prefix="/facebook")


def _company_id() -> int:
    return int(session["current_company_id"])


@bp.get("/vacancies/<int:vacancy_id>/post-generator")
@require_company
def post_generator(vacancy_id: int):
    db = db_session()
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id, Vacancy.company_id == _company_id()).first()
    if not vacancy:
        db.close()
        return redirect(url_for("vacancies.list_vacancies"))
    variant_id = request.args.get("variant_id", type=int)
    recent_variants = (
        db.query(FacebookPostVariant)
        .filter(FacebookPostVariant.vacancy_id == vacancy_id, FacebookPostVariant.company_id == _company_id())
        .order_by(FacebookPostVariant.id.desc())
        .limit(8)
        .all()
    )
    selected_variant = None
    if variant_id:
        selected_variant = next((variant for variant in recent_variants if variant.id == variant_id), None)
    if not selected_variant and recent_variants:
        selected_variant = recent_variants[0]
    continuity = build_vacancy_fb_continuity_map(db, _company_id(), [vacancy_id]).get(vacancy_id)
    db.close()
    return render_template(
        "fb_post_generator.html",
        vacancy=vacancy,
        recent_variants=[serialize_post_variant(variant) for variant in recent_variants],
        selected_variant=serialize_post_variant(selected_variant) if selected_variant else None,
        continuity=continuity,
        title=f"Facebook Post Generator — {vacancy.title}",
    )


@bp.get("/vacancies/<int:vacancy_id>/groups")
@require_company
def group_selector(vacancy_id: int):
    db = db_session()
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id, Vacancy.company_id == _company_id()).first()
    if not vacancy:
        db.close()
        return redirect(url_for("vacancies.list_vacancies"))

    variant_id = request.args.get("variant_id", type=int)
    variant = None
    if variant_id:
        variant = (
            db.query(FacebookPostVariant)
            .filter(
                FacebookPostVariant.id == variant_id,
                FacebookPostVariant.vacancy_id == vacancy_id,
                FacebookPostVariant.company_id == _company_id(),
            )
            .first()
        )
    if not variant:
        variant = (
            db.query(FacebookPostVariant)
            .filter(
                FacebookPostVariant.vacancy_id == vacancy_id,
                FacebookPostVariant.company_id == _company_id(),
                FacebookPostVariant.status == FacebookPostVariantStatus.approved,
            )
            .order_by(FacebookPostVariant.id.desc())
            .first()
        )
    if not variant:
        variant = (
            db.query(FacebookPostVariant)
            .filter(
                FacebookPostVariant.vacancy_id == vacancy_id,
                FacebookPostVariant.company_id == _company_id(),
            )
            .order_by(FacebookPostVariant.id.desc())
            .first()
        )
    serialized_variant = serialize_post_variant(variant) if variant else None
    latest_unfinished_run = (
        db.query(FacebookPostingRun)
        .filter(
            FacebookPostingRun.vacancy_id == vacancy_id,
            FacebookPostingRun.company_id == _company_id(),
            FacebookPostingRun.status.in_(
                [
                    FacebookPostingRunStatus.draft,
                    FacebookPostingRunStatus.ready,
                    FacebookPostingRunStatus.in_progress,
                ]
            ),
        )
        .order_by(FacebookPostingRun.id.desc())
        .first()
    )
    existing_run_group_ids = []
    if latest_unfinished_run:
        existing_run_group_ids = [
            row.group_id
            for row in db.query(FacebookPostingQueueItem)
            .filter(FacebookPostingQueueItem.run_id == latest_unfinished_run.id)
            .order_by(FacebookPostingQueueItem.position.asc())
            .all()
        ]
    db.close()
    return render_template(
        "fb_group_selector.html",
        vacancy=vacancy,
        variant=serialized_variant,
        latest_unfinished_run=latest_unfinished_run,
        existing_run_group_ids=existing_run_group_ids,
        title=f"Facebook Group Selector — {vacancy.title}",
    )


@bp.get("/vacancies/<int:vacancy_id>/resume")
@require_company
def resume_vacancy_flow(vacancy_id: int):
    db = db_session()
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id, Vacancy.company_id == _company_id()).first()
    if not vacancy:
        db.close()
        return redirect(url_for("vacancies.list_vacancies"))
    continuity = build_vacancy_fb_continuity_map(db, _company_id(), [vacancy_id]).get(vacancy_id)
    db.close()
    if not continuity:
        return redirect(url_for("fb_ui.post_generator", vacancy_id=vacancy_id))
    return redirect(continuity["resume_target"])


@bp.get("/posting-runs/<int:run_id>/queue")
@require_company
def posting_queue(run_id: int):
    db = db_session()
    run = db.query(FacebookPostingRun).filter(FacebookPostingRun.id == run_id, FacebookPostingRun.company_id == _company_id()).first()
    if not run:
        db.close()
        return redirect(url_for("vacancies.list_vacancies"))
    db.close()
    return render_template("fb_posting_queue.html", run_id=run_id, title=f"Facebook Posting Queue #{run_id}")
