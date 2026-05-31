"""Password hashing helpers with legacy SHA-256 migration support."""

from __future__ import annotations

from hashlib import sha256

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def legacy_sha256_hash(password: str) -> str:
    return sha256(password.encode()).hexdigest()


def is_legacy_sha256_hash(stored_hash: str | None) -> bool:
    if not stored_hash or len(stored_hash) != 64:
        return False
    return all(ch in "0123456789abcdef" for ch in stored_hash.lower())


def verify_password(stored_hash: str | None, password: str) -> tuple[bool, bool]:
    """Return (is_valid, should_upgrade_hash)."""
    if not stored_hash:
        return False, False
    if is_legacy_sha256_hash(stored_hash):
        return stored_hash == legacy_sha256_hash(password), True
    try:
        return check_password_hash(stored_hash, password), False
    except ValueError:
        return False, False
