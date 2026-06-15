import os

from flask import Blueprint, render_template, request, session
from common.i18n import ui

bp = Blueprint("pricing", __name__)

PLANS = {
    "ru": [
        {
            "name": "Стартер",
            "price": "299₪",
            "price_note": "/мес",
            "features": [
                "1 активная вакансия",
                "10 каналов (Telegram + Facebook)",
                "Автопостинг в Telegram",
                "Ручной режим Facebook",
                "AI-скрининг кандидатов",
                "Русский + Иврит + English",
                "14 дней бесплатно",
            ],
            "cta": "Попробовать бесплатно",
            "highlight": False,
        },
        {
            "name": "Про",
            "price": "899₪",
            "price_note": "/мес",
            "features": [
                "5 активных вакансий",
                "50 каналов (Telegram + Facebook)",
                "Автопостинг Telegram + ассистент FB",
                "AI-скрининг (расширенный)",
                "Планировщик кампаний",
                "Аналитика по каналам",
                "Приоритетная поддержка",
                "Шаблоны вакансий",
            ],
            "cta": "Начать сейчас",
            "highlight": True,
        },
        {
            "name": "Агентство",
            "price": "1999₪",
            "price_note": "/мес",
            "features": [
                "Безлимит вакансий",
                "Безлимит каналов",
                "Мульти-компания",
                "API доступ",
                "Google Maps поиск клиентов",
                "Автоматический outreach",
                "Персональный менеджер",
                "White-label опция",
            ],
            "cta": "Связаться",
            "highlight": False,
        },
    ],
    "he": [
        {
            "name": "סטארטר",
            "price": "299₪",
            "price_note": "/חודש",
            "features": [
                "משרה פעילה אחת",
                "10 ערוצים (טלגרם + פייסבוק)",
                "פרסום אוטומטי בטלגרם",
                "מצב ידני בפייסבוק",
                "סינון AI של מועמדים",
                "רוסית + עברית + אנגלית",
                "14 ימי ניסיון חינם",
            ],
            "cta": "נסה בחינם",
            "highlight": False,
        },
        {
            "name": "פרו",
            "price": "899₪",
            "price_note": "/חודש",
            "features": [
                "5 משרות פעילות",
                "50 ערוצים (טלגרם + פייסבוק)",
                "פרסום אוטומטי + עוזר FB",
                "סינון AI (מורחב)",
                "מתזמן קמפיינים",
                "אנליטיקה לפי ערוץ",
                "תמיכה בעדיפות",
                "תבניות משרות",
            ],
            "cta": "התחל עכשיו",
            "highlight": True,
        },
        {
            "name": "סוכנות",
            "price": "1999₪",
            "price_note": "/חודש",
            "features": [
                "ללא הגבלת משרות",
                "ללא הגבלת ערוצים",
                "ריבוי חברות",
                "גישת API",
                "חיפוש לקוחות ב-Google Maps",
                "פנייה אוטומטית",
                "מנהל אישי",
                "White-label",
            ],
            "cta": "צור קשר",
            "highlight": False,
        },
    ],
    "en": [
        {
            "name": "Starter",
            "price": "299₪",
            "price_note": "/mo",
            "features": [
                "1 active vacancy",
                "10 channels (Telegram + Facebook)",
                "Auto-post to Telegram",
                "Manual Facebook mode",
                "AI candidate screening",
                "Russian + Hebrew + English",
                "14 days free trial",
            ],
            "cta": "Try Free",
            "highlight": False,
        },
        {
            "name": "Pro",
            "price": "899₪",
            "price_note": "/mo",
            "features": [
                "5 active vacancies",
                "50 channels (Telegram + Facebook)",
                "Auto Telegram + FB assistant",
                "AI screening (advanced)",
                "Campaign scheduler",
                "Per-channel analytics",
                "Priority support",
                "Vacancy templates",
            ],
            "cta": "Start Now",
            "highlight": True,
        },
        {
            "name": "Agency",
            "price": "1999₪",
            "price_note": "/mo",
            "features": [
                "Unlimited vacancies",
                "Unlimited channels",
                "Multi-company",
                "API access",
                "Google Maps client finder",
                "Automated outreach",
                "Dedicated manager",
                "White-label option",
            ],
            "cta": "Contact Us",
            "highlight": False,
        },
    ],
}


PLAN_KEYS = ["starter", "pro", "agency"]


# ── Region-based pricing ─────────────────────────────────────────────────────
# Currency is a property of the VISITOR'S REGION (where they browse from), NOT of
# the UI language. A Russian-speaker in the US pays USD; an English-speaker in
# Israel pays ₪. Language only controls the surrounding copy.
REGION_PRICES = {
    "US": {"cur": "$", "pos": "pre",  "starter": 29,  "pro": 89,  "agency": 199},
    "IL": {"cur": "₪", "pos": "post", "starter": 299, "pro": 899, "agency": 1999},
    "GB": {"cur": "£", "pos": "pre",  "starter": 25,  "pro": 75,  "agency": 169},
    "EU": {"cur": "€", "pos": "pre",  "starter": 29,  "pro": 85,  "agency": 189},
}
DEFAULT_REGION = os.getenv("DEFAULT_PRICING_REGION", "US")

_EU_COUNTRIES = {"DE","FR","ES","IT","NL","BE","AT","IE","PT","FI","GR","LU","SK",
                 "SI","EE","LV","LT","CY","MT","PL","CZ","HU","RO","BG","HR","DK","SE"}
COUNTRY_TO_REGION = {"US": "US", "IL": "IL", "GB": "GB", **{c: "EU" for c in _EU_COUNTRIES}}


def _resolve_region() -> str:
    """Visitor's pricing region. Priority: explicit override (?region= / cookie)
    -> geo header from the proxy/CDN (CF-IPCountry / X-Country-Code) -> country
    subtag of Accept-Language -> DEFAULT_REGION. Independent of UI language."""
    override = (request.args.get("region") or request.cookies.get("pricing_region") or "").upper()
    if override in REGION_PRICES:
        return override
    cc = (request.headers.get("CF-IPCountry") or request.headers.get("X-Country-Code") or "").upper()
    if not cc:
        import re
        m = re.search(r"[A-Za-z]{2}-([A-Za-z]{2})", request.headers.get("Accept-Language", ""))
        if m:
            cc = m.group(1).upper()
    return COUNTRY_TO_REGION.get(cc, DEFAULT_REGION)


def _format_price(region: str, plan_key: str) -> str:
    p = REGION_PRICES.get(region, REGION_PRICES[DEFAULT_REGION])
    amount, cur = p[plan_key], p["cur"]
    return f"{cur}{amount}" if p["pos"] == "pre" else f"{amount}{cur}"


BILLING_ERROR_KEYS = {
    "billing_not_configured": "billing_not_configured_msg",
    "invalid_plan": "billing_invalid_plan_msg",
    "checkout_failed": "billing_checkout_failed_msg",
}


@bp.route("/pricing")
def pricing_page():
    lang = session.get("ui_lang", "he")
    region = _resolve_region()
    # Copy the per-language plans so we never mutate the module-global PLANS
    # (the old code appended checkout_url to the shared dicts on every request).
    plans = [dict(p) for p in PLANS.get(lang, PLANS["en"])]
    for i, plan in enumerate(plans):
        if i < len(PLAN_KEYS):
            key = PLAN_KEYS[i]
            plan["price"] = _format_price(region, key)   # region drives currency, not language
            plan["checkout_url"] = f"/billing/checkout/{key}"
    return render_template(
        "pricing.html",
        title="Pricing",
        plans=plans,
        pricing_region=region,
        trial_expired=request.args.get("trial_expired") == "1",
        billing_error_key=BILLING_ERROR_KEYS.get(request.args.get("error", "")),
        support_contact_url=os.getenv("SUPPORT_CONTACT_URL", ""),
    )
