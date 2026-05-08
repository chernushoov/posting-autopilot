"""
FB group browser-automation poster.

Architecture (matches Israeli competitors fbzipper / Postify / FaceBoost):
- Uses Playwright with chromium in headless mode inside the worker container.
- Loads the operator's saved FB session (cookies + localStorage) from
  data/fb_sessions/<name>.json — captured one-time via scripts/fb_capture_session.py.
- Opens a target FB group URL, finds the composer, types the post, clicks Post.
- Captures a screenshot before/after publish for evidence.
- Returns structured result the worker writes into FacebookPostingQueueItem and
  FacebookPostingResult.

Anti-ban:
- Random typing delays (50-150ms per char) instead of paste.
- Random mouse-like waits between actions.
- Browser fingerprint matches a real macOS Chrome (UA, locale, timezone).
- Caller staggers between groups (5-10 min) — handled by worker scheduler,
  not this module.

Failure modes returned:
- not_logged_in       — session expired, operator must re-run capture script
- group_not_found     — URL 404 or redirected, operator should remove group
- composer_not_found  — FB UI changed or group disallows posts (selectors stale)
- post_blocked        — FB blocked the post mid-flight (rate limit / spam check)
- captcha             — FB threw a captcha challenge
- timeout             — generic Playwright timeout
"""
from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from playwright.sync_api import (
    Page,
    Playwright,
    sync_playwright,
    TimeoutError as PWTimeout,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SESSION_DIR = REPO_ROOT / "data" / "fb_sessions"
SCREENSHOT_DIR = REPO_ROOT / "data" / "fb_screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Tuneable timeouts
NAV_TIMEOUT_MS = 30_000
COMPOSER_OPEN_TIMEOUT_MS = 25_000
SUBMIT_TIMEOUT_MS = 45_000


@dataclass
class PostResult:
    ok: bool
    error_kind: Optional[str] = None
    error_message: Optional[str] = None
    final_url: Optional[str] = None
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    duration_seconds: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def session_path(session_name: str) -> Path:
    return SESSION_DIR / f"{session_name}.json"


def session_exists(session_name: str) -> bool:
    p = session_path(session_name)
    return p.exists() and p.stat().st_size > 1024


def screenshot_path(session_name: str, queue_item_id: int, suffix: str) -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    return SCREENSHOT_DIR / f"{session_name}_q{queue_item_id}_{ts}_{suffix}.png"


def _new_browser_and_context(p: Playwright, session_file: Path):
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ],
    )
    storage_state = json.loads(session_file.read_text(encoding="utf-8"))
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0.0.0 Safari/537.36"
        ),
        locale="he-IL",
        timezone_id="Asia/Jerusalem",
        storage_state=storage_state,
    )
    return browser, context


def _human_type(page: Page, locator, text: str) -> None:
    locator.click()
    for ch in text:
        locator.type(ch, delay=random.uniform(40, 140))
        if ch in "\n.,!?:;":
            page.wait_for_timeout(random.randint(80, 200))


def _detect_login_required(page: Page) -> bool:
    url = page.url or ""
    if "/login" in url or "/checkpoint" in url or url.endswith("facebook.com/"):
        try:
            login_form = page.locator('input[name="email"], input[name="pass"]')
            if login_form.count() > 0:
                return True
        except Exception:
            pass
    return False


def _find_composer_box(page: Page):
    """
    Try multiple selectors to find the composer textarea inside a group page.
    FB UI changes often. Best-effort fallback chain.
    """
    candidates = [
        # Hebrew "What's on your mind?" / "מה תרצה לפרסם?" composer
        'div[role="button"][aria-label*="כתוב"]',
        'div[role="button"][aria-label*="פרסם"]',
        'div[role="button"][aria-label*="Write"]',
        'div[role="button"][aria-label*="Create a public post"]',
        'div[role="button"][aria-label*="Create post"]',
        # The "Discussion" tab top composer (group context)
        'div[role="textbox"][contenteditable="true"]',
        'span:has-text("Write something")',
        'span:has-text("מה תרצה לפרסם")',
        'span:has-text("כתוב משהו")',
    ]
    for sel in candidates:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                return loc, sel
        except Exception:
            continue
    return None, None


def _find_active_textbox(page: Page):
    """
    After clicking the composer trigger, FB opens a modal with a real textbox.
    """
    selectors = [
        'div[role="dialog"] div[role="textbox"][contenteditable="true"]',
        'div[role="textbox"][contenteditable="true"]',
        'textarea[name="xc_message"]',
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=5_000)
            if loc.count() > 0:
                return loc, sel
        except Exception:
            continue
    return None, None


def _find_submit_button(page: Page):
    selectors = [
        'div[role="dialog"] div[role="button"][aria-label*="פרסם"]:not([aria-disabled="true"])',
        'div[role="dialog"] div[role="button"][aria-label*="Post"]:not([aria-disabled="true"])',
        'div[aria-label="פרסם"]:not([aria-disabled="true"])',
        'div[aria-label="Post"]:not([aria-disabled="true"])',
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                return loc, sel
        except Exception:
            continue
    return None, None


def post_to_group(
    *,
    session_name: str,
    group_url: str,
    text: str,
    queue_item_id: int = 0,
) -> PostResult:
    """Post `text` to the FB group at `group_url` using the saved session."""
    started = time.time()
    sess = session_path(session_name)
    if not session_exists(session_name):
        return PostResult(
            ok=False,
            error_kind="session_missing",
            error_message=(
                f"FB session '{session_name}' not found at {sess}. "
                "Operator must run scripts/fb_capture_session.py once."
            ),
        )

    notes: list[str] = []
    before_path = screenshot_path(session_name, queue_item_id, "before")
    after_path = screenshot_path(session_name, queue_item_id, "after")

    with sync_playwright() as p:
        browser, context = _new_browser_and_context(p, sess)
        try:
            page = context.new_page()
            page.set_default_timeout(NAV_TIMEOUT_MS)

            try:
                page.goto(group_url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
            except PWTimeout:
                notes.append("nav_timeout_dom")
                # Continue — sometimes the page is usable even after timeout.

            page.wait_for_timeout(random.randint(2500, 4000))

            if _detect_login_required(page):
                page.screenshot(path=str(before_path))
                return PostResult(
                    ok=False,
                    error_kind="not_logged_in",
                    error_message="FB session expired or not authenticated.",
                    final_url=page.url,
                    screenshot_before=str(before_path),
                    duration_seconds=time.time() - started,
                    notes=notes,
                )

            page.screenshot(path=str(before_path), full_page=False)

            composer_trigger, sel = _find_composer_box(page)
            if not composer_trigger:
                return PostResult(
                    ok=False,
                    error_kind="composer_not_found",
                    error_message="No composer button found on group page.",
                    final_url=page.url,
                    screenshot_before=str(before_path),
                    duration_seconds=time.time() - started,
                    notes=notes,
                )
            notes.append(f"composer_selector={sel}")
            try:
                composer_trigger.click(timeout=10_000)
            except Exception as exc:
                return PostResult(
                    ok=False,
                    error_kind="composer_click_failed",
                    error_message=str(exc),
                    final_url=page.url,
                    screenshot_before=str(before_path),
                    duration_seconds=time.time() - started,
                    notes=notes,
                )

            page.wait_for_timeout(random.randint(1500, 2800))

            textbox, t_sel = _find_active_textbox(page)
            if not textbox:
                return PostResult(
                    ok=False,
                    error_kind="textbox_not_found",
                    error_message="Composer dialog did not open or textbox missing.",
                    final_url=page.url,
                    screenshot_before=str(before_path),
                    duration_seconds=time.time() - started,
                    notes=notes,
                )
            notes.append(f"textbox_selector={t_sel}")

            try:
                _human_type(page, textbox, text)
            except Exception as exc:
                return PostResult(
                    ok=False,
                    error_kind="typing_failed",
                    error_message=str(exc),
                    final_url=page.url,
                    screenshot_before=str(before_path),
                    duration_seconds=time.time() - started,
                    notes=notes,
                )

            page.wait_for_timeout(random.randint(800, 1500))

            submit, s_sel = _find_submit_button(page)
            if not submit:
                return PostResult(
                    ok=False,
                    error_kind="submit_not_found",
                    error_message="Post / פרסם button not found or disabled.",
                    final_url=page.url,
                    screenshot_before=str(before_path),
                    duration_seconds=time.time() - started,
                    notes=notes,
                )
            notes.append(f"submit_selector={s_sel}")

            try:
                submit.click(timeout=15_000)
            except Exception as exc:
                return PostResult(
                    ok=False,
                    error_kind="submit_click_failed",
                    error_message=str(exc),
                    final_url=page.url,
                    screenshot_before=str(before_path),
                    duration_seconds=time.time() - started,
                    notes=notes,
                )

            try:
                page.wait_for_load_state("networkidle", timeout=SUBMIT_TIMEOUT_MS)
            except PWTimeout:
                notes.append("post_load_state_timeout")

            page.wait_for_timeout(random.randint(2500, 4500))

            page.screenshot(path=str(after_path), full_page=False)
            final_url = page.url

            try:
                blocked = page.locator(
                    'div[aria-label*="חסום"], div[aria-label*="block"], div:has-text("Action Blocked")'
                ).count()
            except Exception:
                blocked = 0

            try:
                captcha_present = page.locator('iframe[src*="captcha"], div:has-text("captcha")').count()
            except Exception:
                captcha_present = 0

            if blocked:
                return PostResult(
                    ok=False,
                    error_kind="post_blocked",
                    error_message="FB shows an Action Blocked / חסום notice after submit.",
                    final_url=final_url,
                    screenshot_before=str(before_path),
                    screenshot_after=str(after_path),
                    duration_seconds=time.time() - started,
                    notes=notes,
                )
            if captcha_present:
                return PostResult(
                    ok=False,
                    error_kind="captcha",
                    error_message="FB threw a captcha challenge mid-flow.",
                    final_url=final_url,
                    screenshot_before=str(before_path),
                    screenshot_after=str(after_path),
                    duration_seconds=time.time() - started,
                    notes=notes,
                )

            return PostResult(
                ok=True,
                final_url=final_url,
                screenshot_before=str(before_path),
                screenshot_after=str(after_path),
                duration_seconds=time.time() - started,
                notes=notes,
            )
        finally:
            try:
                context.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass


def smoke_session(session_name: str) -> dict:
    """
    Cheap check: open facebook.com with the saved session, take a screenshot,
    confirm we're not on /login. Use to verify session before queueing real posts.
    """
    started = time.time()
    sess = session_path(session_name)
    if not session_exists(session_name):
        return {"ok": False, "error": "session_missing", "path": str(sess)}

    out_path = SCREENSHOT_DIR / f"smoke_{session_name}_{int(time.time())}.png"
    with sync_playwright() as p:
        browser, context = _new_browser_and_context(p, sess)
        try:
            page = context.new_page()
            try:
                page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
            except PWTimeout:
                pass
            page.wait_for_timeout(2500)
            url = page.url
            page.screenshot(path=str(out_path), full_page=False)
            return {
                "ok": not _detect_login_required(page),
                "url": url,
                "screenshot": str(out_path),
                "duration_s": round(time.time() - started, 2),
            }
        finally:
            try:
                context.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass
