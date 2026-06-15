import json
import os, time
from datetime import datetime, timedelta, timezone
from redis import Redis
from rq import Queue
from app.db import db_session
from app.models import Campaign, Company
from app.plans import is_billing_active
from app.schema import bootstrap_schema
from worker.queue import schedule_campaign_tick, enqueue_daily_digest, claim_once

# Simple scheduler: every 60s checks running campaigns and enqueues if interval elapsed.
# Plus a daily-digest fire at DAILY_DIGEST_HOUR Israel time, exactly once per day per company.
# Replace with APScheduler/Cron later.

try:
    from zoneinfo import ZoneInfo
    ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")  # handles IDT/IST transitions (matches worker/queue.py)
except Exception:
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
    bootstrap_schema()
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    Redis.from_url(redis_url)  # connectivity check
    while True:
        db = db_session()
        campaigns = db.query(Campaign).filter(Campaign.is_running == True).all()
        # Evaluate the posting window in Israel local time (the container runs UTC),
        # matching what worker/queue.py and worker/tasks.py enforce.
        now = datetime.now(ISRAEL_TZ)
        for c in campaigns:
            if not _campaign_window_check(c, now):
                continue
            # Cross-process dedup: claim this campaign's interval bucket in Redis so a
            # second scheduler instance (or a restart) can't double-fire the same tick.
            interval = max(int(c.interval_minutes) * 60, 60)
            bucket = int(time.time()) // interval
            if not claim_once(f"sched:tick:{c.id}:{bucket}", interval):
                continue
            # Billing gate: don't post for tenants whose trial expired / plan lapsed.
            company = db.query(Company).filter(Company.id == c.company_id).first()
            if not is_billing_active(db, company):
                continue
            schedule_campaign_tick(c.id, "scheduler_interval")

        # Daily digest at 08:00 Israel (configurable). Fires once per company per day,
        # deduped via Redis across scheduler instances/restarts.
        israel_now = datetime.now(ISRAEL_TZ)
        if israel_now.hour == DAILY_DIGEST_HOUR:
            today_marker = israel_now.strftime("%Y-%m-%d")
            for company in db.query(Company).filter(Company.is_active == True).all():
                if not claim_once(f"sched:digest:{company.id}:{today_marker}", 26 * 3600):
                    continue
                try:
                    enqueue_daily_digest(company.id)
                except Exception:
                    pass

        db.close()
        time.sleep(60)


if __name__ == "__main__":
    main()
