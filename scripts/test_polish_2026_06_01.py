#!/usr/bin/env python3
"""Regression suite for the 2026-06-01 polish session.

Codifies the verifications run while shipping the user-simulation feedback so they
don't silently regress. Pure read/render + in-memory DB — never posts or sends.

Run:  ALLOW_INSECURE_DEV_SECRET=1 .venv-local/bin/python scripts/test_polish_2026_06_01.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("ALLOW_INSECURE_DEV_SECRET", "1")
os.environ.setdefault("DATABASE_URL", "sqlite:///" + os.path.join(tempfile.mkdtemp(), "t.db"))

PASS, FAIL = 0, 0


def ok(msg):
    global PASS
    PASS += 1
    print(f"  ✅ {msg}")


def bad(msg, err):
    global FAIL
    FAIL += 1
    print(f"  ❌ {msg}: {err}")


def check(msg, cond):
    if cond:
        ok(msg)
    else:
        bad(msg, "assertion failed")


import app as app_pkg  # noqa: E402

application = app_pkg.create_app()
application.config["WTF_CSRF_ENABLED"] = False

from app.db import db_session  # noqa: E402
from app.models import (  # noqa: E402
    Company, Vacancy, Source, Candidate, CandidateStatus, PostingAttempt, Campaign, CampaignSource,
)


def seed():
    db = db_session()
    co = Company(owner_id="o@a", name="TopStaff", business_type="company", is_active=True,
                 owner_telegram_id="8175553706")
    db.add(co); db.commit(); cid = co.id
    v = Vacancy(company_id=cid, title="Водитель C", body="b", is_active=True, listing_type="auto")
    db.add(v); db.commit()
    s = Source(company_id=cid, tg_ref="@g", platform="telegram", is_active=True)
    db.add(s); db.commit()
    for i in range(3):
        db.add(PostingAttempt(company_id=cid, vacancy_id=v.id, source_id=s.id, run_key=f"r{i}",
                              platform="telegram", destination="@g", destination_ref="@g",
                              asset_title="t", asset_body="b", action_taken="run",
                              result_status="posted", operator_notes=""))
    db.add(Candidate(company_id=cid, status=CandidateStatus.new, summary="", red_flags="",
                     chat_log_json="[]", classification="hot", full_name="Дани", phone="050-1234567"))
    db.commit(); db.close()
    return cid


def main():
    cid = seed()

    print("# Telegram shared-app credentials (#1)")
    from common.tg_client import shared_app_credentials, has_shared_app_credentials
    os.environ.pop("RECRUITBOT_TG_API_ID", None); os.environ.pop("RECRUITBOT_TG_API_HASH", None)
    check("no env -> no shared creds", shared_app_credentials() == (None, None) and not has_shared_app_credentials())
    os.environ["RECRUITBOT_TG_API_ID"] = "1234567"; os.environ["RECRUITBOT_TG_API_HASH"] = "a" * 32
    check("env set -> shared creds", has_shared_app_credentials() and shared_app_credentials()[0] == 1234567)
    os.environ.pop("RECRUITBOT_TG_API_ID", None); os.environ.pop("RECRUITBOT_TG_API_HASH", None)

    print("# Auto-create campaign (#5)")
    from app.routes.campaigns import ensure_default_campaign
    db = db_session()
    n0 = db.query(Campaign).filter(Campaign.company_id == cid).count(); db.close()
    created = ensure_default_campaign(cid)
    again = ensure_default_campaign(cid)
    db = db_session()
    camps = db.query(Campaign).filter(Campaign.company_id == cid).all()
    links = db.query(CampaignSource).filter(CampaignSource.campaign_id == camps[0].id).count() if camps else 0
    db.close()
    check("creates one campaign, idempotent, not running, links source",
          n0 == 0 and created and not again and len(camps) == 1 and links == 1 and camps[0].is_running is False)

    print("# ROI receipt (#14)")
    from common.roi import compute_roi
    db = db_session(); roi = compute_roi(db, cid); db.close()
    check("roi math (3 posts, 1 resp, 1 hot, hours=(3*3+1*5)/60=0.2)",
          roi == {"posts_published": 3, "responses": 1, "hot_leads": 1, "hours_saved": 0.2})

    print("# Hot-lead targets + sample (#10/#11)")
    from common.notify_targets import resolve_recruit_notify_targets, sample_hot_lead_message
    db = db_session(); comp = db.query(Company).get(cid); tgts = resolve_recruit_notify_targets(comp); db.close()
    check("owner_telegram_id honoured in targets", "8175553706" in tgts)
    check("sample alert: 🔥 + phone, no wa.me, all langs",
          all(sample_hot_lead_message(comp, l).startswith("🔥")
              and "050-1234567" in sample_hot_lead_message(comp, l)
              and "wa.me" not in sample_hot_lead_message(comp, l)
              for l in ("ru", "he", "en")))

    print("# Renders: language detect + panels + ROI card")
    c = application.test_client()
    # Accept-Language detection
    for al, needle in (("ru", "Создать аккаунт"), ("en", "Create account"), ("he", "יצירת חשבון")):
        fresh = application.test_client()
        r = fresh.get("/register", headers={"Accept-Language": al})
        check(f"register lang-detect {al}", r.status_code == 200 and needle in r.get_data(as_text=True))
    # authed renders
    with c.session_transaction() as ss:
        ss.update(is_admin=True, user_id=1, owner_id="o@a", current_company_id=cid, ui_lang="ru")
    dash = c.get("/dashboard").get_data(as_text=True)
    check("dashboard ROI receipt", "Ваши результаты" in dash)
    tg = c.get("/connect/telegram").get_data(as_text=True)
    check("telegram ban-safety panel", "Как мы бережём ваш аккаунт" in tg)
    fb = c.get("/connect/facebook").get_data(as_text=True)
    check("facebook page renders", "</html" in fb.lower() or len(fb) > 500)
    prof = c.get("/profile/").get_data(as_text=True)
    check("profile hot-lead test button", "test-hot-lead" in prof)
    landing = application.test_client().get("/", follow_redirects=True).get_data(as_text=True)
    check("landing verticals (>=4 niche icons)", sum(1 for e in "👷🚗🏠🔧🛒" if e in landing) >= 4)
    check("landing no-bans claim removed", "без банов" not in landing and "no bans" not in landing)

    print(f"\nRESULTS: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
