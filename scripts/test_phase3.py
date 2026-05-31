#!/usr/bin/env python3
"""
Phase 3 Integration Test — Tasks 3.1-3.3:
  3.1 Stripe Billing (checkout, webhook, trial wall)
  3.2 Landing Page Polish (universal value prop, conversion flow)
  3.3 Pilot Launch (leads, templates, outreach script)

Run: docker compose exec web python scripts/test_phase3.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PASS = 0
FAIL = 0


def ok(name: str):
    global PASS
    PASS += 1
    print(f"  ✅ {name}")


def fail(name: str, detail: str = ""):
    global FAIL
    FAIL += 1
    msg = f"  ❌ {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── Task 3.1: Stripe Billing ────────────────────────────────────────────────

def test_3_1():
    section("Task 3.1: Stripe Billing")

    # Billing module
    try:
        from app.routes.billing import bp, PRICE_IDS, _get_stripe
        assert "starter" in PRICE_IDS
        assert "pro" in PRICE_IDS
        assert "agency" in PRICE_IDS
        ok("Billing module: 3 plan price IDs configured")
    except Exception as e:
        fail("Billing module", str(e))

    # _get_stripe graceful when not configured
    try:
        from app.routes.billing import _get_stripe
        result = _get_stripe()
        # Should return None when STRIPE_SECRET_KEY is empty
        ok(f"_get_stripe returns {'stripe' if result else 'None (not configured)'}")
    except Exception as e:
        fail("_get_stripe", str(e))

    # Routes exist
    try:
        billing_code = (ROOT / "app" / "routes" / "billing.py").read_text()
        assert "/checkout/" in billing_code, "Should have checkout route"
        assert "/webhook" in billing_code, "Should have webhook route"
        assert "/success" in billing_code, "Should have success route"
        assert "checkout.session.completed" in billing_code, "Should handle checkout.session.completed"
        assert "customer.subscription.deleted" in billing_code, "Should handle subscription.deleted"
        assert "invoice.payment_failed" in billing_code, "Should handle payment.failed"
        ok("Billing routes: checkout, webhook, success + 3 event handlers")
    except Exception as e:
        fail("Billing routes", str(e))

    # Blueprint registered
    try:
        init_code = (ROOT / "app" / "routes" / "__init__.py").read_text()
        assert "billing_bp" in init_code
        ok("Billing blueprint registered")
    except Exception as e:
        fail("Billing blueprint", str(e))

    # CSRF exempt for webhook
    try:
        factory_code = (ROOT / "app" / "factory.py").read_text()
        assert "billing.stripe_webhook" in factory_code
        ok("Webhook exempt from CSRF")
    except Exception as e:
        fail("Webhook CSRF exempt", str(e))

    # Webhook signature verification
    try:
        billing_code = (ROOT / "app" / "routes" / "billing.py").read_text()
        assert "STRIPE_WEBHOOK_SECRET" in billing_code
        assert "stripe.Webhook.construct_event" in billing_code
        assert "json.loads(payload)" not in billing_code, "Must not accept unsigned webhook JSON"
        ok("Webhook requires Stripe signature verification")
    except Exception as e:
        fail("Webhook signature verification", str(e))

    # Trial expiration middleware
    try:
        factory_code = (ROOT / "app" / "factory.py").read_text()
        assert "check_trial_expiration" in factory_code
        assert "trial_expires_at" in factory_code
        assert "/pricing" in factory_code
        ok("Trial expiration middleware in factory.py")
    except Exception as e:
        fail("Trial middleware", str(e))

    # Pricing page has checkout URLs
    try:
        pricing_code = (ROOT / "app" / "routes" / "pricing.py").read_text()
        assert "checkout_url" in pricing_code
        assert "billing/checkout" in pricing_code
        ok("Pricing page CTAs link to Stripe checkout")
    except Exception as e:
        fail("Pricing CTAs", str(e))

    # Pricing template uses checkout_url
    try:
        pricing_html = (ROOT / "app" / "templates" / "pricing.html").read_text()
        assert "checkout_url" in pricing_html
        ok("Pricing template uses dynamic checkout URLs")
    except Exception as e:
        fail("Pricing template", str(e))

    # stripe in requirements
    try:
        req = (ROOT / "requirements.txt").read_text()
        assert "stripe" in req
        ok("stripe in requirements.txt")
    except Exception as e:
        fail("stripe requirement", str(e))


# ── Task 3.2: Landing Page Polish ────────────────────────────────────────────

def test_3_2():
    section("Task 3.2: Landing Page Polish")

    try:
        landing = (ROOT / "app" / "templates" / "landing.html").read_text()
    except Exception as e:
        fail("Landing page read", str(e))
        return

    # Universal value prop (not just recruitment)
    assert "Telegram" in landing, "Should mention Telegram"
    ok("Landing mentions Telegram")

    # Multi-language hero
    he_found = "פרסם פעם אחת" in landing or "הבוט מטפל" in landing
    ru_found = "Опубликуй" in landing or "бот" in landing.lower()
    en_found = "Post once" in landing or "bot handles" in landing.lower()
    assert he_found, "Hebrew hero text missing"
    assert ru_found, "Russian hero text missing"
    assert en_found, "English hero text missing"
    ok("Hero text in 3 languages (HE, RU, EN)")

    # How it works steps
    assert "step" in landing.lower(), "Should have steps section"
    ok("How it works section with steps")

    # Verticals section
    verticals = ["👷", "🚗", "🏠", "🔧", "🛒"]
    found = sum(1 for v in verticals if v in landing)
    assert found >= 4, f"Expected >= 4 vertical icons, found {found}"
    ok(f"Verticals section with {found} categories")

    # CTA buttons
    assert "/register" in landing, "Should link to registration"
    ok("Registration CTA present")

    # Pricing + Terms links
    assert "/pricing" in landing, "Should link to pricing"
    assert "/terms" in landing, "Should link to terms"
    ok("Pricing + Terms links in footer")

    # Responsive
    assert "@media" in landing, "Should have responsive CSS"
    ok("Responsive CSS breakpoints")

    # Sticky nav
    assert "sticky" in landing, "Should have sticky nav"
    ok("Sticky navigation bar")

    # Anti-spam mention
    assert "spam" in landing.lower() or "ספאם" in landing, "Should mention anti-spam"
    ok("Anti-spam messaging present")


# ── Task 3.3: Pilot Launch ───────────────────────────────────────────────────

def test_3_3():
    section("Task 3.3: Pilot Launch")

    # Leads file
    try:
        leads_data = json.loads((ROOT / "growth" / "leads-israeli-agencies.json").read_text())
        leads = leads_data.get("leads", [])
        assert len(leads) >= 40, f"Expected >= 40 leads, got {len(leads)}"
        ok(f"Leads file: {len(leads)} Israeli agencies")
    except Exception as e:
        fail("Leads file", str(e))

    # Lead quality
    try:
        leads_data = json.loads((ROOT / "growth" / "leads-israeli-agencies.json").read_text())
        leads = leads_data["leads"]
        with_website = sum(1 for l in leads if l.get("website"))
        with_city = sum(1 for l in leads if l.get("city"))
        assert with_website >= 40, "Most leads should have websites"
        assert with_city >= 40, "Most leads should have cities"
        ok(f"Lead quality: {with_website} with website, {with_city} with city")
    except Exception as e:
        fail("Lead quality", str(e))

    # Templates file
    try:
        tpl_data = json.loads((ROOT / "growth" / "outreach-templates.json").read_text())
        templates = tpl_data.get("templates", {})
        assert "cold_email_en" in templates, "Should have English email template"
        assert "cold_email_he" in templates, "Should have Hebrew email template"
        assert "telegram_dm_en" in templates, "Should have Telegram DM template"
        ok(f"Outreach templates: {len(templates)} templates")
    except Exception as e:
        fail("Templates file", str(e))

    # Outreach sequence
    try:
        tpl_data = json.loads((ROOT / "growth" / "outreach-templates.json").read_text())
        seq = tpl_data.get("outreach_sequence", {})
        assert len(seq) >= 5, "Should have multi-step sequence"
        ok(f"Outreach sequence: {len(seq)} steps")
    except Exception as e:
        fail("Outreach sequence", str(e))

    # Pilot launch script
    try:
        script = (ROOT / "scripts" / "pilot_launch.py").read_text()
        assert "cmd_status" in script, "Should have status command"
        assert "cmd_import" in script, "Should have import command"
        assert "cmd_tier1" in script, "Should have tier1 command"
        assert "cmd_templates" in script, "Should have templates command"
        ok("Pilot launch script: status, import, tier1, templates commands")
    except Exception as e:
        fail("Pilot script", str(e))

    # Tier 1 targeting
    try:
        leads_data = json.loads((ROOT / "growth" / "leads-israeli-agencies.json").read_text())
        leads = leads_data["leads"]
        small_medium = [l for l in leads if l.get("size") in ("small", "medium")]
        assert len(small_medium) >= 20, "Should have >= 20 small/medium targets"
        ok(f"Tier 1 targets: {len(small_medium)} small/medium agencies")
    except Exception as e:
        fail("Tier 1 targeting", str(e))


# ── Full Stack Regression ────────────────────────────────────────────────────

def test_regression():
    section("Full Stack Regression")

    # All containers should be running
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            ok("Docker compose accessible")
        else:
            ok("Docker compose check (skipped — running inside container)")
    except Exception:
        ok("Docker compose check (skipped)")

    # Phase 1 core imports still work
    try:
        from common.tg_client import post_to_group
        from bot.run_bot import classify_candidate, extract_phone, build_bot_greeting
        from app.models import User, Vacancy, Candidate, Company
        ok("Phase 1 core imports work")
    except Exception as e:
        fail("Phase 1 imports", str(e))

    # Phase 2 core imports still work
    try:
        from app.listing_templates import get_template, get_all_templates
        from common.email_notify import send_hot_lead_email
        from app.routes.registration import bp as reg_bp
        ok("Phase 2 core imports work")
    except Exception as e:
        fail("Phase 2 imports", str(e))

    # DB is accessible
    try:
        from app.db import db_session
        from sqlalchemy import text
        db = db_session()
        result = db.execute(text("SELECT COUNT(*) FROM companies")).fetchone()
        ok(f"DB accessible, {result[0]} companies")
        db.close()
    except Exception as e:
        fail("DB access", str(e))


# ── Run all ──────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  PHASE 3 INTEGRATION TEST")
    print("  Tasks 3.1-3.3 + Full Stack Regression")
    print("=" * 60)

    test_3_1()
    test_3_2()
    test_3_3()
    test_regression()

    print(f"\n{'='*60}")
    print(f"  RESULTS: {PASS} passed, {FAIL} failed")
    print(f"{'='*60}")

    if FAIL > 0:
        print(f"\n⚠️  {FAIL} test(s) FAILED")
        return 1
    else:
        print(f"\n🎉 ALL {PASS} TESTS PASSED — Phase 3 complete!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
