"""Start the web-only Render preview after its free datastores are ready."""

from __future__ import annotations

import ipaddress
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from redis import Redis  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.config import Config  # noqa: E402
from app.db import engine  # noqa: E402
from app.schema import bootstrap_schema  # noqa: E402


TRUTHY = {"1", "true", "yes", "on"}
LOCAL_HOSTNAMES = {"localhost", "host.docker.internal"}


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in TRUTHY


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


def _is_local_hostname(hostname: str | None) -> bool:
    if not hostname:
        return True
    if hostname.lower() in LOCAL_HOSTNAMES:
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def validate_preview_environment() -> None:
    errors: list[str] = []
    database = urlparse(Config.DATABASE_URL)
    redis = urlparse(Config.REDIS_URL)
    flask_secret = os.getenv("FLASK_SECRET_KEY", "")
    admin_password = os.getenv("ADMIN_PASSWORD", "")

    if database.scheme not in {"postgres", "postgresql"} or _is_local_hostname(database.hostname):
        errors.append("DATABASE_URL must be a Render Postgres URL")
    if redis.scheme not in {"redis", "rediss"} or _is_local_hostname(redis.hostname):
        errors.append("REDIS_URL must be a Render Key Value URL")
    if len(flask_secret) < 32 or flask_secret in {"dev-secret", "change-me"}:
        errors.append("FLASK_SECRET_KEY must be a generated 32+ character value")
    if len(admin_password) < 12 or admin_password in {"admin123", "change-me"}:
        errors.append("ADMIN_PASSWORD must be a generated 12+ character value")
    if _truthy("BILLING_ENABLED"):
        errors.append("BILLING_ENABLED must remain off in the free customer preview")

    if errors:
        raise RuntimeError("Preview environment validation failed:\n" + "\n".join(f"- {item}" for item in errors))


def wait_for_datastores(timeout_seconds: int = 120) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            Redis.from_url(Config.REDIS_URL).ping()
            return
        except Exception as exc:  # Render can start linked resources in any order.
            last_error = exc
            time.sleep(2)

    raise RuntimeError(f"Preview datastores were not ready after {timeout_seconds}s: {last_error}")


def gunicorn_command() -> list[str]:
    workers = _positive_int("WEB_CONCURRENCY", 1)
    port = _positive_int("PORT", 10000)
    return [
        sys.executable,
        "-m",
        "gunicorn",
        "--workers",
        str(workers),
        "--threads",
        "2",
        "--timeout",
        "120",
        "--access-logfile",
        "-",
        "--error-logfile",
        "-",
        "--bind",
        f"0.0.0.0:{port}",
        "app.factory:create_app()",
    ]


def main() -> None:
    validate_preview_environment()
    wait_for_datastores()
    bootstrap_schema()

    if _truthy("PREVIEW_SEED"):
        from scripts.seed import main as seed

        seed()

    os.execv(sys.executable, gunicorn_command())


if __name__ == "__main__":
    main()
