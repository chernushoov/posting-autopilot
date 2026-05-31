from __future__ import annotations

import json
import os
import re
import tempfile

from app import create_app
from app.db import db_session, engine
from app.models import Base, FacebookGroup
from common.fb_safe_workflow import (
    ensure_company_for_seed,
    ensure_vacancy_for_company,
    import_group_seed_file,
    write_sample_seed_file,
)


def _extract_csrf_token(body: str) -> str:
    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', body)
    if match:
        return match.group(1)
    match = re.search(r'name="csrf_token" value="([^"]+)"', body)
    if match:
        return match.group(1)
    raise RuntimeError("csrf token missing from workflow page")


def main():
    Base.metadata.create_all(bind=engine)
    db = db_session()
    company = ensure_company_for_seed(db)
    vacancy = ensure_vacancy_for_company(db, company.id)
    db.commit()
    db.refresh(company)
    db.refresh(vacancy)
    company_id = company.id
    vacancy_id = vacancy.id
    owner_id = company.owner_id

    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as handle:
        sample_path = handle.name
    write_sample_seed_file(sample_path)
    import_report = import_group_seed_file(
        db,
        company_id=company_id,
        path=sample_path,
        source_label="ui_smoke_seed",
        collected_by="ui_smoke",
        default_source_type="seed_csv",
    )
    db.commit()
    os.unlink(sample_path)
    group_ids = [row.id for row in db.query(FacebookGroup).filter(FacebookGroup.company_id == company_id).order_by(FacebookGroup.id.asc()).limit(2).all()]
    db.close()

    app = create_app()
    client = app.test_client()
    with client.session_transaction() as session:
        session["is_admin"] = True
        session["owner_id"] = owner_id
        session["current_company_id"] = company_id

    vacancies_page = client.get("/vacancies/")
    generator_page = client.get(f"/facebook/vacancies/{vacancy_id}/post-generator")
    csrf_token = _extract_csrf_token(generator_page.get_data(as_text=True))
    csrf_headers = {"X-CSRFToken": csrf_token}
    initial_resume = client.get(f"/facebook/vacancies/{vacancy_id}/resume", follow_redirects=False)

    generated = client.post(
        "/api/fb/post-variants/generate",
        json={
            "vacancy_id": vacancy_id,
            "tone": "professional",
            "length_mode": "medium",
            "cta_mode": "dm_cv",
            "requirements": ["ניסיון בגיוס", "עבודה עם לקוחות"],
            "benefits": ["סביבת עבודה גמישה"],
            "save": True,
            "save_status": "draft",
        },
        headers=csrf_headers,
    )
    generated_json = generated.get_json()
    variant_id = generated_json["saved_variant"]["id"]

    approved = client.post(
        f"/api/fb/post-variants/{variant_id}/approve",
        json={"full_text": generated_json["saved_variant"]["full_text"], "headline": generated_json["saved_variant"]["headline"]},
        headers=csrf_headers,
    )
    resume_after_approve = client.get(f"/facebook/vacancies/{vacancy_id}/resume", follow_redirects=False)
    group_selector_page = client.get(f"/facebook/vacancies/{vacancy_id}/groups?variant_id={variant_id}")

    run = client.post(
        "/api/fb/posting-runs",
        json={
            "vacancy_id": vacancy_id,
            "post_variant_id": variant_id,
            "group_ids": group_ids,
            "name": "UI smoke run",
        },
        headers=csrf_headers,
    )
    run_json = run.get_json()
    run_id = run_json["id"]
    resume_after_run = client.get(f"/facebook/vacancies/{vacancy_id}/resume", follow_redirects=False)
    queue_page = client.get(f"/facebook/posting-runs/{run_id}/queue")
    first_queue_item_id = run_json["queue_items"][0]["id"]

    opened = client.post(f"/api/fb/queue-items/{first_queue_item_id}/action", json={"action": "opened"}, headers=csrf_headers)
    posted = client.post(
        f"/api/fb/queue-items/{first_queue_item_id}/mark-posted",
        json={"group_note": "posted from UI smoke"},
        headers=csrf_headers,
    )
    result = client.post(
        f"/api/fb/results/{first_queue_item_id}",
        json={"result_status": "got_cvs", "cv_count": 1, "result_note": "demo result"},
        headers=csrf_headers,
    )
    vacancy_page_after_result = client.get("/vacancies/")
    queue_api_after_result = client.get(f"/api/fb/posting-runs/{run_id}")
    groups_api = client.get("/api/fb/groups?is_active=true")
    queue_api_json = queue_api_after_result.get_json()
    groups_api_json = groups_api.get_json()
    first_group_payload = groups_api_json["groups"][0]

    summary = {
        "import_rows_seen": import_report["rows_seen"],
        "vacancies_page": vacancies_page.status_code,
        "vacancies_has_entrypoint": "Facebook Flow" in vacancies_page.get_data(as_text=True),
        "vacancies_has_continuity": "No FB flow started" in vacancies_page.get_data(as_text=True),
        "vacancies_has_latest_signal": "Latest signal" in vacancy_page_after_result.get_data(as_text=True),
        "generator_page": generator_page.status_code,
        "generator_has_heading": "Post Generator" in generator_page.get_data(as_text=True),
        "initial_resume_location": initial_resume.headers.get("Location"),
        "resume_after_approve_location": resume_after_approve.headers.get("Location"),
        "resume_after_run_location": resume_after_run.headers.get("Location"),
        "group_selector_page": group_selector_page.status_code,
        "group_selector_has_heading": "Group Selector" in group_selector_page.get_data(as_text=True),
        "queue_page": queue_page.status_code,
        "queue_has_heading": "Posting Queue" in queue_page.get_data(as_text=True),
        "generate_status": generated.status_code,
        "approve_status": approved.status_code,
        "run_status": run.status_code,
        "opened_status": opened.status_code,
        "posted_status": posted.status_code,
        "result_status": result.status_code,
        "queue_api_has_latest_signal": bool(queue_api_json.get("latest_signal")),
        "queue_api_attention_label": queue_api_json.get("attention_label"),
        "groups_api_has_warning_inputs": bool(first_group_payload.get("warning_chips")) or bool(first_group_payload.get("requires_admin_approval")),
        "groups_api_has_relative_time": bool(first_group_payload.get("last_posted_label")),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
