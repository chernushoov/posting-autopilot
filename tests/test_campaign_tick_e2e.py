"""C4 + C5 end-to-end through the real campaign_tick (the hottest posting path).

Mocks only the network leaf (_send_telegram_post) and drives the real campaign_tick:
  - kill switch -> tick sends nothing and records no attempt (C4)
  - active     -> tick sends once and records a 'posted' attempt
  - immediate re-run -> anti-duplicate guard skips the same vacancy->source (C5)

    .venv-local/bin/python tests/test_campaign_tick_e2e.py
"""
import os
import sys
import tempfile

os.environ["RA_DATA_DIR"] = tempfile.mkdtemp(prefix="tick_e2e_guard_")
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t.db"
os.environ["ALLOW_INSECURE_DEV_SECRET"] = "1"
os.environ.setdefault("FLASK_SECRET_KEY", "x" * 40)
os.environ["WARMUP_RAMP_DAYS"] = "0"        # isolate: disable ramp so cap == configured
os.environ["MIN_REPOST_INTERVAL_HOURS"] = "20"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base, Company, Vacancy, Campaign, Source, CampaignSource, PostingAttempt  # noqa: E402
from app.db import db_session, engine  # noqa: E402
from common import posting_guard as pg  # noqa: E402
import worker.tasks as wt  # noqa: E402

Base.metadata.create_all(bind=engine)

FAILS = []
SENT = []


def check(name, cond):
    print(("  PASS " if cond else "  FAIL ") + name)
    if not cond:
        FAILS.append(name)


def fake_send(source, company, text, file_path=None):
    SENT.append((getattr(source, "id", None), text))
    return True, "sent(test)", "telethon"


def attempts(db, run_key):
    return db.query(PostingAttempt).filter(PostingAttempt.run_key == run_key).all()


def main():
    wt._send_telegram_post = fake_send  # mock the network leaf only

    db = db_session()
    comp = Company(owner_id="o1", name="Tick Co")
    db.add(comp); db.commit()
    vac = Vacancy(company_id=comp.id, title="Welder", body="Build stuff")
    db.add(vac); db.commit()
    camp = Campaign(company_id=comp.id, vacancy_id=vac.id, is_running=True,
                    interval_minutes=60, max_posts_per_day=10)
    db.add(camp); db.commit()
    src = Source(company_id=comp.id, tg_ref="@beta_group", label="Beta group",
                 last_check_ok=True, is_active=True, platform="telegram", destination_kind="group")
    db.add(src); db.commit()
    db.add(CampaignSource(campaign_id=camp.id, source_id=src.id)); db.commit()
    cid = camp.id
    db.close()

    print("C4 — paused: campaign_tick sends nothing, records no attempt:")
    pg.pause(reason="e2e")
    SENT.clear()
    wt.campaign_tick(cid, run_key="r_paused", trigger="operator_run_now")
    db = db_session()
    check("no send while paused", len(SENT) == 0)
    check("no attempt row created while paused", len(attempts(db, "r_paused")) == 0)
    db.close()

    print("C? — active: campaign_tick sends once, records 'posted':")
    pg.resume()
    SENT.clear()
    wt.campaign_tick(cid, run_key="r1", trigger="operator_run_now")
    db = db_session()
    a1 = attempts(db, "r1")
    check("exactly one send", len(SENT) == 1)
    check("attempt recorded as posted", len(a1) == 1 and a1[0].result_status == "posted")
    db.close()

    print("C5 — immediate re-run: anti-duplicate guard skips same vacancy->source:")
    SENT.clear()
    wt.campaign_tick(cid, run_key="r2", trigger="operator_run_now")
    db = db_session()
    a2 = attempts(db, "r2")
    check("no second send (duplicate blocked)", len(SENT) == 0)
    check("attempt recorded as skipped/duplicate_skipped",
          len(a2) == 1 and a2[0].result_status == "skipped" and a2[0].action_taken == "duplicate_skipped")
    db.close()

    print("")
    if FAILS:
        print(f"RESULT: {len(FAILS)} FAILED -> {FAILS}")
        return 1
    print("RESULT: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
