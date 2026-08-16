#!/usr/bin/env python3
"""Side-effect-free smoke for the first paying-customer setup path."""

from __future__ import annotations

import html
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# This smoke must never connect to the operator's configured database or services.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FLASK_SECRET_KEY"] = "customer-flow-smoke-only"
os.environ["ADMIN_PASSWORD"] = "customer-flow-smoke-only"
os.environ["RECRUITBOT_AI_PROVIDER"] = "stub"

from app import create_app  # noqa: E402
from app.db import db_session  # noqa: E402
from app.models import Campaign, Company, Source, Vacancy  # noqa: E402


CSRF_PATTERN = re.compile(r'name="csrf_token" value="([^"]+)"')


def csrf_token(response) -> str:
    match = CSRF_PATTERN.search(response.get_data(as_text=True))
    if not match:
        raise AssertionError(f"CSRF token missing from {response.request.path}")
    return html.unescape(match.group(1))


def main() -> int:
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()
    checks: list[dict[str, object]] = []

    def check(name: str, condition: object, detail: str = "") -> None:
        passed = bool(condition)
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            raise AssertionError(f"{name}: {detail}")

    register_page = client.get("/register")
    check("register_page", register_page.status_code == 200, str(register_page.status_code))
    signup = client.post(
        "/register",
        data={
            "csrf_token": csrf_token(register_page),
            "email": "qa-owner@example.com",
            "password": "strong-demo-pass",
            "company_name": "QA Customer",
        },
        follow_redirects=False,
    )
    check(
        "signup_redirect",
        signup.status_code == 302 and urlparse(signup.location).path == "/dashboard",
        f"{signup.status_code} {signup.location}",
    )
    dashboard = client.get("/dashboard")
    check(
        "dashboard_after_signup",
        dashboard.status_code == 200 and b"QA Customer" in dashboard.data,
        str(dashboard.status_code),
    )

    vacancy_page = client.get("/vacancies/new")
    vacancy_create = client.post(
        "/vacancies/new",
        data={
            "csrf_token": csrf_token(vacancy_page),
            "title": "Warehouse Operator - Tel Aviv",
            "body": "Stable full-time warehouse role.",
            "city": "Tel Aviv",
            "language": "en",
            "questions": "Do you have warehouse experience?\nWhen can you start?",
            "salary_text": "ILS 7,500-8,500",
            "schedule_text": "Sun-Thu",
            "contact_text": "Apply in the platform",
            "listing_type": "recruitment",
            "final_post_title": "Warehouse Operator",
            "final_post_body": "Join a stable warehouse team in Tel Aviv.",
            "whatsapp_number": "0501234567",
        },
        follow_redirects=False,
    )
    check(
        "vacancy_create_redirect",
        vacancy_create.status_code == 302
        and urlparse(vacancy_create.location).path.startswith("/vacancies/"),
        f"{vacancy_create.status_code} {vacancy_create.location}",
    )

    db = db_session()
    company = db.query(Company).filter_by(name="QA Customer").one()
    vacancy = db.query(Vacancy).filter_by(
        company_id=company.id,
        title="Warehouse Operator - Tel Aviv",
    ).one()
    check("vacancy_persisted", vacancy.final_post_body and vacancy.apply_url, f"id={vacancy.id}")

    sources_page = client.get("/sources/")
    source_create = client.post(
        "/sources/new",
        data={
            "csrf_token": csrf_token(sources_page),
            "platform": "facebook",
            "destination_kind": "group",
            "posting_mode": "assisted_manual",
            "destination_url": "https://www.facebook.com/groups/qa-demo-group",
            "label": "QA Jobs Tel Aviv",
        },
        follow_redirects=False,
    )
    check("facebook_source_create", source_create.status_code == 302, str(source_create.status_code))
    source = db.query(Source).filter_by(company_id=company.id, label="QA Jobs Tel Aviv").one()
    check(
        "facebook_source_ready_manual",
        source.last_check_ok and source.posting_mode == "assisted_manual",
        source.tg_ref,
    )

    campaign_page = client.get("/campaigns/new")
    campaign_create = client.post(
        "/campaigns/new",
        data={
            "csrf_token": csrf_token(campaign_page),
            "name": "QA customer pilot",
            "vacancy_id": str(vacancy.id),
            "interval_minutes": "180",
            "active_start_hour": "9",
            "active_end_hour": "19",
            "max_posts_per_day": "3",
            "days_of_week": ["0", "1", "2", "3", "4"],
            "source_ids": [str(source.id)],
        },
        follow_redirects=False,
    )
    check(
        "campaign_create_redirect",
        campaign_create.status_code == 302
        and urlparse(campaign_create.location).path == "/campaigns/",
        f"{campaign_create.status_code} {campaign_create.location}",
    )
    campaign = db.query(Campaign).filter_by(
        company_id=company.id,
        name="QA customer pilot",
    ).one()
    check("campaign_persisted_paused", not campaign.is_running, f"id={campaign.id}")

    for path, needle in (
        ("/vacancies/", b"Warehouse Operator"),
        ("/sources/", b"QA Jobs Tel Aviv"),
        ("/campaigns/", b"QA customer pilot"),
    ):
        page = client.get(path)
        check(f"page_{path}", page.status_code == 200 and needle in page.data, str(page.status_code))

    second_client = app.test_client()
    second_register = second_client.get("/register")
    second_signup = second_client.post(
        "/register",
        data={
            "csrf_token": csrf_token(second_register),
            "email": "second@example.com",
            "password": "second-demo-pass",
            "company_name": "Second Tenant",
        },
        follow_redirects=False,
    )
    check("second_signup", second_signup.status_code == 302, str(second_signup.status_code))
    second_vacancies = second_client.get("/vacancies/")
    check(
        "tenant_list_isolation",
        second_vacancies.status_code == 200 and b"Warehouse Operator" not in second_vacancies.data,
        str(second_vacancies.status_code),
    )
    second_detail = second_client.get(f"/vacancies/{vacancy.id}", follow_redirects=False)
    check("tenant_detail_isolation", second_detail.status_code == 302, str(second_detail.status_code))
    db.close()

    output = {"ok": all(item["passed"] for item in checks), "checks": checks}
    print(json.dumps(output, indent=2))
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
