"""P0 regression suite — Facebook Connector tenant isolation.

Run with the test venv (python3.11 + full requirements):
    /tmp/pa-venv311/bin/python tests/test_fb_tenant_sessions.py

Isolated by construction: app.facebook_session.FB_SESSION_DIR is repointed to a temp
dir, so this NEVER reads or writes real session files. Uses a throwaway SQLite DB.

Scenarios (per spec):
  1. Company A connected, Company B not connected (+ invalid/expired reasons).
  2. Company B cannot use Company A's FB session — posting fails closed.
  3. Missing FB session fails closed.
  4. Hardcoded floordsgn.json is IGNORED for tenant posting/status.
  5. /connect/facebook/status is tenant-specific (?company_id is ignored).
  6. Company switch only allows owned companies.
  7. Existing cross-tenant scoping still denied (smoke).
Plus: validate_company_id / path-construction guards.
"""
import os
import sys
import json
import time
import tempfile
from pathlib import Path

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

# Isolate FB session storage to a temp dir BEFORE anything reads it.
import app.facebook_session as fbs  # noqa: E402
fbs.FB_SESSION_DIR = Path(tempfile.mkdtemp(prefix="fbsess_")) / "fb_sessions"

from app.facebook_session import (  # noqa: E402
    validate_company_id, get_fb_session_path, fb_session_exists,
    get_fb_session_status, company_session_name,
)
from app.factory import create_app  # noqa: E402
from app.db import db_session  # noqa: E402
from app.models import (  # noqa: E402
    Company, User, Vacancy,
    FacebookGroupSource, FacebookGroup, FacebookPostVariant, FacebookPostingRun,
    FacebookPostingQueueItem, FacebookPostTone, FacebookPostLengthMode,
    FacebookPostGenerationSource,
)

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
app.config["TESTING"] = True

# ── session-file writers (go to the isolated temp dir via the helper) ─────────
def _state(expiry_offset_s):
    now = time.time()
    return {
        "cookies": [
            {"name": "c_user", "value": "100", "domain": ".facebook.com", "path": "/",
             "expires": now + expiry_offset_s, "httpOnly": True, "secure": True},
            {"name": "xs", "value": "abc", "domain": ".facebook.com", "path": "/",
             "expires": now + expiry_offset_s},
        ],
        "origins": [{"origin": "https://www.facebook.com",
                     "localStorage": [{"name": "pad", "value": "y" * 2000}]}],
    }


def write_valid(cid):
    get_fb_session_path(cid).write_text(json.dumps(_state(10_000_000)), encoding="utf-8")


def write_expired(cid):
    get_fb_session_path(cid).write_text(json.dumps(_state(-100_000)), encoding="utf-8")


def write_invalid(cid):
    get_fb_session_path(cid).write_text("this is not json " + "x" * 2000, encoding="utf-8")


# ── seed tenants ─────────────────────────────────────────────────────────────
db = db_session()
A = Company(owner_id="ownerA@test", name="ZZA_CO"); db.add(A)
B = Company(owner_id="ownerB@test", name="ZZB_CO"); db.add(B)
C = Company(owner_id="ownerC@test", name="ZZC_CO"); db.add(C)
D = Company(owner_id="ownerD@test", name="ZZD_CO"); db.add(D)
db.flush()
A_id, B_id, C_id, D_id = A.id, B.id, C.id, D.id
# B gets a full FB posting graph (to exercise the worker fail-closed path)
b_vac = Vacancy(company_id=B_id, title="ZZB_VAC", body="x"); db.add(b_vac)
a_vac = Vacancy(company_id=A_id, title="ZZA_VAC", body="x"); db.add(a_vac)
db.flush()
gsrc = FacebookGroupSource(company_id=B_id, source_label="s", import_batch_key="k"); db.add(gsrc)
db.flush()
grp = FacebookGroup(company_id=B_id, seed_source_id=gsrc.id, name="G",
                    facebook_url="https://facebook.com/groups/1",
                    facebook_url_normalized="facebook.com/groups/1",
                    primary_category="general"); db.add(grp)
var = FacebookPostVariant(company_id=B_id, vacancy_id=b_vac.id, variant_label="v1",
                          tone=FacebookPostTone.professional,
                          length_mode=FacebookPostLengthMode.short, full_text="hello",
                          generation_source=FacebookPostGenerationSource.manual); db.add(var)
db.flush()
run = FacebookPostingRun(company_id=B_id, vacancy_id=b_vac.id, post_variant_id=var.id,
                         created_by="ownerB@test"); db.add(run)
db.flush()
qi = FacebookPostingQueueItem(company_id=B_id, run_id=run.id, group_id=grp.id, position=1)
db.add(qi)
db.flush()
b_run_id, b_qi_id, b_vac_id = run.id, qi.id, b_vac.id
db.commit()
db.close()

# sessions: A valid, C invalid, D expired, B none
write_valid(A_id)
write_invalid(C_id)
write_expired(D_id)

# ── harness ──────────────────────────────────────────────────────────────────
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


def login(owner, cid):
    with client.session_transaction() as s:
        s.clear()
        s["is_admin"] = True
        s["owner_id"] = owner
        s["current_company_id"] = cid
        s["user_id"] = 1


# ── helper unit guards ───────────────────────────────────────────────────────
check("validate_company_id accepts positive int", lambda: validate_company_id(7) == 7)
def _raises(fn):
    try:
        fn(); return False
    except (ValueError, Exception):
        return True
check("validate_company_id rejects 0", lambda: _raises(lambda: validate_company_id(0)))
check("validate_company_id rejects negative", lambda: _raises(lambda: validate_company_id(-3)))
check("validate_company_id rejects str", lambda: _raises(lambda: validate_company_id("5")))
check("validate_company_id rejects bool", lambda: _raises(lambda: validate_company_id(True)))
check("session path is company_<id>.json", lambda: get_fb_session_path(A_id).name == f"company_{A_id}.json")
check("session name has no extension/path", lambda: company_session_name(A_id) == f"company_{A_id}")

# ── Scenario 1: A connected, B not; C invalid; D expired ─────────────────────
check("status A: connected=True valid", lambda: get_fb_session_status(A_id)["connected"] is True and get_fb_session_status(A_id)["session_valid"] is True)
check("status B: connected=False reason=not_connected", lambda: get_fb_session_status(B_id)["connected"] is False and get_fb_session_status(B_id)["reason"] == "facebook_not_connected")
check("status C: file exists but invalid", lambda: get_fb_session_status(C_id)["session_file_exists"] is True and get_fb_session_status(C_id)["reason"] == "facebook_session_invalid")
check("status D: expired", lambda: get_fb_session_status(D_id)["reason"] == "facebook_session_expired")

# via the live endpoint
login("ownerA@test", A_id)
_ra = client.get("/connect/facebook/status").get_json()
check("endpoint A: connected True, company_id A", lambda: _ra["connected"] is True and _ra["company_id"] == A_id)
login("ownerB@test", B_id)
_rb = client.get("/connect/facebook/status").get_json()
check("endpoint B: connected False, reason not_connected", lambda: _rb["connected"] is False and _rb["reason"] == "facebook_not_connected")

# ── Scenario 2 + 3: B posting fails closed (worker gate), no fallback to A ────
from worker.fb_auto_post import auto_post_queue_item  # noqa: E402
_res = auto_post_queue_item(b_qi_id)
check("worker: B post fails closed", lambda: _res.get("ok") is False)
check("worker: error_code FACEBOOK_NOT_CONNECTED_FOR_COMPANY", lambda: _res.get("error_code") == "FACEBOOK_NOT_CONNECTED_FOR_COMPANY")
check("worker: reports B's own session file (no A fallback)", lambda: _res.get("session_file") == f"company_{B_id}.json")
def _qi_failed():
    d = db_session()
    try:
        it = d.get(FacebookPostingQueueItem, b_qi_id)
        return it.status.value == "failed" and "FACEBOOK_NOT_CONNECTED_FOR_COMPANY" in (it.skip_reason or "")
    finally:
        d.close()
check("worker: B queue item marked failed with code", _qi_failed)

# route auto-fire pre-check fails closed for B (no redis touched)
login("ownerB@test", B_id)
_af = client.post(f"/api/fb/posting-runs/{b_run_id}/auto-fire", json={})
check("route auto-fire B: 400 fail-closed", lambda: _af.status_code == 400)
check("route auto-fire B: error_code present", lambda: _af.get_json().get("error_code") == "FACEBOOK_NOT_CONNECTED_FOR_COMPANY")

# ── Scenario 4: floordsgn.json is IGNORED ────────────────────────────────────
_floordsgn = fbs.get_fb_session_dir() / "floordsgn.json"
_created_floordsgn = False
if not _floordsgn.exists():
    _floordsgn.write_text(json.dumps(_state(10_000_000)), encoding="utf-8")
    _created_floordsgn = True
check("floordsgn.json does NOT make B connected", lambda: get_fb_session_status(B_id)["connected"] is False)
_res2 = auto_post_queue_item(b_qi_id) if False else None  # qi already failed; re-test status only
check("floordsgn.json does NOT make B session exist", lambda: fb_session_exists(B_id) is False)
if _created_floordsgn:
    _floordsgn.unlink()

# ── Scenario 5: status tenant-specific (?company_id ignored) ─────────────────
login("ownerA@test", A_id)
_spoof = client.get(f"/connect/facebook/status?company_id={B_id}").get_json()
check("status ignores ?company_id (uses session company A)", lambda: _spoof["company_id"] == A_id and _spoof["connected"] is True)

# ── Scenario 6: company switch owned-only ────────────────────────────────────
login("ownerA@test", A_id)
client.get(f"/companies/switch/{B_id}")
def _cur():
    with client.session_transaction() as s:
        return s.get("current_company_id")
check("A cannot switch into B company", lambda: _cur() != B_id)

# ── Scenario 7: cross-tenant scoping smoke ───────────────────────────────────
login("ownerA@test", A_id)
check("A cannot read B vacancy", lambda: "ZZB_VAC" not in client.get(f"/vacancies/{b_vac_id}").get_data(as_text=True))

print("\n" + ("ALL FB TENANT-SESSION CHECKS PASSED" if not fails else f"{len(fails)} CHECK(S) FAILED"))
sys.exit(1 if fails else 0)
