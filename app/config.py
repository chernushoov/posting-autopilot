import os
from common.runtime_env import get_ai_api_key, get_ai_provider, get_recruitbot_token

class Config:
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")
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
