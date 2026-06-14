"""
Application-layer encryption for secrets at rest (Fernet = AES-128-CBC + HMAC-SHA256).

We encrypt the few high-value tenant secrets that would let an attacker take over a
customer's Telegram or Facebook account if the database were ever leaked:
  - Company.tg_api_hash      (Telegram app api_hash — paired with api_id)
  - Company.fb_access_token  (Facebook Graph token; scopes incl. pages_manage_posts)

KEY: env var DATA_ENCRYPTION_KEY — a urlsafe-base64 32-byte Fernet key. Generate with:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

SAFE ROLLOUT / GRACEFUL DEGRADATION (so enabling this can never brick the app):
  - If the key (or the `cryptography` package) is absent, enc()/dec() become no-ops
    and log a one-time warning. The app keeps running on plaintext (dev/CI). Set the
    key in production to turn encryption on.
  - dec() transparently passes through any value that is NOT our ciphertext (legacy
    plaintext rows written before the key existed). So turning encryption on never
    destroys existing data; those rows get encrypted on their next write.

USAGE: put the EncryptedString SQLAlchemy type on a column — encryption/decryption
then happens transparently on every write/read and no call site needs to change.
"""
from __future__ import annotations

import logging
import os

from sqlalchemy.types import TypeDecorator, Text

logger = logging.getLogger(__name__)

_ENV_KEY = "DATA_ENCRYPTION_KEY"
_warned_missing = [False]


def _load_fernet():
    """Return a cached Fernet instance, or None if encryption is disabled
    (no key set, key invalid, or `cryptography` not installed)."""
    cached = getattr(_load_fernet, "_cached", "unset")
    if cached != "unset":
        return cached
    fernet = None
    key = (os.getenv(_ENV_KEY) or "").strip()
    if key:
        try:
            from cryptography.fernet import Fernet
            fernet = Fernet(key.encode("ascii"))
        except Exception as exc:  # invalid key, or cryptography missing
            logger.error(
                "[crypto] %s is set but unusable (%s) — secrets will NOT be "
                "encrypted. Fix the key.", _ENV_KEY, exc,
            )
            fernet = None
    _load_fernet._cached = fernet
    return fernet


def reset_cache() -> None:
    """Drop the cached Fernet (tests change the env var at runtime)."""
    if hasattr(_load_fernet, "_cached"):
        del _load_fernet._cached
    _warned_missing[0] = False


def encryption_active() -> bool:
    """True when a usable key is configured (used by health/diagnostic checks)."""
    return _load_fernet() is not None


def _warn_once_missing() -> None:
    if not _warned_missing[0]:
        logger.warning(
            "[crypto] %s not set — secrets are stored in PLAINTEXT. "
            "Set it in production.", _ENV_KEY,
        )
        _warned_missing[0] = True


def enc(value):
    """Encrypt a value to a ciphertext str. None passes through. No-op without a key."""
    if value is None:
        return None
    text_value = str(value)
    fernet = _load_fernet()
    if fernet is None:
        _warn_once_missing()
        return text_value
    return fernet.encrypt(text_value.encode("utf-8")).decode("ascii")


def dec(value):
    """Decrypt our ciphertext back to str. None passes through. Values that are not
    our ciphertext (legacy plaintext) pass through unchanged."""
    if value is None:
        return None
    fernet = _load_fernet()
    if fernet is None:
        return value
    raw = value.encode("utf-8") if isinstance(value, str) else value
    try:
        return fernet.decrypt(raw).decode("utf-8")
    except Exception:
        # Not a valid Fernet token for this key → legacy plaintext; return as-is.
        return value


class EncryptedString(TypeDecorator):
    """Transparently encrypt a text column at rest with Fernet.

    Stored as TEXT because ciphertext is longer than plaintext. Reads decrypt and
    writes encrypt. Legacy plaintext is passed through on read, so enabling
    encryption is non-destructive. cache_ok=True: the type takes no parameters that
    would change the generated SQL.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return enc(value)

    def process_result_value(self, value, dialect):
        return dec(value)
