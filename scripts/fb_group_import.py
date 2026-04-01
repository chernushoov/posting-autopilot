import argparse
import json

from app.db import db_session, engine
from app.models import Base, Company
from common.fb_safe_workflow import import_group_seed_file


def _company_id(db, explicit_company_id: int | None) -> int:
    if explicit_company_id:
        return explicit_company_id
    company = db.query(Company).order_by(Company.id.asc()).first()
    if not company:
        raise SystemExit("No company found. Run python -m scripts.seed first or pass --company-id.")
    return company.id


def main():
    parser = argparse.ArgumentParser(description="Import Facebook group seed data into fb_group_sources/fb_groups.")
    parser.add_argument("path", help="CSV or JSON seed file path")
    parser.add_argument("--company-id", type=int, default=None)
    parser.add_argument("--source-label", default=None)
    parser.add_argument("--collected-by", default="codex_seed_import")
    parser.add_argument("--default-source-type", default=None)
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = db_session()
    try:
        company_id = _company_id(db, args.company_id)
        report = import_group_seed_file(
            db,
            company_id=company_id,
            path=args.path,
            source_label=args.source_label,
            collected_by=args.collected_by,
            default_source_type=args.default_source_type,
        )
        db.commit()
    except Exception:
        db.rollback()
        db.close()
        raise
    db.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
