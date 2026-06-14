#!/usr/bin/env python3
"""
One-shot FB session capture for the operator.

Usage (run on operator's Mac, NOT inside docker):
    cd ~/Desktop/recruit-autopilot-core
    python3 -m venv .venv-fb
    .venv-fb/bin/pip install playwright
    .venv-fb/bin/playwright install chromium
    .venv-fb/bin/python scripts/fb_capture_session.py

What it does:
- Opens a real Chromium window (NOT headless).
- Navigates to facebook.com.
- Operator logs in normally (with 2FA if enabled).
- Operator presses Enter in the terminal once they see their FB feed.
- Script saves the full browser context (cookies + localStorage) to
  data/fb_sessions/floordsgn.json.
- Docker worker container reads that file at posting time.

The captured session is the operator's regular FB account state. Browser
automation will use it to post to groups as if the operator were typing
themselves. This means:
- The IP that hits FB is operator's home IP (Mac → docker → out to FB).
- Login state is real, no password handling on our side.
- 2FA / device verification are passed once during capture.

Re-run this script every 1-2 weeks to refresh the session before FB
expires it (depending on activity, 7-30 day window).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SESSION_DIR = REPO_ROOT / "data" / "fb_sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed.")
        print("Run:")
        print("  python3 -m venv .venv-fb")
        print("  .venv-fb/bin/pip install playwright")
        print("  .venv-fb/bin/playwright install chromium")
        print("  .venv-fb/bin/python scripts/fb_capture_session.py")
        return 1

    if len(sys.argv) < 2:
        print("Usage: fb_capture_session.py <session_name>  (per-company, e.g. company_7)")
        print("Refusing to default to a shared FB identity — pass the per-company session name.")
        return 2
    session_name = sys.argv[1]
    session_path = SESSION_DIR / f"{session_name}.json"

    print(f"\n→ Capturing FB session for: {session_name}")
    print(f"→ Will save to: {session_path}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0.0.0 Safari/537.36"
            ),
            locale="he-IL",
            timezone_id="Asia/Jerusalem",
        )
        page = context.new_page()

        print("→ Opening facebook.com... please log in to your account.")
        try:
            page.goto("https://www.facebook.com/", timeout=30_000)
        except Exception as exc:
            print(f"WARN: navigation timeout, continuing anyway: {exc}")

        print("\n" + "=" * 60)
        print("LOG IN to Facebook in the open browser window.")
        print("Once you see your Facebook home feed, come back here")
        print("and press Enter.")
        print("=" * 60 + "\n")

        try:
            input("Press Enter when ready to save session... ")
        except KeyboardInterrupt:
            print("\nAborted.")
            browser.close()
            return 130

        page.goto("https://www.facebook.com/", timeout=30_000)
        time.sleep(2)

        try:
            page_url = page.url
        except Exception:
            page_url = "unknown"

        if "login" in page_url or "/checkpoint" in page_url:
            print(f"\nWARN: still on login/checkpoint page: {page_url}")
            print("Make sure you actually logged in before pressing Enter.")
            confirm = input("Save anyway? [y/N] ").strip().lower()
            if confirm != "y":
                browser.close()
                return 1

        state = context.storage_state()
        session_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        cookies = state.get("cookies", [])
        fb_cookies = [c for c in cookies if "facebook.com" in c.get("domain", "")]

        print(f"\n✓ Saved {len(cookies)} cookies ({len(fb_cookies)} for facebook.com)")
        print(f"✓ Session file: {session_path}")
        print(f"✓ Final URL: {page_url}")

        critical = {"c_user", "xs", "fr"}
        present = {c["name"] for c in fb_cookies if c["name"] in critical}
        missing = critical - present
        if missing:
            print(
                f"\nWARN: missing critical FB cookies: {missing}. "
                "Posting will fail. Re-run after a successful login."
            )
        else:
            print("\n✓ Critical FB cookies present (c_user, xs, fr).")

        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
