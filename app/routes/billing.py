"""Billing — Paddle (Merchant of Record). Overlay checkout + webhook + trial expiry.

Replaced Stripe with Paddle on 2026-06-15: Stripe does not onboard Israeli sellers,
Paddle does (payout via Payoneer/wire) and handles VAT as Merchant of Record.

Access model (unchanged): User.trial_expires_at — future = trial, None = paid
(perpetual), past = expired (enforce_paywall redirects to /pricing). The webhook is
the source of truth: subscription.activated grants, subscription.canceled revokes.
"""
import os
import json
import hmac
import hashlib
import logging
from datetime import datetime

from flask import Blueprint, redirect, request, url_for, session, jsonify, render_template

from ..auth import require_company
from ..config import Config
from ..db import db_session
from ..models import User

logger = logging.getLogger(__name__)

bp = Blueprint("billing", __name__, url_prefix="/billing")


def _paddle_client_token() -> str:
    return os.getenv("PADDLE_CLIENT_TOKEN", "").strip()


def _paddle_webhook_secret() -> str:
    return os.getenv("PADDLE_WEBHOOK_SECRET", "").strip()


def _paddle_env() -> str:
    return (os.getenv("PADDLE_ENV", "sandbox").strip().lower() or "sandbox")


def _price_ids() -> dict[str, str]:
    return {
        "starter": os.getenv("PADDLE_PRICE_STARTER", "").strip(),
        "pro": os.getenv("PADDLE_PRICE_PRO", "").strip(),
        "agency": os.getenv("PADDLE_PRICE_AGENCY", "").strip(),
    }


@bp.get("/checkout/<plan>")
@require_company
def checkout(plan: str):
    """Render the Paddle.js overlay-checkout page for the chosen plan.

    Keeps the existing /billing/checkout/<plan> links working; the page loads
    Paddle.js and opens the overlay with the plan's price + the user's id in
    customData (so the webhook can map the resulting subscription back to us)."""
    if not Config.billing_enabled():
        return redirect(url_for("pricing.pricing_page") + "?error=billing_disabled")
    price_id = _price_ids().get(plan)
    token = _paddle_client_token()
    if not price_id or not token:
        return redirect(url_for("pricing.pricing_page") + "?error=invalid_plan")
    base_url = request.host_url.rstrip("/")
    return render_template(
        "paddle_checkout.html",
        paddle_token=token,
        paddle_env=_paddle_env(),
        price_id=price_id,
        plan=plan,
        customer_email=session.get("owner_id", "") or "",
        user_id=str(session.get("user_id") or ""),
        company_id=str(session.get("current_company_id") or ""),
        success_url=f"{base_url}/billing/success",
    )


@bp.get("/success")
def checkout_success():
    """Post-checkout success page (access itself is granted by the webhook)."""
    return redirect(url_for("auth.dashboard") + "?message=subscription_active")


def _verify_paddle_signature(raw_body: bytes, header: str, secret: str) -> bool:
    """Paddle-Signature: 'ts=<unix>;h1=<hex>'. Signed payload = ts + ':' + raw body,
    HMAC-SHA256 with the notification-destination secret. Timing-safe compare.
    We don't reject on timestamp age — Paddle retries can be delayed, and a replayed
    valid event is idempotent here (it just re-sets trial_expires_at)."""
    if not secret or not header:
        return False
    ts = h1 = None
    for part in header.split(";"):
        key, _, val = part.partition("=")
        if key.strip() == "ts":
            ts = val.strip()
        elif key.strip() == "h1":
            h1 = val.strip()
    if not ts or not h1:
        return False
    signed = ts.encode() + b":" + raw_body
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, h1)


@bp.post("/webhook")
def paddle_webhook():
    """Handle Paddle webhook events. Never trust an unsigned/forged event."""
    secret = _paddle_webhook_secret()
    if not secret:
        logger.error("[billing] webhook rejected: PADDLE_WEBHOOK_SECRET not set")
        return jsonify({"error": "webhook not configured"}), 400

    raw = request.get_data()  # raw bytes, exactly as received
    sig = request.headers.get("Paddle-Signature", "")
    if not _verify_paddle_signature(raw, sig, secret):
        logger.error("[billing] webhook signature verification failed")
        return jsonify({"error": "invalid signature"}), 400

    try:
        event = json.loads(raw.decode("utf-8"))
    except Exception:
        return jsonify({"error": "bad json"}), 400

    etype = event.get("event_type", "")
    data = event.get("data", {}) or {}
    status = (data.get("status") or "").lower()

    if etype in ("subscription.activated", "subscription.created", "transaction.completed"):
        if etype.startswith("subscription") and status in ("canceled", "paused"):
            logger.info(f"[billing] {etype} status={status} — not granting")
        else:
            _grant_access(data)
    elif etype == "subscription.canceled":
        _revoke_access(data)
    elif etype in ("transaction.payment_failed", "subscription.past_due"):
        logger.warning(f"[billing] payment issue: {etype} id={data.get('id')}")

    return jsonify({"status": "ok"})


def _user_id_from(data: dict):
    return (data.get("custom_data") or {}).get("user_id")


def _grant_access(data: dict):
    uid = _user_id_from(data)
    if not uid:
        logger.warning("[billing] grant: no user_id in custom_data")
        return
    db = db_session()
    try:
        user = db.query(User).filter(User.id == int(uid)).first()
        if user:
            user.trial_expires_at = None  # perpetual access = paying
            db.commit()
            logger.info(f"[billing] access granted user={uid}")
    except Exception as e:
        logger.error(f"[billing] grant error: {e}")
        db.rollback()
    finally:
        db.close()


def _revoke_access(data: dict):
    uid = _user_id_from(data)
    if not uid:
        logger.warning("[billing] revoke: no user_id in custom_data — cannot revoke")
        return
    db = db_session()
    try:
        user = db.query(User).filter(User.id == int(uid)).first()
        if user:
            user.trial_expires_at = datetime.utcnow()  # expired -> paywall
            db.commit()
            logger.info(f"[billing] access revoked user={uid}")
    except Exception as e:
        logger.error(f"[billing] revoke error: {e}")
        db.rollback()
    finally:
        db.close()
