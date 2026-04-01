from app.db import engine
from app.models import Base
from common.fb_safe_workflow import ensure_all_tables


def main():
    report = ensure_all_tables(engine=engine, base_metadata=Base.metadata)
    print("Migration status:", report["status"])
    print("FB tables:", ", ".join(report["fb_tables"]))


if __name__ == "__main__":
    main()
