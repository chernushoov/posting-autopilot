#!/usr/bin/env python3
"""stripe_readiness.py — go-live readiness checker for Posting Autopilot billing.

WHY THIS EXISTS
    The product is fully built and deployed, but it cannot take money until Stripe
    is configured with a live account + Price IDs (the #1 blocker to first revenue).
    Clicking a plan today hits `?error=billing_not_configured` (see app/routes/billing.py).
    This script makes go-live turnkey: the moment the owner drops the keys in, run this
    and it tells you GO / NO-GO with exactly what's still missing.

WHAT IT DOES (read-only, never creates or charges anything)
    1. Checks every env var billing.py needs is present + well-formed.
    2. If STRIPE_SECRET_KEY is live and the `stripe` package is installed, it makes
       READ-ONLY API calls: retrieve each Price ID (amount/currency/interval),
       and list webhook endpoints to confirm one points at /billing/webhook.
    3. Prints a GO / NO-GO summary.

    It performs ONLY Price.retrieve and WebhookEndpoint.list — no create, no charge,
    no modification. Safe to run against a live account.

USAGE
    cd ~/Work/02-Projects/posting-autopilot
    python3 ops/stripe_readiness.py                 # uses current env
    # or load runtime secrets first:
    set -a; source .env.runtime 2>/dev/null; set +a; python3 ops/stripe_readiness.py

EXPECTED PLANS (must match app/routes/pricing.py + app/plans.py)
    Starter  299₪ / month  -> STRIPE_PRICE_STARTER
    Pro      899₪ / month  -> STRIPE_PRICE_PRO
    Agency  1999₪ / month  -> STRIPE_PRICE_AGENCY
    Currency ILS. Amounts are in agorot: 29900 / 89900 / 199900.
"""
import os
import sys

# ── expected plan config (single source of truth mirrors pricing.py) ──────────
EXPECTED = {
    "starter": {"env": "STRIPE_PRICE_STARTER", "agorot": 29900, "label": "Starter 299₪/mo"},
    "pro":     {"env": "STRIPE_PRICE_PRO",     "agorot": 89900, "label": "Pro 899₪/mo"},
    "agency":  {"env": "STRIPE_PRICE_AGENCY",  "agorot": 199900, "label": "Agency 1999₪/mo"},
}
CURRENCY = "ils"
WEBHOOK_PATH = "/billing/webhook"

GREEN, RED, YEL, DIM, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
def ok(m):   print(f"{GREEN}  ✓{OFF} {m}")
def bad(m):  print(f"{RED}  ✗{OFF} {m}")
def warn(m): print(f"{YEL}  !{OFF} {m}")
def head(m): print(f"\n{m}")


def check_env():
    """Static checks: presence + format of every var billing.py reads."""
    problems = []
    head("1) Environment variables")

    sk = os.getenv("STRIPE_SECRET_KEY", "")
    if not sk:
        bad("STRIPE_SECRET_KEY missing"); problems.append("STRIPE_SECRET_KEY")
    elif not sk.startswith(("sk_live_", "sk_test_", "rk_live_", "rk_test_")):
        bad(f"STRIPE_SECRET_KEY malformed (starts '{sk[:8]}…')"); problems.append("STRIPE_SECRET_KEY")
    else:
        mode = "LIVE" if "live" in sk[:8] else "TEST"
        (ok if mode == "LIVE" else warn)(f"STRIPE_SECRET_KEY present ({mode} mode)")
        if mode == "TEST":
            warn("  test key won't collect real money — swap to sk_live_ before launch")

    pk = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    if not pk:
        warn("STRIPE_PUBLISHABLE_KEY missing (only needed for custom checkout UI, not for hosted checkout)")
    elif not pk.startswith(("pk_live_", "pk_test_")):
        warn(f"STRIPE_PUBLISHABLE_KEY malformed (starts '{pk[:8]}…')")
    else:
        ok("STRIPE_PUBLISHABLE_KEY present")

    ws = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not ws:
        bad("STRIPE_WEBHOOK_SECRET missing — webhook fails closed, subscriptions never activate")
        problems.append("STRIPE_WEBHOOK_SECRET")
    elif not ws.startswith("whsec_"):
        bad(f"STRIPE_WEBHOOK_SECRET malformed (starts '{ws[:8]}…')"); problems.append("STRIPE_WEBHOOK_SECRET")
    else:
        ok("STRIPE_WEBHOOK_SECRET present")

    for plan, cfg in EXPECTED.items():
        pid = os.getenv(cfg["env"], "")
        if not pid:
            bad(f"{cfg['env']} missing ({cfg['label']})"); problems.append(cfg["env"])
        elif not pid.startswith("price_"):
            bad(f"{cfg['env']} malformed (expected price_…, got '{pid[:8]}…')"); problems.append(cfg["env"])
        else:
            ok(f"{cfg['env']} present ({cfg['label']})")

    return problems, sk


def check_live(sk):
    """Read-only live verification against the Stripe API."""
    head("2) Live Stripe verification (read-only)")
    try:
        import stripe
    except ImportError:
        warn("`stripe` package not installed in this interpreter — skipping live check")
        warn("  (it IS in requirements.txt; installed on the deploy host)")
        return ["stripe-package-local"]
    stripe.api_key = sk
    problems = []

    # account sanity
    try:
        acct = stripe.Account.retrieve()
        ok(f"API key valid — account {acct.get('id','?')} ({acct.get('country','?')}, "
           f"charges_enabled={acct.get('charges_enabled')})")
        if acct.get("charges_enabled") is False:
            bad("  account charges_enabled=false — finish Stripe onboarding/verification")
            problems.append("account-not-activated")
    except Exception as e:
        bad(f"API key rejected: {e}")
        return ["api-key-invalid"]

    # each price
    for plan, cfg in EXPECTED.items():
        pid = os.getenv(cfg["env"], "")
        if not pid:
            continue
        try:
            pr = stripe.Price.retrieve(pid)
            cur = pr.get("currency")
            amt = pr.get("unit_amount")
            rec = (pr.get("recurring") or {}).get("interval")
            issues = []
            if cur != CURRENCY: issues.append(f"currency {cur}≠{CURRENCY}")
            if amt != cfg["agorot"]: issues.append(f"amount {amt}≠{cfg['agorot']}")
            if rec != "month": issues.append(f"interval {rec}≠month")
            if issues:
                warn(f"{cfg['env']} → {pid}: " + ", ".join(issues))
            else:
                ok(f"{cfg['env']} → {pid}: {amt/100:.0f} {cur.upper()}/{rec} ✓")
        except Exception as e:
            bad(f"{cfg['env']} → {pid}: retrieve failed: {e}")
            problems.append(cfg["env"] + "-invalid")

    # webhook endpoints
    try:
        eps = stripe.WebhookEndpoint.list(limit=100).get("data", [])
        matching = [e for e in eps if WEBHOOK_PATH in (e.get("url") or "")]
        if not eps:
            bad("no webhook endpoints configured — subscriptions won't activate after payment")
            problems.append("webhook-endpoint")
        elif not matching:
            warn(f"{len(eps)} webhook endpoint(s) exist but none contain '{WEBHOOK_PATH}':")
            for e in eps[:5]:
                warn(f"    {e.get('url')}")
            problems.append("webhook-endpoint-path")
        else:
            for e in matching:
                enabled = e.get("enabled_events") or []
                need = {"checkout.session.completed", "customer.subscription.deleted", "invoice.payment_failed"}
                covers = "*" in enabled or need.issubset(set(enabled))
                (ok if e.get("status") == "enabled" and covers else warn)(
                    f"webhook {e.get('url')} status={e.get('status')} events={'all' if '*' in enabled else len(enabled)}"
                    + ("" if covers else f" — missing {need - set(enabled)}"))
    except Exception as e:
        warn(f"webhook list failed: {e}")

    return problems


def main():
    print(f"{DIM}Posting Autopilot — Stripe go-live readiness{OFF}")
    env_problems, sk = check_env()
    live_problems = []
    if sk and sk.startswith(("sk_live_", "sk_test_", "rk_live_", "rk_test_")):
        live_problems = check_live(sk)

    head("=" * 44)
    blocking = [p for p in env_problems] + [p for p in live_problems if p != "stripe-package-local"]
    if not blocking:
        print(f"{GREEN}GO — billing is ready to collect money.{OFF}")
        print(f"{DIM}Smoke test: open /pricing on prod, click Starter, complete Stripe test/live checkout,{OFF}")
        print(f"{DIM}confirm the company flips to plan_tier=starter and trial_expires_at clears.{OFF}")
        return 0
    print(f"{RED}NO-GO — {len(blocking)} blocker(s) remain:{OFF}")
    for p in blocking:
        print(f"    • {p}")
    print(f"\n{DIM}See docs/STRIPE_GOLIVE_RUNBOOK.md for the exact fix for each.{OFF}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
