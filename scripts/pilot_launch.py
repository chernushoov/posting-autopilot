#!/usr/bin/env python3
"""
Task 3.3: Pilot Launch — import leads, show outreach status, track pipeline.

Usage:
  python scripts/pilot_launch.py status      — Show lead pipeline
  python scripts/pilot_launch.py import      — Import leads from growth/ into DB
  python scripts/pilot_launch.py tier1       — Show top 10 targets (small agencies)
  python scripts/pilot_launch.py templates   — Show outreach templates
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LEADS_FILE = ROOT / "growth" / "leads-israeli-agencies.json"
TEMPLATES_FILE = ROOT / "growth" / "outreach-templates.json"


def load_leads() -> list[dict]:
    data = json.loads(LEADS_FILE.read_text())
    return data.get("leads", [])


def load_templates() -> dict:
    return json.loads(TEMPLATES_FILE.read_text())


def cmd_status():
    """Show lead pipeline status."""
    leads = load_leads()
    total = len(leads)
    by_status = {}
    for lead in leads:
        s = lead.get("status", "new")
        by_status[s] = by_status.get(s, 0) + 1
    by_size = {}
    for lead in leads:
        s = lead.get("size", "unknown")
        by_size[s] = by_size.get(s, 0) + 1

    print(f"\n{'='*50}")
    print(f"  PILOT LAUNCH — Lead Pipeline")
    print(f"{'='*50}")
    print(f"\n  Total leads: {total}")
    print(f"\n  By status:")
    for s, c in sorted(by_status.items()):
        bar = "█" * c
        print(f"    {s:15s} {c:3d} {bar}")
    print(f"\n  By size:")
    for s, c in sorted(by_size.items()):
        print(f"    {s:15s} {c:3d}")
    print()


def cmd_import():
    """Import leads into Prospect table in DB."""
    from app.db import db_session
    from app.models import Prospect, Company

    db = db_session()
    comp = db.query(Company).filter(Company.is_active == True).order_by(Company.id.asc()).first()
    if not comp:
        print("ERROR: No active company. Create one first.")
        db.close()
        return

    leads = load_leads()
    imported = 0
    skipped = 0

    for lead in leads:
        existing = db.query(Prospect).filter(
            Prospect.company_id == comp.id,
            Prospect.name == lead["name"]
        ).first()
        if existing:
            skipped += 1
            continue

        p = Prospect(
            company_id=comp.id,
            name=lead["name"],
            category=lead.get("specialization", ""),
            website=lead.get("website", ""),
            city=lead.get("city", ""),
            source_query=f"growth/leads-israeli-agencies.json#id={lead.get('id', '')}",
        )
        db.add(p)
        imported += 1

    db.commit()
    db.close()
    print(f"\n  Imported: {imported}")
    print(f"  Skipped (existing): {skipped}")
    print(f"  Total in file: {len(leads)}")


def cmd_tier1():
    """Show top 10 targets — small/medium agencies best for pilot."""
    leads = load_leads()
    # Tier 1: small agencies — easier to close, more flexible
    tier1 = [l for l in leads if l.get("size") in ("small", "medium")]
    tier1 = tier1[:10]

    print(f"\n{'='*50}")
    print(f"  TIER 1 TARGETS — Best for pilot")
    print(f"{'='*50}")
    for i, lead in enumerate(tier1, 1):
        print(f"\n  {i}. {lead['name']}")
        print(f"     Web: {lead.get('website', '-')}")
        print(f"     City: {lead.get('city', '-')}")
        print(f"     Focus: {lead.get('specialization', '-')}")
        print(f"     Notes: {lead.get('notes', '-')}")
    print()


def cmd_templates():
    """Show outreach templates and sequence."""
    data = load_templates()
    templates = data.get("templates", {})
    sequence = data.get("outreach_sequence", {})

    print(f"\n{'='*50}")
    print(f"  OUTREACH TEMPLATES")
    print(f"{'='*50}")

    for name, tpl in templates.items():
        print(f"\n  [{name}]")
        if isinstance(tpl, dict):
            for k, v in tpl.items():
                if isinstance(v, list):
                    print(f"    {k}:")
                    for item in v[:3]:
                        print(f"      - {item[:80]}")
                elif isinstance(v, str):
                    preview = v[:120].replace("\n", " ")
                    print(f"    {k}: {preview}...")

    print(f"\n  SEQUENCE:")
    for day, action in sequence.items():
        print(f"    {day:10s} → {action}")
    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/pilot_launch.py [status|import|tier1|templates]")
        return

    cmd = sys.argv[1]
    if cmd == "status":
        cmd_status()
    elif cmd == "import":
        cmd_import()
    elif cmd == "tier1":
        cmd_tier1()
    elif cmd == "templates":
        cmd_templates()
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
