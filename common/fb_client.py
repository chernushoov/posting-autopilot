"""
Facebook Graph API client — OAuth + official Page sync.

Environment variables:
  FB_APP_ID — Facebook App ID from developers.facebook.com
  FB_APP_SECRET — Facebook App Secret
"""
import os
import logging
import requests
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

FB_GRAPH_URL = "https://graph.facebook.com/v19.0"


def _app_id():
    return os.getenv("FB_APP_ID", "")

def _app_secret():
    return os.getenv("FB_APP_SECRET", "")

def is_configured() -> bool:
    return bool(_app_id() and _app_secret())

# Keep module-level for backward compat
FB_APP_ID = _app_id()
FB_APP_SECRET = _app_secret()


def get_login_url(redirect_uri: str, state: str = "", app_id: str | None = None) -> str:
    """Build Facebook OAuth login URL for the official Pages flow."""
    params = {
        "client_id": app_id or _app_id(),
        "redirect_uri": redirect_uri,
        "scope": "public_profile,pages_show_list,pages_read_engagement,pages_manage_posts",
        "response_type": "code",
    }
    if state:
        params["state"] = state
    return f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"


def exchange_code(
    code: str,
    redirect_uri: str,
    app_id: str | None = None,
    app_secret: str | None = None,
) -> dict:
    """Exchange authorization code for access token."""
    try:
        r = requests.get(f"{FB_GRAPH_URL}/oauth/access_token", params={
            "client_id": app_id or _app_id(),
            "client_secret": app_secret or _app_secret(),
            "redirect_uri": redirect_uri,
            "code": code,
        }, timeout=10)
        data = r.json()
        if "access_token" in data:
            return {"ok": True, "access_token": data["access_token"], "token_type": data.get("token_type", "")}
        return {"ok": False, "error": data.get("error", {}).get("message", "Token exchange failed")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_long_lived_token(
    short_token: str,
    app_id: str | None = None,
    app_secret: str | None = None,
) -> dict:
    """Exchange short-lived token for long-lived (60 days)."""
    try:
        r = requests.get(f"{FB_GRAPH_URL}/oauth/access_token", params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id or _app_id(),
            "client_secret": app_secret or _app_secret(),
            "fb_exchange_token": short_token,
        }, timeout=10)
        data = r.json()
        if "access_token" in data:
            return {"ok": True, "access_token": data["access_token"]}
        return {"ok": False, "error": data.get("error", {}).get("message", "Long token exchange failed")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_user_info(access_token: str) -> dict:
    """Get basic user info."""
    try:
        r = requests.get(f"{FB_GRAPH_URL}/me", params={
            "access_token": access_token,
            "fields": "id,name,email",
        }, timeout=10)
        data = r.json()
        if "id" in data:
            return {"ok": True, "user": data}
        return {"ok": False, "error": data.get("error", {}).get("message", "Failed to get user info")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_user_pages(access_token: str) -> dict:
    """Get Facebook Pages available to the app user through the official Pages API."""
    pages = []
    url = f"{FB_GRAPH_URL}/me/accounts"
    params = {
        "access_token": access_token,
        "fields": "id,name,link,category,access_token,tasks",
        "limit": 100,
    }
    try:
        while url:
            r = requests.get(url, params=params, timeout=15)
            data = r.json()
            if "error" in data:
                return {"ok": False, "error": data["error"].get("message", "API error")}
            for page in data.get("data", []):
                pages.append({
                    "id": page["id"],
                    "name": page.get("name", ""),
                    "link": page.get("link") or f"https://facebook.com/{page['id']}",
                    "category": page.get("category", ""),
                    "tasks": page.get("tasks", []),
                })
            # Pagination
            paging = data.get("paging", {})
            url = paging.get("next")
            params = {}  # next URL has params built-in
        return {"ok": True, "pages": pages, "total": len(pages)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_user_groups(access_token: str) -> dict:
    """Groups sync is not available in the legal/official flow anymore."""
    logger.warning("Facebook Groups sync requested, but the official Groups API path is deprecated.")
    return {
        "ok": False,
        "error": (
            "Official Facebook Groups sync is not available for this product path. "
            "Use manual group URLs instead."
        ),
    }
