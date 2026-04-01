"""Task 2.4: Email notifications for hot leads.

Sends email via SMTP when configured. Gracefully skips if SMTP not set up.
Environment variables:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@postingautopilot.com")


def is_email_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def send_hot_lead_email(
    to_email: str,
    listing_title: str,
    lead_name: str,
    lead_phone: str,
    lead_score: int,
    lead_summary: str,
    lead_telegram: str = "",
) -> bool:
    """Send email notification about a hot lead. Returns True if sent."""
    if not is_email_configured():
        logger.info("[email] SMTP not configured — skipping email notification")
        return False

    if not to_email:
        return False

    subject = f"🔥 Hot Lead: {listing_title}"

    body = f"""New hot lead for your listing!

Listing: {listing_title}
Name: {lead_name}
Phone: {lead_phone}
Score: {lead_score}
Summary: {lead_summary}
"""
    if lead_telegram:
        body += f"Telegram: @{lead_telegram}\n"
    if lead_phone:
        wa_num = lead_phone.lstrip('+').replace('-', '').replace(' ', '')
        if not wa_num.startswith('972') and wa_num.startswith('0'):
            wa_num = '972' + wa_num[1:]
        body += f"WhatsApp: https://wa.me/{wa_num}\n"

    body += "\n— Posting Autopilot"

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"[email] Hot lead email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"[email] Failed to send to {to_email}: {e}")
        return False
