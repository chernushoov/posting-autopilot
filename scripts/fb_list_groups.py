#!/usr/bin/env python3
"""Read the operator's Facebook groups via the captured browser session.

FB's API does not expose the groups you're a member of, so we read them the way
a human would: load the saved session, open the "groups you've joined" page,
scroll to load them all, and scrape group name + URL. Output goes to
data/fb_sessions/<name>_groups.json for import into the service.

Run:  .venv-fb/bin/python scripts/fb_list_groups.py [session_name]
Env:  FB_HEADLESS=0 to watch it work.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SESSION_DIR = REPO_ROOT / "data" / "fb_sessions"

GROUP_HREF_RE = re.compile(r"facebook\.com/groups/([A-Za-z0-9._-]+)/?")
SKIP_SLUGS = {"joins", "feed", "discover", "create", "your_groups", "category"}


def main() -> int:
    from playwright.sync_api import sync_playwright

    name = sys.argv[1] if len(sys.argv) > 1 else "floordsgn"
    session_path = SESSION_DIR / f"{name}.json"
    if not session_path.exists():
        print(f"ERROR: no session at {session_path}. Run fb_capture_session_auto.py first.")
        return 1
    out_path = SESSION_DIR / f"{name}_groups.json"
    headless = os.getenv("FB_HEADLESS", "1") != "0"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            storage_state=str(session_path),
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
            ),
            locale="he-IL",
            timezone_id="Asia/Jerusalem",
        )
        page = context.new_page()
        print("→ opening groups-you've-joined page...")
        page.goto("https://www.facebook.com/groups/joins/", timeout=45_000)
        time.sleep(4)

        if "login" in page.url or "/checkpoint" in page.url:
            print(f"WARN: session not authenticated (url={page.url}). Re-capture the session.")
            browser.close()
            return 2

        # JS extractor: per group link, pull name (aria-label/text) + member-count text.
        extract_js = r"""() => {
          const skip = ['joins','feed','discover','create','category','your_groups'];
          const seen = {};
          document.querySelectorAll('a[href*="/groups/"]').forEach(a => {
            const m = (a.getAttribute('href')||'').match(/\/groups\/([A-Za-z0-9._-]+)/);
            if (!m) return;
            const slug = m[1];
            if (skip.includes(slug) || slug.length < 2) return;
            let name = (a.getAttribute('aria-label')||'').trim();
            if (!name) name = (a.textContent||'').trim().split('\n')[0].trim();
            let members = null, el = a;
            for (let i=0;i<5 && el;i++){
              const t = el.textContent||'';
              const mm = t.match(/([\d.,]+)\s*(тыс\.?|K|אלף|mil)?\s*(участник|member|חבר|員)/i);
              if (mm){ members = mm[0].trim(); break; }
              el = el.parentElement;
            }
            if (!seen[slug] || (name && !(seen[slug].name))) seen[slug] = {id:slug, name, members};
          });
          return Object.values(seen);
        }"""

        # Lazy-scroll to load the whole list, merging extractions each pass.
        groups: dict[str, dict] = {}
        last_count, stable = 0, 0
        for _ in range(45):
            for g in page.evaluate(extract_js):
                slug = g["id"]
                if slug not in groups or (g.get("name") and not groups[slug].get("name")):
                    groups[slug] = g
                if g.get("members") and not groups[slug].get("members"):
                    groups[slug]["members"] = g["members"]
            if len(groups) == last_count:
                stable += 1
                if stable >= 3:
                    break
            else:
                stable = 0
            last_count = len(groups)
            page.mouse.wheel(0, 3200)
            time.sleep(1.5)

        rows = [
            {"group_id": slug, "name": (g.get("name") or ""), "members_raw": g.get("members"),
             "url": f"https://www.facebook.com/groups/{slug}/"}
            for slug, g in groups.items()
        ]
        out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n✓ found {len(rows)} groups → {out_path}")
        for r in rows[:15]:
            print(f"   · {r['name'] or '(no name)'}  [{r['group_id']}]")
        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
