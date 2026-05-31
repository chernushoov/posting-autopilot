#!/usr/bin/env python3
"""Auto-detecting FB session capture (no terminal Enter needed).

Opens a real (non-headless) Chromium window, navigates to facebook.com, and
POLLS for a successful login (the critical c_user/xs/fr cookies). As soon as the
operator finishes logging in (incl. 2FA) and lands on their feed, it saves the
full browser session to data/fb_sessions/<name>.json and exits.

This is the I-can-launch-it variant of fb_capture_session.py: the assistant can
start it in the background; the operator just logs in in the window that opens.

Run:  .venv-fb/bin/python scripts/fb_capture_session_auto.py [session_name]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SESSION_DIR = REPO_ROOT / "data" / "fb_sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SESSION_NAME = "floordsgn"
CRITICAL = {"c_user", "xs", "fr"}
POLL_SECONDS = 3
TIMEOUT_SECONDS = 420  # 7 minutes to log in (allows for 2FA)


def _fb_cookies(context):
    return [c for c in context.cookies() if "facebook.com" in c.get("domain", "")]


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed in this venv.")
        return 1

    session_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SESSION_NAME
    session_path = SESSION_DIR / f"{session_name}.json"
    print(f"\n→ FB session capture (auto) for: {session_name}")
    print(f"→ Will save to: {session_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
            ),
            locale="he-IL",
            timezone_id="Asia/Jerusalem",
        )
        page = context.new_page()
        try:
            page.goto("https://www.facebook.com/", timeout=30_000)
        except Exception as exc:
            print(f"WARN: navigation issue, continuing: {exc}")

        print("\n" + "=" * 60)
        print("LOG IN to Facebook in the window that just opened.")
        print("Waiting for login to complete (auto-detect)...")
        print("=" * 60)

        waited = 0
        while waited < TIMEOUT_SECONDS:
            try:
                present = {c["name"] for c in _fb_cookies(context) if c["name"] in CRITICAL}
            except Exception:
                present = set()
            if CRITICAL.issubset(present):
                break
            time.sleep(POLL_SECONDS)
            waited += POLL_SECONDS

        fb_cookies = _fb_cookies(context)
        present = {c["name"] for c in fb_cookies if c["name"] in CRITICAL}
        missing = CRITICAL - present
        if missing:
            print(f"\nWARN: login not detected within {TIMEOUT_SECONDS}s; missing {missing}.")
            print("Saving whatever state exists — re-run if posting fails.")

        state = context.storage_state()
        session_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        all_cookies = state.get("cookies", [])
        print(f"\n✓ Saved {len(all_cookies)} cookies ({len(fb_cookies)} for facebook.com)")
        print(f"✓ Session file: {session_path}")
        if not missing:
            print("✓ Critical FB cookies present (c_user, xs, fr) — session is good.")
        browser.close()
        return 0 if not missing else 2


if __name__ == "__main__":
    sys.exit(main())
