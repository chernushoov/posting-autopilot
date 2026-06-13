import json
import os, time
from datetime import datetime, timedelta, timezone
from redis import Redis
from rq import Queue
from app.db import db_session
from app.models import Campaign, Company
from app.schema import bootstrap_schema
from common.env_guard import validate_runtime_environment
from worker.queue import schedule_campaign_tick, enqueue_daily_digest

# Simple scheduler: every 60s checks running campaigns and enqueues if interval elapsed.
# Plus a daily-digest fire at DAILY_DIGEST_HOUR Israel time, exactly once per day per company.
# Replace with APScheduler/Cron later.

ISRAEL_TZ = timezone(timedelta(hours=3))
DAILY_DIGEST_HOUR = int(os.getenv("DAILY_DIGEST_HOUR_IL", "8"))


def _campaign_window_check(c, now: datetime):
    try:
        hours = json.loads(c.active_hours_json or '{"start":9,"end":19}')
        days = json.loads(c.days_of_week_json or '[0,1,2,3,4,5]')
    except Exception:
        hours = {"start": 9, "end": 19}
        days = [0, 1, 2, 3, 4, 5]
    start_hour = int(hours.get("start", 9))
    end_hour = int(hours.get("end", 19))
    if c.interval_minutes <= 0:
        return False
    if now.weekday() not in days:
        return False
    if now.hour < start_hour or now.hour >= end_hour:
        return False
    return True


def main():
    validate_runtime_environment("scheduler")
    bootstrap_schema()
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    Redis.from_url(redis_url)  # connectivity check
    last_run = {}
    last_digest_date_by_company: dict[int, str] = {}
    while True:
        db = db_session()
        campaigns = db.query(Campaign).filter(Campaign.is_running == True).all()
        now = datetime.now()
        for c in campaigns:
            if not _campaign_window_check(c, now):
                continue
            prev = last_run.get(c.id)
            if not prev or (now - prev).total_seconds() >= c.interval_minutes * 60:
                schedule_campaign_tick(c.id, "scheduler_interval")
                last_run[c.id] = now

        # Daily digest at 08:00 Israel (configurable). Fires once per company per day.
        # If the scheduler restarts after the trigger hour but before the next day,
        # the per-company date marker prevents double-firing.
        israel_now = datetime.now(ISRAEL_TZ)
        if israel_now.hour == DAILY_DIGEST_HOUR:
            today_marker = israel_now.strftime("%Y-%m-%d")
            for company in db.query(Company).filter(Company.is_active == True).all():
                if last_digest_date_by_company.get(company.id) == today_marker:
                    continue
                try:
                    enqueue_daily_digest(company.id)
                    last_digest_date_by_company[company.id] = today_marker
                except Exception:
                    pass

        db.close()
        time.sleep(60)


if __name__ == "__main__":
    main()
