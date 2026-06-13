#!/usr/bin/env python3
"""End-to-end smoke for the self-serve flow on a running web instance.

Checks:
  register -> user+company created -> vacancy created -> source created ->
  dashboard auto-creates first campaign -> campaigns page loads.
"""

from __future__ import annotations

import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import db_session
from app.models import Campaign, Company, Source, User, Vacancy


BASE_URL = os.getenv("SMOKE_BASE_URL", "http://127.0.0.1:8080").rstrip("/")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def open_text(opener: urllib.request.OpenerDirector, url: str, data: bytes | None = None) -> tuple[int, str]:
    request = urllib.request.Request(url, data=data)
    with opener.open(request, timeout=15) as response:
        status = getattr(response, "status", response.getcode())
        body = response.read().decode("utf-8", errors="replace")
        return status, body


def extract_csrf_token(body: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', body)
    if not match:
        fail("missing csrf_token in HTML response")
    return match.group(1)


def submit_form(opener: urllib.request.OpenerDirector, path: str, fields: dict[str, str]) -> tuple[int, str]:
    payload = urllib.parse.urlencode(fields, doseq=True).encode()
    return open_text(opener, f"{BASE_URL}{path}", payload)


def main() -> None:
    cookie_jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    unique = f"{int(time.time())}{random.randint(100, 999)}"
    email = f"smoke-{unique}@example.com"
    password = "SmokePass123!"
    company_name = f"Smoke Company {unique}"

    status, body = open_text(opener, f"{BASE_URL}/register")
    if status != 200:
        fail(f"/register returned {status}")
    register_csrf = extract_csrf_token(body)

    register_fields = {
        "csrf_token": register_csrf,
        "email": email,
        "password": password,
        "company_name": company_name,
    }
    invite_code = (os.getenv("SIGNUP_INVITE_CODE") or "").strip()
    if invite_code:
        register_fields["invite_code"] = invite_code

    status, body = submit_form(opener, "/register", register_fields)
    if status != 200 or "Posting<em>Autopilot</em>" not in body:
        fail("registration did not land on the authenticated dashboard flow")

    db = db_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            fail("user row was not created")
        company = db.query(Company).filter(Company.id == user.company_id).first()
        if not company or company.name != company_name:
            fail("company row was not created correctly")
        company_id = company.id
    finally:
        db.close()

    status, body = open_text(opener, f"{BASE_URL}/vacancies/new")
    if status != 200:
        fail(f"/vacancies/new returned {status}")
    vacancy_csrf = extract_csrf_token(body)

    vacancy_fields = {
        "csrf_token": vacancy_csrf,
        "title": "Smoke Warehouse Role",
        "body": "Warehouse role for smoke testing only.",
        "city": "Tel Aviv",
        "language": "en",
        "listing_type": "recruitment",
        "questions": "Do you have warehouse experience?\nWhen can you start?",
    }
    status, _ = submit_form(opener, "/vacancies/new", vacancy_fields)
    if status != 200:
        fail("vacancy creation did not complete")

    db = db_session()
    try:
        vacancy = db.query(Vacancy).filter(Vacancy.company_id == company_id).order_by(Vacancy.id.desc()).first()
        if not vacancy or vacancy.title != "Smoke Warehouse Role":
            fail("vacancy row was not created")
    finally:
        db.close()

    status, body = open_text(opener, f"{BASE_URL}/sources/")
    if status != 200:
        fail(f"/sources/ returned {status}")
    source_csrf = extract_csrf_token(body)

    source_fields = {
        "csrf_token": source_csrf,
        "platform": "telegram",
        "destination_kind": "group",
        "tg_ref": f"@smoke_group_{unique}",
        "posting_mode": "auto",
        "label": "Smoke Group",
        "destination_url": "",
    }
    status, _ = submit_form(opener, "/sources/new", source_fields)
    if status != 200:
        fail("source creation did not complete")

    db = db_session()
    try:
        source = db.query(Source).filter(Source.company_id == company_id).order_by(Source.id.desc()).first()
        if not source or source.label != "Smoke Group":
            fail("source row was not created")
    finally:
        db.close()

    status, body = open_text(opener, f"{BASE_URL}/dashboard")
    if status != 200:
        fail(f"/dashboard returned {status}")
    if "Telegram" not in body and "Facebook" not in body:
        fail("dashboard did not render expected onboarding content")

    db = db_session()
    try:
        campaign_count = db.query(Campaign).filter(Campaign.company_id == company_id).count()
        if campaign_count < 1:
            fail("dashboard did not auto-create the first campaign")
    finally:
        db.close()

    status, body = open_text(opener, f"{BASE_URL}/campaigns/")
    if status != 200:
        fail(f"/campaigns/ returned {status}")
    if "Smoke Warehouse Role" not in body:
        fail("campaigns page did not expose the created campaign/listing flow")

    print("PASS: signup -> vacancy -> source -> campaign flow completed")


if __name__ == "__main__":
    main()
