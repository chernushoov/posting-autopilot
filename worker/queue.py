import os
import json
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from redis import Redis
from rq import Queue
from app.db import db_session
from app.models import Campaign, CampaignSource, PostingAttempt, Source, Vacancy

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(REDIS_URL)
# Default job_timeout matches worker-level RQ_WORKER_TIMEOUT (see worker/run_worker.py).
# Anti-spam delay in common/tg_client.py can run multi-minutes; default 900s avoids
# silent job expiry mid-post. Override per-enqueue with `job_timeout=` if needed.
RQ_DEFAULT_TIMEOUT = int(os.getenv("RQ_WORKER_TIMEOUT", "900"))
q_default = Queue(
    os.getenv("RQ_DEFAULT_QUEUE", "default"),
    connection=redis_conn,
    default_timeout=RQ_DEFAULT_TIMEOUT,
)


def _within_campaign_window(campaign: Campaign) -> bool:
    try:
        hours = json.loads(campaign.active_hours_json or '{"start":9,"end":19}')
    except Exception:
        hours = {"start": 9, "end": 19}
    try:
        days = json.loads(campaign.days_of_week_json or '[0,1,2,3,4,5]')
    except Exception:
        days = [0, 1, 2, 3, 4, 5]

    israel_tz = timezone(timedelta(hours=3))
    now = datetime.now(israel_tz)
    if now.weekday() not in days:
        return False
    start_hour = int(hours.get("start", 9))
    end_hour = int(hours.get("end", 19))
    return start_hour <= now.hour < end_hour

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
    if trigger == "scheduler_interval" and not _within_campaign_window(campaign):
        db.close()
        return None, None

    # R2 in-flight guard: refuse a duplicate concurrent run for the same campaign.
    # A double-clicked "Run now", or a scheduler tick racing a manual run, would
    # otherwise mint a second batch of attempts and post the same ad twice to
    # every group. If a run for this campaign was started in the last 90s and is
    # still scheduled/pending/posting, skip this one.
    recent_cutoff = datetime.utcnow() - timedelta(seconds=90)
    inflight = (
        db.query(PostingAttempt)
        .filter(
            PostingAttempt.campaign_id == campaign.id,
            PostingAttempt.result_status.in_(["scheduled", "pending", "posting"]),
            PostingAttempt.created_at >= recent_cutoff,
        )
        .first()
    )
    if inflight:
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
    try:
        job = q_default.enqueue(campaign_tick, campaign_id, run_key, trigger, job_timeout=1800)
    except Exception:
        # R1: background queue (Redis) is offline. Don't leave phantom "scheduled"
        # rows that nothing will ever process — mark them failed, then re-raise so
        # the caller can surface a friendly "queue offline" message.
        cleanup = db_session()
        try:
            cleanup.query(PostingAttempt).filter(
                PostingAttempt.run_key == run_key,
                PostingAttempt.result_status == "scheduled",
            ).update(
                {PostingAttempt.result_status: "failed",
                 PostingAttempt.error_message: "Background queue offline (Redis); run not dispatched."},
                synchronize_session=False,
            )
            cleanup.commit()
        finally:
            cleanup.close()
        raise
    return job, run_key

def enqueue_campaign_tick(campaign_id: int, trigger: str = "scheduler_interval"):
    from .tasks import campaign_tick
    return q_default.enqueue(campaign_tick, campaign_id, None, trigger, job_timeout=1800)

def enqueue_daily_digest(company_id: int):
    from .tasks import daily_digest
    return q_default.enqueue(daily_digest, company_id)
