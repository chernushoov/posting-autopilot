from __future__ import annotations

from app.db import db_session
from app.models import Campaign, CampaignSource, Company, Source, Vacancy


TOPSTAFF_NAME = "TopStaff Israel"
FLOORDSGN_NAME = "FloorDSGN"
SOURCE_VACANCY_ID = 6
SOURCE_TELEGRAM_ID = 17
SOURCE_FACEBOOK_ID = 19
TARGET_CAMPAIGN_NAME = "TopStaff Worker Pilot — Concrete Floors"


def _copy_vacancy(target_company_id: int, source_vacancy: dict) -> Vacancy:
    db = db_session()
    existing = (
        db.query(Vacancy)
        .filter(Vacancy.company_id == target_company_id, Vacancy.title == source_vacancy["title"])
        .first()
    )
    if existing:
        vacancy = existing
    else:
        vacancy = Vacancy(company_id=target_company_id, title=source_vacancy["title"])
        db.add(vacancy)
        db.flush()

    vacancy.body = source_vacancy["body"]
    vacancy.city = source_vacancy["city"]
    vacancy.language = source_vacancy["language"]
    vacancy.salary_text = source_vacancy["salary_text"]
    vacancy.schedule_text = source_vacancy["schedule_text"]
    vacancy.contact_text = source_vacancy["contact_text"]
    vacancy.apply_url = source_vacancy["apply_url"]
    vacancy.final_post_title = source_vacancy["final_post_title"]
    vacancy.final_post_body = source_vacancy["final_post_body"]
    vacancy.interview_questions_json = source_vacancy["interview_questions_json"]
    vacancy.listing_type = source_vacancy["listing_type"]
    vacancy.bot_introduction = source_vacancy["bot_introduction"]
    vacancy.bot_faq_knowledge = source_vacancy["bot_faq_knowledge"]
    vacancy.bot_qualifying_questions = source_vacancy["bot_qualifying_questions"]
    vacancy.bot_hot_criteria = source_vacancy["bot_hot_criteria"]
    vacancy.bot_cold_criteria = source_vacancy["bot_cold_criteria"]
    vacancy.whatsapp_number = source_vacancy["whatsapp_number"]
    vacancy.image_path = source_vacancy["image_path"]
    vacancy.is_active = True
    db.commit()
    db.refresh(vacancy)
    db.close()
    return vacancy


def _copy_source(target_company_id: int, source_template: dict) -> Source:
    db = db_session()
    existing = (
        db.query(Source)
        .filter(
            Source.company_id == target_company_id,
            Source.tg_ref == source_template["tg_ref"],
            Source.platform == source_template["platform"],
        )
        .first()
    )
    if existing:
        source = existing
    else:
        source = Source(company_id=target_company_id, tg_ref=source_template["tg_ref"])
        db.add(source)
        db.flush()

    source.label = source_template["label"]
    source.source_type = source_template["source_type"]
    source.platform = source_template["platform"]
    source.destination_kind = source_template["destination_kind"]
    source.posting_mode = source_template["posting_mode"]
    source.destination_url = source_template["destination_url"]
    source.folder = source_template["folder"]
    source.last_check_ok = source_template["last_check_ok"]
    source.last_check_message = source_template["last_check_message"]
    source.last_post_at = None
    source.is_active = True
    db.commit()
    db.refresh(source)
    db.close()
    return source


def _ensure_campaign(target_company_id: int, vacancy_id: int, telegram_source_id: int) -> Campaign:
    db = db_session()
    campaign = (
        db.query(Campaign)
        .filter(Campaign.company_id == target_company_id, Campaign.name == TARGET_CAMPAIGN_NAME)
        .first()
    )
    if not campaign:
        campaign = Campaign(
            company_id=target_company_id,
            vacancy_id=vacancy_id,
            name=TARGET_CAMPAIGN_NAME,
        )
        db.add(campaign)
        db.flush()

    campaign.vacancy_id = vacancy_id
    campaign.interval_minutes = 360
    campaign.active_hours_json = '{"start": 9, "end": 19}'
    campaign.days_of_week_json = '[0, 1, 2, 3, 4, 5, 6]'
    campaign.max_posts_per_day = 10
    campaign.is_running = True

    link = (
        db.query(CampaignSource)
        .filter(CampaignSource.campaign_id == campaign.id, CampaignSource.source_id == telegram_source_id)
        .first()
    )
    if not link:
        db.add(CampaignSource(campaign_id=campaign.id, source_id=telegram_source_id))

    db.query(CampaignSource).filter(
        CampaignSource.campaign_id == campaign.id,
        CampaignSource.source_id != telegram_source_id,
    ).delete(synchronize_session=False)

    db.commit()
    db.refresh(campaign)
    db.close()
    return campaign


def _pause_wrong_floor_campaigns() -> list[int]:
    db = db_session()
    floordsgn = db.query(Company).filter(Company.name == FLOORDSGN_NAME).first()
    paused_ids: list[int] = []
    if floordsgn:
        campaigns = (
            db.query(Campaign)
            .filter(Campaign.company_id == floordsgn.id, Campaign.vacancy_id == SOURCE_VACANCY_ID, Campaign.is_running == True)
            .all()
        )
        for campaign in campaigns:
            campaign.is_running = False
            paused_ids.append(campaign.id)
        db.commit()
    db.close()
    return paused_ids


def main() -> None:
    db = db_session()
    topstaff = db.query(Company).filter(Company.name == TOPSTAFF_NAME).first()
    source_vacancy = db.query(Vacancy).filter(Vacancy.id == SOURCE_VACANCY_ID).first()
    source_telegram = db.query(Source).filter(Source.id == SOURCE_TELEGRAM_ID).first()
    source_facebook = db.query(Source).filter(Source.id == SOURCE_FACEBOOK_ID).first()
    if not topstaff or not source_vacancy or not source_telegram:
        missing = {
            "topstaff": bool(topstaff),
            "source_vacancy": bool(source_vacancy),
            "source_telegram": bool(source_telegram),
            "source_facebook": bool(source_facebook),
        }
        db.close()
        raise SystemExit(f"missing required seed entities: {missing}")

    source_vacancy_payload = {
        "title": source_vacancy.title,
        "body": source_vacancy.body,
        "city": source_vacancy.city,
        "language": source_vacancy.language,
        "salary_text": source_vacancy.salary_text,
        "schedule_text": source_vacancy.schedule_text,
        "contact_text": source_vacancy.contact_text,
        "apply_url": source_vacancy.apply_url,
        "final_post_title": source_vacancy.final_post_title,
        "final_post_body": source_vacancy.final_post_body,
        "interview_questions_json": source_vacancy.interview_questions_json,
        "listing_type": source_vacancy.listing_type,
        "bot_introduction": source_vacancy.bot_introduction,
        "bot_faq_knowledge": source_vacancy.bot_faq_knowledge,
        "bot_qualifying_questions": source_vacancy.bot_qualifying_questions,
        "bot_hot_criteria": source_vacancy.bot_hot_criteria,
        "bot_cold_criteria": source_vacancy.bot_cold_criteria,
        "whatsapp_number": source_vacancy.whatsapp_number,
        "image_path": source_vacancy.image_path,
    }
    source_telegram_payload = {
        "tg_ref": source_telegram.tg_ref,
        "label": source_telegram.label,
        "source_type": source_telegram.source_type,
        "platform": source_telegram.platform,
        "destination_kind": source_telegram.destination_kind,
        "posting_mode": source_telegram.posting_mode,
        "destination_url": source_telegram.destination_url,
        "folder": source_telegram.folder,
        "last_check_ok": source_telegram.last_check_ok,
        "last_check_message": source_telegram.last_check_message,
    }
    source_facebook_payload = None
    if source_facebook:
        source_facebook_payload = {
            "tg_ref": source_facebook.tg_ref,
            "label": source_facebook.label,
            "source_type": source_facebook.source_type,
            "platform": source_facebook.platform,
            "destination_kind": source_facebook.destination_kind,
            "posting_mode": source_facebook.posting_mode,
            "destination_url": source_facebook.destination_url,
            "folder": source_facebook.folder,
            "last_check_ok": source_facebook.last_check_ok,
            "last_check_message": source_facebook.last_check_message,
        }

    topstaff.is_active = True
    db.commit()
    target_company_id = topstaff.id
    db.close()

    vacancy = _copy_vacancy(target_company_id, source_vacancy_payload)
    telegram_source = _copy_source(target_company_id, source_telegram_payload)
    facebook_source = _copy_source(target_company_id, source_facebook_payload) if source_facebook_payload else None
    campaign = _ensure_campaign(target_company_id, vacancy.id, telegram_source.id)
    paused_floor_campaign_ids = _pause_wrong_floor_campaigns()

    print(
        {
            "company_id": target_company_id,
            "vacancy_id": vacancy.id,
            "telegram_source_id": telegram_source.id,
            "facebook_source_id": facebook_source.id if facebook_source else None,
            "campaign_id": campaign.id,
            "paused_floor_campaign_ids": paused_floor_campaign_ids,
        }
    )


if __name__ == "__main__":
    main()
