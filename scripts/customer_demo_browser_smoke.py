#!/usr/bin/env python3
"""Browser-level proof for the first-customer demo path.

The smoke is intentionally self-contained: it uses a temporary SQLite database,
starts the Flask app on an ephemeral localhost port, blocks external requests and
drives the customer flow through real forms in Chrome.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import threading
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_OUTPUT = Path(tempfile.gettempdir()) / "posting-autopilot-demo-evidence"
SYSTEM_CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
EXPECTED_SCREENSHOTS = [
    "01-register-desktop.png",
    "02-dashboard-desktop.png",
    "03-vacancy-desktop.png",
    "04-source-desktop.png",
    "05-campaign-desktop.png",
    "06-campaign-ready-desktop.png",
    "07-dashboard-mobile.png",
    "08-vacancies-mobile.png",
    "09-sources-mobile.png",
    "10-campaigns-mobile.png",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Screenshot/report directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--strict-mobile",
        action="store_true",
        help="Fail instead of warn when an operator page overflows at 390px.",
    )
    return parser.parse_args()


def configure_isolated_runtime(database_path: Path) -> None:
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"
    os.environ["FLASK_SECRET_KEY"] = "browser-demo-smoke-secret"
    os.environ["ADMIN_PASSWORD"] = "browser-demo-smoke-admin"
    os.environ["RECRUITBOT_AI_PROVIDER"] = "stub"
    os.environ["BILLING_ENABLED"] = "0"
    os.environ.pop("FORCE_HTTPS", None)


def chrome_launch_options(playwright) -> dict[str, str]:
    bundled = Path(playwright.chromium.executable_path)
    if bundled.is_file():
        return {"executable_path": str(bundled)}
    if SYSTEM_CHROME.is_file():
        return {"channel": "chrome"}
    return {}


def horizontal_overflow(page) -> tuple[int, dict[str, int]]:
    dimensions = page.evaluate(
        """() => ({
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        })"""
    )
    return max(dimensions["scrollWidth"] - dimensions["clientWidth"], 0), dimensions


def assert_no_horizontal_overflow(page, label: str) -> None:
    overflow, dimensions = horizontal_overflow(page)
    if overflow > 1:
        raise AssertionError(f"{label}: horizontal overflow {dimensions}")


def block_external_requests(context, base_url: str, blocked: list[str]) -> None:
    def route_request(route) -> None:
        if route.request.url.startswith(base_url):
            route.continue_()
            return
        blocked.append(route.request.url)
        route.abort()

    context.route("**/*", route_request)


def attach_failure_collectors(page, base_url: str, failures: list[str]) -> None:
    page.on(
        "console",
        lambda message: failures.append(f"console:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: failures.append(f"pageerror:{error}"))
    page.on(
        "requestfailed",
        lambda request: failures.append(
            f"requestfailed:{request.method} {request.url} {request.failure}"
        )
        if request.url.startswith(base_url)
        else None,
    )
    page.on(
        "response",
        lambda response: failures.append(
            f"http:{response.status} {response.request.method} {response.url}"
        )
        if response.url.startswith(base_url) and response.status >= 400
        else None,
    )


def run_desktop_flow(browser, base_url: str, output_dir: Path, failures: list[str], blocked: list[str]):
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    block_external_requests(context, base_url, blocked)
    page = context.new_page()
    attach_failure_collectors(page, base_url, failures)

    page.goto(f"{base_url}/set-lang/en")
    page.goto(f"{base_url}/register")
    page.locator('input[name="email"]').fill("browser-owner@example.com")
    page.locator('input[name="password"]').fill("browser-demo-pass")
    page.locator('input[name="company_name"]').fill("Browser Demo Customer")
    page.screenshot(path=output_dir / "01-register-desktop.png", full_page=True)
    page.locator('form button[type="submit"]').click()
    page.wait_for_url(f"{base_url}/dashboard")
    page.get_by_text("Browser Demo Customer", exact=False).first.wait_for()
    assert_no_horizontal_overflow(page, "dashboard desktop")
    page.screenshot(path=output_dir / "02-dashboard-desktop.png", full_page=True)

    page.locator('a[href="/vacancies/"]').first.click()
    page.locator('a[href="/vacancies/new"]').first.click()
    page.locator('input[name="title"]').fill("Warehouse Operator - Tel Aviv")
    page.locator('input[name="city"]').fill("Tel Aviv")
    page.locator('select[name="language"]').select_option("en")
    page.locator('textarea[name="body"]').fill("Stable full-time warehouse role.")
    page.locator("#wiz-next").click()
    page.locator('input[name="salary_text"]').fill("ILS 7,500-8,500")
    page.locator('input[name="schedule_text"]').fill("Sun-Thu")
    page.locator('input[name="contact_text"]').fill("Apply in the platform")
    page.locator('input[name="whatsapp_number"]').fill("0501234567")
    page.locator("#post-asset-override summary").click()
    page.locator('input[name="final_post_title"]').fill("Warehouse Operator")
    page.locator('textarea[name="final_post_body"]').fill(
        "Join a stable warehouse team in Tel Aviv."
    )
    page.locator('textarea[name="questions"]').fill(
        "Do you have warehouse experience?\nWhen can you start?"
    )
    page.locator("#wiz-next").click()
    page.locator('textarea[name="bot_qualifying_questions"]').fill(
        "Do you have warehouse experience?\nWhen can you start?"
    )
    page.screenshot(path=output_dir / "03-vacancy-desktop.png", full_page=True)
    page.locator("#wiz-submit").click()
    page.wait_for_url(
        lambda url: url.startswith(f"{base_url}/vacancies/")
        and url != f"{base_url}/vacancies/new"
    )
    page.get_by_text("Warehouse Operator", exact=False).first.wait_for()

    page.locator('a[href="/sources/"]').first.click()
    source_form = page.locator('form[action="/sources/new"]').first
    source_form.locator('select[name="platform"]').select_option("facebook")
    source_form.locator('select[name="destination_kind"]').select_option("group")
    source_form.locator('select[name="posting_mode"]').select_option("assisted_manual")
    source_form.locator('input[name="label"]').fill("QA Jobs Tel Aviv")
    source_form.locator('input[name="destination_url"]').fill(
        "https://www.facebook.com/groups/qa-demo-group"
    )
    source_form.locator('button[type="submit"]').click()
    page.wait_for_url(lambda url: url.startswith(f"{base_url}/sources/"))
    page.get_by_text("QA Jobs Tel Aviv", exact=True).wait_for()
    page.screenshot(path=output_dir / "04-source-desktop.png", full_page=True)

    page.locator('a[href="/campaigns/"]').first.click()
    page.locator('a[href="/campaigns/new"]').first.click()
    page.locator('input[name="name"]').fill("QA customer pilot")
    page.locator('input[name="interval_minutes"]').fill("180")
    page.locator('input[name="active_start_hour"]').fill("9")
    page.locator('input[name="active_end_hour"]').fill("19")
    page.locator('input[name="max_posts_per_day"]').fill("3")
    page.locator('input[name="source_ids"]').check()
    page.screenshot(path=output_dir / "05-campaign-desktop.png", full_page=True)
    campaign_form = page.locator(
        'form:has(input[name="name"]):has(input[name="source_ids"])'
    )
    form_contract = campaign_form.evaluate(
        """form => ({
          action: form.action,
          method: form.method,
          valid: form.checkValidity(),
          invalid: [...form.elements]
            .filter(element => !element.checkValidity())
            .map(element => ({name: element.name, message: element.validationMessage})),
          button: (() => {
            const button = form.querySelector('button[type="submit"]');
            return button && {
              disabled: button.disabled,
              connectedToForm: button.form === form,
              text: button.textContent.trim(),
            };
          })(),
        })"""
    )
    if not form_contract["valid"]:
        raise AssertionError(f"campaign form invalid before submit: {form_contract}")
    campaign_button = campaign_form.locator('button[type="submit"]')
    campaign_button.scroll_into_view_if_needed()
    # Keyboard activation exercises the same native submit contract without
    # depending on pixel hit-testing in whichever Chrome build is installed.
    campaign_button.press("Enter")
    page.wait_for_timeout(500)
    campaign_name = page.get_by_text("QA customer pilot", exact=True)
    if campaign_name.count() == 0:
        alerts = page.locator(".alert").all_inner_texts()
        body = page.locator("body").inner_text()[:500]
        page.screenshot(path=output_dir / "campaign-submit-failure.png", full_page=True)
        raise AssertionError(
            "campaign not visible after submit: "
            f"url={page.url} alerts={alerts} failures={failures} "
            f"form={form_contract} body={body!r}"
        )
    assert_no_horizontal_overflow(page, "campaigns desktop")
    page.screenshot(path=output_dir / "06-campaign-ready-desktop.png", full_page=True)

    storage_state = context.storage_state()
    context.close()
    return storage_state


def run_mobile_check(
    browser,
    base_url: str,
    output_dir: Path,
    storage_state,
    failures: list[str],
    blocked: list[str],
    warnings: list[str],
    strict_mobile: bool,
) -> None:
    context = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=1,
        is_mobile=True,
        storage_state=storage_state,
    )
    block_external_requests(context, base_url, blocked)
    page = context.new_page()
    attach_failure_collectors(page, base_url, failures)

    for index, (path, label) in enumerate(
        (
            ("/dashboard", "dashboard"),
            ("/vacancies/", "vacancies"),
            ("/sources/", "sources"),
            ("/campaigns/", "campaigns"),
        ),
        start=7,
    ):
        page.goto(f"{base_url}{path}")
        overflow, dimensions = horizontal_overflow(page)
        if overflow > 1:
            message = f"{label} mobile horizontal overflow: {dimensions}"
            (failures if strict_mobile else warnings).append(message)
        page.screenshot(path=output_dir / f"{index:02d}-{label}-mobile.png", full_page=True)

    context.close()


def verify_persistence() -> dict[str, object]:
    from app.db import db_session
    from app.models import Campaign, Company, Source, Vacancy

    db = db_session()
    try:
        company = db.query(Company).filter_by(name="Browser Demo Customer").one()
        vacancy = db.query(Vacancy).filter_by(
            company_id=company.id,
            title="Warehouse Operator - Tel Aviv",
        ).one()
        source = db.query(Source).filter_by(company_id=company.id, label="QA Jobs Tel Aviv").one()
        campaign = db.query(Campaign).filter_by(
            company_id=company.id,
            name="QA customer pilot",
        ).one()
        return {
            "company_id": company.id,
            "vacancy_id": vacancy.id,
            "source_id": source.id,
            "campaign_id": campaign.id,
            "source_mode": source.posting_mode,
            "campaign_running": campaign.is_running,
        }
    finally:
        db.close()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="posting-browser-smoke-") as temp_dir:
        configure_isolated_runtime(Path(temp_dir) / "demo.db")

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("ERROR: install the project requirements before running this smoke.", file=sys.stderr)
            return 2

        from app import create_app
        from werkzeug.serving import WSGIRequestHandler, make_server

        class QuietHandler(WSGIRequestHandler):
            def log(self, request_type, message, *args):
                return

        app = create_app()
        server = make_server("127.0.0.1", 0, app, request_handler=QuietHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        failures: list[str] = []
        blocked: list[str] = []
        warnings: list[str] = []

        try:
            with sync_playwright() as playwright:
                launch_options = chrome_launch_options(playwright)
                if not launch_options:
                    print(
                        "ERROR: Chrome is unavailable. Install Playwright Chromium or system Chrome.",
                        file=sys.stderr,
                    )
                    return 2
                browser = playwright.chromium.launch(headless=True, **launch_options)
                try:
                    storage_state = run_desktop_flow(
                        browser,
                        base_url,
                        output_dir,
                        failures,
                        blocked,
                    )
                    run_mobile_check(
                        browser,
                        base_url,
                        output_dir,
                        storage_state,
                        failures,
                        blocked,
                        warnings,
                        args.strict_mobile,
                    )
                finally:
                    browser.close()

            persistence = verify_persistence()
            if persistence["source_mode"] != "assisted_manual":
                failures.append(f"unsafe Facebook source mode: {persistence['source_mode']}")
            if persistence["campaign_running"]:
                failures.append("new campaign unexpectedly started external posting")
            missing_screenshots = [
                name for name in EXPECTED_SCREENSHOTS if not (output_dir / name).is_file()
            ]
            if missing_screenshots:
                failures.append(f"missing screenshots: {missing_screenshots}")

            report = {
                "ok": not failures,
                "flow": "signup -> vacancy -> Facebook source -> campaign",
                "external_requests_blocked": sorted(set(blocked)),
                "failures": failures,
                "warnings": warnings,
                "persistence": persistence,
                "screenshots": [
                    name for name in EXPECTED_SCREENSHOTS if (output_dir / name).is_file()
                ],
            }
            report_path = output_dir / "report.json"
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(json.dumps({**report, "report": str(report_path)}, indent=2))
            return 0 if report["ok"] else 1
        finally:
            server.shutdown()
            server_thread.join(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
