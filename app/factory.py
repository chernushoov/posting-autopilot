from flask import Flask, session, request, redirect
from urllib.parse import urlparse
from redis import Redis
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .operator_copilot import build_operator_copilot
from .routes import register_routes
from .schema import bootstrap_schema
from common.i18n import ui, is_rtl, status_label
from common.env_guard import validate_runtime_environment

SUPPORTED_LANGS = ["en", "ru", "he"]

# Rate limiting: track login attempts per IP (in-memory, resets on restart)
_login_attempts: dict[str, list[float]] = {}
LOGIN_RATE_LIMIT = 10  # max attempts per window
LOGIN_RATE_WINDOW = 300  # 5 minutes


def create_app():
    validate_runtime_environment("web")
    bootstrap_schema()
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.config["SECRET_KEY"] = Config.flask_secret_key()
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = Config.session_cookie_secure()
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
    app.config["PREFERRED_URL_SCHEME"] = "https" if Config.session_cookie_secure() else "http"

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response

    # CSRF protection via flask-wtf
    csrf = None
    try:
        from flask_wtf.csrf import CSRFProtect, generate_csrf
        csrf = CSRFProtect(app)
        app.jinja_env.globals["csrf_token"] = generate_csrf
        # Exempt API endpoints that don't use forms
        csrf.exempt("fb_safe_workflow.api_groups")
        csrf.exempt("billing.stripe_webhook")
        csrf.exempt("auth.fb_callback")

        # Auto-inject CSRF token into all POST forms via after_request
        @app.after_request
        def inject_csrf_token(response):
            if response.content_type and "text/html" in response.content_type:
                token = generate_csrf()
                hidden_field = f'<input type="hidden" name="csrf_token" value="{token}">'
                data = response.get_data(as_text=True)
                # Inject after every <form that has method="post"
                import re
                data = re.sub(
                    r'(<form[^>]*method=["\']post["\'][^>]*>)',
                    r'\1' + hidden_field,
                    data,
                    flags=re.IGNORECASE,
                )
                response.set_data(data)
            return response
    except ImportError:
        pass  # flask-wtf not installed — skip CSRF

    register_routes(app)

    # Liveness/health endpoint — must be reachable without auth or trial gating.
    # Registered directly on app (not a blueprint) so it bypasses login_required
    # decorators on individual blueprints.
    @app.route("/health")
    def health():
        return {"ok": True, "service": "recruit-autopilot"}, 200

    @app.route("/ready")
    def ready():
        errors: list[str] = []

        try:
            from .db import engine as _engine
            with _engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:
            errors.append(f"database: {exc}")

        try:
            Redis.from_url(Config.REDIS_URL).ping()
        except Exception as exc:
            errors.append(f"redis: {exc}")

        if errors:
            return {"ok": False, "service": "recruit-autopilot", "errors": errors}, 503
        return {"ok": True, "service": "recruit-autopilot"}, 200

    # Browser favicon — Flask serves /static/favicon.ico, but most browsers fetch
    # /favicon.ico directly and we want a 200, not a 404 in web logs.
    @app.route("/favicon.ico")
    def favicon():
        from flask import send_from_directory
        import os as _os
        static_dir = _os.path.join(app.root_path, "static")
        return send_from_directory(static_dir, "favicon.ico", mimetype="image/x-icon")

    # Serve uploaded photos only to the owning tenant. Files live in
    # <repo>/data/uploads/<basename>; the route only resolves the basename so
    # path-traversal attempts ("../etc/passwd") are blocked.
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename: str):
        from flask import abort, send_from_directory
        import json as _json
        import os as _os
        if not (session.get("is_admin") or session.get("user_id")):
            abort(404)
        company_id = session.get("current_company_id")
        if not company_id:
            abort(404)

        basename = _os.path.basename(filename)
        from .db import db_session as _db_session
        from .models import Vacancy, Company, Creative
        db = _db_session()
        try:
            allowed = False
            # The company's own logo is served to its tenant.
            company = db.query(Company).filter(Company.id == company_id).first()
            if company and company.logo_path and _os.path.basename(company.logo_path) == basename:
                allowed = True
            # Creative-library assets (banners/posters/logos) belong to the tenant.
            if not allowed:
                creatives = db.query(Creative).filter(Creative.company_id == company_id).all()
                if any(_os.path.basename(cr.file_path) == basename for cr in creatives):
                    allowed = True
            vacancies = db.query(Vacancy).filter(Vacancy.company_id == company_id).all()
            for vacancy in vacancies:
                paths = []
                if vacancy.image_path:
                    paths.append(vacancy.image_path)
                if vacancy.images_json:
                    try:
                        parsed = _json.loads(vacancy.images_json)
                        if isinstance(parsed, list):
                            paths.extend(str(item) for item in parsed if item)
                    except Exception:
                        pass
                if any(_os.path.basename(path) == basename for path in paths):
                    allowed = True
                    break
        finally:
            db.close()
        if not allowed:
            abort(404)

        upload_dir = _os.path.join(app.root_path, "..", "data", "uploads")
        upload_dir = _os.path.abspath(upload_dir)
        return send_from_directory(upload_dir, basename)

    # Trial expiration check middleware
    @app.before_request
    def check_trial_expiration():
        from datetime import datetime
        # Skip for public routes
        public_paths = {"/", "/login", "/register", "/user-login", "/pricing",
                        "/billing/", "/terms", "/set-lang/", "/static/", "/health",
                        "/favicon.ico"}
        path = request.path
        if any(path.startswith(p) or path == p for p in public_paths):
            return None
        user_id = session.get("user_id")
        if not user_id:
            return None  # Admin login — no trial check
        from .db import db_session as _db
        from .models import User
        db = _db()
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.trial_expires_at and datetime.utcnow() > user.trial_expires_at:
            db.close()
            return redirect("/pricing?trial_expired=1")
        db.close()
        return None

    @app.route("/set-lang/<lang>")
    def set_lang(lang):
        if lang in SUPPORTED_LANGS:
            session["ui_lang"] = lang
        referrer = request.referrer or ""
        ref = urlparse(referrer)
        host = ref.netloc or request.host
        marketing_host = (Config.PUBLIC_MARKETING_URL or "").replace("https://", "").replace("http://", "").split("/", 1)[0]
        is_marketing_home = (not referrer) or (ref.path in {"", "/"} and (not marketing_host or host == marketing_host or host == request.host))
        if lang in SUPPORTED_LANGS and is_marketing_home:
            return redirect(f"/?lang={lang}")
        return redirect(request.referrer or "/")

    @app.before_request
    def _detect_ui_lang():
        # First-visit language: honour the browser's Accept-Language so RU/EN ad
        # traffic doesn't land on the Hebrew-RTL default. Runs once — the explicit
        # /set-lang switch and the saved session always win afterwards.
        if session.get("ui_lang"):
            return
        header = request.headers.get("Accept-Language", "")
        for part in header.split(","):
            code = part.split(";")[0].strip().lower().split("-")[0]
            if code in SUPPORTED_LANGS:
                session["ui_lang"] = code
                break

    @app.context_processor
    def inject_globals():
        lang = session.get("ui_lang", "he")
        company_id = session.get("current_company_id")
        company_name = None
        operator_copilot = None
        public_app_url = Config.PUBLIC_APP_URL
        public_marketing_url = Config.PUBLIC_MARKETING_URL
        public_login_url = f"{public_app_url}/login" if public_app_url else "/login"
        public_register_url = f"{public_app_url}/register" if public_app_url else "/register"
        if company_id:
            from .db import db_session
            from .models import Company
            db = db_session()
            c = db.query(Company).filter(Company.id == company_id).first()
            company_name = c.name if c else None
            db.close()
        if session.get("is_admin") or session.get("user_id"):
            operator_copilot = build_operator_copilot(session, request.path, lang)
        # Surface night-mode pause status to all admin templates so operators see why
        # campaigns are quiet between 23:00–07:00 IL. Behaviour is unchanged — this is
        # purely a UI flag; the actual freeze lives in common/tg_client._is_night_hours.
        try:
            from common.tg_client import _is_night_hours as _is_night
            night_mode_active = bool(_is_night())
        except Exception:
            night_mode_active = False
        return {
            "current_company_name": company_name,
            "operator_copilot": operator_copilot,
            "ui_lang": lang,
            "is_rtl": is_rtl(lang),
            "supported_langs": SUPPORTED_LANGS,
            "night_mode_active": night_mode_active,
            "night_mode_window": "23:00–07:00 Asia/Jerusalem",
            "trial_days": Config.trial_days(),
            "billing_enabled": Config.billing_enabled(),
            "public_app_url": public_app_url,
            "public_marketing_url": public_marketing_url,
            "public_login_url": public_login_url,
            "public_register_url": public_register_url,
        }

    app.jinja_env.globals["ui"] = lambda key, **kw: ui(key, session.get("ui_lang", "he"), **kw)
    app.jinja_env.globals["slabel"] = lambda status: status_label(status, session.get("ui_lang", "ru"))

    return app
