"""C3 — tenant isolation tests.

Covers (a) the scoped() primitive denying cross-tenant read/modify, and (b) the bot
lead-attribution fix (_resolve_company picks the vacancy's company, not "the first
active company"). Runs against a throwaway sqlite DB so the real data is untouched:

    .venv-local/bin/python tests/test_tenant_isolation.py

Exits non-zero on any failure.
"""
import os
import sys
import tempfile

_TMP = tempfile.mkdtemp(prefix="ra_isolation_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["ALLOW_INSECURE_DEV_SECRET"] = "1"
os.environ.setdefault("FLASK_SECRET_KEY", "x" * 40)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base, Company, Vacancy, Candidate  # noqa: E402
from app.db import db_session, engine  # noqa: E402
import app.tenant as tenant  # noqa: E402
from bot.run_bot import _resolve_company  # noqa: E402

Base.metadata.create_all(bind=engine)

FAILS = []


def check(name, cond):
    print(("  PASS " if cond else "  FAIL ") + name)
    if not cond:
        FAILS.append(name)


def main():
    db = db_session()

    a = Company(owner_id="ownerA", name="Alpha Co")
    b = Company(owner_id="ownerB", name="Beta Co")
    db.add_all([a, b])
    db.commit()
    va = Vacancy(company_id=a.id, title="Alpha welder", body="A")
    vb = Vacancy(company_id=b.id, title="Beta driver", body="B")
    db.add_all([va, vb])
    db.commit()
    lead_b = Candidate(company_id=b.id, tg_user_id="tg_b", full_name="Beta lead")
    db.add(lead_b)
    db.commit()
    a_id, b_id, va_id, vb_id, lead_b_id = a.id, b.id, va.id, vb.id, lead_b.id

    print("C3 — scoped() cross-tenant READ denial:")
    tenant.current_company_id = lambda: a_id  # act as company A
    check("A cannot read B's vacancy", tenant.scoped(db, Vacancy).filter(Vacancy.id == vb_id).first() is None)
    check("A cannot read B's lead", tenant.scoped(db, Candidate).filter(Candidate.id == lead_b_id).first() is None)
    check("A CAN read its own vacancy", tenant.scoped(db, Vacancy).filter(Vacancy.id == va_id).first() is not None)
    tenant.current_company_id = lambda: b_id  # act as company B
    check("B can read its own vacancy", tenant.scoped(db, Vacancy).filter(Vacancy.id == vb_id).first() is not None)
    check("B can read its own lead", tenant.scoped(db, Candidate).filter(Candidate.id == lead_b_id).first() is not None)

    print("C3 — scoped() cross-tenant MODIFY denial (the web update pattern):")
    # Web edit/delete handlers do scoped(...).filter(id==x).first() then mutate; for
    # company A that handle on B's row is None, so there is nothing to modify.
    tenant.current_company_id = lambda: a_id
    check("A's modify-handle on B's vacancy is None", tenant.scoped(db, Vacancy).filter(Vacancy.id == vb_id).first() is None)
    check("A's modify-handle on B's lead is None", tenant.scoped(db, Candidate).filter(Candidate.id == lead_b_id).first() is None)

    print("C3 — bot lead attribution (_resolve_company fix):")
    check("apply to B's vacancy -> company B", getattr(_resolve_company(db, vb), "id", None) == b_id)
    check("apply to A's vacancy -> company A", getattr(_resolve_company(db, va), "id", None) == a_id)
    check("no vacancy -> primary fallback (lowest id = A)", getattr(_resolve_company(db, None), "id", None) == a_id)

    db.close()

    print("")
    if FAILS:
        print(f"RESULT: {len(FAILS)} FAILED -> {FAILS}")
        return 1
    print("RESULT: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
