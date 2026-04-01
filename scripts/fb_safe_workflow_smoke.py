from __future__ import annotations

import json
import os
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


def main():
    Base.metadata.create_all(bind=engine)
    db = db_session()
    company = ensure_company_for_seed(db)
    vacancy = ensure_vacancy_for_company(db, company.id)
    db.commit()
    db.refresh(company)
    db.refresh(vacancy)
    company_id = company.id
    owner_id = company.owner_id
    vacancy_id = vacancy.id

    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as handle:
        sample_path = handle.name
    write_sample_seed_file(sample_path)
    report = import_group_seed_file(
        db,
        company_id=company_id,
        path=sample_path,
        source_label="smoke_sample",
        collected_by="smoke_test",
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

    generated = client.post(
        "/api/fb/post-variants/generate",
        json={
            "vacancy_id": vacancy_id,
            "tone": "professional",
            "length_mode": "medium",
            "cta_mode": "dm_cv",
            "requirements": ["ניסיון בגיוס", "עבודה עם לקוחות", "עברית מצוינת"],
            "benefits": ["סביבת עבודה גמישה"],
            "save": True,
            "save_status": "draft",
        },
    )
    generated_json = generated.get_json()
    variant_id = generated_json["saved_variant"]["id"]

    approved = client.post(
        f"/api/fb/post-variants/{variant_id}/approve",
        json={"notes": "approved in smoke"},
    )
    approved_json = approved.get_json()

    run = client.post(
        "/api/fb/posting-runs",
        json={
            "vacancy_id": vacancy_id,
            "post_variant_id": variant_id,
            "group_ids": group_ids,
            "name": "Smoke run",
        },
    )
    run_json = run.get_json()
    first_queue_item_id = run_json["queue_items"][0]["id"]

    client.post(f"/api/fb/queue-items/{first_queue_item_id}/action", json={"action": "opened"})
    posted = client.post(
        f"/api/fb/queue-items/{first_queue_item_id}/mark-posted",
        json={"post_url_manual": "https://www.facebook.com/groups/tech.jobs.tlv/posts/1"},
    )
    posted_json = posted.get_json()

    result = client.post(
        f"/api/fb/results/{first_queue_item_id}",
        json={"result_status": "got_cvs", "cv_count": 2, "response_count": 3, "owner_note": "good flow"},
    )
    result_json = result.get_json()

    summary = {
        "seed_import": report,
        "generated_status": generated.status_code,
        "approved_status": approved.status_code,
        "run_status": run.status_code,
        "posted_status": posted.status_code,
        "result_status": result.status_code,
        "approved_variant_status": approved_json["status"],
        "run_state": posted_json["status"],
        "result_state": result_json["result_status"],
        "queue_items": len(run_json["queue_items"]),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
