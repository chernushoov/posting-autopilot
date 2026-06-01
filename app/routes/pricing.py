from flask import Blueprint, render_template, session
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


@bp.route("/pricing")
def pricing_page():
    lang = session.get("ui_lang", "he")
    plans = PLANS.get(lang, PLANS["en"])
    # A signed-out visitor clicking a "Try free" plan must reach SIGNUP, not the Stripe
    # checkout (which @require_company bounces to the sign-in page — a dead end for a
    # brand-new user). Only authenticated trial users get the real upgrade checkout.
    signed_in = bool(session.get("is_admin") or session.get("user_id"))
    for i, plan in enumerate(plans):
        if i < len(PLAN_KEYS):
            plan["checkout_url"] = f"/billing/checkout/{PLAN_KEYS[i]}" if signed_in else "/register"
    return render_template("pricing.html", title="Pricing", plans=plans)
