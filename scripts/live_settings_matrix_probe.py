#!/usr/bin/env python3

from __future__ import annotations

import json
import ssl
import sys
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, HTTPSHandler, Request, build_opener


ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_URL = "https://posting-autopilot-next.vercel.app"
LOGIN_PATH = "/login?next=/settings"
SETTINGS_PATH = "/settings"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_opener_with_cookies() -> tuple[object, CookieJar]:
    jar = CookieJar()
    context = ssl._create_unverified_context()
    opener = build_opener(HTTPCookieProcessor(jar), HTTPSHandler(context=context))
    opener.addheaders = [("User-Agent", "RecruitAutopilotProbe/1.0")]
    return opener, jar


def fetch(opener, url: str, data: dict | None = None) -> tuple[int, str, list[tuple[str, str]]]:
    payload = None
    headers = {}
    if data is not None:
        payload = urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = Request(url, data=payload, headers=headers, method="POST" if data is not None else "GET")
    try:
        with opener.open(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), body, list(resp.headers.items())
    except Exception as exc:
        status = getattr(exc, "code", 0) or 0
        body = ""
        headers = []
        if hasattr(exc, "read"):
            try:
                body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
        if hasattr(exc, "headers") and exc.headers:
            headers = list(exc.headers.items())
        return status, body or str(exc), headers


def headers_to_dict(items: list[tuple[str, str]]) -> dict[str, str]:
    return {k.lower(): v for k, v in items}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else BASE_URL
    stamp = now_iso()
    out_dir = ROOT_DIR / "ops" / "prelaunch_artifacts" / "live_settings_matrix" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    opener, _jar = build_opener_with_cookies()

    login_status, login_body, login_headers = fetch(opener, f"{base_url}{LOGIN_PATH}")
    write_text(out_dir / "login_get.html", login_body)

    login_post_status, login_post_body, login_post_headers = fetch(
        opener,
        f"{base_url}{LOGIN_PATH}",
        {
            "email": "demo@postingautopilot.local",
            "password": "demo123",
        },
    )
    write_text(out_dir / "login_post.html", login_post_body)
    write_text(out_dir / "login_post_headers.json", json.dumps(headers_to_dict(login_post_headers), indent=2, ensure_ascii=False) + "\n")

    cases = [
        ("full_payload", {
            "full_name": f"QA Matrix {stamp}",
            "timezone": "Asia/Jerusalem",
            "default_cta": f"Reply {stamp}",
            "posting_window": "11:00-17:00",
            "notifications_enabled": "on",
        }),
        ("full_name_only", {"full_name": f"QA Matrix Name {stamp}"}),
        ("timezone_only", {"timezone": "Asia/Jerusalem"}),
        ("default_cta_only", {"default_cta": f"Reply {stamp}"}),
        ("posting_window_only", {"posting_window": "11:00-17:00"}),
        ("notifications_only", {"notifications_enabled": "on"}),
        ("full_name_and_timezone", {"full_name": f"QA Matrix Combo {stamp}", "timezone": "Asia/Jerusalem"}),
        ("cta_and_window", {"default_cta": f"Reply {stamp}", "posting_window": "11:00-17:00"}),
    ]

    results = []
    for name, payload in cases:
        status, body, headers = fetch(opener, f"{base_url}{SETTINGS_PATH}", payload)
        case_dir = out_dir / name
        case_dir.mkdir(parents=True, exist_ok=True)
        write_text(case_dir / "response.html", body)
        write_text(case_dir / "headers.json", json.dumps(headers_to_dict(headers), indent=2, ensure_ascii=False) + "\n")
        results.append(
            {
                "case": name,
                "status_code": status,
                "ok": status in {200, 302},
                "payload": payload,
                "response_path": str(case_dir / "response.html"),
                "headers_path": str(case_dir / "headers.json"),
            }
        )

    summary = {
        "checked_at": stamp,
        "base_url": base_url,
        "login_get_status": login_status,
        "login_post_status": login_post_status,
        "cases": results,
    }
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if all(item["ok"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
