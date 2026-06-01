"""Build Telegram deep-links into the screening bot.

NOTE: this module was imported by app/routes/vacancies.py and worker/tasks.py
but had never been committed to this repo — the live machine carried it
untracked, so a fresh clone / deploy crashed on import. Reconstructed from the
call sites (build_recruitbot_apply_link(vacancy_id)) and the bot username used
throughout the codebase (@AutopillotRecruit_bot).
"""
import os

DEFAULT_BOT_USERNAME = "AutopillotRecruit_bot"


def get_bot_username() -> str:
    """Resolve the screening bot's @username (without the leading @).

    Override via env for other deployments; defaults to the username hardcoded
    across the UI/i18n strings in this repo.
    """
    for key in (
        "RECRUITBOT_BOT_USERNAME",
        "RECRUIT_BOT_USERNAME",
        "RECRUITBOT_TELEGRAM_BOT_USERNAME",
        "BOT_USERNAME",
    ):
        val = os.environ.get(key)
        if val and val.strip():
            return val.strip().lstrip("@")
    return DEFAULT_BOT_USERNAME


def build_recruitbot_apply_link(vacancy_id) -> str:
    """Deep-link a candidate straight into the apply/screening flow for a vacancy.

    Opening this link starts a chat with the bot and passes `apply_<vacancy_id>`
    as the /start payload, which the bot handler parses to attach the applicant
    to the right vacancy.
    """
    return f"https://t.me/{get_bot_username()}?start=apply_{vacancy_id}"
