import os
from common.runtime_env import get_ai_api_key, get_ai_provider, get_recruitbot_token

_DEV_SECRET = "dev-secret"


def _resolve_secret_key() -> str:
    """Resolve the Flask signing key, failing closed in production.

    The session cookie (is_admin / owner_id / current_company_id) is signed with
    this key — if it is the shipped default in prod, anyone can forge an admin
    session and read/write every tenant's data. So: only the explicit dev escape
    hatch (FLASK_DEBUG=1 or FLASK_ENV=development) is allowed to use the default;
    everywhere else an unset/default key is a hard startup error.
    """
    key = os.getenv("FLASK_SECRET_KEY", "")
    is_dev = os.getenv("FLASK_DEBUG", "") == "1" or os.getenv("FLASK_ENV", "") == "development"
    if not key or key == _DEV_SECRET:
        if is_dev:
            return _DEV_SECRET
        raise RuntimeError(
            "FLASK_SECRET_KEY is unset or equals the insecure default 'dev-secret'. "
            "Generate a strong random key (e.g. `python -c \"import secrets;print(secrets.token_urlsafe(48))\"`) "
            "and set it in the environment, or set FLASK_DEBUG=1 for local development only."
        )
    return key


class Config:
    FLASK_SECRET_KEY = _resolve_secret_key()
    ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

    if not ADMIN_PASSWORD:
        import warnings
        warnings.warn("ADMIN_PASSWORD not set — admin login disabled")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ra.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    TELEGRAM_BOT_TOKEN = get_recruitbot_token()
    AI_PROVIDER = get_ai_provider()
    AI_API_KEY = get_ai_api_key()
