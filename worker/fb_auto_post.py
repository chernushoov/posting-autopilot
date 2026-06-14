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
        if item.status not in (
            FacebookPostingQueueItemStatus.pending,
            FacebookPostingQueueItemStatus.current,
            FacebookPostingQueueItemStatus.opened,
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

        from common.fb_browser_poster import post_to_group, session_exists, company_session_name
        # Per-company session ONLY — never fall back to another tenant's FB session.
        session_name = company_session_name(company_id)

        if not session_exists(session_name):
            err = (
                f"FB session for company {company_id} not captured "
                f"(expected data/fb_sessions/{session_name}.json). Capture it for THIS "
                f"company before auto-posting — fail closed, no shared session."
            )
            item.status = FacebookPostingQueueItemStatus.failed
            item.skipped_at = datetime.utcnow()
            item.skip_reason = err
            db.commit()
            return {"ok": False, "error": err}

        item.status = FacebookPostingQueueItemStatus.opened
        item.opened_at = item.opened_at or datetime.utcnow()
        if not item.copied_at:
            item.copied_at = datetime.utcnow()
        db.commit()

        logger.info(
            f"[fb_auto_post] firing queue_item={item.id} run={run.id} "
            f"group={group.id} url={group.facebook_url}"
        )
        result = post_to_group(
            session_name=session_name,
            group_url=group.facebook_url,
            text=variant.full_text,
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
                    recorded_by="fb_auto_post_worker",
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
                    recorded_by="fb_auto_post_worker",
                )
            )

        db.commit()
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
