from flask import Flask, session, request, redirect
from .config import Config
from .operator_copilot import build_operator_copilot
from .routes import register_routes
from .schema import bootstrap_schema
from common.i18n import ui, is_rtl

SUPPORTED_LANGS = ["en", "ru", "he"]

# Rate limiting: track login attempts per IP (in-memory, resets on restart)
_login_attempts: dict[str, list[float]] = {}
LOGIN_RATE_LIMIT = 10  # max attempts per window
LOGIN_RATE_WINDOW = 300  # 5 minutes


def create_app():
    bootstrap_schema()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.FLASK_SECRET_KEY
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    # Only set Secure flag when not running locally (HTTPS required for Secure cookies)
    import os
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("FORCE_HTTPS", "") == "1"

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

    # Browser favicon — Flask serves /static/favicon.ico, but most browsers fetch
    # /favicon.ico directly and we want a 200, not a 404 in web logs.
    @app.route("/favicon.ico")
    def favicon():
        from flask import send_from_directory
        import os as _os
        static_dir = _os.path.join(app.root_path, "static")
        return send_from_directory(static_dir, "favicon.ico", mimetype="image/x-icon")

    # Serve uploaded photos (vacancy carousel for real estate / cars). Files
    # live in <repo>/data/uploads/<basename>; the route only resolves the
    # basename so path-traversal attempts ("../etc/passwd") are blocked by
    # send_from_directory.
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename: str):
        from flask import send_from_directory
        import os as _os
        upload_dir = _os.path.join(app.root_path, "..", "data", "uploads")
        upload_dir = _os.path.abspath(upload_dir)
        return send_from_directory(upload_dir, filename)

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
        return redirect(request.referrer or "/")

    @app.context_processor
    def inject_globals():
        lang = session.get("ui_lang", "he")
        company_id = session.get("current_company_id")
        company_name = None
        operator_copilot = None
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
        }

    app.jinja_env.globals["ui"] = lambda key, **kw: ui(key, session.get("ui_lang", "he"), **kw)

    return app
