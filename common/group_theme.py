"""Lightweight multilingual (HE/RU/EN) theme classifier for TG/FB group names.

Pure and dependency-free. Used READ-ONLY to tag groups by vertical for display
(so the cabinet can organize/colour groups by theme). Does NOT touch the
connect/sync flow, posting routing, or storage — purely a presentation helper.

Returns a vertical key whose i18n label key (vert.*) already exists in
app/static/i18n.js for all three languages, so it translates on language switch.
"""

# vertical key -> i18n label key (resolved client-side via PA_I18N.t)
THEME_LABEL_KEY = {
    "home": "vert.home",      # real estate / rentals
    "users": "vert.users",    # jobs / recruitment
    "car": "vert.car",        # auto
    "wrench": "vert.wrench",  # services
    "other": "vert.other",
}

# (vertical, [lowercased substrings]) — order = match priority. Hebrew has no case.
_KEYWORDS = [
    ("home", [
        'נדל"ן', "נדל״ן", "נדלן", "דירה", "דירות", "להשכרה", "למכירה", "נכס", "שכירות", "דיור", "סאבלט",
        "недвиж", "квартир", "аренд", "жиль", "снять", "сдат", "комнат", "ипотек", "сабленд",
        "real estate", "apartment", " rent", "property", "housing", "sublet", "realty", "for rent",
    ]),
    ("users", [
        "דרושים", "דרוש", "עבוד", "משרה", "משרות", "גיוס", "קריירה", "ג'וב", "ג׳וב",
        "ваканс", "работ", "сотрудник", "требуется", "подработ", "персонал", "найм", "карьер", "резюме",
        "job", "vacanc", "hiring", "recruit", "career", " work", "staff", "employ",
    ]),
    ("car", [
        "רכב", "אוטו", "מכונית", "גלגלים", "טרייד",
        "авто", "машин", "автомобил", "транспорт",
        " car", "cars", "vehicle", "motors", "autos",
    ]),
    ("wrench", [
        "שירות", "שיפוץ", "ניקיון", "הובלות", "חשמלאי", "אינסטלטור", "שרברב", "מקצוע", "תיקון",
        "услуг", "ремонт", "мастер", "уборк", "сантехник", "электрик", "переезд", "сервис",
        "service", "repair", "cleaning", "plumb", "electric", "moving", "handyman",
    ]),
]


def classify_theme(name: str) -> str:
    """Best-effort vertical for a group name. Falls back to 'other'."""
    s = (name or "").lower()
    if not s.strip():
        return "other"
    for vert, kws in _KEYWORDS:
        for kw in kws:
            if kw in s:
                return vert
    return "other"


def theme_label_key(name: str) -> str:
    """i18n label key (vert.*) for the group's classified theme."""
    return THEME_LABEL_KEY[classify_theme(name)]
