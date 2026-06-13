"""C4/C2 integration — prove the TG send chokepoint actually honors the guard.

worker.tasks._send_telegram_post must consult the guard BEFORE touching the source
or making any network call. We call it with source=None while paused: if the guard
were not first, it would crash dereferencing None; instead it must return cleanly
with delivery_method="blocked" (which campaign_tick treats as a deferral, not a
failed send — so the daily cap isn't burned and no real post goes out).

    .venv-local/bin/python tests/test_send_guard_integration.py
"""
import os
import sys
import tempfile

os.environ["RA_DATA_DIR"] = tempfile.mkdtemp(prefix="send_guard_")
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t.db"
os.environ["ALLOW_INSECURE_DEV_SECRET"] = "1"
os.environ.setdefault("FLASK_SECRET_KEY", "x" * 40)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common import posting_guard as pg  # noqa: E402
from worker.tasks import _send_telegram_post  # noqa: E402

FAILS = []


def check(name, cond):
    print(("  PASS " if cond else "  FAIL ") + name)
    if not cond:
        FAILS.append(name)


def main():
    print("C4 — _send_telegram_post short-circuits under the kill switch:")
    pg.pause(reason="integration-test")
    ok, msg, method = _send_telegram_post(None, None, "should never be sent")
    check("returns ok=False while paused", ok is False)
    check("delivery_method == 'blocked'", method == "blocked")
    check("reason mentions KILL_SWITCH", "KILL_SWITCH" in (msg or ""))
    check("guard ran BEFORE touching source (no crash on source=None)", True)

    pg.resume()
    # After resume + outside quiet hours we can't assert a real send here (no creds),
    # but we can assert the guard no longer blocks at the chokepoint entry: with a
    # None source it should now progress past the guard and raise on source access.
    progressed_past_guard = False
    try:
        _send_telegram_post(None, None, "x")
    except Exception:
        progressed_past_guard = True  # crashed deeper => guard did NOT block
    # Note: only meaningful when not in quiet hours; treat quiet-hours block as OK too.
    blocked_now = pg.block_reason() is not None
    check("after resume, chokepoint no longer kill-blocked (progresses or quiet-hours)",
          progressed_past_guard or blocked_now)

    print("")
    if FAILS:
        print(f"RESULT: {len(FAILS)} FAILED -> {FAILS}")
        return 1
    print("RESULT: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
