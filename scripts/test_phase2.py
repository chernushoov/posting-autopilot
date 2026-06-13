#!/usr/bin/env python3
"""
Phase 2 Integration Test — verifies Tasks 2.1-2.6:
  2.1 Self-Service Signup (User model, registration, trial)
  2.2 Listing Templates (pre-fill system)
  2.3 WhatsApp Integration (wa.me links)
  2.4 Email Notifications (module, function)
  2.5 CSV Export (endpoint, format)
  2.6 Security (CSRF, rate limiting, ToS)

Run: docker compose exec web python scripts/test_phase2.py
"""
from __future__ import annotations
import json
import os
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


# ── Task 2.1: Self-Service Signup ────────────────────────────────────────────

def test_2_1():
    section("Task 2.1: Self-Service Signup")

    # User model
    try:
        from app.models import User, UserRole
        assert hasattr(User, 'email'), "User missing email"
        assert hasattr(User, 'password_hash'), "User missing password_hash"
        assert hasattr(User, 'company_id'), "User missing company_id"
        assert hasattr(User, 'role'), "User missing role"
        assert hasattr(User, 'trial_expires_at'), "User missing trial_expires_at"
        ok("User model has all fields")
    except Exception as e:
        fail("User model", str(e))

    # UserRole enum
    try:
        from app.models import UserRole
        assert hasattr(UserRole, 'admin')
        assert hasattr(UserRole, 'owner')
        assert hasattr(UserRole, 'member')
        ok("UserRole enum: admin, owner, member")
    except Exception as e:
        fail("UserRole enum", str(e))

    # Registration route
    try:
        from app.routes.registration import bp, _hash_password, _valid_email, TRIAL_DAYS
        assert TRIAL_DAYS == 3, f"Trial should be 3 days, got {TRIAL_DAYS}"
        ok(f"Registration module importable, trial={TRIAL_DAYS} days")
    except Exception as e:
        fail("Registration module", str(e))

    # Password hashing
    try:
        from app.routes.registration import _hash_password
        from common.passwords import verify_password
        h = _hash_password("test123")
        assert len(h) > 64, "Password hash should use a salted KDF, not raw SHA-256"
        valid, should_upgrade = verify_password(h, "test123")
        assert valid is True, "Generated hash should verify with the original password"
        assert should_upgrade is False, "Fresh hashes should not need upgrade"
        invalid, _ = verify_password(h, "other")
        assert invalid is False, "Different password should not verify"
        ok("Password hashing uses salted Werkzeug hashes")
    except Exception as e:
        fail("Password hashing", str(e))

    # Email validation
    try:
        from app.routes.registration import _valid_email
        assert _valid_email("test@example.com") == True
        assert _valid_email("user@co.il") == True
        assert _valid_email("invalid") == False
        assert _valid_email("@no-user.com") == False
        ok("Email validation works")
    except Exception as e:
        fail("Email validation", str(e))

    # Templates exist
    try:
        register_html = (ROOT / "app" / "templates" / "register.html").read_text()
        assert "email" in register_html, "Register form should have email field"
        assert "password" in register_html, "Register form should have password field"
        assert "company_name" in register_html, "Register form should have company_name"
        # The trial is now advertised via i18n (reg_subtitle), not a hardcoded English
        # string, so the page reads correctly in RU/HE/EN. Verify the key is used and
        # the translated copy still mentions the 3-day trial.
        assert "reg_subtitle" in register_html, "Register page should show the trial subtitle"
        from common.i18n import ui as _ui
        assert "3" in _ui("reg_subtitle", "en", days=TRIAL_DAYS) and "3" in _ui("reg_subtitle", "ru", days=TRIAL_DAYS), "reg_subtitle should mention the 3-day trial"
        ok("register.html template exists and has required fields")

        login_html = (ROOT / "app" / "templates" / "user_login.html").read_text()
        assert "email" in login_html
        ok("user_login.html template exists")
    except Exception as e:
        fail("Registration templates", str(e))

    # DB table
    try:
        from app.schema import bootstrap_schema
        from app.db import engine
        from sqlalchemy import inspect
        bootstrap_schema()
        cols = {column["name"] for column in inspect(engine).get_columns("users")}
        assert 'email' in cols, "users.email missing"
        assert 'password_hash' in cols, "users.password_hash missing"
        assert 'trial_expires_at' in cols, "users.trial_expires_at missing"
        ok("DB: users table exists with all columns")
    except Exception as e:
        fail("Users DB table", str(e))


# ── Task 2.2: Listing Templates ─────────────────────────────────────────────

def test_2_2():
    section("Task 2.2: Listing Templates")

    try:
        from app.listing_templates import get_template, get_all_templates, TEMPLATES
        assert len(TEMPLATES) >= 5, f"Expected >= 5 templates, got {len(TEMPLATES)}"
        ok(f"Templates module: {len(TEMPLATES)} templates defined")
    except Exception as e:
        fail("Templates module", str(e))
        return

    # Each template has required fields
    try:
        from app.listing_templates import TEMPLATES
        required = ['label', 'emoji', 'listing_type', 'bot_introduction',
                     'bot_faq_knowledge', 'bot_qualifying_questions',
                     'bot_hot_criteria', 'bot_cold_criteria']
        for key, tpl in TEMPLATES.items():
            for field in required:
                assert field in tpl, f"Template '{key}' missing '{field}'"
        ok("All templates have required fields")
    except Exception as e:
        fail("Template fields", str(e))

    # Specific templates
    try:
        from app.listing_templates import get_template
        auto = get_template("auto")
        assert "car" in auto['label'].lower() or "auto" in auto['listing_type'], "Auto template should be about cars"
        assert len(auto['bot_qualifying_questions']) >= 2, "Should have qualifying questions"
        ok("Auto (car) template has content")

        realestate = get_template("realestate")
        assert len(realestate['bot_qualifying_questions']) >= 3, "Realestate should have questions"
        ok("Realestate template has content")

        custom = get_template("custom")
        assert custom['bot_introduction'] == "", "Custom should be blank"
        ok("Custom template is blank (as expected)")
    except Exception as e:
        fail("Template content", str(e))

    # Template picker in form
    try:
        form_code = (ROOT / "app" / "templates" / "vacancy_new.html").read_text()
        assert "loadTemplate" in form_code, "Form should have loadTemplate JS function"
        assert "template-btn" in form_code, "Form should have template buttons"
        assert "/api/template/" in form_code, "Form should fetch template data via API"
        ok("vacancy_new.html has template picker UI + JS")
    except Exception as e:
        fail("Template picker UI", str(e))

    # API endpoint
    try:
        route_code = (ROOT / "app" / "routes" / "vacancies.py").read_text()
        assert "get_template_data" in route_code or "api/template" in route_code
        ok("Vacancies route has template API endpoint")
    except Exception as e:
        fail("Template API endpoint", str(e))


# ── Task 2.3: WhatsApp Integration ──────────────────────────────────────────

def test_2_3():
    section("Task 2.3: WhatsApp field (no auto-redirects)")

    # Model field — the owner can still store a contact number for reference
    try:
        from app.models import Vacancy
        assert hasattr(Vacancy, 'whatsapp_number'), "Vacancy missing whatsapp_number"
        ok("Vacancy model has whatsapp_number")
    except Exception as e:
        fail("Vacancy whatsapp_number", str(e))

    # Posting asset must NOT inject a wa.me redirect into public posts (invite-only:
    # the bot handles contact, we don't push people to the owner's WhatsApp)
    try:
        tasks_code = (ROOT / "worker" / "tasks.py").read_text()
        assert "wa.me" not in tasks_code, "tasks.py should NOT generate wa.me redirects"
        ok("Posting asset builder has no wa.me redirect")
    except Exception as e:
        fail("WhatsApp removed from posting asset", str(e))

    # Hot-lead notification must NOT contain a wa.me redirect (phone is shown instead)
    try:
        bot_code = (ROOT / "bot" / "run_bot.py").read_text()
        assert "wa.me" not in bot_code, "Bot notifications should NOT include wa.me redirects"
        ok("Hot lead notification has no wa.me redirect")
    except Exception as e:
        fail("WhatsApp removed from notification", str(e))

    # Form has WhatsApp field
    try:
        form_code = (ROOT / "app" / "templates" / "vacancy_new.html").read_text()
        assert "whatsapp_number" in form_code, "Form should have WhatsApp number field"
        ok("Vacancy form has WhatsApp number field")
    except Exception as e:
        fail("WhatsApp form field", str(e))

    # DB column
    try:
        from app.schema import bootstrap_schema
        from app.db import engine
        from sqlalchemy import inspect
        bootstrap_schema()
        cols = {column["name"] for column in inspect(engine).get_columns("vacancies")}
        assert "whatsapp_number" in cols, "whatsapp_number column missing from DB"
        ok("DB: vacancies.whatsapp_number exists")
    except Exception as e:
        fail("WhatsApp DB column", str(e))


# ── Task 2.4: Email Notifications ────────────────────────────────────────────

def test_2_4():
    section("Task 2.4: Email Notifications")

    try:
        from common.email_notify import send_hot_lead_email, is_email_configured
        ok("email_notify module importable")
    except ImportError as e:
        fail("email_notify import", str(e))
        return

    try:
        from common.email_notify import is_email_configured
        # Should return False (no SMTP configured in test env)
        assert isinstance(is_email_configured(), bool)
        ok("is_email_configured() works")
    except Exception as e:
        fail("is_email_configured", str(e))

    # Bot imports and uses email
    try:
        bot_code = (ROOT / "bot" / "run_bot.py").read_text()
        assert "send_hot_lead_email" in bot_code, "Bot should call send_hot_lead_email"
        ok("Bot calls send_hot_lead_email on HOT leads")
    except Exception as e:
        fail("Email in bot", str(e))


# ── Task 2.5: CSV Export ─────────────────────────────────────────────────────

def test_2_5():
    section("Task 2.5: CSV Export")

    # Route exists
    try:
        route_code = (ROOT / "app" / "routes" / "candidates.py").read_text()
        assert "export_csv" in route_code or "/export" in route_code
        assert "text/csv" in route_code, "Should return CSV content type"
        assert "candidates_export.csv" in route_code, "Should set filename"
        ok("CSV export endpoint exists with proper content type")
    except Exception as e:
        fail("CSV export route", str(e))

    # CSV has correct columns
    try:
        route_code = (ROOT / "app" / "routes" / "candidates.py").read_text()
        expected_cols = ["Name", "Phone", "Status", "Classification", "Score", "Summary", "Listing"]
        for col in expected_cols:
            assert col in route_code, f"CSV should include {col} column"
        ok(f"CSV includes all {len(expected_cols)} required columns")
    except Exception as e:
        fail("CSV columns", str(e))

    # Export button in template
    try:
        tpl_code = (ROOT / "app" / "templates" / "candidates.html").read_text()
        assert "export" in tpl_code.lower(), "Template should have export link"
        assert "CSV" in tpl_code, "Template should mention CSV"
        ok("Candidates template has Export CSV button")
    except Exception as e:
        fail("Export button", str(e))

    # Phone + classification visible in table
    try:
        tpl_code = (ROOT / "app" / "templates" / "candidates.html").read_text()
        assert "c.phone" in tpl_code, "Table should show phone"
        assert "c.classification" in tpl_code, "Table should show classification"
        assert "hot" in tpl_code, "Should have hot styling"
        ok("Candidates table shows phone + classification with styling")
    except Exception as e:
        fail("Candidates table", str(e))


# ── Task 2.6: Security ──────────────────────────────────────────────────────

def test_2_6():
    section("Task 2.6: Security")

    # CSRF
    try:
        factory_code = (ROOT / "app" / "factory.py").read_text()
        assert "CSRFProtect" in factory_code, "factory.py should use CSRFProtect"
        ok("CSRF protection enabled via flask-wtf")
    except Exception as e:
        fail("CSRF protection", str(e))

    # CSRF token in layout
    try:
        layout_code = (ROOT / "app" / "templates" / "_layout.html").read_text()
        assert "csrf_token" in layout_code, "Layout should include csrf_token meta tag"
        ok("CSRF token in layout meta tag")
    except Exception as e:
        fail("CSRF in layout", str(e))

    # Rate limiting on login
    try:
        auth_code = (ROOT / "app" / "routes" / "auth_routes.py").read_text()
        assert "_check_rate_limit" in auth_code, "Login should check rate limit"
        assert "_record_attempt" in auth_code, "Login should record attempts"
        assert "Too many" in auth_code, "Should show rate limit message"
        ok("Login rate limiting implemented")
    except Exception as e:
        fail("Login rate limiting", str(e))

    # Rate limit config
    try:
        factory_code = (ROOT / "app" / "factory.py").read_text()
        assert "LOGIN_RATE_LIMIT" in factory_code
        assert "LOGIN_RATE_WINDOW" in factory_code
        ok("Rate limit constants configured")
    except Exception as e:
        fail("Rate limit config", str(e))

    # Legacy user-login POST also rate-limited
    try:
        registration_code = (ROOT / "app" / "routes" / "registration.py").read_text()
        assert "_check_rate_limit" in registration_code
        assert "_record_attempt" in registration_code
        ok("Legacy /user-login POST uses login rate limiter")
    except Exception as e:
        fail("Legacy user-login rate limiting", str(e))

    # Flask session secret hardening
    try:
        config_code = (ROOT / "app" / "config.py").read_text()
        factory_code = (ROOT / "app" / "factory.py").read_text()
        assert 'os.getenv("FLASK_SECRET_KEY", "").strip()' in config_code
        assert "FORBIDDEN_FLASK_SECRET_KEYS" in config_code
        assert "flask_secret_key()" in factory_code
        ok("Flask session key rejects weak defaults at startup")
    except Exception as e:
        fail("Flask secret hardening", str(e))

    # Upload hardening
    try:
        vacancies_code = (ROOT / "app" / "routes" / "vacancies.py").read_text()
        factory_code = (ROOT / "app" / "factory.py").read_text()
        assert "secure_filename" in vacancies_code
        assert "ALLOWED_IMAGE_EXTENSIONS" in vacancies_code
        assert "MAX_CONTENT_LENGTH" in factory_code
        assert "X-Content-Type-Options" in factory_code
        assert 'session.get("current_company_id")' in factory_code
        assert "Vacancy.company_id == company_id" in factory_code
        ok("Image uploads constrain filenames, types, and request size")
    except Exception as e:
        fail("Upload hardening", str(e))

    # Connection secrets must not live in Flask's client-side session/templates
    try:
        auth_code = (ROOT / "app" / "routes" / "auth_routes.py").read_text()
        tg_html = (ROOT / "app" / "templates" / "connect_telegram.html").read_text()
        fb_html = (ROOT / "app" / "templates" / "connect_facebook.html").read_text()
        assert "create_connection_flow" in auth_code
        assert 'session["tg_api_hash"]' not in auth_code
        assert 'session["tg_phone_code_hash"]' not in auth_code
        assert 'session["fb_app_secret"]' not in auth_code
        assert 'name="api_hash" value="{{ tg_api_hash' not in tg_html
        assert 'name="phone_code_hash"' not in tg_html
        assert "session.get('fb_app_id'" not in fb_html
        ok("Connection credentials use server-side opaque flow storage")
    except Exception as e:
        fail("Connection credential flow storage", str(e))

    # Facebook OAuth state validation
    try:
        auth_code = (ROOT / "app" / "routes" / "auth_routes.py").read_text()
        fb_client_code = (ROOT / "common" / "fb_client.py").read_text()
        assert "oauth_state = secrets.token_urlsafe" in auth_code
        assert "state=oauth_state" in auth_code
        assert 'request.args.get("state"' in auth_code
        assert "OAuth state mismatch" in auth_code
        assert 'params["state"] = state' in fb_client_code
        ok("Facebook OAuth uses and validates state")
    except Exception as e:
        fail("Facebook OAuth state", str(e))

    # Terms of Service
    try:
        terms_html = (ROOT / "app" / "templates" / "terms.html").read_text()
        assert "Terms of Service" in terms_html
        assert "Anti-Spam" in terms_html or "spam" in terms_html.lower()
        assert "Privacy" in terms_html or "Data" in terms_html
        ok("Terms of Service page exists with content")
    except Exception as e:
        fail("Terms page", str(e))

    # Terms route
    try:
        auth_code = (ROOT / "app" / "routes" / "auth_routes.py").read_text()
        assert "/terms" in auth_code, "Should have /terms route"
        ok("/terms route exists")
    except Exception as e:
        fail("Terms route", str(e))

    # flask-wtf in requirements
    try:
        req = (ROOT / "requirements.txt").read_text()
        assert "flask-wtf" in req, "flask-wtf should be in requirements.txt"
        ok("flask-wtf in requirements.txt")
    except Exception as e:
        fail("flask-wtf requirement", str(e))


# ── Backward Compatibility ───────────────────────────────────────────────────

def test_backward_compat():
    section("Backward Compatibility")

    # Admin login still works
    try:
        auth_code = (ROOT / "app" / "routes" / "auth_routes.py").read_text()
        assert "admin_login_ok" in auth_code, "Admin login should still exist"
        assert "/login" in auth_code
        ok("Admin login route still exists")
    except Exception as e:
        fail("Admin login", str(e))

    # Landing is invite-gated: sign-in present, no public self-serve register CTA
    try:
        landing = (ROOT / "app" / "templates" / "landing.html").read_text()
        assert "user-login" in landing or "login" in landing, "Landing should link to login"
        assert "/register" not in landing, "Landing should NOT push public self-serve registration (invite-only)"
        ok("Landing page is invite-gated (sign-in, no public register CTA)")
    except Exception as e:
        fail("Landing links", str(e))


# ── Run all ──────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  PHASE 2 INTEGRATION TEST")
    print("  Tasks 2.1-2.6 Verification")
    print("=" * 60)

    test_2_1()
    test_2_2()
    test_2_3()
    test_2_4()
    test_2_5()
    test_2_6()
    test_backward_compat()

    print(f"\n{'='*60}")
    print(f"  RESULTS: {PASS} passed, {FAIL} failed")
    print(f"{'='*60}")

    if FAIL > 0:
        print(f"\n⚠️  {FAIL} test(s) FAILED")
        return 1
    else:
        print(f"\n🎉 ALL {PASS} TESTS PASSED — Phase 2 complete!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
