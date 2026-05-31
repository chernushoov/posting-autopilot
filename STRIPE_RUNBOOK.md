# STRIPE RUNBOOK — turn on payments

The checkout + webhook code is already written (`app/routes/billing.py`). It is inert
until these env values exist. Use **test mode** first (`sk_test_…`), then flip to live.

## 1. Create the products/prices (Stripe Dashboard → Products)
Create 3 **recurring monthly** prices in ILS (₪):
| Plan    | Price/mo | Copy the Price ID into |
|---------|----------|------------------------|
| Starter | ₪299     | STRIPE_PRICE_STARTER   |
| Pro     | ₪899     | STRIPE_PRICE_PRO       |
| Agency  | ₪1999    | STRIPE_PRICE_AGENCY    |

Each "Price ID" looks like `price_1QabcdEf...`.

## 2. Get the API keys (Dashboard → Developers → API keys)
- `STRIPE_SECRET_KEY` = `sk_test_…` (later `sk_live_…`)
- `STRIPE_PUBLISHABLE_KEY` = `pk_test_…`

## 3. Add the webhook (Dashboard → Developers → Webhooks → Add endpoint)
- Endpoint URL: `https://<your-domain>/billing/webhook`
- Events to send: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`
- Copy the **Signing secret** → `STRIPE_WEBHOOK_SECRET` (`whsec_…`).
  NOTE: the app now **rejects** unsigned webhooks, so this value is mandatory.

## 4. Put them in .env and restart
```bash
nano .env        # fill the STRIPE_* block
./deploy.sh      # restart web/worker with the new env
```

## 5. Test the flow (Stripe test mode)
1. Open `https://<domain>/pricing`, click a plan → you should reach Stripe Checkout.
2. Pay with test card `4242 4242 4242 4242`, any future expiry, any CVC.
3. You should land on `/billing/success` and the user's trial flips to an active subscription
   (driven by the `checkout.session.completed` webhook).
4. Confirm in Stripe Dashboard → Payments that the test payment appears.

## 6. Go live
Swap the test keys/price-ids for `sk_live_…` / `pk_live_…` / live price ids, redo the webhook
in live mode, restart. Do a single real ₪ transaction yourself to confirm before selling.

## Reality note
Until step 5 passes, the pricing buttons loop back to `/pricing?error=billing_not_configured`.
That is expected when STRIPE_* is unset — it is config, not a code bug.
