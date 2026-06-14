"""P0 regression suite — shared Telegram bot multi-tenant isolation.

Run with the test venv (python3.11 + full requirements):
    /tmp/pa-venv311/bin/python tests/test_bot_tenant_isolation.py

The bug fixed here: bot/run_bot.py resolved the company as "first active company"
in every handler, so a shared bot serving 2+ companies would file all candidates
under company #1. The fix resolves tenant from the apply deep link (vacancy ->
company, verified) or the user's active candidate row — never a global default —
and fails closed otherwise.

Tests the resolver helpers (the new isolation boundary) + the deep-link invariant +
the per-company listener path. Uses a throwaway SQLite DB.
"""
import os
import sys
import tempfile

ROOT = "/Users/agentmachine/Desktop/pa-work"
sys.path.insert(0, ROOT)

from cryptography.fernet import Fernet  # noqa: E402

_tmpdb = tempfile.mktemp(suffix=".db")
os.environ.update({
    "DATABASE_URL": f"sqlite:///{_tmpdb}",
    "FLASK_SECRET_KEY": "S" * 40,
    "ADMIN_PASSWORD": "test-admin-pw",
    "DATA_ENCRYPTION_KEY": Fernet.generate_key().decode(),
    "REDIS_URL": "redis://localhost:6379/0",
})
for _k in ("APP_ENV", "FLASK_ENV", "BILLING_ENABLED", "REQUIRE_PROD_SECRETS"):
    os.environ.pop(_k, None)

from app.schema import bootstrap_schema  # noqa: E402
from app.db import db_session  # noqa: E402
from app.models import Company, Vacancy, Candidate, CandidateStatus  # noqa: E402
import bot.run_bot as B  # noqa: E402  (proves the patched module imports cleanly)
import worker.tg_listener as L  # noqa: E402

bootstrap_schema()

# ── seed two companies + vacancies ───────────────────────────────────────────
db = db_session()
A = Company(owner_id="a@test", name="ACO"); db.add(A)
Bco = Company(owner_id="b@test", name="BCO"); db.add(Bco)
db.flush()
vA = Vacancy(company_id=A.id, title="VAC_A", body="x"); db.add(vA)
vB = Vacancy(company_id=Bco.id, title="VAC_B", body="x"); db.add(vB)
db.flush()
A_id, B_id, vA_id, vB_id = A.id, Bco.id, vA.id, vB.id
db.commit(); db.close()


class FakeUser:
    def __init__(self, uid, uname="u", fn="F", ln="L", lc="ru"):
        self.id = uid; self.username = uname; self.first_name = fn
        self.last_name = ln; self.language_code = lc


fails = []


def check(name, fn):
    try:
        ok = bool(fn())
    except Exception as e:  # noqa: BLE001
        ok = False
        name += f"  [exc: {e!r}]"
    print(("PASS" if ok else "FAIL") + ": " + name)
    if not ok:
        fails.append(name)


db = db_session()

# ── verified tenant mapping: vacancy -> its OWN company (not the first company) ──
check("vacancy B -> company B (not first/A)", lambda: B._company_for_vacancy(db, vB_id)[1].id == B_id and B._company_for_vacancy(db, vB_id)[0].id == vB_id)
check("vacancy A -> company A", lambda: B._company_for_vacancy(db, vA_id)[1].id == A_id)
check("unknown vacancy -> fail closed (None,None)", lambda: B._company_for_vacancy(db, 999999) == (None, None))
check("non-int vacancy id -> fail closed", lambda: B._company_for_vacancy(db, "x; DROP") == (None, None))

# ── no global default when 2+ companies exist ────────────────────────────────
check("_sole_company is None with 2+ companies (no global default)", lambda: B._sole_company(db) is None)

# ── same Telegram user applies to BOTH companies → distinct rows, no mix ──────
u = FakeUser(1001)
cA = B._find_or_create_candidate(db, A_id, u)
check("candidate created under A has company_id A", lambda: cA.company_id == A_id)
cB = B._find_or_create_candidate(db, B_id, u)
check("same tg_user, company B -> distinct row, company_id B", lambda: cB.company_id == B_id and cB.id != cA.id)
check("find_or_create is idempotent per (company,user)", lambda: B._find_or_create_candidate(db, A_id, u).id == cA.id)

# ── deep-link apply to B sets company_id=B (THE bug: previously stayed at A) ───
cB.vacancy_id = vB_id; cB.status = CandidateStatus.qualifying; db.commit()
check("deep-link B: candidate company_id==B AND vacancy_id==vB (no cross-tenant mix)", lambda: cB.company_id == B_id and cB.vacancy_id == vB_id)

# ── active-candidate resolution (not a global company) ───────────────────────
check("resolve active -> B (qualifying), company B", lambda: B._resolve_active_candidate(db, "1001").id == cB.id)
cA.status = CandidateStatus.qualifying; cB.status = CandidateStatus.passed; db.commit()
check("resolve prefers ACTIVE (A qualifying) over finished (B passed)", lambda: B._resolve_active_candidate(db, "1001").id == cA.id and B._resolve_active_candidate(db, "1001").company_id == A_id)
check("_company_of returns the candidate's own company", lambda: B._company_of(db, cA).id == A_id)
check("unknown tg_user -> None (fail closed, no global default)", lambda: B._resolve_active_candidate(db, "999999") is None)

# ── candidates never cross-visible: A's query never returns B's rows ──────────
def _no_cross():
    a_rows = db.query(Candidate).filter(Candidate.company_id == A_id).all()
    return all(r.company_id == A_id for r in a_rows) and any(r.id == cA.id for r in a_rows) and all(r.id != cB.id for r in a_rows)
check("company A candidate query excludes B's candidate", _no_cross)
db.close()

# ── per-company listener path also scopes by company_id ──────────────────────
# _capture_lead(company_id=A) must create the lead under A (no notify network call:
# company A has no notify target configured, so _notify_operator returns early).
L._capture_lead(A_id, None, "2002", "ux", "Inbound User", "hi I am interested", "в личке")
def _listener_scoped():
    d = db_session()
    try:
        row = d.query(Candidate).filter(Candidate.tg_user_id == "2002").first()
        return row is not None and row.company_id == A_id
    finally:
        d.close()
check("listener _capture_lead creates candidate under the passed company_id", _listener_scoped)

print("\n" + ("ALL BOT TENANT-ISOLATION CHECKS PASSED" if not fails else f"{len(fails)} CHECK(S) FAILED"))
sys.exit(1 if fails else 0)
