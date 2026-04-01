import json
import os, time
from datetime import datetime, timedelta
from redis import Redis
from rq import Queue
from app.db import db_session
from app.models import Campaign
from app.schema import bootstrap_schema
from worker.queue import schedule_campaign_tick

# Simple scheduler: every 60s checks running campaigns and enqueues if interval elapsed.
# Replace with APScheduler/Cron later.

def main():
    bootstrap_schema()
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    Redis.from_url(redis_url)  # connectivity check
    last_run = {}
    while True:
        db = db_session()
        campaigns = db.query(Campaign).filter(Campaign.is_running == True).all()
        now = datetime.now()
        for c in campaigns:
            try:
                hours = json.loads(c.active_hours_json or '{"start":9,"end":19}')
                days = json.loads(c.days_of_week_json or '[0,1,2,3,4,5]')
            except Exception:
                hours = {"start": 9, "end": 19}
                days = [0, 1, 2, 3, 4, 5]
            start_hour = int(hours.get("start", 9))
            end_hour = int(hours.get("end", 19))
            if c.interval_minutes <= 0:
                continue
            if now.weekday() not in days:
                continue
            if now.hour < start_hour or now.hour >= end_hour:
                continue
            prev = last_run.get(c.id)
            if not prev or (now - prev).total_seconds() >= c.interval_minutes * 60:
                schedule_campaign_tick(c.id, "scheduler_interval")
                last_run[c.id] = now
        db.close()
        time.sleep(60)

if __name__ == "__main__":
    main()
