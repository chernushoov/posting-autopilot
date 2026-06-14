"""Task 3.1: Stripe Billing — checkout, webhook, trial expiration."""
import os
import logging

from flask import Blueprint, redirect, request, url_for, session, jsonify

from ..auth import require_company
from ..config import Config
from ..db import db_session
from ..models import User

logger = logging.getLogger(__name__)

bp = Blueprint("billing", __name__, url_prefix="/billing")

def _stripe_secret_key() -> str:
    return os.getenv("STRIPE_SECRET_KEY", "").strip()


def _stripe_webhook_secret() -> str:
    return os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()


def _price_ids() -> dict[str, str]:
    return {
        "starter": os.getenv("STRIPE_PRICE_STARTER", "").strip(),
        "pro": os.getenv("STRIPE_PRICE_PRO", "").strip(),
        "agency": os.getenv("STRIPE_PRICE_AGENCY", "").strip(),
    }


PRICE_IDS = _price_ids()


def _get_stripe():
    """Lazy-load stripe module. Returns None if not configured."""
    if not Config.billing_enabled():
        return None
    secret_key = _stripe_secret_key()
    if not secret_key:
        return None
    try:
        import stripe
        stripe.api_key = secret_key
        return stripe
    except ImportError:
        logger.warning("[billing] stripe package not installed")
        return None


@bp.get("/checkout/<plan>")
@require_company
def checkout(plan: str):
    """Create Stripe Checkout session and redirect."""
    stripe = _get_stripe()
    if not stripe:
        return redirect(url_for("pricing.pricing_page") + "?error=billing_disabled")

    price_id = _price_ids().get(plan)
    if not price_id:
        return redirect(url_for("pricing.pricing_page") + "?error=invalid_plan")

    user_id = session.get("user_id")
    company_id = session.get("current_company_id")

    try:
        base_url = request.host_url.rstrip("/")
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/pricing",
            metadata={
                "user_id": str(user_id or ""),
                "company_id": str(company_id or ""),
                "plan": plan,
            },
            # Carry user_id onto the SUBSCRIPTION too (not just the session) so the
            # customer.subscription.deleted webhook can map back to our user and
            # revoke access on cancellation.
            subscription_data={
                "metadata": {
                    "user_id": str(user_id or ""),
                    "company_id": str(company_id or ""),
                    "plan": plan,
                },
            },
        )
        return redirect(checkout_session.url)
    except Exception as e:
        logger.error(f"[billing] Checkout error: {e}")
        return redirect(url_for("pricing.pricing_page") + f"?error=checkout_failed")


@bp.get("/success")
def checkout_success():
    """Post-checkout success page."""
    return redirect(url_for("auth.dashboard") + "?message=subscription_active")


@bp.post("/webhook")
def stripe_webhook():
    """Handle Stripe webhook events."""
    stripe = _get_stripe()
    if not stripe:
        return jsonify({"error": "not configured"}), 400

    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature", "")

    # Security: never trust an unsigned webhook. Without the signing secret we
    # cannot prove Stripe sent this, so a forged checkout.session.completed could
    # grant anyone a paid/cleared trial. Reject rather than parse raw JSON.
    if not _stripe_webhook_secret():
        logger.error("[billing] Webhook rejected: STRIPE_WEBHOOK_SECRET is not set")
        return jsonify({"error": "webhook not configured"}), 400

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, _stripe_webhook_secret())
    except Exception as e:
        logger.error(f"[billing] Webhook signature verification failed: {e}")
        return jsonify({"error": "invalid signature"}), 400

    event_type = event.get("type", "")
    data = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(data)
    elif event_type == "customer.subscription.deleted":
        _handle_subscription_cancelled(data)
    elif event_type == "invoice.payment_failed":
        _handle_payment_failed(data)

    return jsonify({"status": "ok"})


def _handle_checkout_completed(session_data: dict):
    """Activate subscription after successful checkout."""
    metadata = session_data.get("metadata", {})
    user_id = metadata.get("user_id")
    plan = metadata.get("plan", "starter")

    if not user_id:
        logger.warning("[billing] checkout.session.completed without user_id")
        return

    db = db_session()
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            # Remove trial expiration — user is now paying
            user.trial_expires_at = None
            db.commit()
            logger.info(f"[billing] User {user_id} subscribed to {plan}")
    except Exception as e:
        logger.error(f"[billing] Error activating subscription: {e}")
        db.rollback()
    finally:
        db.close()


def _handle_subscription_cancelled(sub_data: dict):
    """Revoke access on cancellation: expire the trial so enforce_paywall redirects
    the user to /pricing on their next request. Without this a cancelled customer
    kept full access (the access signal is User.trial_expires_at; checkout sets it
    to None = perpetual, so cancellation must set it back to 'now' = expired).
    user_id rides on the subscription metadata we set at checkout."""
    from datetime import datetime
    metadata = sub_data.get("metadata", {}) or {}
    user_id = metadata.get("user_id")
    logger.info(f"[billing] Subscription cancelled: {sub_data.get('id')} user={user_id}")
    if not user_id:
        logger.warning("[billing] cancellation without user_id metadata — cannot revoke access")
        return
    db = db_session()
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            user.trial_expires_at = datetime.utcnow()  # immediately expired -> paywall
            db.commit()
            logger.info(f"[billing] Access revoked for user {user_id} after cancellation")
    except Exception as e:
        logger.error(f"[billing] Error revoking access on cancellation: {e}")
        db.rollback()
    finally:
        db.close()


def _handle_payment_failed(invoice_data: dict):
    """Handle failed payment."""
    logger.warning(f"[billing] Payment failed for invoice: {invoice_data.get('id')}")
