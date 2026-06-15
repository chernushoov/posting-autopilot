import json
import os, time
from datetime import datetime, timedelta, timezone
from redis import Redis
from rq import Queue
from app.db import db_session
from app.models import Campaign, Company, User, TrialReminder
from app.schema import bootstrap_schema
from common.env_guard import validate_runtime_environment
from worker.queue import schedule_campaign_tick, enqueue_daily_digest

# Simple scheduler: every 60s checks running campaigns and enqueues if interval elapsed.
# Plus a daily-digest fire at DAILY_DIGEST_HOUR Israel time, exactly once per day per company.
# Replace with APScheduler/Cron later.

ISRAEL_TZ = timezone(timedelta(hours=3))
DAILY_DIGEST_HOUR = int(os.getenv("DAILY_DIGEST_HOUR_IL", "8"))
TRIAL_REMINDER_HOUR_IL = int(os.getenv("TRIAL_REMINDER_HOUR_IL", "10"))


def _trial_email(stage: str, base: str, days_left: int):
    """English-primary reminder (US market). No-op-safe: send_email silently does
    nothing until an email provider is configured."""
    pricing = base + "/pricing"
    cab = base + "/cabinet"
    if stage == "expired":
        subj = "Your trial has ended — posting is paused · Posting Autopilot"
        body = ("<p>Hi,</p>"
                "<p>Your Pro trial has ended and auto-posting is paused. "
                "Pick a plan to resume posting and your AI assistant.</p>"
                f'<p><a href="{pricing}">Choose a plan →</a></p>')
        txt = f"Your trial has ended. Choose a plan: {pricing}"
    else:
        d = max(1, days_left)
        subj = f"{d} day(s) left in your trial · Posting Autopilot"
        body = ("<p>Hi,</p>"
                f"<p>You have <b>{d}</b> day(s) left in your Pro trial. "
                "Pick a plan now to keep auto-posting and your AI assistant running without interruption.</p>"
                f'<p><a href="{pricing}">Choose a plan →</a> &nbsp;·&nbsp; <a href="{cab}">Open cabinet</a></p>')
        txt = f"{d} day(s) left in your trial. Choose a plan: {pricing}"
    html = f'<div style="font-family:Arial,Helvetica,sans-serif;line-height:1.6">{body}</div>'
    return subj, html, txt


def _run_trial_reminders(db) -> int:
    """Once-daily scan: email users whose Pro trial ends in 3d / 1d / just expired.
    Deduped per (user, stage) via the trial_reminders table (survives restarts)."""
    from app.mailer import send_email
    from app.config import Config
    now = datetime.utcnow()
    base = (getattr(Config, "PUBLIC_APP_URL", "") or "").rstrip("/")
    users = db.query(User).filter(User.is_active == True, User.trial_expires_at.isnot(None)).all()
    sent = 0
    for u in users:
        secs = (u.trial_expires_at - now).total_seconds()
        if secs > 3 * 86400:
            continue
        if secs > 86400:
            stage = "d3"
        elif secs > 0:
            stage = "d1"
        elif secs >= -2 * 86400:
            stage = "expired"
        else:
            continue  # long-expired — don't blast dead accounts
        if db.query(TrialReminder).filter(TrialReminder.user_id == u.id, TrialReminder.stage == stage).first():
            continue
        days_left = max(0, int((secs + 86399) // 86400))  # ceil to whole days
        subj, html, txt = _trial_email(stage, base, days_left)
        try:
            send_email(u.email, subj, html, text=txt)
        except Exception:
            pass
        db.add(TrialReminder(user_id=u.id, stage=stage))
        sent += 1
    if sent:
        db.commit()
    return sent


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
    last_trial_reminder_date: str | None = None
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

        # Trial-ending reminders — once/day at TRIAL_REMINDER_HOUR_IL.
        # The trial_reminders table dedupes per (user, stage) across restarts.
        if israel_now.hour == TRIAL_REMINDER_HOUR_IL:
            tmark = israel_now.strftime("%Y-%m-%d")
            if last_trial_reminder_date != tmark:
                try:
                    n = _run_trial_reminders(db)
                    last_trial_reminder_date = tmark
                    if n:
                        print(f"[scheduler] sent {n} trial reminder(s)", flush=True)
                except Exception:
                    pass

        db.close()
        time.sleep(60)


if __name__ == "__main__":
    main()
