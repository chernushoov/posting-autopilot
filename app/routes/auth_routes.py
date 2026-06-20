import time
import secrets
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from ..auth import admin_login_ok, require_company, is_logged_in, _login_redirect, revalidate_company, login_required
from ..db import db_session
from ..models import Company, User
from ..cabinet_data import build_cabinet_boot
from common.connection_flows import (
    create_connection_flow,
    delete_connection_flow,
    get_connection_flow,
    update_connection_flow,
)
from common.passwords import hash_password, verify_password

bp = Blueprint("auth", __name__)

@bp.get("/")
def index():
    if session.get("is_admin"):
        return redirect(url_for("auth.cabinet"))
    # Premium white landing — one curated template per language (he default).
    requested_lang = (request.args.get("lang") or "").strip().lower()
    if requested_lang in {"en", "ru", "he"}:
        session["ui_lang"] = requested_lang
    lang = session.get("ui_lang", "he")
    template = {"en": "landing_en.html", "ru": "landing_ru.html"}.get(lang, "landing.html")
    return render_template(template)


# ── GEO/SEO discovery files (additive, marketing site) ───────────────────────
# Static lastmod — a fixed date is fine; bump it when the marketing copy changes.
_SEO_LASTMOD = "2026-06-20"


@bp.get("/robots.txt")
def robots_txt():
    from flask import Response
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "Sitemap: https://posting-autopilot.com/sitemap.xml\n"
    )
    return Response(body, mimetype="text/plain")


@bp.get("/sitemap.xml")
def sitemap_xml():
    from flask import Response
    from xml.sax.saxutils import escape
    # Only canonical URLs. /?lang= variants are NOT listed: they canonicalize to apex,
    # so listing them would put non-canonical duplicates in the sitemap.
    urls = [
        "https://posting-autopilot.com/",
        "https://posting-autopilot.com/terms",
        "https://posting-autopilot.com/privacy",
    ]
    entries = "".join(
        f"  <url><loc>{escape(u)}</loc><lastmod>{_SEO_LASTMOD}</lastmod></url>\n"
        for u in urls
    )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}"
        "</urlset>\n"
    )
    return Response(body, mimetype="application/xml")


@bp.get("/llms.txt")
def llms_txt():
    from flask import Response
    body = (
        "# Posting Autopilot\n"
        "\n"
        "> Post one ad to 50+ Telegram and Facebook groups at once, then an AI lead "
        "bot answers replies, screens them and collects phone numbers so you only "
        "handle hot leads.\n"
        "\n"
        "Posting Autopilot is a SaaS for small businesses and recruiters. It auto-"
        "posts a single listing across many Telegram and Facebook groups, and an AI "
        "bot qualifies the incoming replies (detects language, answers from your FAQ, "
        "asks screening questions, collects the phone number). Works in Hebrew, "
        "Russian and English. Plans (ILS/month): Starter 299, Pro 899, Agency 1999.\n"
        "\n"
        "## Key pages\n"
        "\n"
        "- [Home](https://posting-autopilot.com/): product overview and sign-up\n"
        "- [Home (English)](https://posting-autopilot.com/?lang=en): English landing page\n"
        "- [Home (Russian)](https://posting-autopilot.com/?lang=ru): Russian landing page\n"
        "- [Terms](https://posting-autopilot.com/terms): terms of service\n"
        "- [Privacy](https://posting-autopilot.com/privacy): privacy policy\n"
    )
    return Response(body, mimetype="text/plain")


@bp.get("/cabinet")
@login_required
def cabinet():
    # New white SPA cabinet (claude.ai/design) served behind real auth, fed with
    # live, tenant-scoped data. Defense-in-depth: drop a stale/foreign company first.
    revalidate_company()
    db = db_session()
    try:
        owner_id = session.get("owner_id")
        company_id = session.get("current_company_id")
        uid = session.get("user_id")
        user = db.query(User).get(uid) if uid is not None else None
        boot = build_cabinet_boot(db, owner_id, company_id, user)
    except Exception:
        # Safety net: never strand the user on a 500 — fall back to the proven
        # server-rendered dashboard if the SPA bootstrap ever fails on real data.
        current_app.logger.exception("cabinet boot failed; falling back to /dashboard")
        return redirect("/dashboard?legacy=1")
    finally:
        db.close()
    return render_template("cabinet.html", cabinet_boot=boot)

@bp.get("/login")
def login():
    if session.get("is_admin"):
        return redirect(url_for("auth.cabinet"))
    return render_template("login.html")

def _check_rate_limit() -> bool:
    """Check if current IP has exceeded login rate limit."""
    from ..factory import _login_attempts, LOGIN_RATE_LIMIT, LOGIN_RATE_WINDOW
    ip = request.remote_addr or "unknown"
    now = time.time()
    attempts = _login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < LOGIN_RATE_WINDOW]
    _login_attempts[ip] = attempts
    return len(attempts) < LOGIN_RATE_LIMIT


def _record_attempt():
    from ..factory import _login_attempts
    ip = request.remote_addr or "unknown"
    _login_attempts.setdefault(ip, []).append(time.time())


def _log_in_owner_session(owner_id: str, company_id=None, user_id=None):
    session["is_admin"] = True
    session["owner_id"] = owner_id
    if user_id is not None:
        session["user_id"] = user_id
    else:
        session.pop("user_id", None)
    if company_id is not None:
        session["current_company_id"] = company_id
    else:
        session.pop("current_company_id", None)


@bp.post("/login")
def login_post():
    if not _check_rate_limit():
        return render_template("login.html", error="Too many attempts. Please wait 5 minutes.")
    _record_attempt()
    login = request.form.get("login", "").strip()
    password = request.form.get("password", "").strip()

    if admin_login_ok(login, password):
        _log_in_owner_session("admin_owner")
        db = db_session()
        companies = db.query(Company).filter(Company.owner_id == session["owner_id"], Company.is_active == True).order_by(Company.id.asc()).all()
        if len(companies) == 1:
            session["current_company_id"] = companies[0].id
        db.close()
        return redirect(url_for("auth.cabinet"))

    db = db_session()
    user = db.query(User).filter(User.email == login.lower(), User.is_active == True).first()
    password_ok = False
    should_upgrade_hash = False
    if user:
        password_ok, should_upgrade_hash = verify_password(user.password_hash, password)
    if user and password_ok:
        if user.trial_expires_at and datetime.utcnow() > user.trial_expires_at:
            db.close()
            return redirect(url_for("pricing.pricing_page"))
        if should_upgrade_hash:
            user.password_hash = hash_password(password)
            db.commit()
        _log_in_owner_session(user.email, company_id=user.company_id, user_id=user.id)
        db.close()
        return redirect(url_for("auth.cabinet"))
    db.close()
    return render_template("login.html", error="Invalid login or password.")

@bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.index"))

@bp.get("/dashboard")
def dashboard():
    if not is_logged_in():
        return _login_redirect()
    # The new SPA cabinet is the canonical authed home. /dashboard now redirects there;
    # it only renders the legacy server-side dashboard as an internal fallback (?legacy=1).
    if not request.args.get("legacy"):
        return redirect("/cabinet")
    # Defense-in-depth: drop a stale/foreign current_company_id before use, but keep the
    # empty-state dashboard for a principal who simply has no company selected yet.
    revalidate_company()
    db = db_session()
    company_id = session.get("current_company_id")

    from ..models import Vacancy, Source, Campaign, Candidate, CandidateStatus, PostingAttempt

    has_company = company_id is not None
    company_name = ""
    company_phone = ""
    company_emoji = ""
    if has_company:
        c = db.query(Company).get(company_id)
        company_name = c.name if c else ""
        company_phone = getattr(c, 'phone', '') or '' if c else ""
        company_emoji = getattr(c, 'logo_emoji', '') or ('🏢' if getattr(c, 'business_type', 'company') == 'company' else '👤') if c else ""

    vacancy_count = db.query(Vacancy).filter(Vacancy.company_id == company_id, Vacancy.is_active == True).count() if has_company else 0
    has_vacancy = vacancy_count > 0

    telegram_sources = db.query(Source).filter(Source.company_id == company_id, Source.platform == "telegram", Source.is_active == True).all() if has_company else []
    facebook_sources = db.query(Source).filter(Source.company_id == company_id, Source.platform == "facebook", Source.is_active == True).all() if has_company else []
    telegram_count = len(telegram_sources)
    facebook_count = len(facebook_sources)
    has_telegram = telegram_count > 0
    has_facebook = facebook_count > 0

    # Collapse the path-to-value: as soon as the user has a vacancy + at least one
    # destination, silently create their campaign so they never meet the "campaign"
    # concept. Idempotent and never auto-starts posting.
    if has_company and has_vacancy and (has_telegram or has_facebook):
        try:
            from .campaigns import ensure_default_campaign
            ensure_default_campaign(company_id)
        except Exception:
            pass

    campaign_count = db.query(Campaign).filter(Campaign.company_id == company_id).count() if has_company else 0
    has_campaign = campaign_count > 0

    posting_count = db.query(PostingAttempt).filter(PostingAttempt.company_id == company_id).count() if has_company else 0
    has_posted = posting_count > 0

    candidate_count = db.query(Candidate).filter(Candidate.company_id == company_id).count() if has_company else 0
    active_campaign_count = db.query(Campaign).filter(Campaign.company_id == company_id, Campaign.is_running == True).count() if has_company else 0
    candidate_status_counts = {status.value: 0 for status in CandidateStatus}
    recent_candidates = []
    if has_company:
        for status in CandidateStatus:
            candidate_status_counts[status.value] = db.query(Candidate).filter(
                Candidate.company_id == company_id,
                Candidate.status == status,
            ).count()

        recent_candidate_rows = db.query(Candidate).filter(
            Candidate.company_id == company_id
        ).order_by(Candidate.id.desc()).limit(8).all()
        vacancy_titles = {}
        vacancy_ids = {candidate.vacancy_id for candidate in recent_candidate_rows if candidate.vacancy_id}
        if vacancy_ids:
            for vacancy in db.query(Vacancy).filter(Vacancy.id.in_(vacancy_ids)).all():
                vacancy_titles[vacancy.id] = vacancy.title
        recent_candidates = [
            {
                "id": candidate.id,
                "name": candidate.full_name or candidate.tg_username or candidate.tg_user_id or f"Candidate #{candidate.id}",
                "status": candidate.status.value if candidate.status else "new",
                "classification": getattr(candidate, "classification", None),
                "score": candidate.score,
                "phone": getattr(candidate, "phone", None),
                "vacancy_title": vacancy_titles.get(candidate.vacancy_id, ""),
                "created_at": candidate.created_at,
            }
            for candidate in recent_candidate_rows
        ]

    # Facebook is OPTIONAL for the pilot — a Telegram-only setup must reach 100%.
    # FB is a bonus channel, not a required onboarding step.
    steps_done = sum([has_company, has_vacancy, has_telegram, has_campaign, has_posted])
    steps_total = 5
    progress_pct = int((steps_done / steps_total) * 100)

    from common.roi import compute_roi
    roi = compute_roi(db, company_id) if has_company else {
        "posts_published": 0, "responses": 0, "hot_leads": 0, "hours_saved": 0,
    }

    db.close()
    return render_template("dashboard.html",
        has_company=has_company, company_name=company_name, company_phone=company_phone, company_emoji=company_emoji,
        has_vacancy=has_vacancy, vacancy_count=vacancy_count,
        has_telegram=has_telegram, telegram_count=telegram_count,
        has_facebook=has_facebook, facebook_count=facebook_count,
        has_campaign=has_campaign, campaign_count=campaign_count,
        has_posted=has_posted, posting_count=posting_count,
        candidate_count=candidate_count,
        candidate_status_counts=candidate_status_counts,
        recent_candidates=recent_candidates,
        active_campaign_count=active_campaign_count,
        steps_done=steps_done, steps_total=steps_total, progress_pct=progress_pct,
        roi=roi,
    )

@bp.get("/terms")
def terms():
    return render_template("terms.html")


@bp.get("/privacy")
def privacy():
    return render_template("privacy.html")


@bp.get("/connect/telegram")
@require_company
def connect_telegram():
    company_id = session.get("current_company_id")
    if not company_id:
        return redirect(url_for("companies.list_companies"))

    db = db_session()
    from ..models import Source, Candidate, Vacancy
    telegram_sources = db.query(Source).filter(Source.company_id == company_id, Source.platform == "telegram", Source.is_active == True).all()
    # None-safe pre-sort by folder (template's |sort(attribute='folder') chokes on
    # mixed NULL + non-NULL folders; that broke /connect/telegram with a
    # TypeError "<" not supported between NoneType and str on 2026-05-08 after
    # we curated 5 new sources with folder='pilot' alongside legacy folder=NULL).
    telegram_sources.sort(key=lambda s: ((s.folder or ""), s.id))
    existing_ids = {str(s.tg_ref) for s in telegram_sources}

    # Recent bot conversations for live feed
    import json
    recent_candidates = db.query(Candidate).filter(
        Candidate.company_id == company_id
    ).order_by(Candidate.id.desc()).limit(20).all()

    recent_conversations = []
    for cand in recent_candidates:
        vacancy_title = ""
        if cand.vacancy_id:
            v = db.query(Vacancy).filter(Vacancy.id == cand.vacancy_id).first()
            vacancy_title = v.title if v else ""
        last_message = ""
        try:
            log = json.loads(cand.chat_log_json or "[]")
            for entry in reversed(log):
                if entry.get("text"):
                    last_message = entry["text"]
                    break
        except Exception:
            pass
        recent_conversations.append({
            "full_name": cand.full_name,
            "tg_username": cand.tg_username,
            "status": cand.status,
            "classification": getattr(cand, 'classification', None),
            "phone": getattr(cand, 'phone', None),
            "vacancy_title": vacancy_title,
            "last_message": last_message,
            "created_at": cand.created_at,
        })

    tg_flow = get_connection_flow(session.get("tg_flow_id"), kind="telegram", company_id=company_id)
    tg_api_id = tg_flow.get("api_id") if tg_flow else None
    tg_phone = tg_flow.get("phone") if tg_flow else None
    tg_authorized = False
    tg_user = session.get("tg_user")
    # Load synced groups from file cache (too large for session cookie)
    synced_groups = []
    try:
        import os
        cache_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'tg_sessions', f'groups_{company_id}.json')
        if os.path.exists(cache_path):
            import json as _json
            with open(cache_path) as f:
                synced_groups = _json.load(f)
    except Exception:
        pass

    # Check authorization — also check DB credentials if session is empty
    awaiting_code = bool(tg_flow and tg_flow.get("awaiting_code"))
    check_api_id = None
    check_api_hash = None
    # Try from DB (Company) — credentials are never copied into the browser session.
    try:
        db2 = db_session()
        comp = db2.query(Company).filter(Company.id == company_id).first() if company_id else None
        db2.close()
    except Exception:
        comp = None
    if comp and getattr(comp, 'tg_api_id', None) and getattr(comp, 'tg_api_hash', None):
        check_api_id = comp.tg_api_id
        check_api_hash = comp.tg_api_hash
        tg_api_id = tg_api_id or check_api_id

    if check_api_id and check_api_hash:
        try:
            from common.tg_client import is_authorized
            tg_authorized = is_authorized(int(check_api_id), check_api_hash, company_id)
        except Exception:
            tg_authorized = False
    # If actually authorized, clear awaiting_code (session may be stale)
    if tg_authorized:
        awaiting_code = False
        delete_connection_flow(session.pop("tg_flow_id", None))

    db.close()

    from common.tg_client import has_shared_app_credentials
    tg_shared_creds = has_shared_app_credentials()

    return render_template("connect_telegram.html",
        telegram_sources=telegram_sources,
        existing_ids=existing_ids,
        recent_conversations=recent_conversations,
        tg_api_id=tg_api_id, tg_phone=tg_phone,
        tg_authorized=tg_authorized,
        tg_shared_creds=tg_shared_creds,
        tg_user=tg_user,
        synced_groups=synced_groups,
        awaiting_code=awaiting_code,
        error=request.args.get("error"),
        message=request.args.get("message"),
    )

@bp.post("/connect/telegram/send-code")
@require_company
def tg_send_code():
    import re as _re
    company_id = session.get("current_company_id")
    api_id = request.form.get("api_id", "").strip()
    api_hash = request.form.get("api_hash", "").strip()
    # Normalise the phone: strip spaces/dashes/parens so a copy-pasted number
    # like "+972 50-123-4567" doesn't get rejected by Telegram for formatting.
    phone = _re.sub(r"[^0-9+]", "", request.form.get("phone", "").strip())
    if phone and not phone.startswith("+"):
        phone = "+" + phone

    # Phone-only onboarding: if the user didn't supply their own developer app
    # credentials, fall back to the service's managed shared app. This removes the
    # #1 onboarding wall (my.telegram.org → create app → copy 2 secrets).
    if not api_id or not api_hash:
        from common.tg_client import shared_app_credentials
        shared_id, shared_hash = shared_app_credentials()
        if shared_id and shared_hash:
            api_id = api_id or str(shared_id)
            api_hash = api_hash or shared_hash

    if not phone:
        return redirect(url_for("auth.connect_telegram", error="Phone number is required"))
    if not api_id or not api_hash:
        return redirect(url_for("auth.connect_telegram", error="Telegram API credentials are not configured. Open Advanced and enter your API ID and API Hash, or ask the operator to enable phone-only connect."))

    try:
        from common.tg_client import send_code
        phone_code_hash = send_code(int(api_id), api_hash, phone, company_id)
        delete_connection_flow(session.pop("tg_flow_id", None))
        session["tg_flow_id"] = create_connection_flow(
            "telegram",
            company_id,
            {
                "api_id": api_id,
                "api_hash": api_hash,
                "phone": phone,
                "phone_code_hash": phone_code_hash,
                "awaiting_code": True,
            },
        )
        return redirect(url_for("auth.connect_telegram", message="Code sent! Check your Telegram app."))
    except Exception as e:
        delete_connection_flow(session.pop("tg_flow_id", None))
        raw = str(e).lower()
        if "phone number is invalid" in raw or "phone_number_invalid" in raw:
            msg = ("Неверный номер телефона. Укажите его с кодом страны и без пробелов — "
                   "например +972501234567 (Израиль) или +79991234567 (Россия).")
        elif "flood" in raw or "too many" in raw or "wait" in raw:
            msg = "Слишком много попыток за короткое время. Подождите пару минут и попробуйте снова."
        elif "api_id" in raw or "api id" in raw or "api_hash" in raw:
            msg = ("Сервис Telegram не настроен. Откройте «Дополнительно: использовать свои API-ключи» "
                   "и введите ваши API ID и API Hash с my.telegram.org.")
        elif "banned" in raw or "deactivated" in raw:
            msg = "Этот номер заблокирован или деактивирован в Telegram."
        else:
            msg = "Не удалось отправить код: " + str(e)[:160]
        return redirect(url_for("auth.connect_telegram", error=msg))

@bp.post("/connect/telegram/verify")
@require_company
def tg_verify():
    company_id = session.get("current_company_id")
    tg_flow_id = session.get("tg_flow_id")
    tg_flow = get_connection_flow(tg_flow_id, kind="telegram", company_id=company_id)
    if not tg_flow:
        return redirect(url_for("auth.connect_telegram", error="Telegram verification expired. Send a new code."))
    api_id = str(tg_flow.get("api_id", "")).strip()
    api_hash = str(tg_flow.get("api_hash", "")).strip()
    phone = str(tg_flow.get("phone", "")).strip()
    code = request.form.get("code", "").strip()
    phone_code_hash = str(tg_flow.get("phone_code_hash", "")).strip()
    password = request.form.get("password", "").strip() or None

    if not code:
        return redirect(url_for("auth.connect_telegram", error="Please enter the verification code"))

    try:
        from common.tg_client import verify_code
        result = verify_code(int(api_id), api_hash, phone, code, phone_code_hash, company_id, password)
        if result.get("ok"):
            session["tg_user"] = result
            delete_connection_flow(session.pop("tg_flow_id", None))
            # Persist Telethon credentials to Company for worker access
            db = db_session()
            comp = db.query(Company).filter(Company.id == company_id).first()
            if comp:
                comp.tg_api_id = api_id
                comp.tg_api_hash = api_hash
                db.commit()
            db.close()
            return redirect(url_for("auth.connect_telegram", message="Telegram connected!"))
        elif result.get("error") == "2FA_REQUIRED":
            # Stay on Step 2 but ask for 2FA password
            update_connection_flow(tg_flow_id, {"awaiting_code": True})
            return redirect(url_for("auth.connect_telegram", error="Two-factor password required. Enter it and try again."))
        else:
            # Code wrong — send a NEW code automatically and stay on Step 2
            try:
                from common.tg_client import send_code
                new_hash = send_code(int(api_id), api_hash, phone, company_id)
                update_connection_flow(tg_flow_id, {"phone_code_hash": new_hash, "awaiting_code": True})
            except Exception:
                pass
            return redirect(url_for("auth.connect_telegram", error="Wrong code. A new code was sent — check Telegram."))
    except Exception as e:
        err_msg = str(e)[:200]
        # If code expired or invalid, resend automatically
        if "phone code" in err_msg.lower() or "expired" in err_msg.lower() or "invalid" in err_msg.lower():
            try:
                from common.tg_client import send_code
                new_hash = send_code(int(api_id), api_hash, phone, company_id)
                update_connection_flow(tg_flow_id, {"phone_code_hash": new_hash, "awaiting_code": True})
            except Exception:
                pass
            return redirect(url_for("auth.connect_telegram", error="Code expired. New code sent — check Telegram."))
        return redirect(url_for("auth.connect_telegram", error=err_msg))

@bp.post("/connect/telegram/sync")
@require_company
def tg_sync():
    company_id = session.get("current_company_id")
    api_id = None
    api_hash = None

    db = db_session()
    comp = db.query(Company).filter(Company.id == company_id).first() if company_id else None
    if comp and comp.tg_api_id and comp.tg_api_hash:
        api_id = comp.tg_api_id
        api_hash = comp.tg_api_hash
    db.close()

    if not api_id or not api_hash:
        return redirect(url_for("auth.connect_telegram", error="API credentials missing"))

    try:
        from common.tg_client import sync_dialogs
        import json as _json
        result = sync_dialogs(int(api_id), api_hash, company_id)
        if result.get("ok"):
            # Store in file (too large for session cookie)
            import os
            cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'tg_sessions')
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, f'groups_{company_id}.json')
            with open(cache_path, 'w') as f:
                _json.dump(result["groups"], f, ensure_ascii=False)
            session["tg_synced_groups_count"] = result["total"]
            return redirect(url_for("auth.connect_telegram", message=f"Synced {result['total']} groups/channels"))
        else:
            return redirect(url_for("auth.connect_telegram", error=result.get("error", "Sync failed")))
    except Exception as e:
        return redirect(url_for("auth.connect_telegram", error=str(e)[:200]))

@bp.post("/connect/telegram/add-selected")
@require_company
def tg_add_selected():
    company_id = session.get("current_company_id")
    group_ids = request.form.get("group_ids", "").split(",")
    # Load from file cache
    synced = []
    try:
        import os, json as _json
        cache_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'tg_sessions', f'groups_{company_id}.json')
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                synced = _json.load(f)
    except Exception:
        pass

    db = db_session()
    from ..models import Source, SourceType
    added = 0
    for gid in group_ids:
        gid = gid.strip()
        if not gid:
            continue
        group = next((g for g in synced if str(g["id"]) == gid), None)
        if not group:
            continue
        tg_ref = f"@{group['username']}" if group.get("username") else str(group["id"])
        existing = db.query(Source).filter(Source.company_id == company_id, Source.tg_ref == tg_ref).first()
        if existing:
            continue
        source = Source(
            company_id=company_id,
            tg_ref=tg_ref,
            label=group["name"],
            source_type=SourceType.group if group["type"] == "group" else SourceType.channel,
            platform="telegram",
            destination_kind=group["type"],
            posting_mode="auto",
            last_check_ok=True,
            last_check_message=f"Synced from account ({group.get('members', 0)} members)",
        )
        db.add(source)
        added += 1
    db.commit()
    db.close()
    return redirect(url_for("auth.connect_telegram", message=f"Added {added} destinations"))

@bp.get("/connect/facebook")
@require_company
def connect_facebook():
    company_id = session.get("current_company_id")
    if not company_id:
        return redirect(url_for("companies.list_companies"))

    db = db_session()
    from ..models import Source
    facebook_sources = db.query(Source).filter(Source.company_id == company_id, Source.platform == "facebook", Source.is_active == True).all() if company_id else []
    existing_urls = {s.destination_url for s in facebook_sources if s.destination_url}

    # Check if Facebook is connected (token in Company)
    comp = db.query(Company).filter(Company.id == company_id).first()
    fb_connected = bool(comp and comp.fb_access_token)
    fb_user_name = comp.fb_user_name if comp else None

    # Browser-session connection (the EZPost-style path): a captured FB session +
    # imported groups count as "connected" even without an OAuth token — which
    # can't read groups or post to Marketplace anyway. This is what actually
    # powers group/Marketplace automation.
    import os as _os
    from ..models import FacebookGroup
    from ..facebook_session import fb_session_exists as _fb_session_exists
    # Per-company browser session ONLY — never reveal another tenant's connected state.
    fb_browser_connected = _fb_session_exists(company_id)
    fb_group_count = db.query(FacebookGroup).filter(FacebookGroup.company_id == company_id).count() if company_id else 0
    if fb_browser_connected and fb_group_count > 0:
        fb_connected = True
    # Materialize the imported groups into plain dicts (so the template can list
    # them after the session closes). These are the browser-synced groups — the
    # FacebookGroup table — separate from the legacy Source-based facebook_sources.
    fb_groups_list = [
        {
            "name": g.name,
            "url": g.facebook_url_normalized or g.facebook_url or "",
            "members": g.member_count_estimate,
            "category": (g.primary_category or "general"),
        }
        for g in (
            db.query(FacebookGroup)
            .filter(FacebookGroup.company_id == company_id)
            .order_by(FacebookGroup.name)
            .limit(500)
            .all()
        )
    ] if company_id else []

    # Load synced pages from cache
    fb_pages = []
    try:
        import os, json as _json
        cache_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fb_cache', f'pages_{company_id}.json')
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                fb_pages = _json.load(f)
    except Exception:
        pass

    db.close()

    from common.fb_client import is_configured, FB_APP_ID
    return render_template("connect_facebook.html",
        facebook_sources=facebook_sources,
        existing_urls=existing_urls,
        fb_configured=is_configured(),
        fb_app_id=FB_APP_ID,
        fb_app_secret=_os.getenv("FB_APP_SECRET", ""),
        fb_connected=fb_connected,
        fb_browser_connected=fb_browser_connected,
        fb_group_count=fb_group_count,
        fb_groups_list=fb_groups_list,
        fb_user_name=fb_user_name,
        fb_pages=fb_pages,
        official_pages_sync_enabled=True,
        official_groups_sync_enabled=False,
        official_marketplace_api_enabled=False,
        error=request.args.get("error"),
        message=request.args.get("message"),
    )


@bp.get("/connect/facebook/status")
@require_company
def connect_facebook_status():
    """Tenant-safe Facebook connection status (JSON). company_id is derived ONLY from
    the server-side authenticated session — a ?company_id= param is ignored by
    construction, so one tenant can never probe another's connected state."""
    from flask import jsonify
    from ..facebook_session import get_fb_session_status
    company_id = session.get("current_company_id")
    status = get_fb_session_status(company_id)
    if status.get("connected"):
        db = db_session()
        try:
            comp = db.query(Company).filter(Company.id == company_id).first()
            hint = (comp.fb_user_name if comp else None) or None
        finally:
            db.close()
        if hint:
            status["account_hint"] = hint
    return jsonify(status)


@bp.post("/connect/facebook/browser-connect")
@require_company
def fb_browser_connect():
    """Start the one-time Facebook login that captures THIS company's browser
    session (the path that powers group + Marketplace posting).

    Cloud path (FB_SERVER_CAPTURE): run the login ON THE SERVER inside a virtual
    display and let the owner drive it through a noVNC tab — posting later runs
    headless from the same server. Desktop fallback (FB_ALLOW_LOCAL_CAPTURE):
    spawn a visible browser on the local machine.
    """
    import os as _os
    import sys as _sys
    import subprocess
    from ..facebook_session import company_session_name, fb_session_exists as _fb_session_exists

    company_id = session.get("current_company_id")
    user_id = session.get("user_id")
    if _fb_session_exists(company_id):
        return redirect(url_for("auth.connect_facebook", message="Facebook уже подключён. Нажмите «Синхронизировать», чтобы обновить группы."))

    # ── Cloud path: server-side capture via noVNC ────────────────────────────
    from .. import fb_capture_server as _cap
    if _cap.is_enabled():
        res = _cap.start_capture(company_id, user_id)
        if res.get("busy"):
            return redirect(url_for("auth.connect_facebook", error="Сейчас на сервере идёт другое подключение Facebook. Подождите минуту и попробуйте снова."))
        if not res.get("ok"):
            return redirect(url_for("auth.connect_facebook", error="Не удалось запустить подключение Facebook: " + str(res.get("error", ""))[:160]))
        return redirect(url_for("auth.fb_capture_view"))

    # ── Desktop fallback (local install only) ────────────────────────────────
    gate = _os.getenv("FB_ALLOW_LOCAL_CAPTURE", "").strip().lower()
    if gate not in {"1", "true", "yes", "on"}:
        return redirect(url_for(
            "auth.connect_facebook",
            error="Подключение Facebook через сервер сейчас выключено. Добавьте группы и Marketplace, вставив ссылки в форме выше.",
        ))
    try:
        session_label = company_session_name(company_id)
        repo_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
        script = _os.path.join(repo_root, "scripts", "fb_capture_session_auto.py")
        py = _os.path.join(repo_root, ".venv-fb", "bin", "python")
        if not _os.path.exists(py):
            py = _sys.executable
        subprocess.Popen(
            [py, script, session_label],
            cwd=repo_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return redirect(url_for(
            "auth.connect_facebook",
            message="Открывается окно браузера — войдите в Facebook. Потом вернитесь и нажмите «Синхронизировать».",
        ))
    except Exception as exc:  # pragma: no cover - best effort launch
        return redirect(url_for("auth.connect_facebook", error="Не удалось запустить вход в Facebook: " + str(exc)[:160]))


@bp.get("/connect/facebook/capture")
@require_company
def fb_capture_view():
    """Authed viewer for the server-side FB login: shows the live browser via noVNC
    and polls until the session is captured. The VNC password is delivered ONLY on
    this page, to the authenticated owner of the active capture slot."""
    from .. import fb_capture_server as _cap
    if not _cap.is_enabled():
        return redirect(url_for("auth.connect_facebook"))
    company_id = session.get("current_company_id")
    user_id = session.get("user_id")
    pwd = _cap.current_password(company_id, user_id)
    if not pwd:
        return redirect(url_for("auth.connect_facebook"))
    from urllib.parse import quote
    vnc_url = ("/fbvnc/vnc.html?autoconnect=1&resize=remote&reconnect=1"
               "&path=" + quote("fbvnc/websockify") + "&password=" + quote(pwd))
    return render_template("connect_facebook_capture.html", vnc_url=vnc_url)


@bp.get("/connect/facebook/capture/status")
@require_company
def fb_capture_status():
    from flask import jsonify
    from .. import fb_capture_server as _cap
    company_id = session.get("current_company_id")
    user_id = session.get("user_id")
    return jsonify(_cap.get_status(company_id, user_id))


@bp.post("/connect/facebook/capture/cancel")
@require_company
def fb_capture_cancel():
    from .. import fb_capture_server as _cap
    company_id = session.get("current_company_id")
    user_id = session.get("user_id")
    _cap.cancel(company_id, user_id)
    return redirect(url_for("auth.connect_facebook", message="Подключение Facebook отменено."))


@bp.route("/connect/facebook/capture/authz", methods=["GET", "POST", "HEAD"])
def fb_capture_authz():
    """Caddy forward_auth target for /fbvnc/*. Returns ONLY 200 (allow) or 403
    (deny) — never a 3xx, so a redirect can't be mistaken for success. No
    @require_company here (it can 302); we check the session directly. Allow iff
    there is a logged-in user whose validated company owns the live capture slot."""
    from .. import fb_capture_server as _cap
    user_id = session.get("user_id")
    company_id = session.get("current_company_id")
    if not user_id or not company_id:
        return ("", 403)
    if _cap.authz(company_id, user_id):
        return ("", 200)
    return ("", 403)


@bp.post("/connect/facebook/setup")
@require_company
def fb_setup():
    """Save FB App credentials and redirect to Facebook OAuth (official Pages flow)."""
    fb_app_id = request.form.get("fb_app_id", "").strip()
    fb_app_secret = request.form.get("fb_app_secret", "").strip()
    if not fb_app_id or not fb_app_secret:
        return redirect(url_for("auth.connect_facebook", error="App ID and Secret required"))

    # Redirect to Facebook OAuth
    from common.fb_client import get_login_url
    redirect_uri = request.host_url.rstrip("/") + "/connect/facebook/callback"
    oauth_state = secrets.token_urlsafe(32)
    delete_connection_flow(session.pop("fb_flow_id", None))
    session["fb_flow_id"] = create_connection_flow(
        "facebook",
        company_id=session.get("current_company_id"),
        payload={
            "app_id": fb_app_id,
            "app_secret": fb_app_secret,
            "state": oauth_state,
        },
    )
    oauth_url = get_login_url(redirect_uri, state=oauth_state, app_id=fb_app_id)
    return redirect(oauth_url)


@bp.get("/connect/facebook/callback")
@require_company
def fb_callback():
    """Facebook OAuth callback — exchange code for token, sync Pages."""
    company_id = session.get("current_company_id")
    code = request.args.get("code")
    state = request.args.get("state", "")
    error = request.args.get("error")

    if error or not code:
        return redirect(url_for("auth.connect_facebook", error=error or "Facebook login cancelled"))

    fb_flow_id = session.get("fb_flow_id")
    fb_flow = get_connection_flow(fb_flow_id, kind="facebook", company_id=company_id)
    if not fb_flow or not state or state != fb_flow.get("state"):
        delete_connection_flow(session.pop("fb_flow_id", None))
        return redirect(url_for("auth.connect_facebook", error="Facebook OAuth state mismatch. Please reconnect."))
    fb_app_id = fb_flow.get("app_id", "")
    fb_app_secret = fb_flow.get("app_secret", "")
    if not fb_app_id or not fb_app_secret:
        delete_connection_flow(session.pop("fb_flow_id", None))
        return redirect(url_for("auth.connect_facebook", error="Facebook credentials expired. Please reconnect."))

    from common.fb_client import exchange_code, get_long_lived_token, get_user_info, get_user_pages
    redirect_uri = request.host_url.rstrip("/") + "/connect/facebook/callback"

    # Exchange code for token
    result = exchange_code(code, redirect_uri, app_id=fb_app_id, app_secret=fb_app_secret)
    if not result.get("ok"):
        delete_connection_flow(session.pop("fb_flow_id", None))
        return redirect(url_for("auth.connect_facebook", error=result.get("error", "Token exchange failed")))

    # Get long-lived token
    long = get_long_lived_token(result["access_token"], app_id=fb_app_id, app_secret=fb_app_secret)
    token = long["access_token"] if long.get("ok") else result["access_token"]

    # Get user info
    user_info = get_user_info(token)

    # Save to Company
    db = db_session()
    comp = db.query(Company).filter(Company.id == company_id).first()
    if comp:
        comp.fb_access_token = token
        if user_info.get("ok"):
            comp.fb_user_id = user_info["user"].get("id")
            comp.fb_user_name = user_info["user"].get("name")
        db.commit()
    db.close()

    # Sync Pages
    pages_result = get_user_pages(token)
    if pages_result.get("ok"):
        import os, json as _json
        cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fb_cache')
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f'pages_{company_id}.json')
        with open(cache_path, 'w') as f:
            _json.dump(pages_result["pages"], f, ensure_ascii=False)
        msg = f"Facebook connected! Synced {pages_result['total']} Pages."
    else:
        msg = "Facebook connected but could not sync Pages: " + pages_result.get("error", "")

    delete_connection_flow(session.pop("fb_flow_id", None))
    return redirect(url_for("auth.connect_facebook", message=msg))


@bp.post("/connect/facebook/sync")
@require_company
def fb_sync():
    """Re-sync Facebook Pages through the official Pages API."""
    company_id = session.get("current_company_id")

    db = db_session()
    comp = db.query(Company).filter(Company.id == company_id).first()
    if not comp or not comp.fb_access_token:
        db.close()
        return redirect(url_for("auth.connect_facebook", error="Facebook not connected"))
    token = comp.fb_access_token
    db.close()

    from common.fb_client import get_user_pages
    result = get_user_pages(token)
    if result.get("ok"):
        import os, json as _json
        cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fb_cache')
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f'pages_{company_id}.json')
        with open(cache_path, 'w') as f:
            _json.dump(result["pages"], f, ensure_ascii=False)
        return redirect(url_for("auth.connect_facebook", message=f"Synced {result['total']} Pages"))
    return redirect(url_for("auth.connect_facebook", error=result.get("error", "Pages sync failed")))

@bp.post("/connect/facebook/add-selected-pages")
@require_company
def fb_add_selected_pages():
    """Add selected Facebook Pages as posting destinations."""
    company_id = session.get("current_company_id")
    page_ids = request.form.get("page_ids", "").split(",")

    # Load from cache
    fb_pages = []
    try:
        import os, json as _json
        cache_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fb_cache', f'pages_{company_id}.json')
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                fb_pages = _json.load(f)
    except Exception:
        pass

    db = db_session()
    from ..models import Source, SourceType
    added = 0
    for page_id in page_ids:
        page_id = page_id.strip()
        if not page_id:
            continue
        page = next((item for item in fb_pages if str(item["id"]) == page_id), None)
        if not page:
            continue
        fb_url = page.get("link") or f"https://facebook.com/{page['id']}"
        existing = db.query(Source).filter(Source.company_id == company_id, Source.destination_url == fb_url).first()
        if existing:
            continue
        source = Source(
            company_id=company_id,
            tg_ref=f"fb-page-{page['id']}",
            label=page["name"],
            source_type=SourceType.group,
            platform="facebook",
            destination_kind="page",
            posting_mode="assisted_manual",
            destination_url=fb_url,
            last_check_ok=True,
            last_check_message=f"Synced from Facebook Pages API ({page.get('category', 'Page')})",
        )
        db.add(source)
        added += 1
    db.commit()
    db.close()
    return redirect(url_for("auth.connect_facebook", message=f"Added {added} Pages"))


# ── GDPR: data export + account deletion ──────────────────────────────────────
@bp.get("/account/export")
@require_company
def account_export():
    """Download ALL of this tenant's data as JSON (right to access/portability).
    Strictly scoped to the session company_id."""
    from flask import Response
    import json as _json
    company_id = session.get("current_company_id")
    db = db_session()
    try:
        from ..models import (Company, Vacancy, Source, Campaign, Candidate,
                              PostingAttempt, User, Creative, Prospect)

        def rows(model):
            return [
                {c.name: getattr(r, c.name) for c in model.__table__.columns}
                for r in db.query(model).filter(model.company_id == company_id).all()
            ]

        comp = db.query(Company).get(company_id)
        data = {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "company": ({c.name: getattr(comp, c.name) for c in Company.__table__.columns} if comp else None),
            "vacancies": rows(Vacancy),
            "sources": rows(Source),
            "campaigns": rows(Campaign),
            "candidates": rows(Candidate),
            "posting_attempts": rows(PostingAttempt),
            "creatives": rows(Creative),
            "prospects": rows(Prospect),
            "team": [
                {"id": u.id, "email": u.email, "role": str(getattr(u, "role", "")),
                 "created_at": getattr(u, "created_at", None)}
                for u in db.query(User).filter(User.company_id == company_id).all()
            ],
        }
    finally:
        db.close()
    payload = _json.dumps(data, ensure_ascii=False, indent=2, default=str)
    return Response(payload, mimetype="application/json",
                    headers={"Content-Disposition": f"attachment; filename=posting-autopilot-export-{company_id}.json"})


@bp.get("/account/delete")
@require_company
def account_delete():
    company_id = session.get("current_company_id")
    db = db_session()
    try:
        comp = db.query(Company).get(company_id)
        name = comp.name if comp else ""
    finally:
        db.close()
    return render_template("account_delete.html", company_name=name)


@bp.post("/account/delete")
@require_company
def account_delete_post():
    """Right to erasure: hard-delete the whole tenant (company + users + all data),
    FK-safe order, scoped by company_id. Owner-only, confirm by typing company name."""
    company_id = session.get("current_company_id")
    confirm = request.form.get("confirm", "").strip()
    db = db_session()
    comp = None
    try:
        from ..models import (
            Company, Vacancy, Source, Campaign, CampaignSource, Candidate, PostingAttempt,
            User, UserRole, Creative, Prospect, OutreachAttempt, PasswordResetToken,
            FacebookGroup, FacebookGroupSource, FacebookPostVariant, FacebookPostingRun,
            FacebookPostingQueueItem, FacebookPostingResult,
        )
        comp = db.query(Company).get(company_id)
        if not comp:
            return redirect("/cabinet")
        me = db.query(User).get(session.get("user_id")) if session.get("user_id") else None
        if me is not None and getattr(me, "role", None) != UserRole.owner:
            return render_template("account_delete.html", company_name=comp.name,
                                   error="Удалить компанию может только владелец аккаунта.")
        if confirm != comp.name:
            return render_template("account_delete.html", company_name=comp.name,
                                   error="Введите точное название компании для подтверждения.")
        camp_ids = [c.id for c in db.query(Campaign).filter(Campaign.company_id == company_id).all()]
        user_ids = [u.id for u in db.query(User).filter(User.company_id == company_id).all()]
        # children -> parents, all scoped to this tenant
        db.query(FacebookPostingResult).filter(FacebookPostingResult.company_id == company_id).delete(synchronize_session=False)
        db.query(FacebookPostingQueueItem).filter(FacebookPostingQueueItem.company_id == company_id).delete(synchronize_session=False)
        db.query(FacebookPostingRun).filter(FacebookPostingRun.company_id == company_id).delete(synchronize_session=False)
        db.query(FacebookPostVariant).filter(FacebookPostVariant.company_id == company_id).delete(synchronize_session=False)
        db.query(FacebookGroup).filter(FacebookGroup.company_id == company_id).delete(synchronize_session=False)
        db.query(FacebookGroupSource).filter(FacebookGroupSource.company_id == company_id).delete(synchronize_session=False)
        db.query(OutreachAttempt).filter(OutreachAttempt.company_id == company_id).delete(synchronize_session=False)
        db.query(Prospect).filter(Prospect.company_id == company_id).delete(synchronize_session=False)
        db.query(PostingAttempt).filter(PostingAttempt.company_id == company_id).delete(synchronize_session=False)
        if camp_ids:
            db.query(CampaignSource).filter(CampaignSource.campaign_id.in_(camp_ids)).delete(synchronize_session=False)
        db.query(Candidate).filter(Candidate.company_id == company_id).delete(synchronize_session=False)
        db.query(Campaign).filter(Campaign.company_id == company_id).delete(synchronize_session=False)
        db.query(Source).filter(Source.company_id == company_id).delete(synchronize_session=False)
        db.query(Vacancy).filter(Vacancy.company_id == company_id).delete(synchronize_session=False)
        db.query(Creative).filter(Creative.company_id == company_id).delete(synchronize_session=False)
        if user_ids:
            db.query(PasswordResetToken).filter(PasswordResetToken.user_id.in_(user_ids)).delete(synchronize_session=False)
        db.query(User).filter(User.company_id == company_id).delete(synchronize_session=False)
        db.query(Company).filter(Company.id == company_id).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        current_app.logger.exception("account deletion failed")
        return render_template("account_delete.html",
                               company_name=(comp.name if comp else ""),
                               error="Не удалось удалить: " + str(e)[:140])
    finally:
        db.close()
    # Best-effort: remove this tenant's TG/FB session files too.
    try:
        import os, glob
        base = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        for sub in ("tg_sessions", "fb_sessions"):
            for f in glob.glob(os.path.join(base, sub, f"company_{company_id}.*")):
                os.remove(f)
    except Exception:
        pass
    session.clear()
    return redirect("/?deleted=1")
