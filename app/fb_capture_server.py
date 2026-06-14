"""Server-side, one-time Facebook login capture (the cloud "headless browser on
the server" path the owner chose 2026-06-14).

WHY
---
Posting to FB groups/Marketplace cannot be done with the Meta API; it needs a
real logged-in browser. The poster (common/fb_browser_poster.py) already runs
chromium HEADLESS in the worker using a saved Playwright storage_state — that is
fully cloud-ready. The only step that needs a human is the ONE-TIME login that
produces that storage_state.

This module runs that one-time login ON THE SERVER:
  Xvfb (virtual display) -> chromium HEADFUL on it -> x11vnc -> websockify/noVNC
so the owner can see and drive the real Facebook login from a browser tab, then
we dump storage_state to data/fb_sessions/company_<id>.json and tear everything
down. Logging in from the same server/IP that later posts is also better for
anti-ban than capturing on a laptop and posting from a datacenter.

SECURITY
--------
- Disabled unless FB_SERVER_CAPTURE is truthy.
- ONE capture slot at a time (single display/ports). A second tenant gets BUSY,
  never another tenant's screen.
- x11vnc binds 127.0.0.1 only (inside the web container). websockify is reachable
  only on the docker network and is gated by Caddy forward_auth -> /authz which
  checks the app session + that the active capture belongs to THIS company.
- One-time random VNC password, delivered only via the authed viewer page.
- Hard TTL auto-teardown; capture also tears down the instant login is detected.
- The captured session is per-company (app/facebook_session.py contract).

This module is the ONLY place that maps a company -> capture processes.
"""
from __future__ import annotations

import json
import os
import secrets
import signal
import string
import subprocess
import time
from pathlib import Path

from .facebook_session import (
    validate_company_id,
    company_session_name,
    fb_session_exists,
    get_fb_session_status,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CAPTURE_DIR = REPO_ROOT / "data" / "fb_capture"
STATE_PATH = CAPTURE_DIR / "state.json"
CAPTURE_SCRIPT = REPO_ROOT / "scripts" / "fb_capture_session_auto.py"

# Single fixed slot (one concurrent capture). Ports are container-internal.
DISPLAY = ":99"
VNC_PORT = 5900          # x11vnc, bound to 127.0.0.1 only
WS_PORT = 6080           # websockify, reachable on docker net, gated by Caddy
SCREEN = "1360x900x24"

TTL_SECONDS = 600        # 10 min hard cap for the whole capture window
NOVNC_WEB = "/usr/share/novnc"


def is_enabled() -> bool:
    return os.getenv("FB_SERVER_CAPTURE", "").strip().lower() in {"1", "true", "yes", "on"}


def _capture_dir() -> Path:
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    return CAPTURE_DIR


def _pid_alive(pid) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def _read_state() -> dict | None:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_state(state: dict) -> None:
    _capture_dir()
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    os.replace(tmp, STATE_PATH)


def _kill(pid, sig=signal.SIGTERM) -> None:
    try:
        if pid:
            os.kill(int(pid), sig)
    except (OSError, ValueError):
        pass


def _sweep_orphans() -> None:
    """Authoritative cleanup: SIGKILL any capture-signature process regardless of
    tracked pids. Guards against a stale/forked pid ever leaving an Xvfb / x11vnc /
    websockify running on the web container. Scoped tightly to our fixed single-slot
    display + ports so it can never touch the headless poster's chromium (different
    container) or anything unrelated. Killing Xvfb drops the display, so any orphan
    capture chromium dies with it. Dependency-free (no ps/pkill in the slim image)."""
    try:
        entries = os.listdir("/proc")
    except OSError:
        return
    for d in entries:
        if not d.isdigit():
            continue
        try:
            cl = open("/proc/%s/cmdline" % d, "rb").read().replace(b"\x00", b" ").decode("utf-8", "ignore")
        except Exception:
            continue
        if not cl or "storepasswd" in cl:
            continue
        sig = (
            ("Xvfb" in cl and DISPLAY in cl)
            or ("x11vnc" in cl and str(VNC_PORT) in cl)
            or ("websockify" in cl and str(WS_PORT) in cl)
        )
        if sig:
            try:
                os.kill(int(d), signal.SIGKILL)
            except (OSError, ValueError):
                pass


def _teardown(state: dict | None) -> None:
    """Kill all capture processes and clear the slot. Killing Xvfb last drops the
    display, which makes any leftover chromium exit too. Best-effort, idempotent."""
    if state:
        pids = state.get("pids", {})
        # Order: app procs first, display last.
        for key in ("capture", "websockify", "x11vnc"):
            _kill(pids.get(key), signal.SIGTERM)
        time.sleep(0.4)
        for key in ("capture", "websockify", "x11vnc"):
            _kill(pids.get(key), signal.SIGKILL)
        # Xvfb last so the display disappears under any orphan chromium.
        _kill(pids.get("xvfb"), signal.SIGTERM)
        time.sleep(0.3)
        _kill(pids.get("xvfb"), signal.SIGKILL)
        pwd_file = state.get("passwd_file")
        if pwd_file:
            try:
                os.remove(pwd_file)
            except OSError:
                pass
    # Belt-and-suspenders: kill anything matching our capture signature even if a
    # tracked pid was stale. Never leave a browser/VNC running on the server.
    _sweep_orphans()
    try:
        STATE_PATH.unlink()
    except OSError:
        pass


def _slot_active(state: dict | None) -> bool:
    """A slot is 'active' if it exists, is within TTL, and its capture proc lives."""
    if not state:
        return False
    if (time.time() - state.get("started_at", 0)) > TTL_SECONDS:
        return False
    return _pid_alive(state.get("pids", {}).get("capture"))


def _wait_display(display_num: str, timeout: float = 6.0) -> bool:
    sock = Path("/tmp/.X11-unix") / ("X" + display_num.lstrip(":"))
    deadline = time.time() + timeout
    while time.time() < deadline:
        if sock.exists():
            return True
        time.sleep(0.2)
    return False


def start_capture(company_id: int, user_id) -> dict:
    """Start a one-time FB login capture for this company. Returns:
      {"ok": True, "password": <vnc pwd>}      capture running, viewer can connect
      {"busy": True}                            another capture is in progress
      {"ok": False, "error": "..."}            failed to start
    """
    if not is_enabled():
        return {"ok": False, "error": "server_capture_disabled"}
    company_id = validate_company_id(company_id)

    existing = _read_state()
    if _slot_active(existing):
        if existing.get("company_id") == company_id and existing.get("user_id") == user_id:
            # Same owner re-entered: reuse the live slot + its password.
            return {"ok": True, "password": existing.get("password", "")}
        return {"busy": True}
    # Stale/dead slot -> reclaim.
    if existing:
        _teardown(existing)

    _capture_dir()
    session_name = company_session_name(company_id)   # company_<id>
    token = secrets.token_urlsafe(24)
    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for _ in range(8))  # VNC truncates to 8
    passwd_file = str(CAPTURE_DIR / f"vncpass_{token}")

    procs: dict[str, int] = {}
    try:
        # 1) Virtual display
        xvfb = subprocess.Popen(
            ["Xvfb", DISPLAY, "-screen", "0", SCREEN, "-nolisten", "tcp"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        procs["xvfb"] = xvfb.pid
        if not _wait_display(DISPLAY):
            raise RuntimeError("Xvfb display did not come up")

        # 2) VNC password file (obfuscated) for x11vnc -rfbauth
        subprocess.run(["x11vnc", "-storepasswd", password, passwd_file],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 3) x11vnc on 127.0.0.1 only
        x11 = subprocess.Popen(
            ["x11vnc", "-display", DISPLAY, "-rfbport", str(VNC_PORT), "-localhost",
             "-rfbauth", passwd_file, "-forever", "-shared", "-noxdamage", "-quiet"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        procs["x11vnc"] = x11.pid

        # 4) websockify + noVNC web (reachable only on docker net; Caddy gates it)
        ws = subprocess.Popen(
            ["websockify", "--web", NOVNC_WEB, str(WS_PORT), f"127.0.0.1:{VNC_PORT}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        procs["websockify"] = ws.pid

        # 5) the headful capture browser on the virtual display (reuses the proven
        #    fb_capture_session_auto.py: polls for c_user/xs/fr, dumps storage_state)
        env = dict(os.environ)
        env["DISPLAY"] = DISPLAY
        cap = subprocess.Popen(
            ["python", str(CAPTURE_SCRIPT), session_name],
            cwd=str(REPO_ROOT), env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        procs["capture"] = cap.pid
    except Exception as e:
        _teardown({"pids": procs, "passwd_file": passwd_file})
        return {"ok": False, "error": str(e)[:160]}

    _write_state({
        "company_id": company_id,
        "user_id": user_id,
        "session_name": session_name,
        "token": token,
        "password": password,
        "passwd_file": passwd_file,
        "display": DISPLAY,
        "ws_port": WS_PORT,
        "pids": procs,
        "started_at": time.time(),
    })
    return {"ok": True, "password": password}


def get_status(company_id: int, user_id=None) -> dict:
    """Sanitized status for THIS company. Never leaks another tenant's state,
    password, or pids. Tears the slot down on success/expiry."""
    try:
        company_id = validate_company_id(company_id)
    except ValueError:
        return {"state": "idle"}

    # Already connected (independent of any live slot)?
    if fb_session_exists(company_id):
        st = get_fb_session_status(company_id)
        if st.get("connected"):
            existing = _read_state()
            if existing and existing.get("company_id") == company_id:
                _teardown(existing)
            return {"state": "connected"}

    existing = _read_state()
    if not existing:
        return {"state": "idle"}
    if existing.get("company_id") != company_id:
        return {"state": "busy_other"}

    # Our slot. Did the capture finish (session written) ?
    if fb_session_exists(company_id):
        _teardown(existing)
        return {"state": "connected"}
    # Expired?
    if (time.time() - existing.get("started_at", 0)) > TTL_SECONDS:
        _teardown(existing)
        return {"state": "expired"}
    # Capture process died without a session -> failed.
    if not _pid_alive(existing.get("pids", {}).get("capture")):
        _teardown(existing)
        return {"state": "failed"}
    return {"state": "awaiting_login"}


def authz(company_id: int, user_id=None) -> bool:
    """For Caddy forward_auth on /fbvnc/*. Allow only if there is a live capture
    slot owned by this authenticated company (and user, when provided)."""
    try:
        company_id = validate_company_id(company_id)
    except ValueError:
        return False
    state = _read_state()
    if not _slot_active(state):
        return False
    if state.get("company_id") != company_id:
        return False
    if user_id is not None and state.get("user_id") not in (None, user_id):
        return False
    return True


def current_password(company_id: int, user_id=None) -> str | None:
    """Return the VNC password ONLY for the owner of the active slot (for the
    authed viewer page to build the noVNC URL). None otherwise."""
    state = _read_state()
    if not _slot_active(state):
        return None
    if state.get("company_id") != validate_company_id(company_id):
        return None
    if user_id is not None and state.get("user_id") not in (None, user_id):
        return None
    return state.get("password")


def cancel(company_id: int, user_id=None) -> None:
    """Owner-initiated teardown of their own slot."""
    state = _read_state()
    if state and state.get("company_id") == company_id:
        _teardown(state)
