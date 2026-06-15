"""Error tracking (Sentry), env-driven. No-op until SENTRY_DSN is set, so prod
runs unchanged until you add the DSN. send_default_pii=False — we never auto-ship
candidate phones / chat logs to Sentry. Flask + RQ integrations auto-enable."""
import logging
import os

logger = logging.getLogger(__name__)
_inited = False


def init_sentry(component: str = "app") -> bool:
    global _inited
    if _inited:
        return True
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0") or 0),
            send_default_pii=False,
            release=(os.getenv("APP_RELEASE", "").strip() or None),
        )
        sentry_sdk.set_tag("component", component)
        _inited = True
        logger.info("[sentry] initialized for %s", component)
        return True
    except Exception as e:  # never let observability break the app
        logger.warning("[sentry] init failed: %s", e)
        return False
