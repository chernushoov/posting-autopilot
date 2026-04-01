"""
Extract email addresses from business websites.
Simple HTTP GET + regex approach — no browser automation.
"""

import re
import requests

EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
SKIP_EMAILS = {"example@example.com", "info@example.com", "noreply@", "no-reply@", "wixpress.com", "sentry.io"}
REQUEST_TIMEOUT = 10


def extract_emails_from_website(url: str) -> list[str]:
    """
    Fetch a website and extract email addresses from HTML.
    Returns deduplicated list of emails, most likely contact emails first.
    """
    if not url or not url.startswith("http"):
        return []

    try:
        resp = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (compatible; RecruitBot/1.0)"},
            allow_redirects=True,
        )
        resp.raise_for_status()
    except Exception:
        return []

    raw_emails = EMAIL_REGEX.findall(resp.text)
    cleaned = []
    seen = set()
    for email in raw_emails:
        email_lower = email.lower()
        if email_lower in seen:
            continue
        if any(skip in email_lower for skip in SKIP_EMAILS):
            continue
        if email_lower.endswith((".png", ".jpg", ".gif", ".svg", ".css", ".js")):
            continue
        seen.add(email_lower)
        cleaned.append(email)

    # Prioritize: info@, contact@, office@ first
    def _priority(e: str) -> int:
        el = e.lower()
        if el.startswith("info@"):
            return 0
        if el.startswith("contact@"):
            return 1
        if el.startswith("office@"):
            return 2
        if el.startswith("hr@"):
            return 3
        return 10

    cleaned.sort(key=_priority)
    return cleaned[:5]  # max 5 emails per site
