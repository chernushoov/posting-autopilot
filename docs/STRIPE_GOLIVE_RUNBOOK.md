# Stripe Go-Live Runbook — Posting Autopilot

**Purpose:** turn on paid subscriptions. The product is built and deployed; this is the
one remaining gate to first revenue. ~15 minutes of owner action in the Stripe Dashboard,
then one deploy of env vars (Codex owns the Hetzner deploy).

The code is done and verified — `app/routes/billing.py` already: creates Checkout sessions,
verifies webhook signatures, **fails closed** if the webhook secret is missing (no free
subscriptions), and activates/cancels the company plan on the right events. Nothing to build.

---

## What you're creating

Three monthly subscription **Prices** in **ILS**, matching the pricing page exactly:

| Plan | Price | Amount (agorot) | Env var |
|---|---|---|---|
| Starter | 299 ₪ / mo | `29900` | `STRIPE_PRICE_STARTER` |
| Pro | 899 ₪ / mo | `89900` | `STRIPE_PRICE_PRO` |
| Agency | 1999 ₪ / mo | `199900` | `STRIPE_PRICE_AGENCY` |

---

## Step 1 — Stripe account (owner, once)

1. Create/verify a Stripe account for the business (Israel, currency **ILS**).
   Finish onboarding until **charges are enabled** (bank + business details).
2. Toggle to **Live mode** (top-right) for real money. (You can rehearse everything in
   Test mode first with `sk_test_…` — the checker labels which mode a key is.)

## Step 2 — Create the 3 products/prices (owner)

For each plan: **Products → Add product** → name (Starter/Pro/Agency) →
Price = recurring, **Monthly**, currency **ILS**, amount from the table above → Save.
Copy each resulting **Price ID** (`price_…`).

## Step 3 — Webhook endpoint (owner)

**Developers → Webhooks → Add endpoint:**
- URL: `https://app.posting-autopilot.com/billing/webhook`
- Events: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`
- Save, then copy the **Signing secret** (`whsec_…`).

## Step 4 — Collect the 6 values

```
STRIPE_SECRET_KEY=sk_live_…
STRIPE_PUBLISHABLE_KEY=pk_live_…        # optional (only for custom checkout UI)
STRIPE_WEBHOOK_SECRET=whsec_…
STRIPE_PRICE_STARTER=price_…
STRIPE_PRICE_PRO=price_…
STRIPE_PRICE_AGENCY=price_…
```

> These are **secrets** — hand them off privately, never commit them. They belong in the
> prod `.env.runtime` on Hetzner, not in git.

## Step 5 — Verify BEFORE deploy (turnkey)

Drop the values into a local `.env.runtime` (gitignored) and run the checker:

```bash
cd ~/Work/02-Projects/posting-autopilot
set -a; source .env.runtime; set +a
python3 ops/stripe_readiness.py
```

It prints **GO** or **NO-GO** with exactly what's missing — validates key formats, and
(read-only) confirms each Price is ILS/monthly/correct-amount and the webhook points at
`/billing/webhook` with the right events. Read-only: it never creates or charges anything.

## Step 6 — Deploy (Codex owns Hetzner; resting until Jul 29)

Add the 6 vars to the prod `.env.runtime` at `root@167.233.98.210` and restart the web
service (compose). **Do not** deploy prod without Codex/owner. Until then, everything above
can be fully rehearsed in Stripe **Test mode** so day-of go-live is one paste + one restart.

## Step 7 — Smoke test (after deploy)

Open `https://app.posting-autopilot.com/pricing`, click **Starter**, complete Stripe
checkout. Confirm the company flips to `plan_tier=starter` and the trial gate clears.
`invoice.payment_failed` and `customer.subscription.deleted` handling is already wired.

---

## Notes

- **Acquisition is currently invite-only** (self-serve CTAs were removed). First paying
  customer is a **done-for-you / manual sale**: you onboard them, they pay via the plan link.
  A self-serve funnel is a separate, later task.
- The checker is safe to run repeatedly and against a live account (read-only API calls).
