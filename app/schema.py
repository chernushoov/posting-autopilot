from sqlalchemy import inspect, text

from .db import engine
from .models import Base


def _ensure_columns(table_name: str, column_defs: dict[str, str]) -> None:
    inspector = inspect(engine)
    existing = {column["name"] for column in inspector.get_columns(table_name)}
    missing = {name: ddl for name, ddl in column_defs.items() if name not in existing}
    if not missing:
        return
    with engine.begin() as conn:
        for name, ddl in missing.items():
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {name} {ddl}"))


def bootstrap_schema() -> None:
    Base.metadata.create_all(bind=engine)

    _ensure_columns(
        "vacancies",
        {
            "salary_text": "TEXT",
            "schedule_text": "TEXT",
            "contact_text": "TEXT",
            "apply_url": "TEXT",
            "final_post_title": "TEXT",
            "final_post_body": "TEXT",
        },
    )
    _ensure_columns(
        "vacancies",
        {
            "listing_type": "VARCHAR(40) NOT NULL DEFAULT 'recruitment'",
            "bot_introduction": "TEXT",
            "bot_faq_knowledge": "TEXT",
            "bot_qualifying_questions": "TEXT",
            "bot_hot_criteria": "TEXT",
            "bot_cold_criteria": "TEXT",
            "whatsapp_number": "VARCHAR(20)",
            "image_path": "VARCHAR(500)",
            # Multi-photo support — JSON array of upload paths. Real estate
            # listings need 8-15 photos per apartment; cars need 8-15 too.
            # Recruitment usually one photo. image_path stays as legacy "primary"
            # photo; images_json is the canonical list when set.
            "images_json": "TEXT",
        },
    )
    _ensure_columns(
        "candidates",
        {
            "language": "VARCHAR(10)",
            "phone": "VARCHAR(30)",
            "classification": "VARCHAR(10)",
        },
    )
    _ensure_columns(
        "sources",
        {
            "platform": "VARCHAR(20) NOT NULL DEFAULT 'telegram'",
            "destination_kind": "VARCHAR(20) NOT NULL DEFAULT 'group'",
            "posting_mode": "VARCHAR(30) NOT NULL DEFAULT 'auto'",
            "destination_url": "TEXT",
            "folder": "VARCHAR(100)",
        },
    )

    _ensure_columns(
        "companies",
        {
            "tg_api_id": "VARCHAR(20)",
            "tg_api_hash": "VARCHAR(64)",
            "fb_access_token": "TEXT",
            "fb_user_id": "VARCHAR(64)",
            "fb_user_name": "VARCHAR(200)",
            "business_type": "VARCHAR(20) NOT NULL DEFAULT 'company'",
            "contact_person": "VARCHAR(200)",
            "phone": "VARCHAR(30)",
            "email": "VARCHAR(300)",
            "website": "VARCHAR(500)",
            "logo_emoji": "VARCHAR(10)",
            "owner_telegram_id": "VARCHAR(64)",
        },
    )

    # Ensure 'he' value exists in the language enum (Postgres)
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TYPE language ADD VALUE IF NOT EXISTS 'he'"))
        except Exception:
            pass  # SQLite or enum already has 'he'

    # Prospects + OutreachAttempts tables are auto-created by Base.metadata.create_all above

    with engine.begin() as conn:
        conn.execute(text("UPDATE vacancies SET final_post_title = COALESCE(final_post_title, title)"))
        conn.execute(text("UPDATE vacancies SET final_post_body = COALESCE(final_post_body, body)"))
        conn.execute(text("UPDATE sources SET platform = COALESCE(platform, 'telegram')"))
        conn.execute(text("UPDATE sources SET destination_kind = COALESCE(destination_kind, CAST(source_type AS VARCHAR(20)), 'group')"))
        conn.execute(text("UPDATE sources SET posting_mode = COALESCE(posting_mode, CASE WHEN platform = 'facebook' THEN 'assisted_manual' ELSE 'auto' END)"))
