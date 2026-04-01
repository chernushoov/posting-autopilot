import requests
from common.runtime_env import get_recruitbot_token

BOT_TOKEN = get_recruitbot_token()

def _api(method: str):
    return f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

def tg_send_message_safe(chat_id_or_username: str, text: str):
    if not BOT_TOKEN:
        return False, "RECRUITBOT_TELEGRAM_BOT_TOKEN/TELEGRAM_BOT_TOKEN missing"
    try:
        r = requests.post(_api("sendMessage"), json={"chat_id": chat_id_or_username, "text": text})
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}: {r.text[:120]}"
        data = r.json()
        if not data.get("ok"):
            return False, f"API error: {data}"
        return True, "sent"
    except Exception as e:
        return False, f"exception: {e}"
