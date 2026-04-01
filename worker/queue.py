import os
from datetime import datetime
from uuid import uuid4
from redis import Redis
from rq import Queue
from app.db import db_session
from app.models import Campaign, CampaignSource, PostingAttempt, Source, Vacancy

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(REDIS_URL)
q_default = Queue(os.getenv("RQ_DEFAULT_QUEUE", "default"), connection=redis_conn)

def enqueue_check_source(source_id: int):
    from .tasks import check_source_access
    return q_default.enqueue(check_source_access, source_id)

def enqueue_test_message(source_id: int, text: str):
    from .tasks import send_test_message
    return q_default.enqueue(send_test_message, source_id, text)

def schedule_campaign_tick(campaign_id: int, trigger: str = "scheduler_interval"):
    db = db_session()
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        db.close()
        return None, None

    vacancy = db.query(Vacancy).filter(Vacancy.id == campaign.vacancy_id).first()
    links = db.query(CampaignSource).filter(CampaignSource.campaign_id == campaign.id).all()
    run_key = f"run_{campaign.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"
    for link in links:
        source = db.query(Source).filter(Source.id == link.source_id, Source.company_id == campaign.company_id, Source.is_active == True).first()
        if not source:
            continue
        db.add(
            PostingAttempt(
                company_id=campaign.company_id,
                campaign_id=campaign.id,
                vacancy_id=campaign.vacancy_id,
                source_id=source.id,
                run_key=run_key,
                platform=(source.platform or "telegram"),
                destination=(source.label or source.tg_ref),
                destination_ref=(source.destination_url or source.tg_ref or ""),
                asset_title=(vacancy.final_post_title if vacancy and vacancy.final_post_title else vacancy.title if vacancy else ""),
                asset_body=(vacancy.final_post_body if vacancy and vacancy.final_post_body else vacancy.body if vacancy else ""),
                action_taken=trigger,
                result_status="scheduled",
            )
        )
    db.commit()
    db.close()

    from .tasks import campaign_tick
    job = q_default.enqueue(campaign_tick, campaign_id, run_key, trigger)
    return job, run_key

def enqueue_campaign_tick(campaign_id: int, trigger: str = "scheduler_interval"):
    from .tasks import campaign_tick
    return q_default.enqueue(campaign_tick, campaign_id, None, trigger)

def enqueue_daily_digest(company_id: int):
    from .tasks import daily_digest
    return q_default.enqueue(daily_digest, company_id)
