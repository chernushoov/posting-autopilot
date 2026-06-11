import time
from flask import Blueprint, render_template, request, redirect, url_for, session
from ..auth import admin_login_ok
from ..db import db_session
from ..models import Company, User
from .registration import _login_user, _verify_and_upgrade_password

bp = Blueprint("auth", __name__)

@bp.get("/")
def index():
    if session.get("is_admin"):
        return redirect(url_for("auth.dashboard"))
    return render_template("landing.html")

@bp.get("/login")
def login():
    if session.get("is_admin") or session.get("user_id"):
        return redirect(url_for("auth.dashboard"))
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


@bp.post("/login")
def login_post():
    if not _check_rate_limit():
        return render_template("login.html", error="Too many attempts. Please wait 5 minutes.")
    _record_attempt()
    login = request.form.get("login","")
    password = request.form.get("password","")
    next_url = request.args.get("next") or request.form.get("next") or url_for("auth.dashboard")

    if "@" in login:
        db = db_session()
        user = db.query(User).filter(User.email == login.strip().lower(), User.is_active == True).first()
        if user and _verify_and_upgrade_password(user, password, db):
            _login_user(user, db)
            db.close()
            return redirect(next_url)
        db.close()
        return render_template("login.html", error="Invalid email or password.")

    if not admin_login_ok(login, password):
        return render_template("login.html", error="Invalid credentials")
    session["is_admin"] = True
    session["owner_id"] = "admin_owner"
    db = db_session()
    companies = db.query(Company).filter(Company.owner_id == session["owner_id"], Company.is_active == True).order_by(Company.id.asc()).all()
    if len(companies) == 1:
        session["current_company_id"] = companies[0].id
    db.close()
    return redirect(next_url)

@bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.index"))

@bp.get("/dashboard")
def dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("auth.login"))
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
            for vacancy in db.query(Vacancy).filter(
                Vacancy.id.in_(vacancy_ids), Vacancy.company_id == company_id
            ).all():
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

    steps_done = sum([has_company, has_vacancy, has_telegram, has_facebook, has_campaign, has_posted])
    steps_total = 6
    progress_pct = int((steps_done / steps_total) * 100)

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
    )

@bp.get("/terms")
def terms():
    return render_template("terms.html")


@bp.get("/connect/telegram")
def connect_telegram():
    if not session.get("is_admin"):
        return redirect(url_for("auth.login"))
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
            v = db.query(Vacancy).filter(
                Vacancy.id == cand.vacancy_id, Vacancy.company_id == company_id
            ).first()
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

    tg_api_id = session.get("tg_api_id")
    tg_api_hash = session.get("tg_api_hash")
    tg_phone = session.get("tg_phone")
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
    awaiting_code = session.get("tg_awaiting_code", False)
    check_api_id = tg_api_id
    check_api_hash = tg_api_hash
    if not check_api_id or not check_api_hash:
        # Try from DB (Company) — fresh session in case old one expired
        try:
            db2 = db_session()
            comp = db2.query(Company).filter(Company.id == company_id).first() if company_id else None
            db2.close()
        except Exception:
            comp = None
        if comp and getattr(comp, 'tg_api_id', None) and getattr(comp, 'tg_api_hash', None):
            check_api_id = comp.tg_api_id
            check_api_hash = comp.tg_api_hash
            tg_api_id = check_api_id
            tg_api_hash = check_api_hash

    if check_api_id and check_api_hash:
        try:
            from common.tg_client import is_authorized
            tg_authorized = is_authorized(int(check_api_id), check_api_hash, company_id)
        except Exception:
            tg_authorized = False
    # If actually authorized, clear awaiting_code (session may be stale)
    if tg_authorized:
        awaiting_code = False
        session.pop("tg_awaiting_code", None)

    db.close()

    return render_template("connect_telegram.html",
        telegram_sources=telegram_sources,
        existing_ids=existing_ids,
        recent_conversations=recent_conversations,
        tg_api_id=tg_api_id, tg_api_hash=tg_api_hash, tg_phone=tg_phone,
        tg_authorized=tg_authorized,
        tg_user=tg_user,
        synced_groups=synced_groups,
        awaiting_code=awaiting_code,
        phone_code_hash=session.get("tg_phone_code_hash"),
        error=request.args.get("error"),
        message=request.args.get("message"),
    )

@bp.post("/connect/telegram/send-code")
def tg_send_code():
    if not session.get("is_admin"):
        return redirect(url_for("auth.login"))
    company_id = session.get("current_company_id")
    api_id = request.form.get("api_id", "").strip()
    api_hash = request.form.get("api_hash", "").strip()
    phone = request.form.get("phone", "").strip()

    if not api_id or not api_hash or not phone:
        return redirect(url_for("auth.connect_telegram", error="All fields required"))

    session["tg_api_id"] = api_id
    session["tg_api_hash"] = api_hash
    session["tg_phone"] = phone

    try:
        from common.tg_client import send_code
        phone_code_hash = send_code(int(api_id), api_hash, phone, company_id)
        session["tg_phone_code_hash"] = phone_code_hash
        session["tg_awaiting_code"] = True
        return redirect(url_for("auth.connect_telegram", message="Code sent! Check your Telegram app."))
    except Exception as e:
        # Clear awaiting state on error
        session.pop("tg_awaiting_code", None)
        session.pop("tg_phone_code_hash", None)
        return redirect(url_for("auth.connect_telegram", error=str(e)[:200]))

@bp.post("/connect/telegram/verify")
def tg_verify():
    if not session.get("is_admin"):
        return redirect(url_for("auth.login"))
    company_id = session.get("current_company_id")
    api_id = request.form.get("api_id", "").strip() or session.get("tg_api_id", "")
    api_hash = request.form.get("api_hash", "").strip() or session.get("tg_api_hash", "")
    phone = request.form.get("phone", "").strip() or session.get("tg_phone", "")
    code = request.form.get("code", "").strip()
    phone_code_hash = request.form.get("phone_code_hash", "").strip() or session.get("tg_phone_code_hash", "")
    password = request.form.get("password", "").strip() or None

    if not code:
        return redirect(url_for("auth.connect_telegram", error="Please enter the verification code"))

    try:
        from common.tg_client import verify_code
        result = verify_code(int(api_id), api_hash, phone, code, phone_code_hash, company_id, password)
        if result.get("ok"):
            session["tg_user"] = result
            session["tg_awaiting_code"] = False
            session.pop("tg_phone_code_hash", None)
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
            session["tg_awaiting_code"] = True
            return redirect(url_for("auth.connect_telegram", error="Two-factor password required. Enter it and try again."))
        else:
            # Code wrong — send a NEW code automatically and stay on Step 2
            try:
                from common.tg_client import send_code
                new_hash = send_code(int(api_id), api_hash, phone, company_id)
                session["tg_phone_code_hash"] = new_hash
                session["tg_awaiting_code"] = True
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
                session["tg_phone_code_hash"] = new_hash
                session["tg_awaiting_code"] = True
            except Exception:
                pass
            return redirect(url_for("auth.connect_telegram", error="Code expired. New code sent — check Telegram."))
        return redirect(url_for("auth.connect_telegram", error=err_msg))

@bp.post("/connect/telegram/sync")
def tg_sync():
    if not session.get("is_admin"):
        return redirect(url_for("auth.login"))
    company_id = session.get("current_company_id")
    api_id = session.get("tg_api_id")
    api_hash = session.get("tg_api_hash")

    # Fallback to DB credentials
    if not api_id or not api_hash:
        db = db_session()
        comp = db.query(Company).filter(Company.id == company_id).first() if company_id else None
        if comp and comp.tg_api_id and comp.tg_api_hash:
            api_id = comp.tg_api_id
            api_hash = comp.tg_api_hash
            session["tg_api_id"] = api_id
            session["tg_api_hash"] = api_hash
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
def tg_add_selected():
    if not session.get("is_admin"):
        return redirect(url_for("auth.login"))
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
    from ..models import Company, Source, SourceType
    from ..plans import UPGRADE_HINT, source_slots_left
    company = db.query(Company).filter(Company.id == company_id).first()
    slots = source_slots_left(db, company) if company else 0
    added = 0
    skipped_by_plan = 0
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
        if slots is not None and added >= slots:
            skipped_by_plan += 1
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
    if skipped_by_plan:
        return redirect(url_for(
            "auth.connect_telegram",
            message=f"Added {added} destinations. {skipped_by_plan} skipped — plan destination limit reached. {UPGRADE_HINT}",
        ))
    return redirect(url_for("auth.connect_telegram", message=f"Added {added} destinations"))

@bp.get("/connect/facebook")
def connect_facebook():
    if not session.get("is_admin"):
        return redirect(url_for("auth.login"))
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
        fb_connected=fb_connected,
        fb_user_name=fb_user_name,
        fb_pages=fb_pages,
        official_pages_sync_enabled=True,
        official_groups_sync_enabled=False,
        official_marketplace_api_enabled=False,
        error=request.args.get("error"),
        message=request.args.get("message"),
    )


@bp.post("/connect/facebook/setup")
def fb_setup():
    """Save FB App credentials and redirect to Facebook OAuth (official Pages flow)."""
    if not session.get("is_admin"):
        return redirect(url_for("auth.login"))
    fb_app_id = request.form.get("fb_app_id", "").strip()
    fb_app_secret = request.form.get("fb_app_secret", "").strip()
    if not fb_app_id or not fb_app_secret:
        return redirect(url_for("auth.connect_facebook", error="App ID and Secret required"))

    # Save to session for callback
    session["fb_app_id"] = fb_app_id
    session["fb_app_secret"] = fb_app_secret

    # Also save to env-like storage for fb_client
    import os
    os.environ["FB_APP_ID"] = fb_app_id
    os.environ["FB_APP_SECRET"] = fb_app_secret

    # Redirect to Facebook OAuth
    from common.fb_client import get_login_url
    redirect_uri = request.host_url.rstrip("/") + "/connect/facebook/callback"
    oauth_url = get_login_url(redirect_uri)
    return redirect(oauth_url)


@bp.get("/connect/facebook/callback")
def fb_callback():
    """Facebook OAuth callback — exchange code for token, sync Pages."""
    if not session.get("is_admin"):
        return redirect(url_for("auth.login"))
    company_id = session.get("current_company_id")
    code = request.args.get("code")
    error = request.args.get("error")

    if error or not code:
        return redirect(url_for("auth.connect_facebook", error=error or "Facebook login cancelled"))

    # Use credentials from session (set during setup)
    import os
    fb_app_id = session.get("fb_app_id") or os.getenv("FB_APP_ID", "")
    fb_app_secret = session.get("fb_app_secret") or os.getenv("FB_APP_SECRET", "")
    if fb_app_id:
        os.environ["FB_APP_ID"] = fb_app_id
    if fb_app_secret:
        os.environ["FB_APP_SECRET"] = fb_app_secret

    from common.fb_client import exchange_code, get_long_lived_token, get_user_info, get_user_pages
    redirect_uri = request.host_url.rstrip("/") + "/connect/facebook/callback"

    # Exchange code for token
    result = exchange_code(code, redirect_uri)
    if not result.get("ok"):
        return redirect(url_for("auth.connect_facebook", error=result.get("error", "Token exchange failed")))

    # Get long-lived token
    long = get_long_lived_token(result["access_token"])
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

    return redirect(url_for("auth.connect_facebook", message=msg))


@bp.post("/connect/facebook/sync")
def fb_sync():
    """Re-sync Facebook Pages through the official Pages API."""
    if not session.get("is_admin"):
        return redirect(url_for("auth.login"))
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
def fb_add_selected_pages():
    """Add selected Facebook Pages as posting destinations."""
    if not session.get("is_admin"):
        return redirect(url_for("auth.login"))
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
    from ..models import Company, Source, SourceType
    from ..plans import UPGRADE_HINT, source_slots_left
    company = db.query(Company).filter(Company.id == company_id).first()
    slots = source_slots_left(db, company) if company else 0
    added = 0
    skipped_by_plan = 0
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
        if slots is not None and added >= slots:
            skipped_by_plan += 1
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
    if skipped_by_plan:
        return redirect(url_for(
            "auth.connect_facebook",
            message=f"Added {added} Pages. {skipped_by_plan} skipped — plan destination limit reached. {UPGRADE_HINT}",
        ))
    return redirect(url_for("auth.connect_facebook", message=f"Added {added} Pages"))
