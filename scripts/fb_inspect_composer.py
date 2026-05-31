#!/usr/bin/env python3
"""Inspect a FB group's live DOM to find the real post-composer trigger/box.

Loads the saved session, opens the group, waits for render, then dumps the
candidate composer elements (role=button aria-labels, contenteditable boxes,
"write something"-style text) so we can target the right selectors instead of
guessing. Read-only — never posts.

Run:  .venv-fb/bin/python scripts/fb_inspect_composer.py [group_url]
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.fb_browser_poster import session_path, _new_browser_and_context  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

GROUP = sys.argv[1] if len(sys.argv) > 1 else "https://www.facebook.com/groups/143128243021491/"

COMPOSER_RE = r"напиш|что у вас|опублик|создать публикац|начать обсужд|анонимн|write something|create.*post|כתוב|פרסם"

JS = r"""() => {
  const RE = /напиш|что у вас|опублик|создать публикац|начать обсужд|анонимн|write something|create.*post|כתוב|פרסם/i;
  const out = {allButtons: [], composerHits: [], editables: [], texts: []};
  document.querySelectorAll('[role="button"][aria-label]').forEach(el => {
    const al = el.getAttribute('aria-label') || '';
    out.allButtons.push(al);
    if (RE.test(al)) out.composerHits.push('aria=' + al);
  });
  document.querySelectorAll('[contenteditable="true"]').forEach(el => {
    out.editables.push({aria: el.getAttribute('aria-label'), ph: el.getAttribute('data-placeholder') || el.getAttribute('aria-placeholder'), role: el.getAttribute('role')});
  });
  document.querySelectorAll('span,div').forEach(el => {
    if (el.children.length) return;
    const t = (el.textContent || '').trim();
    if (t && t.length < 50 && RE.test(t)) out.texts.push(t);
  });
  out.allButtons = [...new Set(out.allButtons)].slice(0, 50);
  out.composerHits = [...new Set(out.composerHits)];
  out.texts = [...new Set(out.texts)].slice(0, 15);
  return out;
}"""


def dump(page, label):
    data = page.evaluate(JS)
    print(f"\n===== {label} =====")
    print("COMPOSER HITS:")
    for b in data["composerHits"]:
        print("   ★", b)
    print("composer-ish texts:")
    for t in data["texts"]:
        print("   ★", t)
    print("contenteditable boxes:")
    for e in data["editables"]:
        print("   •", json.dumps(e, ensure_ascii=False))
    print("ALL role=button aria-labels (first 50):")
    for b in data["allButtons"]:
        print("   ·", b)
    return data


def main():
    sess = session_path("floordsgn")
    with sync_playwright() as p:
        browser, context = _new_browser_and_context(p, sess)
        page = context.new_page()
        page.set_default_timeout(30000)
        page.goto(GROUP, wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_selector('div[role="feed"], div[role="main"]', timeout=25000)
        except Exception:
            print("(render wait timed out)")
        page.wait_for_timeout(4000)

        before = dump(page, "BEFORE any click (group landing)")

        # Try clicking the most promising composer trigger, then re-dump to see the modal.
        clicked = None
        for sel in [
            'div[role="button"][aria-label*="כתוב"]',
            'div[role="button"][aria-label*="פרסם"]',
            'div[role="button"][aria-label*="Write"]',
            'div[role="button"][aria-label*="Create"]',
        ]:
            loc = page.locator(sel).first
            if loc.count() > 0:
                try:
                    loc.click(timeout=8000)
                    clicked = sel
                    break
                except Exception as e:
                    print(f"(click {sel} failed: {e})")
        print(f"\n>>> clicked trigger: {clicked}")
        page.wait_for_timeout(3500)
        dump(page, "AFTER click (modal expected)")
        has_dialog = page.locator('div[role="dialog"]').count()
        dialog_box = page.locator('div[role="dialog"] [contenteditable="true"]').count()
        print(f"\ndialog present: {has_dialog} | dialog contenteditable: {dialog_box}")
        page.screenshot(path=str(REPO := Path(__file__).resolve().parent.parent / "data" / "fb_screenshots" / "inspect_after_click.png"), full_page=False)
        print("screenshot:", REPO)
        browser.close()


if __name__ == "__main__":
    main()
