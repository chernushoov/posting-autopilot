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


def get_plan_tier(company) -> str:
    tier = (getattr(company, "plan_tier", None) or "trial").lower()
    return tier if tier in PLAN_LIMITS else "trial"


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
