from copy import deepcopy

from flask import Blueprint, render_template, request, session

from ..config import Config
from common.i18n import ui

bp = Blueprint("pricing", __name__)

PLAN_KEYS = ["starter", "pro", "agency"]


def _trial_label(lang: str) -> str:
    days = Config.trial_days()
    if lang == "ru":
        return f"{days} дня бесплатно" if days in {2, 3, 4} else f"{days} дней бесплатно"
    if lang == "he":
        return f"{days} ימי ניסיון חינם"
    return f"{days} day free trial" if days == 1 else f"{days} days free trial"


PLANS = {
    "ru": [
        {
            "name": "Стартер",
            "price": "$99",
            "price_note": "/мес",
            "features": [
                "1 активная вакансия",
                "10 каналов (Telegram + Facebook)",
                "Автопостинг в Telegram",
                "Ручной режим Facebook",
                "AI-скрининг кандидатов",
                "Русский + Иврит + English",
                "__TRIAL__",
            ],
            "cta": "Попробовать бесплатно",
            "highlight": False,
        },
        {
            "name": "Про",
            "price": "$299",
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
            "price": "$499",
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
            "price": "$99",
            "price_note": "/חודש",
            "features": [
                "משרה פעילה אחת",
                "10 ערוצים (טלגרם + פייסבוק)",
                "פרסום אוטומטי בטלגרם",
                "מצב ידני בפייסבוק",
                "סינון AI של מועמדים",
                "רוסית + עברית + אנגלית",
                "__TRIAL__",
            ],
            "cta": "נסה בחינם",
            "highlight": False,
        },
        {
            "name": "פרו",
            "price": "$299",
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
            "price": "$499",
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
            "price": "$99",
            "price_note": "/mo",
            "features": [
                "1 active vacancy",
                "10 channels (Telegram + Facebook)",
                "Auto-post to Telegram",
                "Manual Facebook mode",
                "AI candidate screening",
                "Russian + Hebrew + English",
                "__TRIAL__",
            ],
            "cta": "Try Free",
            "highlight": False,
        },
        {
            "name": "Pro",
            "price": "$299",
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
            "price": "$499",
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


def _plans_for(lang: str):
    plans = deepcopy(PLANS.get(lang, PLANS["en"]))
    trial_copy = _trial_label(lang)
    for plan in plans:
        plan["features"] = [trial_copy if feature == "__TRIAL__" else feature for feature in plan["features"]]
    return plans


@bp.route("/pricing")
def pricing_page():
    lang = session.get("ui_lang", "he")
    plans = _plans_for(lang)
    # A signed-out visitor clicking a "Try free" plan must reach SIGNUP, not the Stripe
    # checkout (which @require_company bounces to the sign-in page — a dead end for a
    # brand-new user). Only authenticated trial users get the real upgrade checkout.
    signed_in = bool(session.get("is_admin") or session.get("user_id"))
    for i, plan in enumerate(plans):
        if i < len(PLAN_KEYS):
            if signed_in and Config.billing_enabled():
                plan["checkout_url"] = f"/billing/checkout/{PLAN_KEYS[i]}"
            elif signed_in:
                plan["checkout_url"] = "/pricing?billing=disabled"
            else:
                plan["checkout_url"] = "/register"
    return render_template(
        "pricing.html",
        title="Pricing",
        plans=plans,
        billing_disabled=request.args.get("billing") == "disabled" or request.args.get("error") == "billing_disabled",
    )
