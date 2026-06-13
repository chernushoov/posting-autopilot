from app.db import engine
from app.models import Base
from app.schema import bootstrap_schema
from common.fb_safe_workflow import ensure_all_tables
from common.env_guard import validate_runtime_environment


def main():
    validate_runtime_environment("web")
    bootstrap_schema()
    report = ensure_all_tables(engine=engine, base_metadata=Base.metadata)
    print("Migration status:", report["status"])
    print("FB tables:", ", ".join(report["fb_tables"]))


if __name__ == "__main__":
    main()
