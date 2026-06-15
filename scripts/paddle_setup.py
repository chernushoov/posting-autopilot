#!/usr/bin/env python3
"""One-off: create the 3 Paddle products + recurring prices for Posting Autopilot.

Run AFTER the owner provides PADDLE_API_KEY (sandbox first, then live):
    PADDLE_API_KEY=... PADDLE_ENV=sandbox python scripts/paddle_setup.py

Prints PADDLE_PRICE_STARTER/PRO/AGENCY lines to paste into .env.prod.
Amounts are in the currency's minor unit (USD cents): $99 = 9900.
Override with PADDLE_CURRENCY / edit PLANS amounts if the pricing changes.
"""
import os
import sys

import requests

API_KEY = os.getenv("PADDLE_API_KEY", "").strip()
ENV = (os.getenv("PADDLE_ENV", "sandbox").strip().lower() or "sandbox")
BASE = "https://sandbox-api.paddle.com" if ENV == "sandbox" else "https://api.paddle.com"
CUR = os.getenv("PADDLE_CURRENCY", "USD").strip().upper()

# (env-key, product name, amount in minor units for CUR=USD cents)
PLANS = [
    ("STARTER", "Posting Autopilot — Starter", "9900"),    # $99/mo
    ("PRO",     "Posting Autopilot — Pro",     "29900"),   # $299/mo
    ("AGENCY",  "Posting Autopilot — Agency",  "49900"),   # $499/mo
]


def _headers():
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def main():
    if not API_KEY:
        sys.exit("PADDLE_API_KEY not set")
    print(f"# Paddle {ENV} @ {BASE}  currency={CUR}\n")
    out = {}
    for key, name, amount in PLANS:
        pr = requests.post(f"{BASE}/products", headers=_headers(), json={
            "name": name, "tax_category": "standard", "type": "standard",
        }, timeout=30)
        if not pr.ok:
            sys.exit(f"product create failed for {key}: {pr.status_code} {pr.text}")
        product_id = pr.json()["data"]["id"]
        pc = requests.post(f"{BASE}/prices", headers=_headers(), json={
            "product_id": product_id,
            "description": name,
            "unit_price": {"amount": amount, "currency_code": CUR},
            "billing_cycle": {"interval": "month", "frequency": 1},
            "quantity": {"minimum": 1, "maximum": 1},
        }, timeout=30)
        if not pc.ok:
            sys.exit(f"price create failed for {key}: {pc.status_code} {pc.text}")
        price_id = pc.json()["data"]["id"]
        out[key] = price_id
        print(f"# {key.lower()}: product={product_id} price={price_id}")
    print()
    for key in ("STARTER", "PRO", "AGENCY"):
        print(f"PADDLE_PRICE_{key}={out[key]}")


if __name__ == "__main__":
    main()
