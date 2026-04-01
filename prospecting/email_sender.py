"""
Cold email sender with rate limiting and tracking.
Uses yagmail for Gmail SMTP or standard smtplib as fallback.
"""

import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass

SMTP_USER = os.environ.get("OUTREACH_SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("OUTREACH_SMTP_PASSWORD", "")
SMTP_HOST = os.environ.get("OUTREACH_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("OUTREACH_SMTP_PORT", "587"))
SEND_DELAY_SECONDS = int(os.environ.get("OUTREACH_SEND_DELAY", "30"))
FROM_NAME = os.environ.get("OUTREACH_FROM_NAME", "Recruit Autopilot")


@dataclass
class SendResult:
    success: bool
    error: str = ""


def send_outreach_email(
    to_email: str,
    subject: str,
    html_body: str,
    company_name: str = "",
    unsubscribe_url: str = "",
) -> SendResult:
    """
    Send a single outreach email via SMTP.
    Personalizes {{COMPANY_NAME}} in subject and body.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        return SendResult(success=False, error="SMTP credentials not configured")

    # Personalize template
    subject = subject.replace("{{COMPANY_NAME}}", company_name)
    html_body = html_body.replace("{{COMPANY_NAME}}", company_name)

    # Add unsubscribe footer
    if unsubscribe_url:
        html_body += (
            f'<hr style="margin-top:30px;border:none;border-top:1px solid #ddd">'
            f'<p style="font-size:11px;color:#999">'
            f'<a href="{unsubscribe_url}">Unsubscribe</a></p>'
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return SendResult(success=True)
    except smtplib.SMTPRecipientsRefused as e:
        return SendResult(success=False, error=f"recipient refused: {e}")
    except smtplib.SMTPAuthenticationError:
        return SendResult(success=False, error="SMTP auth failed — check app password")
    except Exception as e:
        return SendResult(success=False, error=str(e)[:200])


def send_bulk_with_rate_limit(
    emails: list[dict],
    delay: int = SEND_DELAY_SECONDS,
) -> list[dict]:
    """
    Send multiple emails with rate limiting.
    Each item: {to, subject, html_body, company_name}
    Returns list of {to, success, error}.
    """
    results = []
    for i, item in enumerate(emails):
        if i > 0:
            time.sleep(delay)
        result = send_outreach_email(
            to_email=item["to"],
            subject=item["subject"],
            html_body=item["html_body"],
            company_name=item.get("company_name", ""),
        )
        results.append({
            "to": item["to"],
            "success": result.success,
            "error": result.error,
        })
    return results
