"""Task 3.1: Stripe Billing — checkout, webhook, trial expiration."""
import os
import logging
from datetime import datetime

from flask import Blueprint, redirect, request, url_for, session, jsonify

from ..auth import require_company
from ..db import db_session
from ..models import Company, User

logger = logging.getLogger(__name__)

bp = Blueprint("billing", __name__, url_prefix="/billing")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

# Price IDs from Stripe Dashboard — set via env vars
PRICE_IDS = {
    "starter": os.getenv("STRIPE_PRICE_STARTER", ""),
    "pro": os.getenv("STRIPE_PRICE_PRO", ""),
    "agency": os.getenv("STRIPE_PRICE_AGENCY", ""),
}


def _get_stripe():
    """Lazy-load stripe module. Returns None if not configured."""
    if not STRIPE_SECRET_KEY:
        return None
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
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
        return redirect(url_for("pricing.pricing_page") + "?error=billing_not_configured")

    if plan not in PRICE_IDS:
        return redirect(url_for("pricing.pricing_page") + "?error=invalid_plan")
    price_id = PRICE_IDS[plan]
    if not price_id:
        # Plan name is valid but no Stripe Price ID configured for it
        return redirect(url_for("pricing.pricing_page") + "?error=billing_not_configured")

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

    if not STRIPE_WEBHOOK_SECRET:
        # Fail closed: without a signing secret any caller could forge
        # checkout.session.completed and activate a subscription for free.
        logger.error("[billing] Webhook rejected: STRIPE_WEBHOOK_SECRET is not set")
        return jsonify({"error": "webhook not configured"}), 400

    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        logger.error(f"[billing] Webhook signature verification failed: {e}")
        return jsonify({"error": "invalid signature"}), 400

    event_id = event.get("id", "")
    event_type = event.get("type", "")
    data = event.get("data", {}).get("object", {})

    # Idempotency: Stripe delivers at-least-once and retries. Record the event id
    # and skip if we've already processed it, so handlers never double-fire.
    if event_id and _already_processed(event_id, event_type):
        logger.info(f"[billing] duplicate webhook {event_id} ({event_type}) ignored")
        return jsonify({"status": "duplicate"})

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(stripe, data)
    elif event_type in ("customer.subscription.updated", "customer.subscription.created"):
        _handle_subscription_updated(data)
    elif event_type == "customer.subscription.deleted":
        _handle_subscription_cancelled(data)
    elif event_type == "invoice.payment_failed":
        _handle_payment_failed(data)
    elif event_type == "invoice.payment_succeeded":
        _handle_payment_succeeded(data)

    return jsonify({"status": "ok"})


def _already_processed(event_id: str, event_type: str) -> bool:
    """Insert the event id; return True if it was seen before. The unique index on
    event_id makes the insert the atomic check (handles concurrent deliveries)."""
    from ..models import StripeWebhookEvent
    db = db_session()
    try:
        if db.query(StripeWebhookEvent).filter(StripeWebhookEvent.event_id == event_id).first():
            return True
        db.add(StripeWebhookEvent(event_id=event_id, event_type=event_type))
        db.commit()
        return False
    except Exception:
        # Unique-constraint violation => a concurrent delivery beat us to it.
        db.rollback()
        return True
    finally:
        db.close()


def _plan_for_price(price_id: str):
    """Reverse-map a Stripe Price id to our plan name. None if unknown."""
    if not price_id:
        return None
    for plan, pid in PRICE_IDS.items():
        if pid and pid == price_id:
            return plan
    return None


def _tier_from_subscription(stripe, sub_id: str):
    """Resolve the real plan from the subscription's price, not from client metadata."""
    if not stripe or not sub_id:
        return None
    try:
        sub = stripe.Subscription.retrieve(sub_id)
        price_id = sub["items"]["data"][0]["price"]["id"]
        return _plan_for_price(price_id)
    except Exception as e:
        logger.warning(f"[billing] could not resolve plan from subscription {sub_id}: {e}")
        return None


def _handle_checkout_completed(stripe, session_data: dict):
    """Activate subscription after successful checkout."""
    metadata = session_data.get("metadata", {})
    user_id = metadata.get("user_id")
    company_id = metadata.get("company_id")
    subscription_id = session_data.get("subscription")

    # Grant the tier that was ACTUALLY paid for (resolved from the subscription's
    # price), not the client-supplied metadata.plan — metadata can be tampered with
    # and can drift from the real price. Fall back to metadata only if Stripe lookup
    # fails, and only if that plan is one we recognise.
    plan = _tier_from_subscription(stripe, subscription_id)
    if not plan:
        meta_plan = metadata.get("plan", "")
        plan = meta_plan if meta_plan in PRICE_IDS else "starter"

    if not user_id:
        logger.warning("[billing] checkout.session.completed without user_id")
        return

    db = db_session()
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            # Remove trial expiration — user is now paying
            user.trial_expires_at = None
        company = None
        if company_id:
            company = db.query(Company).filter(Company.id == int(company_id)).first()
        elif user and user.company_id:
            company = db.query(Company).filter(Company.id == user.company_id).first()
        if company:
            company.plan_tier = plan
            company.stripe_customer_id = session_data.get("customer") or company.stripe_customer_id
            company.stripe_subscription_id = subscription_id or company.stripe_subscription_id
        db.commit()
        logger.info(f"[billing] User {user_id} subscribed to {plan} (company {company.id if company else '?'})")
    except Exception as e:
        logger.error(f"[billing] Error activating subscription: {e}")
        db.rollback()
    finally:
        db.close()


def _set_company_tier_by_subscription(sub_id: str, tier: str) -> None:
    """Update plan_tier for the company owning the given Stripe subscription."""
    if not sub_id:
        return
    db = db_session()
    try:
        company = db.query(Company).filter(Company.stripe_subscription_id == sub_id).first()
        if not company:
            logger.warning(f"[billing] subscription {sub_id} matches no company")
            return
        company.plan_tier = tier
        if tier in ("starter", "pro", "agency"):
            # Active paid subscription — clear any lingering trial expiry that would
            # otherwise still block the Flask gate.
            for user in db.query(User).filter(User.company_id == company.id).all():
                user.trial_expires_at = None
        db.commit()
        logger.info(f"[billing] Company {company.id} tier -> {tier} (sub {sub_id})")
    except Exception as e:
        logger.error(f"[billing] Error setting tier for subscription {sub_id}: {e}")
        db.rollback()
    finally:
        db.close()


# Map Stripe subscription status -> our handling. Active/trialing resolve to the
# paid plan from the price; dunning/terminal states revoke service.
def _handle_subscription_updated(sub_data: dict):
    """Portal-initiated upgrades/downgrades/pauses and dunning transitions."""
    sub_id = sub_data.get("id")
    status = (sub_data.get("status") or "").lower()
    if status in ("past_due", "unpaid"):
        _set_company_tier_by_subscription(sub_id, "past_due")
        return
    if status in ("canceled", "incomplete_expired"):
        _set_company_tier_by_subscription(sub_id, "cancelled")
        return
    if status in ("active", "trialing"):
        price_id = ""
        try:
            price_id = sub_data["items"]["data"][0]["price"]["id"]
        except Exception:
            pass
        plan = _plan_for_price(price_id)
        if plan:
            _set_company_tier_by_subscription(sub_id, plan)
        else:
            logger.warning(f"[billing] subscription {sub_id} active but price {price_id} unmapped")


def _handle_subscription_cancelled(sub_data: dict):
    """Close access when the Stripe subscription ends: mark the company
    cancelled and expire the trial for its users so the trial gate blocks."""
    sub_id = sub_data.get("id")
    logger.info(f"[billing] Subscription cancelled: {sub_id}")
    if not sub_id:
        return
    db = db_session()
    try:
        company = db.query(Company).filter(Company.stripe_subscription_id == sub_id).first()
        if not company:
            logger.warning(f"[billing] cancelled subscription {sub_id} matches no company")
            return
        company.plan_tier = "trial"
        for user in db.query(User).filter(User.company_id == company.id).all():
            user.trial_expires_at = datetime.utcnow()
        db.commit()
        logger.info(f"[billing] Company {company.id} access closed after cancellation")
    except Exception as e:
        logger.error(f"[billing] Error handling cancellation: {e}")
        db.rollback()
    finally:
        db.close()


def _handle_payment_failed(invoice_data: dict):
    """A renewal/charge failed — move the tenant to past_due so the worker stops
    serving paid features. Reactivation happens on the next payment_succeeded /
    subscription.updated(active). We do NOT hard-cancel here (Stripe keeps retrying
    per dunning settings); customer.subscription.deleted is the terminal close."""
    sub_id = invoice_data.get("subscription")
    logger.warning(f"[billing] Payment failed for invoice {invoice_data.get('id')} (sub {sub_id})")
    _set_company_tier_by_subscription(sub_id, "past_due")


def _handle_payment_succeeded(invoice_data: dict):
    """A charge succeeded — restore the paid tier from the subscription's price in
    case a prior failure had moved the tenant to past_due."""
    sub_id = invoice_data.get("subscription")
    if not sub_id:
        return
    stripe = _get_stripe()
    plan = _tier_from_subscription(stripe, sub_id)
    if plan:
        _set_company_tier_by_subscription(sub_id, plan)
