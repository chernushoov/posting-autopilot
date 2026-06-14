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

# Map low-level poster error_kind -> stable, customer-facing error_code (Phase 4).
_POSTER_ERROR_CODE = {
    "session_missing": "FACEBOOK_SESSION_INVALID",
    "not_logged_in": "FACEBOOK_SESSION_EXPIRED",
    "group_not_found": "FACEBOOK_TARGET_UNAVAILABLE",
    "composer_not_found": "FACEBOOK_UI_CHANGED",
    "composer_click_failed": "FACEBOOK_UI_CHANGED",
    "textbox_not_found": "FACEBOOK_UI_CHANGED",
    "submit_not_found": "FACEBOOK_UI_CHANGED",
    "typing_failed": "FACEBOOK_UI_CHANGED",
    "submit_click_failed": "FACEBOOK_UI_CHANGED",
    "post_blocked": "FACEBOOK_PERMISSION_DENIED",
    "captcha": "FACEBOOK_PERMISSION_DENIED",
    "timeout": "POSTING_FAILED_UNKNOWN",
}


def _poster_error_code(error_kind) -> str:
    return _POSTER_ERROR_CODE.get(error_kind or "", "POSTING_FAILED_UNKNOWN")


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

        from app.facebook_session import (
            company_session_name,
            error_code_for_reason,
            get_fb_session_status,
            session_basename,
        )
        from common.fb_browser_poster import post_to_group

        # FAIL CLOSED: post ONLY with THIS company's own valid session. No shared/global
        # session, no 'floordsgn' fallback, never another tenant's session.
        fb_status = get_fb_session_status(company_id)
        if not fb_status.get("connected"):
            error_code = error_code_for_reason(fb_status.get("reason"))
            error_message = (
                "Facebook is not connected for this company. Please connect Facebook first."
                if error_code == "FACEBOOK_NOT_CONNECTED_FOR_COMPANY"
                else "Facebook session is invalid or expired for this company. Please reconnect Facebook."
            )
            item.status = FacebookPostingQueueItemStatus.failed
            item.skipped_at = datetime.utcnow()
            item.skip_reason = f"{error_code}: {error_message}"
            db.commit()
            logger.warning(
                "[fb_auto_post] FAIL-CLOSED company_id=%s run_id=%s queue_item_id=%s "
                "code=%s session=%s", company_id, run.id, item.id, error_code,
                session_basename(company_id),
            )
            return {
                "ok": False, "status": "failed", "error_code": error_code,
                "error_message": error_message, "company_id": company_id,
                "run_id": run.id, "queue_item_id": item.id,
                "session_file": session_basename(company_id),
            }

        session_name = company_session_name(company_id)

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
        error_code = None if result.ok else _poster_error_code(result.error_kind)
        _sess_base = session_basename(company_id)

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
                        f"auto-posted via browser; session={_sess_base}; "
                        f"before={result.screenshot_before}; "
                        f"after={result.screenshot_after}; duration={result.duration_seconds:.1f}s"
                    ),
                    recorded_by="fb_auto_post_worker",
                )
            )
        else:
            item.status = FacebookPostingQueueItemStatus.failed
            item.skipped_at = datetime.utcnow()
            item.skip_reason = f"{error_code}: {result.error_message}"
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
                        f"auto-post failed [{error_code}]: {result.error_kind} — "
                        f"{result.error_message}; session={_sess_base}; "
                        f"before={result.screenshot_before}; after={result.screenshot_after}"
                    ),
                    recorded_by="fb_auto_post_worker",
                )
            )
            logger.warning(
                "[fb_auto_post] POST FAILED company_id=%s run_id=%s queue_item_id=%s "
                "code=%s kind=%s session=%s", company_id, run.id, item.id, error_code,
                result.error_kind, _sess_base,
            )

        db.commit()
        if result.ok:
            logger.info(
                "[fb_auto_post] POSTED company_id=%s run_id=%s queue_item_id=%s session=%s url=%s",
                company_id, run.id, item.id, _sess_base, result.final_url,
            )
        return {
            "ok": result.ok,
            "status": "success" if result.ok else "failed",
            "company_id": company_id,
            "run_id": run.id,
            "queue_item_id": item.id,
            "error_code": error_code,
            "error_kind": result.error_kind,
            "error_message": result.error_message,
            "session_file": _sess_base,
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

        # FAIL CLOSED before scheduling N jobs: the run's company must have its own
        # valid FB session. No shared/global session, no 'floordsgn' fallback.
        from app.facebook_session import get_fb_session_status, error_code_for_reason, session_basename
        fb_status = get_fb_session_status(run.company_id)
        if not fb_status.get("connected"):
            return {
                "ok": False,
                "error_code": error_code_for_reason(fb_status.get("reason")),
                "error_message": "Facebook is not connected for this company. Connect Facebook before auto-firing.",
                "company_id": run.company_id, "run_id": run_id,
                "session_file": session_basename(run.company_id), "scheduled": [],
            }

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
