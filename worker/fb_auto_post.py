"""
Worker task: auto-post a single FB queue item via browser automation.

Flow:
- Take fb_posting_queue_items.id
- Lookup the queue item, its run, vacancy, group, post variant
- Call common.fb_browser_poster.post_to_group(...)
- Update queue item: status=posted/failed, post_url_manual, group_note,
  posted_at/skipped_at; copied_at if not yet set
- Persist a row in fb_posting_results with screenshots + error info

The whole-queue trigger (fire all 5 with stagger) is built on top of this:
schedule N copies with rq scheduled_at gradually offset by RANDOM(5..10) min.
"""
from __future__ import annotations

import logging
import os
import random
from datetime import datetime, timedelta
from typing import Optional

from app.db import db_session
from app.models import (
    Company,
    FacebookGroup,
    FacebookPostingQueueItem,
    FacebookPostingQueueItemStatus,
    FacebookPostingResult,
    FacebookPostingResultStatus,
    FacebookPostingRun,
    FacebookPostVariant,
)

logger = logging.getLogger(__name__)

DEFAULT_SESSION_NAME = os.getenv("FB_BROWSER_SESSION_NAME", "floordsgn")

# Anti-ban guards (env-tunable). Posting byte-identical text to many groups fast
# from one account is the canonical FB spam signature — so we cap per-session daily
# volume, enforce a per-group cooldown, lightly vary each post, and freeze a session
# the moment FB flags it.
MAX_POSTS_PER_SESSION_PER_DAY = int(os.getenv("FB_MAX_POSTS_PER_SESSION_PER_DAY", "20"))
GROUP_COOLDOWN_HOURS = int(os.getenv("FB_GROUP_COOLDOWN_HOURS", "12"))
SESSION_BLOCK_COOLDOWN_SECONDS = int(os.getenv("FB_SESSION_BLOCK_COOLDOWN_SECONDS", str(6 * 3600)))
# Error kinds from the browser poster that mean "FB is flagging this account".
_BLOCK_ERROR_KINDS = {"post_blocked", "captcha", "not_logged_in"}


def _resolve_session_name(company_id: int) -> str:
    return os.getenv(f"FB_BROWSER_SESSION_COMPANY_{company_id}", DEFAULT_SESSION_NAME)


def _redis():
    try:
        from worker.queue import redis_conn
        return redis_conn
    except Exception:
        return None


def _session_blocked(session_name: str) -> bool:
    r = _redis()
    if not r:
        return False
    try:
        return bool(r.get(f"fb:blocked:{session_name}"))
    except Exception:
        return False


def _flag_session_blocked(session_name: str, reason: str) -> None:
    r = _redis()
    if not r:
        return
    try:
        r.setex(f"fb:blocked:{session_name}", SESSION_BLOCK_COOLDOWN_SECONDS, reason)
        logger.error(f"[fb_auto_post] session '{session_name}' frozen for {SESSION_BLOCK_COOLDOWN_SECONDS}s after {reason}")
    except Exception:
        pass


def _daily_count_key(session_name: str) -> str:
    from datetime import timezone
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"fb:postcount:{session_name}:{day}"


def _daily_cap_reached(session_name: str) -> bool:
    r = _redis()
    if not r:
        return False
    try:
        cur = int(r.get(_daily_count_key(session_name)) or 0)
        return cur >= MAX_POSTS_PER_SESSION_PER_DAY
    except Exception:
        return False


def _incr_daily_count(session_name: str) -> None:
    r = _redis()
    if not r:
        return
    try:
        key = _daily_count_key(session_name)
        cur = r.incr(key)
        if cur == 1:
            r.expire(key, 36 * 3600)
    except Exception:
        pass


def _vary_text(text: str, seed: int) -> str:
    """Light, content-preserving variation so the same run does not post a
    byte-identical string to every group. Deterministic per seed (queue item)."""
    leads = ["", "👋 ", "📣 ", "🔔 ", "✨ "]
    tails = ["", " ", "\n", "\n ", " ."]
    lead = leads[seed % len(leads)]
    tail = tails[(seed // len(leads)) % len(tails)]
    return f"{lead}{text}{tail}"


def auto_post_queue_item(queue_item_id: int) -> dict:
    """RQ task. Posts one queue item via browser. Updates DB."""
    db = db_session()
    try:
        item = (
            db.query(FacebookPostingQueueItem)
            .filter(FacebookPostingQueueItem.id == queue_item_id)
            .first()
        )
        if not item:
            return {"ok": False, "error": f"queue_item {queue_item_id} not found"}
        # Idempotency: if a result row already exists, the post already happened.
        # (queue_item_id is UNIQUE on fb_posting_results.) Never re-post.
        if db.query(FacebookPostingResult).filter(
            FacebookPostingResult.queue_item_id == item.id
        ).first():
            return {"ok": False, "error": f"queue_item {queue_item_id} already has a result; skipping"}
        # Only freshly-queued items are eligible. 'opened' is deliberately EXCLUDED:
        # an item left 'opened' means a prior attempt already claimed it (and may
        # have posted before crashing) — re-firing it would double-post.
        if item.status not in (
            FacebookPostingQueueItemStatus.pending,
            FacebookPostingQueueItemStatus.current,
        ):
            return {
                "ok": False,
                "error": f"queue_item {queue_item_id} status={item.status}, not eligible",
            }

        run = (
            db.query(FacebookPostingRun)
            .filter(FacebookPostingRun.id == item.run_id)
            .first()
        )
        if not run:
            return {"ok": False, "error": f"run {item.run_id} not found"}

        group = (
            db.query(FacebookGroup)
            .filter(FacebookGroup.id == item.group_id)
            .first()
        )
        if not group:
            return {"ok": False, "error": f"fb_group {item.group_id} not found"}

        variant = (
            db.query(FacebookPostVariant)
            .filter(FacebookPostVariant.id == run.post_variant_id)
            .first()
        )
        if not variant or not variant.full_text:
            return {"ok": False, "error": f"variant {run.post_variant_id} missing full_text"}

        company_id = run.company_id

        # Cross-tenant safety: the group and variant must belong to the same tenant
        # as the run. Refuse to post one tenant's text to another tenant's group.
        if group.company_id != company_id or variant.company_id != company_id:
            return {
                "ok": False,
                "error": (
                    f"tenant mismatch: run.company={company_id} "
                    f"group.company={group.company_id} variant.company={variant.company_id}"
                ),
            }

        session_name = _resolve_session_name(company_id)

        from common.fb_browser_poster import post_to_group, session_exists

        # Fail-fast: if FB already flagged this session, do not keep firing into it.
        if _session_blocked(session_name):
            return {"ok": False, "error": f"session '{session_name}' is frozen after a recent FB block; skipping"}

        if not session_exists(session_name):
            err = f"FB session '{session_name}' not captured. Run scripts/fb_capture_session.py first."
            item.status = FacebookPostingQueueItemStatus.failed
            item.skipped_at = datetime.utcnow()
            item.skip_reason = err
            db.commit()
            return {"ok": False, "error": err}

        # Daily per-session volume cap.
        if _daily_cap_reached(session_name):
            return {"ok": False, "error": f"session '{session_name}' hit daily post cap ({MAX_POSTS_PER_SESSION_PER_DAY}); skipping"}

        # Per-group cooldown — never hammer the same group repeatedly.
        if group.last_posted_at and (datetime.utcnow() - group.last_posted_at) < timedelta(hours=GROUP_COOLDOWN_HOURS):
            return {"ok": False, "error": f"group {group.id} posted within cooldown ({GROUP_COOLDOWN_HOURS}h); skipping"}

        # Atomic claim: flip pending/current -> opened only if still eligible. If
        # zero rows update, another worker already claimed it -> abort (no double-post).
        from sqlalchemy import func as _sqlfunc
        now = datetime.utcnow()
        claimed = (
            db.query(FacebookPostingQueueItem)
            .filter(
                FacebookPostingQueueItem.id == item.id,
                FacebookPostingQueueItem.status.in_([
                    FacebookPostingQueueItemStatus.pending,
                    FacebookPostingQueueItemStatus.current,
                ]),
            )
            .update(
                {
                    "status": FacebookPostingQueueItemStatus.opened,
                    "opened_at": _sqlfunc.coalesce(FacebookPostingQueueItem.opened_at, now),
                    "copied_at": _sqlfunc.coalesce(FacebookPostingQueueItem.copied_at, now),
                },
                synchronize_session=False,
            )
        )
        db.commit()
        if not claimed:
            return {"ok": False, "error": f"queue_item {queue_item_id} already claimed by another worker; skipping"}
        item = (
            db.query(FacebookPostingQueueItem)
            .filter(FacebookPostingQueueItem.id == queue_item_id)
            .first()
        )

        post_text = _vary_text(variant.full_text, item.id)

        logger.info(
            f"[fb_auto_post] firing queue_item={item.id} run={run.id} "
            f"group={group.id} url={group.facebook_url}"
        )
        result = post_to_group(
            session_name=session_name,
            group_url=group.facebook_url,
            text=post_text,
            queue_item_id=item.id,
        )

        # Re-fetch — lock-step to avoid stale state
        item = (
            db.query(FacebookPostingQueueItem)
            .filter(FacebookPostingQueueItem.id == queue_item_id)
            .first()
        )

        notes_blob = "; ".join(result.notes) if result.notes else None

        if result.ok:
            item.status = FacebookPostingQueueItemStatus.posted
            item.posted_at = datetime.utcnow()
            item.completed_by = "fb_auto_post_worker"
            item.post_url_manual = result.final_url
            item.group_note = notes_blob
            group.last_posted_at = datetime.utcnow()

            db.add(
                FacebookPostingResult(
                    company_id=company_id,
                    queue_item_id=item.id,
                    result_status=FacebookPostingResultStatus.posted,
                    response_count=0,
                    cv_count=0,
                    interview_count=0,
                    hire_count=0,
                    result_note=(
                        f"auto-posted via browser; before={result.screenshot_before}; "
                        f"after={result.screenshot_after}; duration={result.duration_seconds:.1f}s"
                    ),
                    updated_by="fb_auto_post_worker",
                )
            )
        else:
            item.status = FacebookPostingQueueItemStatus.failed
            item.skipped_at = datetime.utcnow()
            item.skip_reason = f"{result.error_kind}: {result.error_message}"
            item.group_note = notes_blob

            db.add(
                FacebookPostingResult(
                    company_id=company_id,
                    queue_item_id=item.id,
                    result_status=FacebookPostingResultStatus.no_signal,
                    response_count=0,
                    cv_count=0,
                    interview_count=0,
                    hire_count=0,
                    result_note=(
                        f"auto-post failed: {result.error_kind} — {result.error_message}; "
                        f"before={result.screenshot_before}; after={result.screenshot_after}"
                    ),
                    updated_by="fb_auto_post_worker",
                )
            )

        db.commit()

        # Post-commit anti-ban bookkeeping (outside the critical write).
        if result.ok:
            _incr_daily_count(session_name)
        elif result.error_kind in _BLOCK_ERROR_KINDS:
            # FB flagged the account — freeze the session so the remaining
            # staggered jobs in this run skip instead of piling onto the block.
            _flag_session_blocked(session_name, result.error_kind or "blocked")
        return {
            "ok": result.ok,
            "queue_item_id": item.id,
            "error_kind": result.error_kind,
            "error_message": result.error_message,
            "final_url": result.final_url,
            "screenshot_before": result.screenshot_before,
            "screenshot_after": result.screenshot_after,
            "duration_seconds": result.duration_seconds,
            "notes": result.notes,
        }
    except Exception as exc:
        db.rollback()
        logger.exception(f"[fb_auto_post] unexpected failure for queue_item={queue_item_id}")
        return {"ok": False, "error": f"unexpected: {exc!r}"}
    finally:
        db.close()


def fire_run_staggered(
    run_id: int,
    *,
    min_delay_seconds: int = 300,
    max_delay_seconds: int = 600,
    first_delay_seconds: int = 5,
) -> dict:
    """
    Enqueue every pending queue item in run_id with staggered delays.
    Default cadence: first item ~immediate, then 5–10 min between each.

    Returns: {scheduled_at: [(queue_item_id, ts), ...], total: N}
    """
    from worker.queue import redis_conn, q_default
    from rq.job import Job
    from datetime import datetime, timedelta

    db = db_session()
    try:
        run = (
            db.query(FacebookPostingRun)
            .filter(FacebookPostingRun.id == run_id)
            .first()
        )
        if not run:
            return {"ok": False, "error": f"run {run_id} not found"}

        # Billing gate: do not fire a posting run for a tenant whose trial expired
        # or whose subscription lapsed (enforced here, not only in the web UI).
        from app.plans import is_billing_active
        company = db.query(Company).filter(Company.id == run.company_id).first()
        if not is_billing_active(db, company):
            return {"ok": False, "error": f"billing inactive for company {run.company_id}; run not fired"}

        items = (
            db.query(FacebookPostingQueueItem)
            .filter(
                FacebookPostingQueueItem.run_id == run_id,
                FacebookPostingQueueItem.status.in_(
                    [
                        FacebookPostingQueueItemStatus.pending,
                        FacebookPostingQueueItemStatus.current,
                    ]
                ),
            )
            .order_by(FacebookPostingQueueItem.position.asc())
            .all()
        )
        if not items:
            return {"ok": True, "scheduled": [], "note": "no eligible items"}

        scheduled = []
        cumulative = first_delay_seconds
        for idx, item in enumerate(items):
            from rq import Queue
            from datetime import timezone

            scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=cumulative)
            job = q_default.enqueue_at(scheduled_at, auto_post_queue_item, item.id)
            scheduled.append(
                {
                    "queue_item_id": item.id,
                    "position": item.position,
                    "fire_at_utc": scheduled_at.isoformat(),
                    "rq_job_id": job.id,
                    "delay_from_start_s": cumulative,
                }
            )
            # Next delay window
            cumulative += random.randint(min_delay_seconds, max_delay_seconds)

        return {
            "ok": True,
            "run_id": run_id,
            "total_scheduled": len(scheduled),
            "scheduled": scheduled,
        }
    finally:
        db.close()
