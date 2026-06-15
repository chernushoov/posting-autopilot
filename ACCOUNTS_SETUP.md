# Accounts the owner must create (and what scoped credential to hand over)

State checked against prod `.env.prod` on 2026-06-15. Each item: where to sign up,
what to create, the exact env key(s) to give me, why. Hand secrets over the SAFE way
(see bottom) — never paste passwords/bank/KYC; scoped revocable tokens only.

Already configured (no action): TELEGRAM_BOT_TOKEN, RECRUITBOT_TG_API_ID/HASH,
FB_APP_ID/SECRET, DATA_ENCRYPTION_KEY, domains + HTTPS.

## TIER 1 — needed before the first paying customer
1. **Paddle** — take money (Merchant of Record; Stripe does NOT onboard Israeli sellers). https://www.paddle.com
   - Sign up from Israel (payout via Payoneer/wire). Paddle reviews the account (~1–3 days; needs the live
     site with Pricing/Terms/Privacy). Market = US/USD, prices $99/$299/$499 (I create them via API).
   - Webhook → `https://app.posting-autopilot.com/billing/webhook` (subscription.activated/canceled, transaction.completed).
   - Give me (sandbox first, then live): `PADDLE_API_KEY`, `PADDLE_CLIENT_TOKEN`, `PADDLE_WEBHOOK_SECRET`.
     I run `scripts/paddle_setup.py` → creates the 3 prices → sets `PADDLE_PRICE_*` + flips `BILLING_ENABLED` + tests.
   - (Billing code is already built + deployed dormant: Paddle overlay checkout + signed webhook.)

2. **Email provider** — password reset / welcome / trial-ending / receipts (all wired, currently no-op).
   https://resend.com (simplest) — or any SMTP (Brevo/Mailgun/Gmail).
   - Sign up, create API key, verify domain posting-autopilot.com (SPF/DKIM DNS — I can add if you give CF token #7).
   - Give me: `RESEND_API_KEY` (re_…) + `MAIL_FROM` (e.g. noreply@posting-autopilot.com).
     (Or SMTP_HOST/SMTP_USER/SMTP_PASSWORD + SMTP_FROM if not Resend.)

## TIER 2 — first days (real product + safety)
3. **AI provider** — the bot's brain (screening + dialog). NOW `AI_PROVIDER=stub` → canned replies.
   https://platform.openai.com OR https://console.anthropic.com
   - Create an API key.
   - Give me: `AI_API_KEY` + which provider → I set AI_PROVIDER + disable stub.
   - Costs per usage (cents/chat). The product's core value; on stub the demo looks dumb.

4. **Sentry** — see prod errors in real time. https://sentry.io (free tier ok)
   - New Python project → copy DSN. Give me: `SENTRY_DSN`.

5. **Off-box backups** — DB backups currently live ON the same server. https://www.backblaze.com/cloud-storage (B2) or Cloudflare R2.
   - Create a bucket + an access key scoped to that bucket. Give me: bucket + key id + secret.

## TIER 3 — Facebook posting (only when we get there; PROTECTION FIRST)
6. **Residential proxy + a SEPARATE FB account** — logging into FB from the server IP = permanent ban.
   Proxy: https://iproyal.com / https://soax.com / https://brightdata.com (residential, IL).
   - Give me: `FB_PROXY_SERVER`, `FB_PROXY_USERNAME`, `FB_PROXY_PASSWORD`.
   - Also make a NON-personal FB account for posting; warm it 1–2 weeks. Telegram works without any of this.

## TIER 4 — convenience / automation (not launch-blocking)
7. **Cloudflare API token** — DNS (for email #2) + domain automation.
   https://dash.cloudflare.com/profile/api-tokens → token scoped to zone posting-autopilot.com (Edit DNS), NOT the Global key.
   - Give me: `CF_API_TOKEN`.
8. **CF Web Analytics** — cookieless traffic stats. https://dash.cloudflare.com → Web Analytics.
   - Give me: `CF_ANALYTICS_TOKEN` (site token).

## Legal / content (when there's time)
9. Legal entity name for invoices + Terms/Privacy pages (Stripe + data-collection compliance).
10. Footer social links — MacBook already added IG/FB/LinkedIn (commit 7f3cab8); just confirm the URLs are right.

## SAFE handover
Do NOT paste secrets into chat or commit them. Best: write them straight into `.env.prod`
on the server (I'll give a one-line command that opens the editor; you paste, save, say "done",
I restart the affected services + verify). Alternatively paste scoped/revocable tokens to me and
I wire them — acceptable for revocable tokens (Stripe restricted key, CF scoped token, Resend key),
but they'd remain in the chat log. Never send passwords / bank / main-email creds.
