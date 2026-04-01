"""
Facebook Graph API client — OAuth + group sync.

Environment variables:
  FB_APP_ID — Facebook App ID from developers.facebook.com
  FB_APP_SECRET — Facebook App Secret
"""
import os
import logging
import requests

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


def get_login_url(redirect_uri: str, state: str = "") -> str:
    """Build Facebook OAuth login URL."""
    params = (
        f"client_id={_app_id()}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=groups_access_member_info,publish_to_groups"
        f"&response_type=code"
    )
    if state:
        params += f"&state={state}"
    return f"https://www.facebook.com/v19.0/dialog/oauth?{params}"


def exchange_code(code: str, redirect_uri: str) -> dict:
    """Exchange authorization code for access token."""
    try:
        r = requests.get(f"{FB_GRAPH_URL}/oauth/access_token", params={
            "client_id": _app_id(),
            "client_secret": _app_secret(),
            "redirect_uri": redirect_uri,
            "code": code,
        }, timeout=10)
        data = r.json()
        if "access_token" in data:
            return {"ok": True, "access_token": data["access_token"], "token_type": data.get("token_type", "")}
        return {"ok": False, "error": data.get("error", {}).get("message", "Token exchange failed")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_long_lived_token(short_token: str) -> dict:
    """Exchange short-lived token for long-lived (60 days)."""
    try:
        r = requests.get(f"{FB_GRAPH_URL}/oauth/access_token", params={
            "grant_type": "fb_exchange_token",
            "client_id": _app_id(),
            "client_secret": _app_secret(),
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


def get_user_groups(access_token: str) -> dict:
    """Get user's Facebook groups (where they are admin/member)."""
    groups = []
    url = f"{FB_GRAPH_URL}/me/groups"
    params = {
        "access_token": access_token,
        "fields": "id,name,member_count,privacy,administrator",
        "limit": 100,
    }
    try:
        while url:
            r = requests.get(url, params=params, timeout=15)
            data = r.json()
            if "error" in data:
                return {"ok": False, "error": data["error"].get("message", "API error")}
            for g in data.get("data", []):
                groups.append({
                    "id": g["id"],
                    "name": g.get("name", ""),
                    "member_count": g.get("member_count", 0),
                    "privacy": g.get("privacy", ""),
                    "is_admin": g.get("administrator", False),
                })
            # Pagination
            paging = data.get("paging", {})
            url = paging.get("next")
            params = {}  # next URL has params built-in
        return {"ok": True, "groups": groups, "total": len(groups)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
