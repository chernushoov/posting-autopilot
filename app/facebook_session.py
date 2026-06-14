"""Single source of truth for per-company Facebook browser-session files.

TENANT ISOLATION CONTRACT
-------------------------
A company's Facebook browser session lives ONLY at:

    data/fb_sessions/company_<company_id>.json

There is NO shared/global session, NO "floordsgn" fallback, and NO default identity
for customer posting. `company_id` is always derived from the server-side
authenticated session (`current_company_id`) AFTER ownership validation — it is never
read from request args/form/json/headers/cookies. Paths are built by construction
from a validated positive integer, so a filename/traversal payload cannot reach the
filesystem. Public status responses never expose the absolute path or cookie content.

This module is the only place allowed to map a company -> session file. Everything
else (web routes, worker, poster) must go through it.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# <repo_root>/data/fb_sessions  (this file is <repo_root>/app/facebook_session.py)
FB_SESSION_DIR = Path(__file__).resolve().parents[1] / "data" / "fb_sessions"

# A real Playwright storage_state with FB cookies is several KB; reject stubs.
MIN_VALID_SESSION_BYTES = 1024

# Shared status / error vocabulary (used by /connect/facebook/status and the poster).
FB_NOT_CONNECTED = "facebook_not_connected"
FB_SESSION_INVALID = "facebook_session_invalid"
FB_SESSION_EXPIRED = "facebook_session_expired"

# status reason -> stable, customer-facing error_code used by posting / auto-fire.
NOT_CONNECTED_ERROR_CODES = {
    FB_NOT_CONNECTED: "FACEBOOK_NOT_CONNECTED_FOR_COMPANY",
    FB_SESSION_INVALID: "FACEBOOK_SESSION_INVALID",
    FB_SESSION_EXPIRED: "FACEBOOK_SESSION_EXPIRED",
}


def error_code_for_reason(reason) -> str:
    return NOT_CONNECTED_ERROR_CODES.get(reason, "FACEBOOK_NOT_CONNECTED_FOR_COMPANY")


def get_fb_session_dir() -> Path:
    FB_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return FB_SESSION_DIR


def validate_company_id(company_id) -> int:
    """company_id must be a positive int. bool is an int subclass — reject it too."""
    if isinstance(company_id, bool) or not isinstance(company_id, int):
        raise ValueError("company_id must be int")
    if company_id <= 0:
        raise ValueError("company_id must be positive")
    return company_id


def company_session_name(company_id) -> str:
    """Session NAME (no extension) handed to the low-level browser poster."""
    return f"company_{validate_company_id(company_id)}"


def session_basename(company_id) -> str:
    """Safe basename for logs/responses (never the absolute path)."""
    return f"company_{validate_company_id(company_id)}.json"


def get_fb_session_path(company_id) -> Path:
    """Absolute path to this company's session file, built by construction."""
    return get_fb_session_dir() / session_basename(company_id)


def fb_session_exists(company_id) -> bool:
    """True iff this company has a non-empty session file. Fail-closed on bad id."""
    try:
        path = get_fb_session_path(company_id)
    except ValueError:
        return False
    return path.is_file() and path.stat().st_size > 0


def get_current_company_fb_session_path() -> Path:
    """Session path for the CURRENT authenticated company. company_id comes ONLY from
    the server-side session (set after ownership validation by require_company).
    Raises ValueError if there is no current company."""
    from flask import session

    company_id = session.get("current_company_id")
    if not company_id:
        raise ValueError("no current company in session")
    return get_fb_session_path(company_id)


def _validate_session_file(path: Path) -> tuple[bool, str | None]:
    """Offline validity of a session file: must be readable, >= MIN bytes, parse as a
    Playwright storage_state with a non-empty cookies list, and not be fully expired.
    Returns (valid, reason). Does NOT hit the network — that is the smoke endpoint's
    job."""
    try:
        if path.stat().st_size < MIN_VALID_SESSION_BYTES:
            return False, FB_SESSION_INVALID
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception:
        return False, FB_SESSION_INVALID
    cookies = data.get("cookies") if isinstance(data, dict) else None
    if not isinstance(cookies, list) or not cookies:
        return False, FB_SESSION_INVALID
    now = datetime.now(timezone.utc).timestamp()
    explicit_exps = [
        c["expires"]
        for c in cookies
        if isinstance(c, dict) and isinstance(c.get("expires"), (int, float)) and c["expires"] > 0
    ]
    if explicit_exps and all(exp < now for exp in explicit_exps):
        return False, FB_SESSION_EXPIRED
    return True, None


def get_fb_session_status(company_id) -> dict:
    """Tenant-safe connection status for ONE company. Never leaks the path or cookies.

    Shapes:
      connected:     {connected:True,  company_id, session_file_exists:True, session_valid:True, last_check_at}
      not connected: {connected:False, company_id, session_file_exists:False, session_valid:False, reason:facebook_not_connected}
      invalid:       {connected:False, company_id, session_file_exists:True,  session_valid:False, reason:facebook_session_invalid|expired}
    """
    try:
        company_id = validate_company_id(company_id)
    except ValueError:
        return {
            "connected": False, "company_id": None, "session_file_exists": False,
            "session_valid": False, "reason": FB_NOT_CONNECTED,
        }
    path = get_fb_session_path(company_id)
    if not (path.is_file() and path.stat().st_size > 0):
        return {
            "connected": False, "company_id": company_id, "session_file_exists": False,
            "session_valid": False, "reason": FB_NOT_CONNECTED,
        }
    valid, reason = _validate_session_file(path)
    if not valid:
        return {
            "connected": False, "company_id": company_id, "session_file_exists": True,
            "session_valid": False, "reason": reason,
        }
    return {
        "connected": True, "company_id": company_id, "session_file_exists": True,
        "session_valid": True, "last_check_at": datetime.now(timezone.utc).isoformat(),
    }
