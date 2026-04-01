#!/usr/bin/env python3
"""Low-conflict smoke check for the local Recruit Autopilot admin panel."""

from __future__ import annotations

import os
import sys
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar


BASE_URL = os.getenv("SMOKE_BASE_URL", "http://localhost:8000")
LOGIN = os.getenv("SMOKE_ADMIN_LOGIN", "admin")
PASSWORD = os.getenv("SMOKE_ADMIN_PASSWORD", "admin123")


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


def main() -> None:
    cookie_jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    status, body = open_text(opener, f"{BASE_URL}/login")
    if status != 200:
        fail(f"/login returned {status}")
    expect_contains(body, "Login", "/login")

    login_payload = urllib.parse.urlencode({"login": LOGIN, "password": PASSWORD}).encode()
    status, body = open_text(opener, f"{BASE_URL}/login", login_payload)
    if status != 200:
        fail(f"POST /login returned {status}")
    expect_contains(body, "Default Company", "login redirect")

    route_expectations = {
        "/companies/": "Default Company",
        "/vacancies/": "Concrete worker",
        "/sources/": "@example_group",
        "/campaigns/": "Campaigns",
        "/candidates/": "Candidates",
        "/ai/settings": "AI settings",
    }

    for route, expected in route_expectations.items():
        status, body = open_text(opener, f"{BASE_URL}{route}")
        if status != 200:
            fail(f"{route} returned {status}")
        expect_contains(body, expected, route)
        print(f"OK: {route}")

    print("PASS: local web smoke completed")


if __name__ == "__main__":
    main()
