#!/usr/bin/env python3

import json
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.factory import create_app
from app.db import db_session
from app.models import Company, Vacancy, Source


def build_client():
    db = db_session()
    company = db.query(Company).filter(Company.is_active == True).first()
    if not company:
        raise RuntimeError("No active company found")
    vacancy = db.query(Vacancy).filter(Vacancy.company_id == company.id, Vacancy.is_active == True).first()
    source = db.query(Source).filter(Source.company_id == company.id, Source.is_active == True).first()
    db.close()
    if not vacancy:
        raise RuntimeError("No active vacancy found for active company")
    if not source:
        raise RuntimeError("No active source found for active company")

    app = create_app()
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["is_admin"] = True
        sess["owner_id"] = company.owner_id
        sess["current_company_id"] = company.id

    return client, vacancy.id, source.id


def main():
    client, vacancy_id, source_id = build_client()
    results = []

    no_sources = client.post(
        "/campaigns/new",
        data={
            "name": "QA no sources",
            "vacancy_id": str(vacancy_id),
            "interval_minutes": "180",
            "active_start_hour": "9",
            "active_end_hour": "19",
            "days_of_week": ["0", "1"],
            "max_posts_per_day": "5",
        },
    )
    no_sources_body = no_sources.get_data(as_text=True)
    results.append(
        {
            "name": "campaign_requires_sources",
            "passed": no_sources.status_code == 200 and "Choose at least one active source before creating a campaign." in no_sources_body,
            "status_code": no_sources.status_code,
        }
    )

    bad_interval = client.post(
        "/campaigns/new",
        data={
            "name": "QA bad interval",
            "vacancy_id": str(vacancy_id),
            "interval_minutes": "0",
            "active_start_hour": "9",
            "active_end_hour": "19",
            "days_of_week": ["0", "1"],
            "max_posts_per_day": "5",
            "source_ids": [str(source_id)],
        },
    )
    bad_interval_body = bad_interval.get_data(as_text=True)
    results.append(
        {
            "name": "campaign_rejects_bad_interval",
            "passed": bad_interval.status_code == 200 and "Interval must be between" in bad_interval_body,
            "status_code": bad_interval.status_code,
        }
    )

    invalid_source = client.post(
        "/sources/new",
        data={"tg_ref": "not-a-real-ref", "label": "broken", "source_type": "group"},
        follow_redirects=False,
    )
    results.append(
        {
            "name": "source_rejects_invalid_ref",
            "passed": invalid_source.status_code == 302 and "error=Telegram+ref+must+look+like" in (invalid_source.headers.get("Location") or ""),
            "status_code": invalid_source.status_code,
            "location": invalid_source.headers.get("Location"),
        }
    )

    unconfirmed_test = client.post(
        f"/sources/test/{source_id}",
        data={},
        follow_redirects=False,
    )
    results.append(
        {
            "name": "source_test_requires_confirmation",
            "passed": unconfirmed_test.status_code == 302 and "error=Confirm+live+send+before+testing+a+source." in (unconfirmed_test.headers.get("Location") or ""),
            "status_code": unconfirmed_test.status_code,
            "location": unconfirmed_test.headers.get("Location"),
        }
    )

    output = {
        "ok": all(item["passed"] for item in results),
        "checks": results,
    }
    print(json.dumps(output, indent=2))
    sys.exit(0 if output["ok"] else 1)


if __name__ == "__main__":
    main()
