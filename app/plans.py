"""Plan tiers and limits — single source of truth for what each plan allows.

Numbers must match the marketing copy in app/routes/pricing.py:
Starter = 1 active vacancy / 10 destinations, Pro = 5 / 50, Agency = unlimited.
Trial gets Pro-level limits so the trial demonstrates real value.
"""
from .models import Source, Vacancy

PLAN_LIMITS = {
    "trial": {"vacancies": 5, "sources": 50},
    "starter": {"vacancies": 1, "sources": 10},
    "pro": {"vacancies": 5, "sources": 50},
    "agency": {"vacancies": None, "sources": None},  # unlimited
}

UPGRADE_HINT = "Upgrade your plan on the Pricing page to add more."

# Tiers that entitle the tenant to the paid service (auto-posting + lead delivery).
PAID_TIERS = {"starter", "pro", "agency"}
# Tiers that explicitly revoke service (set by billing webhooks on failure/cancel).
INACTIVE_TIERS = {"past_due", "cancelled", "canceled", "unpaid"}


def get_plan_tier(company) -> str:
    tier = (getattr(company, "plan_tier", None) or "trial").lower()
    return tier if tier in PLAN_LIMITS else "trial"


def is_billing_active(db, company) -> bool:
    """Whether a tenant may consume the paid service right now.

    Enforced in the *worker* (not only the Flask before_request gate) so a tenant
    whose trial expired, whose card failed, or who cancelled cannot keep getting
    scheduled posts + hot leads for free.

    - Paid tiers (starter/pro/agency): always active.
    - Revoked tiers (past_due/cancelled/unpaid): never active.
    - Trial/unknown: active while at least one owning user's trial has not expired.
      Companies with no self-service user (operator/admin-owned) are treated as
      active so the operator's own pilots are never silently frozen.
    """
    if company is None:
        return False
    raw = (getattr(company, "plan_tier", None) or "trial").lower()
    if raw in PAID_TIERS:
        return True
    if raw in INACTIVE_TIERS:
        return False
    from datetime import datetime
    from .models import User
    users = db.query(User).filter(User.company_id == company.id, User.is_active == True).all()
    if not users:
        return True
    now = datetime.utcnow()
    return any(u.trial_expires_at is None or u.trial_expires_at > now for u in users)


def _limit(company, key: str):
    return PLAN_LIMITS[get_plan_tier(company)][key]


def vacancy_slots_left(db, company):
    """Remaining active-vacancy slots. None = unlimited."""
    limit = _limit(company, "vacancies")
    if limit is None:
        return None
    used = (
        db.query(Vacancy)
        .filter(Vacancy.company_id == company.id, Vacancy.is_active == True)
        .count()
    )
    return max(limit - used, 0)


def source_slots_left(db, company):
    """Remaining active-destination slots. None = unlimited."""
    limit = _limit(company, "sources")
    if limit is None:
        return None
    used = (
        db.query(Source)
        .filter(Source.company_id == company.id, Source.is_active == True)
        .count()
    )
    return max(limit - used, 0)
