"""Provider-agnostic transactional email. Works the moment the owner adds creds:
  - RESEND_API_KEY  -> Resend HTTP API (recommended, simplest)
  - else SMTP_HOST/PORT/USER/PASSWORD -> SMTP
  - else dev/no-provider: log "would send" and return False (nothing crashes).
MAIL_FROM sets the sender (default noreply@posting-autopilot.com).
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

DEFAULT_FROM = "Posting Autopilot <noreply@posting-autopilot.com>"


def mail_configured() -> bool:
    return bool(os.getenv("RESEND_API_KEY", "").strip() or os.getenv("SMTP_HOST", "").strip())


def send_email(to: str, subject: str, html: str, text: str | None = None) -> bool:
    """Best-effort send. Returns True on success, False otherwise (never raises)."""
    frm = os.getenv("MAIL_FROM", "").strip() or DEFAULT_FROM

    # 1) Resend
    key = os.getenv("RESEND_API_KEY", "").strip()
    if key:
        try:
            import requests
            r = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"from": frm, "to": [to], "subject": subject, "html": html, "text": text or ""},
                timeout=15,
            )
            if r.status_code in (200, 201):
                return True
            logger.error(f"[mail] resend {r.status_code}: {r.text[:200]}")
            return False
        except Exception as e:
            logger.error(f"[mail] resend error: {e}")
            return False

    # 2) SMTP
    host = os.getenv("SMTP_HOST", "").strip()
    if host:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = frm
            msg["To"] = to
            if text:
                msg.attach(MIMEText(text, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))
            port = int(os.getenv("SMTP_PORT", "587"))
            with smtplib.SMTP(host, port, timeout=20) as s:
                s.starttls()
                user = os.getenv("SMTP_USER", "").strip()
                if user:
                    s.login(user, os.getenv("SMTP_PASSWORD", "").strip())
                s.sendmail(frm, [to], msg.as_string())
            return True
        except Exception as e:
            logger.error(f"[mail] smtp error: {e}")
            return False

    # 3) No provider configured
    logger.warning(f"[mail] NO PROVIDER set — would send to {to}: {subject!r}")
    return False
