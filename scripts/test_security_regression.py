"""Targeted security regression suite for the 2026-06-14 hardening patch.

Run with the test venv (full requirements, on python3.11):
    /tmp/pa-venv311/bin/python scripts/test_security_regression.py

Covers:
  - Cross-tenant isolation: tenant A cannot READ B's vacancy/candidate, nor MUTATE
    (delete) B's source/creative, nor switch into B's company.
  - /uploads serves only the current tenant's files; path traversal blocked.
  - FB browser session is per-company and FAILS CLOSED when the current company has
    no session (no shared 'floordsgn' fallback).
  - PII encryption at rest: Company.fb_access_token / tg_api_hash are ciphertext in
    the DB and decrypt transparently on read.
  - apply_url stored-XSS defenses: scheme allow-list + JS-context sink no longer uses
    the single-quote breakout form.
  - Demo CSRF token meta is present.
  - Paywall: with BILLING_ENABLED on, an expired trial is blocked (the dead '/'-prefix
    gate is fixed); public routes stay open.

Self-contained: uses a throwaway SQLite DB; billing OFF by default.
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

from datetime import datetime, timedelta  # noqa: E402
import sqlite3  # noqa: E402

from app.factory import create_app  # noqa: E402
from app.db import db_session  # noqa: E402
from app.models import Company, User, Vacancy, Candidate, Source, Creative, Prospect  # noqa: E402

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
app.config["TESTING"] = True

# ── seed two tenants ────────────────────────────────────────────────────────
db = db_session()


def mk_company(owner, name):
    c = Company(owner_id=owner, name=name)
    db.add(c)
    db.flush()
    return c


A = mk_company("ownerA@test", "ZZA_CO")
B = mk_company("ownerB@test", "ZZB_CO")
db.flush()


def seed(c, tag):
    v = Vacancy(company_id=c.id, title=f"{tag}_VAC", body="body")
    cand = Candidate(company_id=c.id, full_name=f"{tag}_CAND")
    src = Source(company_id=c.id, tg_ref=f"@{tag.lower()}_src", label=f"{tag}_SRC")
    crt = Creative(company_id=c.id, kind="banner", title=f"{tag}_CRT", file_path=f"{tag}_upload.png")
    pros = Prospect(company_id=c.id, name=f"{tag}_PROS")
    for o in (v, cand, src, crt, pros):
        db.add(o)
    db.flush()
    return {"v": v.id, "cand": cand.id, "src": src.id, "crt": crt.id, "pros": pros.id}


a = seed(A, "ZZA")
b = seed(B, "ZZB")

uA = User(email="ownera@test", password_hash="x", company_id=A.id,
          trial_expires_at=datetime.utcnow() - timedelta(days=1))  # expired
uB = User(email="ownerb@test", password_hash="x", company_id=B.id)
db.add(uA)
db.add(uB)
db.flush()

# encryption-at-rest integration: write secrets via the real ORM model
A_row = db.get(Company, A.id)
A_row.fb_access_token = "ZZA_FBTOKEN_SECRET"
A_row.tg_api_hash = "ZZA_TGHASH_SECRET"
db.commit()

A_id, B_id, uA_id = A.id, B.id, uA.id
db.close()

# ── harness ─────────────────────────────────────────────────────────────────
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


client = app.test_client()


def login(owner, cid, user_id=1):
    with client.session_transaction() as s:
        s.clear()
        s["is_admin"] = True
        s["owner_id"] = owner
        s["current_company_id"] = cid
        s["user_id"] = user_id


def body_of(path):
    return client.get(path).get_data(as_text=True)


# 1. cross-tenant READ
login("ownerA@test", A_id)
check("A cannot read B vacancy detail", lambda: "ZZB_VAC" not in body_of(f"/vacancies/{b['v']}"))
check("A CAN read own vacancy (control)", lambda: "ZZA_VAC" in body_of(f"/vacancies/{a['v']}"))
check("A cannot read B candidate", lambda: "ZZB_CAND" not in body_of(f"/candidates/{b['cand']}"))

# 2. cross-tenant MUTATION
client.post(f"/sources/delete/{b['src']}")
check("A cannot delete B source", lambda: db_session().get(Source, b["src"]) is not None)
client.post(f"/creatives/{b['crt']}/delete")
check("A cannot delete B creative", lambda: db_session().get(Creative, b["crt"]) is not None)

# 3. company switch owned-only
client.get(f"/companies/switch/{B_id}")
def _cur_company():
    with client.session_transaction() as s:
        return s.get("current_company_id")
check("A cannot switch into B company", lambda: _cur_company() != B_id)

# 4. uploads ownership + traversal
updir = os.path.join(ROOT, "data", "uploads")
os.makedirs(updir, exist_ok=True)
with open(os.path.join(updir, "ZZA_upload.png"), "wb") as f:
    f.write(b"\x89PNG\r\n" + b"0" * 200)
login("ownerA@test", A_id)
check("owner fetches own upload (200)", lambda: client.get("/uploads/ZZA_upload.png").status_code == 200)
login("ownerB@test", B_id)
check("other tenant CANNOT fetch foreign upload (404)", lambda: client.get("/uploads/ZZA_upload.png").status_code == 404)
check("uploads path-traversal blocked (404)", lambda: client.get("/uploads/....//....//etc/passwd").status_code == 404)

# 5. FB per-company session + fail-closed (canonical helper the routes/worker use)
from common.fb_browser_poster import company_session_name, session_exists  # noqa: E402
fbdir = os.path.join(ROOT, "data", "fb_sessions")
os.makedirs(fbdir, exist_ok=True)
with open(os.path.join(fbdir, f"company_{A_id}.json"), "w") as f:
    f.write("{}" + " " * 2000)
check("FB session name is per-company", lambda: company_session_name(A_id) == f"company_{A_id}")
check("FB session present for A", lambda: session_exists(company_session_name(A_id)) is True)
check("FB session ABSENT for B → fail-closed", lambda: session_exists(company_session_name(B_id)) is False)
login("ownerA@test", A_id)
check("connect/facebook renders for A (200)", lambda: client.get("/connect/facebook").status_code == 200)
login("ownerB@test", B_id)
check("connect/facebook renders for B (200, no shared session leak)",
      lambda: client.get("/connect/facebook").status_code == 200)

# 6. PII encryption at rest (raw DB vs ORM)
def _raw(col):
    con = sqlite3.connect(_tmpdb)
    try:
        return con.execute(f"SELECT {col} FROM companies WHERE id=?", (A_id,)).fetchone()[0]
    finally:
        con.close()
check("fb_access_token is CIPHERTEXT at rest",
      lambda: _raw("fb_access_token") not in (None, "ZZA_FBTOKEN_SECRET") and _raw("fb_access_token").startswith("gAAAAA"))
check("tg_api_hash is CIPHERTEXT at rest",
      lambda: _raw("tg_api_hash") not in (None, "ZZA_TGHASH_SECRET") and _raw("tg_api_hash").startswith("gAAAAA"))
check("fb_access_token decrypts on ORM read", lambda: db_session().get(Company, A_id).fb_access_token == "ZZA_FBTOKEN_SECRET")
check("tg_api_hash decrypts on ORM read", lambda: db_session().get(Company, A_id).tg_api_hash == "ZZA_TGHASH_SECRET")

# 7. apply_url stored-XSS defenses
from app.routes.vacancies import _safe_apply_url  # noqa: E402
check("apply_url rejects javascript: scheme", lambda: _safe_apply_url("javascript:alert(1)") is None)
check("apply_url rejects data: scheme", lambda: _safe_apply_url("data:text/html,<script>") is None)
check("apply_url keeps https link", lambda: _safe_apply_url("https://t.me/x") == "https://t.me/x")
_dbx = db_session()
_vv = _dbx.get(Vacancy, a["v"])
_vv.apply_url = "https://x/'+alert(1)+'"
_dbx.commit()
_dbx.close()
login("ownerA@test", A_id)
_det = body_of(f"/vacancies/{a['v']}")
check("apply-link JS sink no longer uses single-quote breakout form",
      lambda: "navigator.clipboard.writeText('" not in _det)

# 8. demo CSRF token meta present
login("ownerA@test", A_id)
check("demo page now renders <meta name=csrf-token>", lambda: 'name="csrf-token"' in body_of("/demo/"))

# 9. paywall: billing ON blocks expired trial; public stays open
os.environ["BILLING_ENABLED"] = "1"
login("ownerA@test", A_id, user_id=uA_id)
_r = client.get("/vacancies/", follow_redirects=False)
check("billing ON: expired trial → 302 /pricing (dead '/'-gate fixed)",
      lambda: _r.status_code == 302 and "/pricing" in _r.headers.get("Location", ""))
check("billing ON: /pricing stays public (200)",
      lambda: client.get("/pricing", follow_redirects=False).status_code == 200)
os.environ.pop("BILLING_ENABLED", None)

# ── summary ─────────────────────────────────────────────────────────────────
print("\n" + ("ALL SECURITY REGRESSION CHECKS PASSED" if not fails else f"{len(fails)} CHECK(S) FAILED"))
sys.exit(1 if fails else 0)
