#!/usr/bin/env python3
"""Regression suite for the 2026-06-15 backend security/reliability audit fixes.

Locks in the behaviour of the remediation so future changes can't silently undo
it. Self-contained (no pytest) — mirrors scripts/test_phase*.py.

Run locally:
    FLASK_DEBUG=1 DATABASE_URL="sqlite:////tmp/pa_audit.db" PYTHONPATH=. \
        python scripts/test_audit_hardening.py
"""
from __future__ import annotations
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("FLASK_DEBUG", "1")
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/pa_audit_hardening_test.db")

PASS = 0
FAIL = 0


def ok(msg):
    global PASS
    PASS += 1
    print(f"  ✅ {msg}")


def fail(name, err):
    global FAIL
    FAIL += 1
    print(f"  ❌ {name} — {err}")


def section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def _fresh_db():
    """Reset schema on the configured (temp) DB. Drop+recreate via the engine
    rather than deleting the file — the module-level engine pools connections, and
    unlinking the sqlite file out from under an open handle corrupts it (readonly)."""
    from app.db import engine
    from app.models import Base
    from app.schema import bootstrap_schema
    Base.metadata.drop_all(bind=engine)
    bootstrap_schema()


# ---------------------------------------------------------------- C1: secret key
def test_secret_key_guard():
    section("C1 — FLASK_SECRET_KEY fails closed in production")
    from app.config import _resolve_secret_key
    saved = dict(os.environ)
    try:
        # Prod (no debug) + unset/default -> must raise
        for bad in ("", "dev-secret"):
            os.environ.pop("FLASK_DEBUG", None)
            os.environ.pop("FLASK_ENV", None)
            if bad:
                os.environ["FLASK_SECRET_KEY"] = bad
            else:
                os.environ.pop("FLASK_SECRET_KEY", None)
            try:
                _resolve_secret_key()
                fail("secret guard", f"did not raise for {bad!r} in prod")
            except RuntimeError:
                ok(f"prod refuses insecure secret ({bad or 'unset'!r})")
        # Dev mode tolerates default
        os.environ["FLASK_DEBUG"] = "1"
        os.environ.pop("FLASK_SECRET_KEY", None)
        assert _resolve_secret_key() == "dev-secret"
        ok("dev mode tolerates default")
        # Real key accepted in prod
        os.environ.pop("FLASK_DEBUG", None)
        os.environ["FLASK_SECRET_KEY"] = "a-real-strong-key"
        assert _resolve_secret_key() == "a-real-strong-key"
        ok("prod accepts a real key")
    except Exception as e:
        fail("secret guard", str(e))
    finally:
        os.environ.clear()
        os.environ.update(saved)


# ---------------------------------------------------------------- billing gate
def test_billing_gate():
    section("HIGH — is_billing_active enforced for worker")
    _fresh_db()
    from app.db import db_session
    from app.models import Company, User
    from app.plans import is_billing_active
    db = db_session()
    try:
        paid = Company(owner_id="o1", name="Paid", plan_tier="pro"); db.add(paid)
        pastdue = Company(owner_id="o2", name="PD", plan_tier="past_due"); db.add(pastdue)
        cancelled = Company(owner_id="o3", name="C", plan_tier="cancelled"); db.add(cancelled)
        admin = Company(owner_id="o4", name="Admin", plan_tier="trial"); db.add(admin)
        trial_ok = Company(owner_id="o5", name="TOK", plan_tier="trial"); db.add(trial_ok)
        trial_exp = Company(owner_id="o6", name="TEX", plan_tier="trial"); db.add(trial_exp)
        db.flush()
        db.add(User(email="ok@x.co", password_hash="h", company_id=trial_ok.id,
                    trial_expires_at=datetime.utcnow() + timedelta(days=3)))
        db.add(User(email="ex@x.co", password_hash="h", company_id=trial_exp.id,
                    trial_expires_at=datetime.utcnow() - timedelta(days=1)))
        db.flush()
        assert is_billing_active(db, paid) is True; ok("paid tier active")
        assert is_billing_active(db, pastdue) is False; ok("past_due inactive")
        assert is_billing_active(db, cancelled) is False; ok("cancelled inactive")
        assert is_billing_active(db, admin) is True; ok("admin-owned (no user) active")
        assert is_billing_active(db, trial_ok) is True; ok("live trial active")
        assert is_billing_active(db, trial_exp) is False; ok("expired trial inactive")
        assert is_billing_active(db, None) is False; ok("None company inactive")
    except Exception as e:
        fail("billing gate", str(e))
    finally:
        db.close()


# ---------------------------------------------------------------- stripe webhook
def test_stripe_idempotency_and_price_map():
    section("HIGH — Stripe webhook idempotency + price-based tier")
    _fresh_db()
    from app.routes.billing import _already_processed, _plan_for_price, PRICE_IDS
    try:
        assert _already_processed("evt_x", "checkout.session.completed") is False
        assert _already_processed("evt_x", "checkout.session.completed") is True
        ok("duplicate webhook event is skipped")
        PRICE_IDS["pro"] = "price_pro_123"
        assert _plan_for_price("price_pro_123") == "pro"
        assert _plan_for_price("price_unknown") is None
        ok("price id maps to plan (and unknown -> None)")
    except Exception as e:
        fail("stripe webhook", str(e))


# ---------------------------------------------------------------- cascade + FK
def test_cascade_delete_and_constraints():
    section("HIGH/CRIT — tenant cascade delete + FK enforcement + stripe uniqueness")
    _fresh_db()
    from app.db import db_session
    from app.models import (Company, Vacancy, Source, Campaign, CampaignSource,
                            Candidate, PostingAttempt)
    from app.routes.companies import _delete_company_cascade
    db = db_session()
    try:
        import sqlalchemy as sa
        assert db.execute(sa.text("PRAGMA foreign_keys")).fetchone()[0] == 1
        ok("SQLite FK enforcement is ON")
        c = Company(owner_id="o", name="T"); db.add(c); db.flush()
        v = Vacancy(company_id=c.id, title="V"); db.add(v); db.flush()
        s = Source(company_id=c.id, tg_ref="@x"); db.add(s); db.flush()
        camp = Campaign(company_id=c.id, vacancy_id=v.id, name="C"); db.add(camp); db.flush()
        db.add(CampaignSource(campaign_id=camp.id, source_id=s.id))
        db.add(Candidate(company_id=c.id, vacancy_id=v.id, tg_user_id="u"))
        db.add(PostingAttempt(company_id=c.id, vacancy_id=v.id, source_id=s.id, run_key="rk"))
        db.commit()
        cid = c.id
        _delete_company_cascade(db, cid); db.commit()
        leftovers = (db.query(Candidate).count() + db.query(PostingAttempt).count()
                     + db.query(CampaignSource).count() + db.query(Campaign).count()
                     + db.query(Source).count() + db.query(Vacancy).count()
                     + db.query(Company).count())
        assert leftovers == 0, f"orphans left: {leftovers}"
        ok("deleting a tenant cascades to all child rows (no orphans)")
        # stripe uniqueness
        db.add(Company(owner_id="a", name="A", stripe_customer_id="cus_dup"))
        db.add(Company(owner_id="b", name="B", stripe_customer_id="cus_dup"))
        try:
            db.commit()
            fail("stripe uniqueness", "duplicate stripe_customer_id allowed")
        except Exception:
            db.rollback()
            ok("stripe_customer_id uniqueness enforced")
    except Exception as e:
        fail("cascade delete", str(e))
    finally:
        db.close()


# ---------------------------------------------------------------- C3 tenant routing
def test_bot_tenant_resolution():
    section("C3 — bot resolves tenant from candidate, not 'first company'")
    _fresh_db()
    from app.db import db_session
    from app.models import Company, Candidate
    from bot.run_bot import _latest_candidate, _company_if_active
    db = db_session()
    try:
        c1 = Company(owner_id="o1", name="First", is_active=True); db.add(c1)
        c2 = Company(owner_id="o2", name="Second", is_active=True); db.add(c2)
        db.flush()
        # user applied to the SECOND (higher-id) company
        db.add(Candidate(company_id=c2.id, tg_user_id="999", status=None))
        db.commit()
        cand = _latest_candidate(db, "999")
        assert cand is not None and cand.company_id == c2.id
        comp = _company_if_active(db, cand.company_id)
        assert comp.id == c2.id, "must resolve the SECOND tenant, not the first"
        ok("returning user routed to their own (non-first) tenant")
        assert _latest_candidate(db, "no-such-user") is None
        ok("unknown tg user resolves to None (no cross-tenant leak)")
    except Exception as e:
        fail("bot tenant routing", str(e))
    finally:
        db.close()


# ---------------------------------------------------------------- FB anti-ban + idempotency
def test_fb_worker_guards():
    section("CRIT/HIGH — FB poster idempotency + content variation")
    _fresh_db()
    from worker.fb_auto_post import _vary_text, auto_post_queue_item
    from app.db import db_session
    from app.models import (Company, Vacancy, FacebookGroupSource, FacebookGroup,
                            FacebookPostVariant, FacebookPostingRun,
                            FacebookPostingQueueItem, FacebookPostingResult,
                            FacebookPostVariantStatus, FacebookPostGenerationSource,
                            FacebookPostTone, FacebookPostLengthMode)
    try:
        base = "Hire painters in Miami"
        variations = {_vary_text(base, i) for i in range(8)}
        assert len(variations) > 1, "variation must differ across items"
        assert all(base in v for v in variations), "variation must preserve original text"
        ok("_vary_text differs per item and preserves the message")
    except Exception as e:
        fail("fb vary_text", str(e))

    db = db_session()
    try:
        c = Company(owner_id="o", name="T"); db.add(c); db.flush()
        v = Vacancy(company_id=c.id, title="V"); db.add(v); db.flush()
        gs = FacebookGroupSource(company_id=c.id, source_label="L", import_batch_key="b"); db.add(gs); db.flush()
        g = FacebookGroup(company_id=c.id, seed_source_id=gs.id, name="G",
                          facebook_url="http://fb/g", facebook_url_normalized="fb/g",
                          primary_category="cat"); db.add(g); db.flush()
        var = FacebookPostVariant(company_id=c.id, vacancy_id=v.id, variant_label="a",
                                  tone=FacebookPostTone.professional,
                                  length_mode=FacebookPostLengthMode.short,
                                  full_text="hello", status=FacebookPostVariantStatus.approved,
                                  generation_source=FacebookPostGenerationSource.manual); db.add(var); db.flush()
        run = FacebookPostingRun(company_id=c.id, vacancy_id=v.id, post_variant_id=var.id,
                                 created_by="t"); db.add(run); db.flush()
        item = FacebookPostingQueueItem(company_id=c.id, run_id=run.id, group_id=g.id, position=1)
        db.add(item); db.flush()
        # Pre-existing result => must short-circuit BEFORE any browser work.
        db.add(FacebookPostingResult(company_id=c.id, queue_item_id=item.id)); db.commit()
        item_id = item.id
        db.close()
        res = auto_post_queue_item(item_id)
        assert res["ok"] is False and "already has a result" in res["error"]
        ok("queue item with an existing result is never re-posted (idempotent)")
    except Exception as e:
        fail("fb idempotency", str(e))
    finally:
        try:
            db.close()
        except Exception:
            pass


# ---------------------------------------------------------------- uploads + compliance
def test_upload_and_compliance():
    section("HIGH — upload validation + CAN-SPAM unsubscribe")
    try:
        from app.routes.vacancies import _looks_like_image, ALLOWED_IMAGE_EXT
        png_magic = b"\x89PNG\r\n\x1a\n" + b"\x00" * 40
        assert _looks_like_image(png_magic, "png") is True
        assert _looks_like_image(b"<svg>evil</svg>", "svg") is False
        assert "svg" not in ALLOWED_IMAGE_EXT and "html" not in ALLOWED_IMAGE_EXT
        ok("image upload accepts real PNG, rejects SVG/HTML by content+ext")
    except Exception as e:
        fail("upload validation", str(e))

    # Unsubscribe signed-token round trip + tamper rejection via the app.
    try:
        from app.factory import create_app
        app = create_app()
        app.config["WTF_CSRF_ENABLED"] = False
        with app.test_request_context():
            from app.routes.prospecting import _unsub_serializer
            tok = _unsub_serializer().dumps(12345)
            assert _unsub_serializer().loads(tok) == 12345
        ok("unsubscribe token signs and verifies")
        client = app.test_client()
        assert client.get("/prospecting/unsubscribe/tampered-token").status_code == 400
        ok("tampered unsubscribe token rejected (400)")
    except Exception as e:
        fail("unsubscribe", str(e))


def main():
    print("\n" + "#" * 60)
    print("#  BACKEND AUDIT-HARDENING REGRESSION SUITE")
    print("#" * 60)
    test_secret_key_guard()
    test_billing_gate()
    test_stripe_idempotency_and_price_map()
    test_cascade_delete_and_constraints()
    test_bot_tenant_resolution()
    test_fb_worker_guards()
    test_upload_and_compliance()
    print("\n" + "=" * 60)
    print(f"  RESULTS: {PASS} passed, {FAIL} failed")
    print("=" * 60)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
