from .auth_routes import bp as auth_bp
from .companies import bp as companies_bp
from .vacancies import bp as vacancies_bp
from .sources import bp as sources_bp
from .campaigns import bp as campaigns_bp
from .candidates import bp as candidates_bp
from .ai_settings import bp as ai_bp
from .fb_safe_workflow import bp as fb_safe_workflow_bp
from .fb_ui import bp as fb_ui_bp
from .analytics import bp as analytics_bp
from .pricing import bp as pricing_bp
from .prospecting import bp as prospecting_bp
from .registration import bp as registration_bp
from .billing import bp as billing_bp
from .profile import bp as profile_bp
from .demo import bp as demo_bp
from .creatives import bp as creatives_bp

def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(registration_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(vacancies_bp)
    app.register_blueprint(sources_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(candidates_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(fb_safe_workflow_bp)
    app.register_blueprint(fb_ui_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(pricing_bp)
    app.register_blueprint(prospecting_bp)
    app.register_blueprint(demo_bp)
    app.register_blueprint(creatives_bp)
