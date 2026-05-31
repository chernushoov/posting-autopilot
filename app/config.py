import os
from common.runtime_env import get_ai_api_key, get_ai_provider, get_recruitbot_token


FORBIDDEN_FLASK_SECRET_KEYS = {
    "",
    "dev-secret",
    "change-me",
    "replace-with-64-char-random-secret",
}


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


class Config:
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "").strip()
    ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
    APP_ENV = os.getenv("APP_ENV", os.getenv("FLASK_ENV", "")).strip().lower()
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(8 * 1024 * 1024)))

    if not ADMIN_PASSWORD:
        import warnings
        warnings.warn("ADMIN_PASSWORD not set — admin login disabled")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ra.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    TELEGRAM_BOT_TOKEN = get_recruitbot_token()
    AI_PROVIDER = get_ai_provider()
    AI_API_KEY = get_ai_api_key()

    @classmethod
    def flask_secret_key(cls) -> str:
        if cls.FLASK_SECRET_KEY not in FORBIDDEN_FLASK_SECRET_KEYS and len(cls.FLASK_SECRET_KEY) >= 32:
            return cls.FLASK_SECRET_KEY
        if _truthy_env("ALLOW_INSECURE_DEV_SECRET"):
            import warnings
            warnings.warn(
                "Using insecure Flask secret key because ALLOW_INSECURE_DEV_SECRET=1. "
                "Never use this in shared or production deployments."
            )
            return cls.FLASK_SECRET_KEY or "dev-secret"
        raise RuntimeError(
            "FLASK_SECRET_KEY must be set to a strong random value (32+ chars). "
            "For local-only throwaway runs, set ALLOW_INSECURE_DEV_SECRET=1 explicitly."
        )

    @classmethod
    def session_cookie_secure(cls) -> bool:
        return _truthy_env("FORCE_HTTPS") or cls.APP_ENV in {"prod", "production", "staging"}
