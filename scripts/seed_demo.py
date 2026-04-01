"""
Seed script for demo-ready data.
Run: docker compose exec web python -m scripts.seed_demo
"""
import json
from datetime import datetime, timedelta
from app.db import engine, db_session
from app.models import (
    Base, Company, Vacancy, Source, Campaign, CampaignSource,
    Candidate, Language, SourceType, CandidateStatus, Tone
)


def main():
    Base.metadata.create_all(bind=engine)
    db = db_session()

    # --- Company ---
    c = db.query(Company).filter(Company.name == "TopStaff Israel").first()
    if not c:
        c = Company(
            owner_id="admin_owner",
            name="TopStaff Israel",
            description="Staffing agency — construction, logistics, cleaning",
            ai_positive_prompt="Be polite, concise, and professional. Ask only the next screening question. Do not promise salary or specific conditions.",
            ai_negative_prompt="Do not discuss competitors. Do not ask for personal documents in chat. Do not make hiring promises.",
            ai_tone=Tone.professional,
            ai_language=Language.auto,
            ai_greeting_template="Welcome! We're reviewing your application. Please answer a few short questions.",
            ai_rejection_template="Thank you for your time. Unfortunately, this vacancy is not the right fit at the moment. We'll keep your profile for future opportunities.",
            ai_success_template="Great news! You've passed the initial screening. A recruiter will contact you shortly.",
        )
        db.add(c)
        db.commit()

    # --- Vacancies ---
    v1 = db.query(Vacancy).filter(Vacancy.company_id == c.id, Vacancy.title == "Warehouse Worker — Ashdod").first()
    if not v1:
        v1 = Vacancy(
            company_id=c.id,
            title="Warehouse Worker — Ashdod",
            city="Ashdod",
            language=Language.ru,
            body=(
                "Требуется работник склада в Ашдоде.\n"
                "Полная ставка, 6 дней в неделю.\n"
                "Зарплата: от 6,500 ₪/мес.\n"
                "Опыт работы на складе — преимущество.\n\n"
                "Для подачи заявки — нажмите кнопку ниже."
            ),
            interview_questions_json=json.dumps([
                "Есть ли у вас опыт работы на складе? Если да, сколько лет?",
                "В каком городе вы проживаете?",
                "Есть ли у вас действующее разрешение на работу в Израиле?",
                "Когда вы можете приступить к работе?",
                "Готовы ли вы работать в ночные смены?"
            ], ensure_ascii=False)
        )
        db.add(v1)
        db.commit()

    v2 = db.query(Vacancy).filter(Vacancy.company_id == c.id, Vacancy.title == "עובד/ת ניקיון — תל אביב").first()
    if not v2:
        v2 = Vacancy(
            company_id=c.id,
            title="עובד/ת ניקיון — תל אביב",
            city="תל אביב",
            language=Language.he,
            body=(
                "דרוש/ה עובד/ת ניקיון למשרדים באזור תל אביב.\n"
                "משרה מלאה, ימים א׳-ה׳.\n"
                "שכר: החל מ-6,000 ₪/חודש.\n"
                "ניסיון — יתרון.\n\n"
                "לפרטים נוספים — לחצו למטה."
            ),
            interview_questions_json=json.dumps([
                "יש לך ניסיון בעבודות ניקיון? אם כן, כמה שנים?",
                "באיזו עיר את/ה גר/ה?",
                "יש לך אישור עבודה בישראל?",
                "מתי את/ה יכול/ה להתחיל?",
            ], ensure_ascii=False)
        )
        db.add(v2)
        db.commit()

    # --- Sources (Telegram groups) ---
    sources_data = [
        ("@rabotaisraeli", "Работа Израиль", SourceType.channel),
        ("@BROOTTO_Jobs", "BROOTTO — Работа в Израиле", SourceType.channel),
        ("@rabotacoil", "Rabota.co.il", SourceType.channel),
        ("@work_israel_apal", "A.P.AL — Работа", SourceType.channel),
        ("@avodahlcol", "עבודה לכל — דרושים", SourceType.channel),
    ]
    source_objects = []
    for tg_ref, label, stype in sources_data:
        s = db.query(Source).filter(Source.company_id == c.id, Source.tg_ref == tg_ref).first()
        if not s:
            s = Source(company_id=c.id, tg_ref=tg_ref, label=label, source_type=stype, last_check_ok=True, last_check_message="OK")
            db.add(s)
            db.commit()
        source_objects.append(s)

    # --- Campaigns ---
    camp1 = db.query(Campaign).filter(Campaign.company_id == c.id, Campaign.name == "Warehouse — RU channels").first()
    if not camp1:
        camp1 = Campaign(
            company_id=c.id,
            vacancy_id=v1.id,
            name="Warehouse — RU channels",
            interval_minutes=240,
            is_running=False,
        )
        db.add(camp1)
        db.commit()
        for s in source_objects[:4]:  # first 4 Russian channels
            cs = CampaignSource(campaign_id=camp1.id, source_id=s.id)
            db.add(cs)
        db.commit()

    camp2 = db.query(Campaign).filter(Campaign.company_id == c.id, Campaign.name == "Cleaning — HE channels").first()
    if not camp2:
        camp2 = Campaign(
            company_id=c.id,
            vacancy_id=v2.id,
            name="Cleaning — HE channels",
            interval_minutes=360,
            is_running=False,
        )
        db.add(camp2)
        db.commit()
        cs = CampaignSource(campaign_id=camp2.id, source_id=source_objects[4].id)
        db.add(cs)
        db.commit()

    # --- Sample candidates (for demo) ---
    now = datetime.utcnow()
    candidates_data = [
        {
            "full_name": "Алексей Петров",
            "tg_username": "aleksei_p",
            "tg_user_id": "100001",
            "language": "ru",
            "vacancy": v1,
            "status": CandidateStatus.passed,
            "score": 82,
            "summary": "3 years warehouse experience. Lives in Ashdod. Has work permit. Available immediately. Open to night shifts.",
            "chat_log": [
                {"role": "assistant", "text": "Добро пожаловать! Ответьте на несколько вопросов для отбора.", "ts": (now - timedelta(hours=5)).isoformat()},
                {"role": "user", "text": "Да, 3 года на складе в Ашдоде", "ts": (now - timedelta(hours=5, minutes=-1)).isoformat()},
                {"role": "assistant", "text": "✓ Принято. В каком городе вы проживаете?", "ts": (now - timedelta(hours=5, minutes=-1)).isoformat()},
                {"role": "user", "text": "Ашдод", "ts": (now - timedelta(hours=5, minutes=-2)).isoformat()},
                {"role": "assistant", "text": "✓ Принято. Есть ли действующее разрешение на работу?", "ts": (now - timedelta(hours=5, minutes=-2)).isoformat()},
                {"role": "user", "text": "Да, гражданство", "ts": (now - timedelta(hours=5, minutes=-3)).isoformat()},
                {"role": "assistant", "text": "✓ Принято. Когда можете приступить?", "ts": (now - timedelta(hours=5, minutes=-3)).isoformat()},
                {"role": "user", "text": "Хоть завтра", "ts": (now - timedelta(hours=5, minutes=-4)).isoformat()},
                {"role": "assistant", "text": "✓ Принято. Готовы работать в ночные смены?", "ts": (now - timedelta(hours=5, minutes=-4)).isoformat()},
                {"role": "user", "text": "Да, без проблем", "ts": (now - timedelta(hours=5, minutes=-5)).isoformat()},
                {"role": "assistant", "text": "Отлично! Вы прошли первичный отбор. Рекрутер свяжется с вами в ближайшее время.", "ts": (now - timedelta(hours=5, minutes=-5)).isoformat()},
            ],
        },
        {
            "full_name": "מריה כהן",
            "tg_username": "maria_k",
            "tg_user_id": "100002",
            "language": "he",
            "vacancy": v2,
            "status": CandidateStatus.passed,
            "score": 75,
            "summary": "2 years cleaning experience. Lives in Bat Yam. Has work permit. Can start next week.",
            "chat_log": [
                {"role": "assistant", "text": "שלום! אנא ענה/י על מספר שאלות סינון.", "ts": (now - timedelta(hours=3)).isoformat()},
                {"role": "user", "text": "שנתיים ניקיון במשרדים", "ts": (now - timedelta(hours=3, minutes=-1)).isoformat()},
                {"role": "assistant", "text": "✓ התקבל. באיזו עיר את/ה גר/ה?", "ts": (now - timedelta(hours=3, minutes=-1)).isoformat()},
                {"role": "user", "text": "בת ים", "ts": (now - timedelta(hours=3, minutes=-2)).isoformat()},
                {"role": "assistant", "text": "✓ התקבל. יש לך אישור עבודה בישראל?", "ts": (now - timedelta(hours=3, minutes=-2)).isoformat()},
                {"role": "user", "text": "כן, אזרחות", "ts": (now - timedelta(hours=3, minutes=-3)).isoformat()},
                {"role": "assistant", "text": "✓ התקבל. מתי את/ה יכול/ה להתחיל?", "ts": (now - timedelta(hours=3, minutes=-3)).isoformat()},
                {"role": "user", "text": "שבוע הבא", "ts": (now - timedelta(hours=3, minutes=-4)).isoformat()},
                {"role": "assistant", "text": "מצוין! עברת את הסינון הראשוני. מגייס ייצור איתך קשר בהקדם.", "ts": (now - timedelta(hours=3, minutes=-4)).isoformat()},
            ],
        },
        {
            "full_name": "Игорь Соколов",
            "tg_username": "igor_s",
            "tg_user_id": "100003",
            "language": "ru",
            "vacancy": v1,
            "status": CandidateStatus.rejected,
            "score": 30,
            "summary": "No warehouse experience. Lives in Haifa (far from Ashdod). No night shift availability.",
            "chat_log": [
                {"role": "assistant", "text": "Добро пожаловать! Ответьте на несколько вопросов для отбора.", "ts": (now - timedelta(hours=4)).isoformat()},
                {"role": "user", "text": "Нет, опыта нет", "ts": (now - timedelta(hours=4, minutes=-1)).isoformat()},
                {"role": "assistant", "text": "✓ Принято. В каком городе вы проживаете?", "ts": (now - timedelta(hours=4, minutes=-1)).isoformat()},
                {"role": "user", "text": "Хайфа", "ts": (now - timedelta(hours=4, minutes=-2)).isoformat()},
                {"role": "assistant", "text": "✓ Принято. Есть ли действующее разрешение на работу?", "ts": (now - timedelta(hours=4, minutes=-2)).isoformat()},
                {"role": "user", "text": "Да", "ts": (now - timedelta(hours=4, minutes=-3)).isoformat()},
                {"role": "assistant", "text": "✓ Принято. Когда можете приступить?", "ts": (now - timedelta(hours=4, minutes=-3)).isoformat()},
                {"role": "user", "text": "Через месяц", "ts": (now - timedelta(hours=4, minutes=-4)).isoformat()},
                {"role": "assistant", "text": "✓ Принято. Готовы работать в ночные смены?", "ts": (now - timedelta(hours=4, minutes=-4)).isoformat()},
                {"role": "user", "text": "Нет, только дневные", "ts": (now - timedelta(hours=4, minutes=-5)).isoformat()},
            ],
        },
        {
            "full_name": "Дмитрий Волков",
            "tg_username": "dima_v",
            "tg_user_id": "100004",
            "language": "ru",
            "vacancy": v1,
            "status": CandidateStatus.interviewing,
            "score": 65,
            "summary": "1 year experience. Lives in Rishon LeZion. Available in 2 weeks.",
            "chat_log": [
                {"role": "assistant", "text": "Добро пожаловать! Ответьте на несколько вопросов для отбора.", "ts": (now - timedelta(hours=2)).isoformat()},
                {"role": "user", "text": "Год на складе продуктов", "ts": (now - timedelta(hours=2, minutes=-1)).isoformat()},
                {"role": "assistant", "text": "✓ Принято. В каком городе вы проживаете?", "ts": (now - timedelta(hours=2, minutes=-1)).isoformat()},
                {"role": "user", "text": "Ришон Ле-Цион", "ts": (now - timedelta(hours=2, minutes=-2)).isoformat()},
                {"role": "assistant", "text": "✓ Принято. Есть ли действующее разрешение на работу?", "ts": (now - timedelta(hours=2, minutes=-2)).isoformat()},
                {"role": "user", "text": "Да, ВНЖ", "ts": (now - timedelta(hours=2, minutes=-3)).isoformat()},
            ],
        },
        {
            "full_name": "אורן לוי",
            "tg_username": "oren_l",
            "tg_user_id": "100005",
            "language": "he",
            "vacancy": v2,
            "status": CandidateStatus.new,
            "score": None,
            "summary": "",
            "chat_log": [
                {"role": "assistant", "text": "שלום! אנא ענה/י על מספר שאלות סינון.", "ts": (now - timedelta(hours=1)).isoformat()},
            ],
        },
    ]

    for cd in candidates_data:
        existing = db.query(Candidate).filter(
            Candidate.company_id == c.id,
            Candidate.tg_user_id == cd["tg_user_id"]
        ).first()
        if not existing:
            cand = Candidate(
                company_id=c.id,
                vacancy_id=cd["vacancy"].id,
                tg_user_id=cd["tg_user_id"],
                tg_username=cd["tg_username"],
                full_name=cd["full_name"],
                language=cd["language"],
                status=cd["status"],
                score=cd["score"],
                summary=cd["summary"],
                chat_log_json=json.dumps(cd["chat_log"], ensure_ascii=False),
            )
            db.add(cand)
    db.commit()

    print("Demo seed complete.")
    print(f"  Company: {c.name} (id={c.id})")
    print(f"  Vacancies: {v1.title}, {v2.title}")
    print(f"  Sources: {len(source_objects)}")
    print(f"  Campaigns: 2")
    print(f"  Candidates: {len(candidates_data)}")
    print("  Login: admin / admin123")
    db.close()


if __name__ == "__main__":
    main()
