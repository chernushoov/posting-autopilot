"""Roundtrip + column-level test for common/crypto (encryption at rest).

Run (generates an ephemeral key automatically):
    /tmp/pa-crypto-venv/bin/python scripts/test_crypto_roundtrip.py

Validates:
  1. enc/dec roundtrip; None passes through.
  2. Legacy plaintext passes through dec() unchanged (non-destructive rollout).
  3. EncryptedString column actually stores CIPHERTEXT in the DB and decrypts on read.
  4. Without a key, enc/dec are no-ops (so the app still runs key-less in dev/CI).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cryptography.fernet import Fernet

os.environ["DATA_ENCRYPTION_KEY"] = Fernet.generate_key().decode()

from common import crypto  # noqa: E402

crypto.reset_cache()

secret = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"  # shaped like a Telegram api_hash

# 1. roundtrip + None
ct = crypto.enc(secret)
assert ct != secret, "ciphertext must differ from plaintext"
assert crypto.dec(ct) == secret, "roundtrip failed"
assert crypto.enc(None) is None and crypto.dec(None) is None, "None must pass through"

# 2. legacy plaintext passthrough
assert crypto.dec("legacy_plaintext_value") == "legacy_plaintext_value", "legacy passthrough failed"

# 3. column-level: ciphertext is what hits the DB, ORM decrypts on read
import sqlalchemy as sa  # noqa: E402
from sqlalchemy.orm import declarative_base, Session  # noqa: E402

Base = declarative_base()


class Row(Base):
    __tablename__ = "t"
    id = sa.Column(sa.Integer, primary_key=True)
    secret = sa.Column(crypto.EncryptedString, nullable=True)


eng = sa.create_engine("sqlite://")
Base.metadata.create_all(eng)
with Session(eng) as s:
    s.add(Row(id=1, secret=secret))
    s.commit()
with eng.connect() as c:
    raw = c.execute(sa.text("SELECT secret FROM t WHERE id=1")).scalar()
assert raw != secret and raw.startswith("gAAAAA"), f"DB must store ciphertext, got {raw!r}"
with Session(eng) as s:
    assert s.get(Row, 1).secret == secret, "ORM read must decrypt"

# 4. no-key mode = no-op
os.environ.pop("DATA_ENCRYPTION_KEY", None)
crypto.reset_cache()
assert crypto.enc(secret) == secret and crypto.dec(secret) == secret, "key-less mode must be a no-op"

print("OK: crypto roundtrip + EncryptedString column + legacy passthrough + no-key no-op")
