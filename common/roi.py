"""ROI estimate: how much manual work the auto-posting + screening replaced.

Time-saved is a transparent estimate, not a measurement: each automated post saves
roughly the minutes a human spends opening a group, pasting, and clearing a captcha;
each captured-and-scored response saves the minutes of reading and triaging it by
hand. The constants are deliberately conservative so the headline number under-promises.
"""
from __future__ import annotations

from sqlalchemy import func

MINUTES_PER_MANUAL_POST = 3
MINUTES_PER_MANUAL_RESPONSE = 5


def compute_roi(db, company_id: int) -> dict:
    """Return the ROI receipt for one company: posts published, responses captured,
    hot leads, and an estimated hours-saved figure. Read-only."""
    from app.models import PostingAttempt, Candidate

    posts_published = db.query(func.count(PostingAttempt.id)).filter(
        PostingAttempt.company_id == company_id,
        PostingAttempt.result_status == "posted",
    ).scalar() or 0
    responses = db.query(func.count(Candidate.id)).filter(
        Candidate.company_id == company_id
    ).scalar() or 0
    hot_leads = db.query(func.count(Candidate.id)).filter(
        Candidate.company_id == company_id,
        Candidate.classification == "hot",
    ).scalar() or 0

    minutes_saved = (
        posts_published * MINUTES_PER_MANUAL_POST
        + responses * MINUTES_PER_MANUAL_RESPONSE
    )
    hours_saved = round(minutes_saved / 60.0, 1)

    return {
        "posts_published": posts_published,
        "responses": responses,
        "hot_leads": hot_leads,
        "hours_saved": hours_saved,
    }
