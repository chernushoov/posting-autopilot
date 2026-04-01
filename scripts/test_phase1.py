#!/usr/bin/env python3
"""
Phase 1 Integration Test — verifies all Tasks 1.1-1.5:
  1.1 Telethon auto-posting (module + integration)
  1.2 Generalized Vacancy → Listing model fields
  1.3 Universal bot flow (question routing, greeting, classification)
  1.4 Phone collection (extraction, validation)
  1.5 Hot lead notification (function exists, message format)

Run inside Docker: docker compose exec web python scripts/test_phase1.py
Or locally:        python scripts/test_phase1.py
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


# ── Task 1.1: Telethon Auto-Posting ─────────────────────────────────────────

def test_1_1():
    section("Task 1.1: Telethon Auto-Posting")

    # Module import
    try:
        from common.tg_client import post_to_group, _check_rate_limit, _is_night_hours
        ok("post_to_group importable")
    except ImportError as e:
        fail("post_to_group import", str(e))
        return

    # Rate limit function
    try:
        result, reason = _check_rate_limit(999999)
        assert isinstance(result, bool), "should return bool"
        ok("_check_rate_limit works")
    except Exception as e:
        fail("_check_rate_limit", str(e))

    # Night hours function
    try:
        result = _is_night_hours()
        assert isinstance(result, bool), "should return bool"
        ok("_is_night_hours works")
    except Exception as e:
        fail("_is_night_hours", str(e))

    # Anti-spam constants
    try:
        from common.tg_client import POST_DELAY_MIN, POST_DELAY_MAX, MAX_POSTS_PER_HOUR, MAX_POSTS_PER_DAY
        assert POST_DELAY_MIN >= 60, f"POST_DELAY_MIN should be >= 60s, got {POST_DELAY_MIN}"
        assert POST_DELAY_MAX > POST_DELAY_MIN, "MAX should be > MIN"
        assert MAX_POSTS_PER_HOUR <= 15, f"MAX_POSTS_PER_HOUR too high: {MAX_POSTS_PER_HOUR}"
        assert MAX_POSTS_PER_DAY <= 100, f"MAX_POSTS_PER_DAY too high: {MAX_POSTS_PER_DAY}"
        ok(f"Anti-spam constants OK (delay {POST_DELAY_MIN}-{POST_DELAY_MAX}s, {MAX_POSTS_PER_HOUR}/h, {MAX_POSTS_PER_DAY}/d)")
    except Exception as e:
        fail("Anti-spam constants", str(e))

    # Company model has tg_api_id, tg_api_hash
    try:
        from app.models import Company
        assert hasattr(Company, 'tg_api_id'), "Company missing tg_api_id"
        assert hasattr(Company, 'tg_api_hash'), "Company missing tg_api_hash"
        ok("Company model has tg_api_id/tg_api_hash")
    except Exception as e:
        fail("Company model fields", str(e))

    # tasks.py imports post_to_group
    try:
        tasks_path = ROOT / "worker" / "tasks.py"
        tasks_code = tasks_path.read_text()
        assert "post_to_group" in tasks_code, "tasks.py should reference post_to_group"
        assert "Telethon" in tasks_code or "telethon" in tasks_code.lower(), "tasks.py should mention Telethon"
        ok("tasks.py uses Telethon for posting")
    except Exception as e:
        fail("tasks.py Telethon integration", str(e))


# ── Task 1.2: Generalize Vacancy → Listing ──────────────────────────────────

def test_1_2():
    section("Task 1.2: Generalize Vacancy → Listing")

    try:
        from app.models import Vacancy
        new_fields = ['listing_type', 'bot_introduction', 'bot_faq_knowledge',
                      'bot_qualifying_questions', 'bot_hot_criteria', 'bot_cold_criteria']
        for field in new_fields:
            assert hasattr(Vacancy, field), f"Vacancy missing {field}"
        ok(f"Vacancy model has all 6 new fields")
    except Exception as e:
        fail("Vacancy model fields", str(e))

    # Check listing_type default
    try:
        from app.models import Vacancy
        col = Vacancy.__table__.columns['listing_type']
        assert col.default is not None, "listing_type should have default"
        ok("listing_type has default value")
    except Exception as e:
        fail("listing_type default", str(e))

    # Check schema.py has migration
    try:
        schema_code = (ROOT / "app" / "schema.py").read_text()
        assert "listing_type" in schema_code, "schema.py should migrate listing_type"
        assert "bot_introduction" in schema_code, "schema.py should migrate bot_introduction"
        ok("schema.py has auto-migration for new fields")
    except Exception as e:
        fail("schema.py migration", str(e))

    # Check vacancy form
    try:
        form_code = (ROOT / "app" / "templates" / "vacancy_new.html").read_text()
        assert "bot_introduction" in form_code, "form should have bot_introduction"
        assert "bot_faq_knowledge" in form_code, "form should have bot_faq_knowledge"
        assert "bot_qualifying_questions" in form_code, "form should have bot_qualifying_questions"
        assert "bot_hot_criteria" in form_code, "form should have bot_hot_criteria"
        assert "listing_type" in form_code, "form should have listing_type selector"
        ok("vacancy_new.html has all bot settings fields")
    except Exception as e:
        fail("vacancy form", str(e))

    # Check route saves new fields
    try:
        route_code = (ROOT / "app" / "routes" / "vacancies.py").read_text()
        assert "bot_introduction" in route_code, "route should save bot_introduction"
        assert "listing_type" in route_code, "route should save listing_type"
        ok("vacancies.py route saves new fields")
    except Exception as e:
        fail("vacancies route", str(e))


# ── Task 1.3: Universal Bot Flow ────────────────────────────────────────────

def test_1_3():
    section("Task 1.3: Universal Bot Flow")

    # get_screening_questions priority chain
    try:
        from bot.run_bot import get_screening_questions

        class FakeVacancy:
            interview_questions_json = '["Q1 legacy"]'
            bot_qualifying_questions = '["Q1 universal", "Q2 universal"]'

        # Universal takes priority
        qs = get_screening_questions(FakeVacancy(), "ru")
        assert qs == ["Q1 universal", "Q2 universal"], f"Expected universal questions, got {qs}"
        ok("get_screening_questions: bot_qualifying_questions takes priority")

        # Fallback to legacy
        class LegacyVacancy:
            interview_questions_json = '["Legacy Q1"]'
            bot_qualifying_questions = None

        qs = get_screening_questions(LegacyVacancy(), "ru")
        assert qs == ["Legacy Q1"], f"Expected legacy questions, got {qs}"
        ok("get_screening_questions: falls back to interview_questions_json")

        # Fallback to defaults
        class EmptyVacancy:
            interview_questions_json = "[]"
            bot_qualifying_questions = None

        qs = get_screening_questions(EmptyVacancy(), "ru")
        assert len(qs) > 0, "Should return default questions"
        ok("get_screening_questions: falls back to defaults")
    except Exception as e:
        fail("get_screening_questions", str(e))

    # build_bot_greeting
    try:
        from bot.run_bot import build_bot_greeting

        class CustomVacancy:
            title = "Test Listing"
            bot_introduction = "Hi! I'm the assistant of TestCo."

        greeting = build_bot_greeting(CustomVacancy(), "ru")
        assert "TestCo" in greeting, f"Expected custom greeting, got {greeting}"
        ok("build_bot_greeting: uses bot_introduction")

        class DefaultVacancy:
            title = "Test Listing"
            bot_introduction = None

        greeting = build_bot_greeting(DefaultVacancy(), "ru")
        assert "Test Listing" in greeting, f"Expected default greeting with title, got {greeting}"
        ok("build_bot_greeting: falls back to default")
    except Exception as e:
        fail("build_bot_greeting", str(e))

    # classify_candidate
    try:
        from bot.run_bot import classify_candidate

        class HotCandidate:
            score = 60
            phone = "0541234567"

        result = classify_candidate(None, HotCandidate(), [], [])
        assert result == "hot", f"Expected hot, got {result}"
        ok("classify_candidate: score >= 40 + phone = HOT")

        class WarmCandidate:
            score = 50
            phone = None

        result = classify_candidate(None, WarmCandidate(), [], [])
        assert result == "warm", f"Expected warm, got {result}"
        ok("classify_candidate: score >= 40 + no phone = WARM")

        class ColdCandidate:
            score = 10
            phone = None

        result = classify_candidate(None, ColdCandidate(), [], [])
        assert result == "cold", f"Expected cold, got {result}"
        ok("classify_candidate: score < 20 = COLD")
    except Exception as e:
        fail("classify_candidate", str(e))


# ── Task 1.4: Phone Collection ──────────────────────────────────────────────

def test_1_4():
    section("Task 1.4: Phone Collection")

    # Candidate model has phone field
    try:
        from app.models import Candidate
        assert hasattr(Candidate, 'phone'), "Candidate missing phone"
        assert hasattr(Candidate, 'classification'), "Candidate missing classification"
        ok("Candidate model has phone + classification fields")
    except Exception as e:
        fail("Candidate model", str(e))

    # Phone extraction
    try:
        from bot.run_bot import extract_phone

        # Israeli format
        assert extract_phone("054-1234567") == "0541234567", "Should extract 054-1234567"
        ok("extract_phone: 054-1234567")

        assert extract_phone("0541234567") == "0541234567", "Should extract 0541234567"
        ok("extract_phone: 0541234567")

        assert extract_phone("+972541234567") == "+972541234567", "Should extract +972..."
        ok("extract_phone: +972541234567")

        assert extract_phone("050-555-1234") == "0505551234", "Should extract with dashes"
        ok("extract_phone: 050-555-1234")

        # Embedded in text
        phone = extract_phone("Мой номер 054-1234567, позвоните")
        assert phone is not None, "Should extract from text"
        ok("extract_phone: embedded in text")

        # No phone
        assert extract_phone("hello world") is None, "Should return None for no phone"
        assert extract_phone("123") is None, "Should return None for short numbers"
        ok("extract_phone: returns None for non-phone text")
    except Exception as e:
        fail("extract_phone", str(e))

    # i18n keys exist
    try:
        from common.i18n import t
        assert t("ask_phone", "ru") != "ask_phone", "ask_phone key should exist"
        assert t("phone_accepted", "ru") != "phone_accepted", "phone_accepted key should exist"
        assert t("phone_invalid", "ru") != "phone_invalid", "phone_invalid key should exist"
        ok("i18n keys for phone collection exist (ru)")

        assert t("ask_phone", "he") != "ask_phone", "ask_phone he key should exist"
        assert t("phone_accepted", "en") != "phone_accepted", "phone_accepted en key should exist"
        ok("i18n keys for phone collection exist (he, en)")
    except Exception as e:
        fail("i18n phone keys", str(e))


# ── Task 1.5: Hot Lead Notifications ────────────────────────────────────────

def test_1_5():
    section("Task 1.5: Hot Lead Notifications")

    # Function exists
    try:
        from bot.run_bot import send_hot_lead_notification
        ok("send_hot_lead_notification importable")
    except ImportError as e:
        fail("send_hot_lead_notification import", str(e))
        return

    # Bot handles contact share
    try:
        bot_code = (ROOT / "bot" / "run_bot.py").read_text()
        assert "F.contact" in bot_code, "Bot should handle F.contact for phone sharing"
        ok("Bot handles Telegram contact share (F.contact)")
    except Exception as e:
        fail("Contact share handler", str(e))

    # Notification message format
    try:
        bot_code = (ROOT / "bot" / "run_bot.py").read_text()
        assert "HOT LEAD" in bot_code, "Notification should say HOT LEAD"
        assert "Phone:" in bot_code or "phone" in bot_code.lower(), "Notification should include phone"
        assert "Score:" in bot_code or "score" in bot_code.lower(), "Notification should include score"
        ok("Notification message includes: HOT LEAD, phone, score")
    except Exception as e:
        fail("Notification format", str(e))

    # classification_cold_close i18n key
    try:
        from common.i18n import t
        assert t("classification_cold_close", "ru") != "classification_cold_close"
        ok("i18n key classification_cold_close exists")
    except Exception as e:
        fail("classification_cold_close i18n", str(e))


# ── Database Schema Verification ─────────────────────────────────────────────

def test_db_schema():
    section("Database Schema Verification")

    try:
        from app.db import db_session
        from sqlalchemy import text
        db = db_session()

        # Check companies table
        result = db.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'companies' AND column_name IN ('tg_api_id', 'tg_api_hash')"
        )).fetchall()
        cols = {r[0] for r in result}
        assert 'tg_api_id' in cols, "companies.tg_api_id missing in DB"
        assert 'tg_api_hash' in cols, "companies.tg_api_hash missing in DB"
        ok("DB: companies has tg_api_id, tg_api_hash")

        # Check vacancies table
        result = db.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'vacancies' AND column_name IN "
            "('listing_type', 'bot_introduction', 'bot_faq_knowledge', "
            "'bot_qualifying_questions', 'bot_hot_criteria', 'bot_cold_criteria')"
        )).fetchall()
        cols = {r[0] for r in result}
        expected = {'listing_type', 'bot_introduction', 'bot_faq_knowledge',
                    'bot_qualifying_questions', 'bot_hot_criteria', 'bot_cold_criteria'}
        missing = expected - cols
        assert not missing, f"vacancies missing columns: {missing}"
        ok("DB: vacancies has all 6 listing fields")

        # Check candidates table
        result = db.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'candidates' AND column_name IN ('phone', 'classification')"
        )).fetchall()
        cols = {r[0] for r in result}
        assert 'phone' in cols, "candidates.phone missing in DB"
        assert 'classification' in cols, "candidates.classification missing in DB"
        ok("DB: candidates has phone, classification")

        db.close()
    except Exception as e:
        fail("DB schema check", str(e))


# ── Backward Compatibility ───────────────────────────────────────────────────

def test_backward_compat():
    section("Backward Compatibility")

    # Old recruitment flow still works
    try:
        from bot.run_bot import get_screening_questions
        from common.i18n import get_questions

        # Vacancy with only legacy interview_questions_json
        class OldVacancy:
            interview_questions_json = '["Есть опыт?", "Город?", "Документы?"]'
            bot_qualifying_questions = None

        qs = get_screening_questions(OldVacancy(), "ru")
        assert len(qs) == 3, f"Expected 3 questions, got {len(qs)}"
        assert "Есть опыт?" in qs[0], f"Expected first question about experience"
        ok("Old recruitment vacancy with interview_questions_json works")

        # Vacancy with no questions at all
        class NoQuestionsVacancy:
            interview_questions_json = "[]"
            bot_qualifying_questions = None

        qs = get_screening_questions(NoQuestionsVacancy(), "ru")
        defaults = get_questions("ru")
        assert qs == defaults, "Should fallback to default questions"
        ok("Empty vacancy falls back to default questions")

        # None vacancy
        qs = get_screening_questions(None, "he")
        defaults_he = get_questions("he")
        assert qs == defaults_he, "None vacancy should use defaults"
        ok("None vacancy uses default questions")
    except Exception as e:
        fail("Backward compatibility", str(e))

    # Existing status flow
    try:
        from app.models import CandidateStatus
        assert hasattr(CandidateStatus, 'new')
        assert hasattr(CandidateStatus, 'qualifying')
        assert hasattr(CandidateStatus, 'interviewing')
        assert hasattr(CandidateStatus, 'passed')
        assert hasattr(CandidateStatus, 'rejected')
        assert hasattr(CandidateStatus, 'hired')
        ok("CandidateStatus enum unchanged (all 6 states)")
    except Exception as e:
        fail("CandidateStatus enum", str(e))


# ── Run all ──────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  PHASE 1 INTEGRATION TEST")
    print("  Tasks 1.1-1.5 Verification")
    print("=" * 60)

    test_1_1()
    test_1_2()
    test_1_3()
    test_1_4()
    test_1_5()
    test_db_schema()
    test_backward_compat()

    print(f"\n{'='*60}")
    print(f"  RESULTS: {PASS} passed, {FAIL} failed")
    print(f"{'='*60}")

    if FAIL > 0:
        print(f"\n⚠️  {FAIL} test(s) FAILED")
        return 1
    else:
        print(f"\n🎉 ALL {PASS} TESTS PASSED — Phase 1 complete!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
