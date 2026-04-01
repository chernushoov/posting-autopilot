from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import Config

engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def db_session():
    return SessionLocal()
