"""Prospecting routes — Google Maps scraping + cold email outreach."""

import os
import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, session, url_for, current_app
from itsdangerous import URLSafeSerializer, BadSignature
from ..auth import require_company
from ..db import db_session
from ..models import Prospect, OutreachAttempt, ProspectStatus, OutreachStatus

bp = Blueprint("prospecting", __name__, url_prefix="/prospecting")

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "prospecting", "templates")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _valid_email(email: str) -> bool:
    return bool(email and _EMAIL_RE.match(email) and len(email) <= 300)


def _unsub_serializer() -> URLSafeSerializer:
    # Signed with the app secret; salt scopes the token to unsubscribe only.
    return URLSafeSerializer(current_app.config["SECRET_KEY"], salt="prospect-unsubscribe")


def _unsubscribe_url(prospect_id: int) -> str:
    token = _unsub_serializer().dumps(prospect_id)
    return url_for("prospecting.unsubscribe", token=token, _external=True)


@bp.route("/unsubscribe/<token>")
def unsubscribe(token: str):
    """Public, no-auth one-click unsubscribe (required by CAN-SPAM / GDPR)."""
    try:
        prospect_id = _unsub_serializer().loads(token)
    except BadSignature:
        return "Invalid unsubscribe link.", 400
    db = db_session()
    try:
        prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
        if prospect:
            prospect.status = ProspectStatus.unsubscribed
            db.commit()
    finally:
        db.close()
    return "You have been unsubscribed and will not receive further emails.", 200


@bp.route("/")
@require_company
def list_prospects():
    db = db_session()
    cid = session["current_company_id"]
    status_filter = request.args.get("status", "")

    q = db.query(Prospect).filter(Prospect.company_id == cid)
    if status_filter:
        q = q.filter(Prospect.status == status_filter)
    prospects = q.order_by(Prospect.created_at.desc()).limit(200).all()

    stats = {
        "total": db.query(Prospect).filter(Prospect.company_id == cid).count(),
        "with_email": db.query(Prospect).filter(Prospect.company_id == cid, Prospect.email.isnot(None)).count(),
        "contacted": db.query(Prospect).filter(Prospect.company_id == cid, Prospect.status == ProspectStatus.contacted).count(),
        "converted": db.query(Prospect).filter(Prospect.company_id == cid, Prospect.status == ProspectStatus.converted).count(),
    }
    db.close()
    return render_template(
        "prospecting.html",
        prospects=prospects,
        stats=stats,
        statuses=[s.value for s in ProspectStatus],
        current_status=status_filter,
        error=request.args.get("error"),
        message=request.args.get("message"),
    )


@bp.route("/scrape", methods=["POST"])
@require_company
def scrape():
    query = request.form.get("query", "").strip()
    if not query:
        return redirect("/prospecting/?error=empty_query")

    cid = session["current_company_id"]
    db = db_session()

    # Try to run scraper (may not be available in all environments)
    try:
        from prospecting.scraper import scrape_google_maps
        businesses = scrape_google_maps(query, timeout=120)
    except FileNotFoundError:
        # Scraper binary not available — allow manual entry mode
        db.close()
        return redirect("/prospecting/?error=scraper_not_installed")
    except Exception as e:
        db.close()
        return redirect(f"/prospecting/?error={str(e)[:100]}")

    # Extract emails from websites
    from prospecting.email_extractor import extract_emails_from_website

    added = 0
    for biz in businesses:
        # Deduplicate by name + company_id
        existing = db.query(Prospect).filter(
            Prospect.company_id == cid,
            Prospect.name == biz.name,
        ).first()
        if existing:
            continue

        emails = extract_emails_from_website(biz.website) if biz.website else []

        prospect = Prospect(
            company_id=cid,
            name=biz.name,
            category=biz.category,
            address=biz.address,
            phone=biz.phone,
            website=biz.website,
            email=emails[0] if emails else None,
            rating=str(biz.rating) if biz.rating else None,
            review_count=biz.review_count,
            city=_extract_city(biz.address),
            source_query=query,
        )
        db.add(prospect)
        added += 1

    db.commit()
    db.close()
    return redirect(f"/prospecting/?message=scraped_{added}_businesses")


@bp.route("/<int:prospect_id>/send", methods=["POST"])
@require_company
def send_email(prospect_id):
    db = db_session()
    cid = session["current_company_id"]
    lang = session.get("ui_lang", "ru")

    prospect = db.query(Prospect).filter(
        Prospect.id == prospect_id,
        Prospect.company_id == cid,
    ).first()

    if not prospect or not prospect.email:
        db.close()
        return redirect("/prospecting/?error=no_email")

    # Never email a scraped address that isn't even a valid email (it's used
    # verbatim as the SMTP recipient).
    if not _valid_email(prospect.email.strip()):
        db.close()
        return redirect("/prospecting/?error=invalid_email")

    # Respect opt-outs — never email an unsubscribed prospect.
    if prospect.status == ProspectStatus.unsubscribed:
        db.close()
        return redirect("/prospecting/?error=unsubscribed")

    # Check not already contacted (scoped to this prospect's tenant)
    existing = db.query(OutreachAttempt).filter(
        OutreachAttempt.prospect_id == prospect_id,
        OutreachAttempt.company_id == cid,
        OutreachAttempt.status == OutreachStatus.sent,
    ).first()
    if existing:
        db.close()
        return redirect("/prospecting/?error=already_sent")

    # Load template
    template_file = os.path.join(TEMPLATE_DIR, f"outreach_{lang}.html")
    if not os.path.isfile(template_file):
        template_file = os.path.join(TEMPLATE_DIR, "outreach_ru.html")
    with open(template_file, "r") as f:
        html_body = f.read()

    subject = {
        "ru": "Нужны рабочие на стройку? — Recruit Autopilot",
        "he": "צריכים עובדים לבנייה? — Recruit Autopilot",
        "en": "Need construction workers? — Recruit Autopilot",
    }.get(lang, "Need construction workers? — Recruit Autopilot")

    from prospecting.email_sender import send_outreach_email

    result = send_outreach_email(
        to_email=prospect.email,
        subject=subject,
        html_body=html_body,
        company_name=prospect.name,
        unsubscribe_url=_unsubscribe_url(prospect.id),
    )

    attempt = OutreachAttempt(
        prospect_id=prospect.id,
        company_id=cid,
        subject=subject,
        body_preview=prospect.name,
        sent_at=datetime.utcnow() if result.success else None,
        status=OutreachStatus.sent if result.success else OutreachStatus.failed,
        error_message=result.error if not result.success else None,
    )
    db.add(attempt)

    if result.success:
        prospect.status = ProspectStatus.contacted
        prospect.contacted_at = datetime.utcnow()

    db.commit()
    db.close()

    status = "sent" if result.success else f"failed_{result.error[:50]}"
    return redirect(f"/prospecting/?message={status}")


@bp.route("/add", methods=["POST"])
@require_company
def add_manual():
    """Manually add a prospect."""
    db = db_session()
    cid = session["current_company_id"]

    email = request.form.get("email", "").strip() or None
    if email and not _valid_email(email):
        db.close()
        return redirect("/prospecting/?error=invalid_email")

    prospect = Prospect(
        company_id=cid,
        name=request.form.get("name", "").strip(),
        phone=request.form.get("phone", "").strip() or None,
        email=email,
        website=request.form.get("website", "").strip() or None,
        city=request.form.get("city", "").strip() or None,
        category=request.form.get("category", "").strip() or None,
        source_query="manual",
    )
    db.add(prospect)
    db.commit()
    db.close()
    return redirect("/prospecting/?message=added")


ISRAEL_CITIES = [
    "Tel Aviv", "Haifa", "Jerusalem", "Beer Sheva", "Netanya",
    "Rishon LeZion", "Petah Tikva", "Ashdod", "Holon", "Ramat Gan",
    "Herzliya", "Kfar Saba", "Bat Yam", "Ashkelon", "Rehovot",
]

SCRAPE_QUERIES = [
    "construction companies {city}",
    "building contractors {city}",
    "renovation companies {city}",
]


@bp.route("/bulk-scrape", methods=["POST"])
@require_company
def bulk_scrape():
    """Scrape construction companies across all major Israeli cities."""
    cid = session["current_company_id"]
    cities = request.form.getlist("cities") or ISRAEL_CITIES[:5]
    # Bound the work per request so a single submit can't spin up an unbounded
    # number of 60s scrapes (resource exhaustion on the shared VPS).
    MAX_CITIES = 10
    if len(cities) > MAX_CITIES:
        cities = cities[:MAX_CITIES]
    query_template = request.form.get("query", "construction companies {city}")

    total_added = 0
    for city in cities:
        query = query_template.replace("{city}", city)
        try:
            from prospecting.scraper import scrape_google_maps
            businesses = scrape_google_maps(query, timeout=60)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("[bulk_scrape] scrape failed for '%s': %s", query, exc)
            continue

        from prospecting.email_extractor import extract_emails_from_website
        db = db_session()

        for biz in businesses:
            existing = db.query(Prospect).filter(
                Prospect.company_id == cid, Prospect.name == biz.name
            ).first()
            if existing:
                continue

            emails = extract_emails_from_website(biz.website) if biz.website else []
            scraped_email = next((e for e in emails if _valid_email(e.strip())), None)
            prospect = Prospect(
                company_id=cid,
                name=biz.name,
                category=biz.category,
                address=biz.address,
                phone=biz.phone,
                website=biz.website,
                email=scraped_email,
                rating=str(biz.rating) if biz.rating else None,
                review_count=biz.review_count,
                city=city,
                source_query=query,
            )
            db.add(prospect)
            total_added += 1

        db.commit()
        db.close()

    return redirect(f"/prospecting/?message=bulk_scraped_{total_added}_from_{len(cities)}_cities")


def _extract_city(address: str) -> str:
    """Try to extract city from address string."""
    if not address:
        return ""
    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 2:
        return parts[-2]  # typically city is second-to-last
    return parts[0]
