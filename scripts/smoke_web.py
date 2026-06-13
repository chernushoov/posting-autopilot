#!/usr/bin/env python3
"""Low-conflict smoke check for the local Recruit Autopilot pilot operator flow."""

from __future__ import annotations

import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from http.cookiejar import CookieJar


BASE_URL = os.getenv("SMOKE_BASE_URL", "http://localhost:8080")
ROOT = Path(__file__).resolve().parents[1]


def load_env_value(key: str) -> str | None:
    for filename in (".env.runtime", ".env"):
        path = ROOT / filename
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            current_key, value = line.split("=", 1)
            if current_key.strip() == key:
                return value.strip().strip("'").strip('"')
    return None


LOGIN = os.getenv("SMOKE_ADMIN_LOGIN") or load_env_value("ADMIN_LOGIN") or "admin"
PASSWORD = os.getenv("SMOKE_ADMIN_PASSWORD") or load_env_value("ADMIN_PASSWORD") or "admin123"
PREFERRED_COMPANY_NAME = os.getenv("SMOKE_COMPANY_NAME", "TopStaff Israel")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def expect_contains(body: str, needle: str, context: str) -> None:
    if needle not in body:
        fail(f"{context} missing expected text: {needle!r}")


def open_text(opener: urllib.request.OpenerDirector, url: str, data: bytes | None = None) -> tuple[int, str]:
    request = urllib.request.Request(url, data=data)
    with opener.open(request, timeout=10) as response:
        status = getattr(response, "status", response.getcode())
        body = response.read().decode("utf-8", errors="replace")
        return status, body


def extract_csrf_token(body: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', body)
    if not match:
        fail("login page missing csrf_token")
    return match.group(1)


def expect_any_contains(body: str, needles: list[str], context: str) -> None:
    for needle in needles:
        if needle in body:
            return
    fail(f"{context} missing all expected markers: {needles!r}")


def maybe_select_company(opener: urllib.request.OpenerDirector, body: str) -> tuple[int, str]:
    if "/companies/switch/" not in body:
        return 200, body

    company_cards = re.findall(
        r'font-weight:600;font-size:15px">([^<]+)</div>.*?href="/companies/switch/(\d+)"',
        body,
        flags=re.S,
    )
    if not company_cards:
        fail("company selector opened but no switch links were found")

    chosen_company_id = None
    for name, company_id in company_cards:
        if name.strip() == PREFERRED_COMPANY_NAME:
            chosen_company_id = company_id
            break
    if chosen_company_id is None:
        chosen_company_id = company_cards[0][1]

    return open_text(opener, f"{BASE_URL}/companies/switch/{chosen_company_id}")


def main() -> None:
    cookie_jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    status, body = open_text(opener, f"{BASE_URL}/login")
    if status != 200:
        fail(f"/login returned {status}")
    expect_contains(body, "Posting<em>Autopilot</em>", "/login")
    expect_contains(body, 'name="login"', "/login")
    expect_contains(body, 'name="password"', "/login")
    csrf_token = extract_csrf_token(body)

    login_payload = urllib.parse.urlencode(
        {"login": LOGIN, "password": PASSWORD, "csrf_token": csrf_token}
    ).encode()
    status, body = open_text(opener, f"{BASE_URL}/login", login_payload)
    if status != 200:
        fail(f"POST /login returned {status}")
    if "/companies/switch/" in body:
        status, body = maybe_select_company(opener, body)
    expect_any_contains(body, ["Default Company", "TopStaff Israel", "/campaigns/", "/vacancies/"], "login redirect")

    route_expectations = {
        "/dashboard": ["Posting<em>Autopilot</em>", "Telegram", "Facebook"],
        "/vacancies/": ["Concrete worker", "Listings", "מודעות", "Объявления"],
        "/sources/": ["Pilot Destination Rules", "Telegram", "Facebook"],
        "/campaigns/": [
            "Warehouse — RU channels",
            "Cleaning — HE channels",
            "Telegram",
            "Facebook",
            "קמפיינים",
        ],
        "/connect/telegram": ["Telegram", "API", "Phone"],
        "/connect/facebook": ["Facebook", "Meta", "Step 1"],
    }

    for route, expected_markers in route_expectations.items():
        status, body = open_text(opener, f"{BASE_URL}{route}")
        if "/companies/switch/" in body:
            _, _ = maybe_select_company(opener, body)
            status, body = open_text(opener, f"{BASE_URL}{route}")
        if status != 200:
            fail(f"{route} returned {status}")
        expect_any_contains(body, expected_markers, route)
        print(f"OK: {route}")

    print("PASS: local pilot web smoke completed")


if __name__ == "__main__":
    main()
