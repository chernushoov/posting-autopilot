from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from .config import Config

engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# SQLite ships with FK enforcement OFF per-connection. Turn it on so that
# ondelete=CASCADE / SET NULL declared on the models is actually honored and
# orphaned tenant rows can't accumulate. No-op on Postgres (handled natively).
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        is_sqlite = "sqlite3" in type(dbapi_connection).__module__
    except Exception:
        is_sqlite = False
    if is_sqlite:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def db_session():
    return SessionLocal()
