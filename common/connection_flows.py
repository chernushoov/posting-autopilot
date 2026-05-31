"""Short-lived server-side storage for connection setup flows.

Flask's default session is signed but not encrypted, so connection secrets must
not live there. Store only an opaque flow id in the client cookie and keep the
temporary credentials server-side until the OAuth/verification callback finishes.
"""

from __future__ import annotations

import json
import secrets
import time
from pathlib import Path
from typing import Any


FLOW_DIR = Path(__file__).resolve().parents[1] / "data" / "connection_flows"
DEFAULT_TTL_SECONDS = 30 * 60


def _flow_path(flow_id: str) -> Path:
    safe_id = "".join(ch for ch in flow_id if ch.isalnum() or ch in {"-", "_"})
    if safe_id != flow_id or not safe_id:
        raise ValueError("Invalid flow id")
    return FLOW_DIR / f"{safe_id}.json"


def _load_record(flow_id: str) -> dict[str, Any] | None:
    try:
        path = _flow_path(flow_id)
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if record.get("expires_at", 0) < time.time():
        delete_connection_flow(flow_id)
        return None
    return record


def create_connection_flow(
    kind: str,
    company_id: int | None,
    payload: dict[str, Any],
    *,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> str:
    FLOW_DIR.mkdir(parents=True, exist_ok=True)
    flow_id = secrets.token_urlsafe(32)
    record = {
        "kind": kind,
        "company_id": company_id,
        "expires_at": time.time() + ttl_seconds,
        "payload": payload,
    }
    path = _flow_path(flow_id)
    path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    path.chmod(0o600)
    return flow_id


def get_connection_flow(
    flow_id: str | None,
    *,
    kind: str | None = None,
    company_id: int | None = None,
) -> dict[str, Any] | None:
    if not flow_id:
        return None
    record = _load_record(flow_id)
    if not record:
        return None
    if kind is not None and record.get("kind") != kind:
        return None
    if company_id is not None and record.get("company_id") != company_id:
        return None
    payload = record.get("payload")
    return payload if isinstance(payload, dict) else None


def update_connection_flow(
    flow_id: str,
    payload_updates: dict[str, Any],
    *,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> bool:
    record = _load_record(flow_id)
    if not record:
        return False
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return False
    payload.update(payload_updates)
    record["expires_at"] = time.time() + ttl_seconds
    path = _flow_path(flow_id)
    path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    path.chmod(0o600)
    return True


def delete_connection_flow(flow_id: str | None) -> None:
    if not flow_id:
        return
    try:
        _flow_path(flow_id).unlink(missing_ok=True)
    except (OSError, ValueError):
        pass
