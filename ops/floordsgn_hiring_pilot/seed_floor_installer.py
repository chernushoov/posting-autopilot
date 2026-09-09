"""
FLOORdsgn — boevaya vakansiya "ukladchik dekorativnyh polov" (HE + RU).

Dogfood-pilot: my sami nanimaem masterov na poly cherez posting-autopilot.
Eto RODNOY keys dvizhka (recruitment) — postit v TG-gruppy, skrining v lichke bota,
skoring + 🔥-uvedomlenie operatoru.

Zapusk (na mashine, gde zhivyot prilozhenie):
    python -m scripts.migrate          # ensure tables
    python ops/floordsgn_hiring_pilot/seed_floor_installer.py

Idempotenten: povtornyy zapusk ne dublirует zapisi.

!!! PERED ZAPUSKOM PROVERIT' / ZAPOLNIT' polya s <<...>>:
    - salary_text (oplata)
    - whatsapp_number / contact_text (telefon kompanii)
    - city (esli ne Tel Aviv)
    - tochnaya specializaciya (mikrocement / epoksid / beton / plitka / parket)
"""
import json
import os
import sys

# allow running both as module and as a file from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import engine, db_session  # noqa: E402
from app.models import Base, Company, Vacancy, Source, Language  # noqa: E402

COMPANY_NAME = "FLOORdsgn"

# ---------------------------------------------------------------------------
# Screening questions (bot asks them in order, FSM). Keep 4 — short funnel.
# ---------------------------------------------------------------------------
SCREENING_RU = [
    "Какой у вас опыт с декоративными полами / микроцементом / эпоксидкой / бетоном? (коротко)",
    "В каком городе вы сейчас и есть ли машина?",
    "Есть разрешение на работу / документы в Израиле?",
    "Когда можете приступить? Оставьте номер телефона — мастер свяжется.",
]
SCREENING_HE = [
    "מה הניסיון שלך בהתקנת רצפות דקורטיביות / מיקרוצמנט / אפוקסי / בטון? (בקצרה)",
    "באיזו עיר את/ה נמצא/ת כרגע ויש לך רכב?",
    "יש לך אישור עבודה / מסמכים בישראל?",
    "מתי את/ה יכול/ה להתחיל? השאר/י מספר טלפון ונחזור אליך.",
]

HOT_RU = ("Есть реальный опыт декоративных/бетонных полов, есть машина, "
          "документы в порядке, может выйти скоро, оставил телефон.")
COLD_RU = "Нет опыта с полами, не в районе работ, нет документов, спам/грубость."
HOT_HE = ("ניסיון אמיתי ברצפות דקורטיביות/בטון, יש רכב, מסמכים תקינים, "
          "יכול/ה להתחיל בקרוב, השאיר/ה טלפון.")
COLD_HE = "אין ניסיון ברצפות, לא באזור העבודה, אין מסמכים, ספאם/גסות."

FAQ_RU = ("Работа: укладка декоративных полов (микроцемент/эпоксид/шлифованный бетон) "
          "на объектах в районе Тель-Авива. Постоянная занятость, поток проектов. "
          "Оплата по опыту. Нужны: опыт, аккуратность, желательно машина и документы.")
FAQ_HE = ("עבודה: התקנת רצפות דקורטיביות (מיקרוצמנט/אפוקסי/בטון מוחלק) "
          "באתרים באזור תל אביב. עבודה קבועה, זרם פרויקטים. "
          "שכר לפי ניסיון. דרוש: ניסיון, דיוק, רצוי רכב ומסמכים.")

BODY_RU = (
    "🔨 Требуется укладчик декоративных полов (микроцемент / эпоксид / шлифованный бетон)\n\n"
    "Компания FLOORdsgn ищет опытного мастера для работы на объектах в центре страны "
    "(Тель-Авив и окрестности).\n\n"
    "Что важно:\n"
    "• опыт укладки декоративных полов / микроцемента / эпоксидки / бетона\n"
    "• права и машина (большой плюс)\n"
    "• разрешение на работу / документы в порядке\n"
    "• аккуратность и ответственность\n\n"
    "Что предлагаем:\n"
    "• постоянную работу и поток объектов\n"
    "• хорошие условия для подходящих\n"
    "• профессиональную команду\n\n"
    "Интересно? Жми — свяжемся 👇"
)
BODY_HE = (
    "🔨 דרוש/ה מתקין/ת רצפות דקורטיביות (מיקרוצמנט / אפוקסי / בטון מוחלק)\n\n"
    "חברת FLOORdsgn מחפשת בעל/ת מקצוע מנוסה לעבודה באתרים באזור המרכז "
    "(תל אביב והסביבה).\n\n"
    "מה אנחנו מחפשים:\n"
    "• ניסיון בהתקנת רצפות דקורטיביות / מיקרוצמנט / אפוקסי / בטון\n"
    "• רישיון נהיגה ורכב (יתרון משמעותי)\n"
    "• אישור עבודה / מסמכים תקינים\n"
    "• עבודה מסודרת, אחריות ודיוק\n\n"
    "מה אנחנו מציעים:\n"
    "• עבודה קבועה ופרויקטים שוטפים\n"
    "• תנאים טובים למתאימים\n"
    "• צוות מקצועי\n\n"
    "מעוניין/ת? לחץ/י ונחזור אליך 👇"
)


def get_or_create_company(db):
    c = db.query(Company).filter(
        Company.owner_id == "admin_owner", Company.name == COMPANY_NAME
    ).first()
    if c:
        return c
    c = Company(owner_id="admin_owner", name=COMPANY_NAME,
                description="FLOORdsgn — наём мастеров на декоративные полы")
    c.ai_positive_prompt = (
        "Будь вежливым, коротким, по делу. Задавай только следующий вопрос. "
        "Цель: понять опыт мастера с полами, наличие машины/документов, готовность выйти "
        "и получить номер телефона."
    )
    c.ai_negative_prompt = (
        "Не обещай конкретную зарплату. Не проси фото документов. Не груби. "
        "Не обсуждай конкурентов."
    )
    db.add(c)
    db.commit()
    return c


def upsert_vacancy(db, company_id, title, language, body, screening, faq, hot, cold):
    v = db.query(Vacancy).filter(
        Vacancy.company_id == company_id, Vacancy.title == title
    ).first()
    if v is None:
        v = Vacancy(company_id=company_id, title=title)
        db.add(v)
    v.language = language
    v.listing_type = "recruitment"
    v.city = "Tel Aviv"  # <<проверить/заменить если другой район>>
    v.body = body
    v.salary_text = "לפי ניסיון / по договорённости"  # <<заполнить реальную вилку>>
    v.schedule_text = "משרה מלאה / полная занятость"
    v.contact_text = "<<WhatsApp/телефон компании>>"
    v.whatsapp_number = ""  # <<972XXXXXXXXX без + для click-to-chat>>
    v.bot_introduction = (
        "Привет! Я помощник по найму мастеров на полы в FLOORdsgn. "
        "Задам пару коротких вопросов и передам мастеру."
        if language == Language.ru else
        "שלום! אני העוזר/ת לגיוס מתקיני רצפות ב-FLOORdsgn. "
        "כמה שאלות קצרות ואעביר הלאה."
    )
    v.bot_faq_knowledge = faq
    v.bot_qualifying_questions = json.dumps(screening, ensure_ascii=False)
    v.bot_hot_criteria = hot
    v.bot_cold_criteria = cold
    v.interview_questions_json = json.dumps(screening, ensure_ascii=False)
    v.is_active = True
    db.commit()
    return v


def main():
    Base.metadata.create_all(bind=engine)
    db = db_session()
    try:
        c = get_or_create_company(db)
        v_he = upsert_vacancy(db, c.id, "מתקין רצפות דקורטיביות / Floor installer (HE)",
                              Language.he, BODY_HE, SCREENING_HE, FAQ_HE, HOT_HE, COLD_HE)
        v_ru = upsert_vacancy(db, c.id, "Укладчик декоративных полов (RU)",
                              Language.ru, BODY_RU, SCREENING_RU, FAQ_RU, HOT_RU, COLD_RU)

        # Placeholder sources — REPLACE with real TG groups via web UI (/sources)
        # before launching. Do NOT auto-post to unknown groups.
        for ref, label in [
            ("<<@real_construction_jobs_group>>", "PLACEHOLDER — заменить на реальную группу"),
        ]:
            exists = db.query(Source).filter(
                Source.company_id == c.id, Source.tg_ref == ref
            ).first()
            if not exists:
                db.add(Source(company_id=c.id, tg_ref=ref, label=label, is_active=False))
        db.commit()

        print("OK FLOORdsgn hiring seed done.")
        print(f"   company_id = {c.id}  ({COMPANY_NAME})")
        print(f"   vacancy HE = {v_he.id}  -> apply: ?start=apply_{v_he.id}")
        print(f"   vacancy RU = {v_ru.id}  -> apply: ?start=apply_{v_ru.id}")
        print("   NEXT: 1) fill <<...>> fields  2) add REAL TG groups in /sources")
        print("         3) create a campaign  4) start it")
    finally:
        db.close()


if __name__ == "__main__":
    main()
