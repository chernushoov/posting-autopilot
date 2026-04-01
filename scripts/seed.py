import os, json
from app.db import engine, db_session
from app.models import Base, Company, Vacancy, Source, Language

def main():
    Base.metadata.create_all(bind=engine)
    db = db_session()

    # create default company
    c = db.query(Company).filter(Company.owner_id=="admin_owner", Company.name=="Default Company").first()
    if not c:
        c = Company(owner_id="admin_owner", name="Default Company", description="Seeded company")
        c.ai_positive_prompt = "Будь вежливым, коротким, дружелюбным. Задавай только следующий вопрос."
        c.ai_negative_prompt = "Не обещай зарплату. Не обсуждай конкурентов. Не проси личные документы публично."
        db.add(c); db.commit()

    # sample vacancy
    v = db.query(Vacancy).filter(Vacancy.company_id==c.id, Vacancy.title=="Concrete worker").first()
    if not v:
        v = Vacancy(company_id=c.id, title="Concrete worker", city="Tel Aviv",
                    body="Нужен работник на декоративный бетон/микротоппинг. Опыт желателен. Пиши в личку.",
                    interview_questions_json=json.dumps(["Опыт?","Город?","Документы?"], ensure_ascii=False))
        db.add(v); db.commit()

    # Hebrew vacancy
    v_he = db.query(Vacancy).filter(Vacancy.company_id==c.id, Vacancy.title=="רצף / Tiler").first()
    if not v_he:
        v_he = Vacancy(
            company_id=c.id, title="רצף / Tiler", city="תל אביב",
            language=Language.he,
            body="דרוש רצף מנוסה לעבודה באתרים בתל אביב. ניסיון של שנתיים לפחות.",
            interview_questions_json=json.dumps([
                "מה הניסיון שלך בעבודת ריצוף?",
                "באיזו עיר את/ה גר/ה?",
                "יש לך כלי עבודה משלך?",
                "מתי את/ה יכול/ה להתחיל?",
            ], ensure_ascii=False))
        db.add(v_he); db.commit()

    # sample source
    s = db.query(Source).filter(Source.company_id==c.id, Source.tg_ref=="@example_group").first()
    if not s:
        s = Source(company_id=c.id, tg_ref="@example_group", label="Example group")
        db.add(s); db.commit()

    db.close()
    print("Seed done. Login: admin / admin123")

if __name__ == "__main__":
    main()
