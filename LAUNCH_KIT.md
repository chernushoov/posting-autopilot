# Posting Autopilot — Launch Kit (TG-only pilot)

> Go-to-market kit for the controlled **Telegram-only** pilot. Branch: `launch/space-2026-06-20`.
> Status of engineering: **GO-FOR-PILOT-WITH-CONDITIONS** (SpaceX-style FRR, 6/6 stations, zero NO-GO).
> Live app: `https://app.posting-autopilot.com` · Landing: `https://posting-autopilot.com`
> Server: Hetzner CPX22 `167.233.98.210` · SSH: `ssh -i ~/.ssh/posting_autopilot_hetzner root@167.233.98.210`
>
> This kit is **documentation only** — it contains NO secrets. The owner pastes real
> values directly into the server's `.env.prod` (never into this file or git).

---

## 0. What the pilot IS (and is NOT)

- **IS:** 1–3 hand-onboarded design partners, **Telegram channels only**, manual billing.
- **IS NOT:** public GA, no Facebook posting yet (FB is a separate gated step — see §2),
  no self-serve Stripe checkout yet.
- The product already supports a **TG-only path end-to-end**: connect Telegram → a campaign is
  auto-created → Run → leads come back through the bot. Facebook is now clearly marked **Optional**
  in the cabinet so a TG-only pilot user is never "stuck".

---

## 1. The 3 owner-only blockers — exact steps

These three are the ONLY things blocking the pilot. Do them in this order
(cheapest/safest first). Each value goes into the server `.env.prod` then a targeted restart.

### Blocker A — Telegram (do FIRST, ~15 min, safest)

This is the whole pilot — the bot that answers leads and the userbot that catches replies.

1. **Bot token** (BotFather): open Telegram → `@BotFather` → `/newbot` (or reuse the existing bot)
   → copy the token.
2. On the server, edit env and set BOTH mirrored keys to the same token:
   ```
   ssh -i ~/.ssh/posting_autopilot_hetzner root@167.233.98.210
   cd /opt/posting-autopilot
   nano .env.prod
   #   TELEGRAM_BOT_TOKEN=<paste>
   #   RECRUITBOT_TELEGRAM_BOT_TOKEN=<same value>
   #   AI: set RECRUITBOT_AI_API_KEY=<key>  (or, for keyword-only fallback:
   #       RECRUITBOT_AI_PROVIDER=stub  and  ALLOW_STUB_AI=1)
   ```
3. Start the bot service:
   ```
   export APP_ENV_FILE=.env.prod APP_RUNTIME_ENV_FILE=.env.runtime
   C="docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml"
   $C up -d bot
   ```
4. **Inbound reply listener (Phase-2, gray-zone, optional for first pilot):** catching
   group/DM replies needs the owner's **personal** TG account login (Telethon userbot).
   - Owner provides phone number + the SMS login code at run time.
   - Then `$C up -d listener`.
   - The `.session` file is the most valuable secret on the box — keep `chmod 0700` on
     `data/tg_sessions` and back it up off-box (see §1 Stripe note about backups).
   - For the very first pilot you can skip the listener and read replies in the bot DM
     directly; turn it on once a partner is live.

### Blocker B — Facebook one-time login (do ONLY after §2 ban-safety is in place)

**Do not log in to Facebook until the ban-safety setup in §2 is done.** When ready:

1. In the cabinet: **Cabinet → Каналы (Channels) → Facebook → Connect**. This launches the
   server-side cloud capture (Xvfb + x11vnc + noVNC) gated by `FB_SERVER_CAPTURE`.
2. The owner completes the FB login **inside that captured browser session** (so the session
   cookie lives on the server, on the same egress IP the poster will use — see §2).
3. Use a **secondary / business** Facebook account, never the founder's personal account,
   until ban behaviour has been watched for 1–2 weeks.
4. After login, the session is stored per-tenant in the `ra_data` volume
   (`data/fb_sessions`), and the headless poster reuses it.

### Blocker C — Stripe (do LAST; bill pilots manually until ready)

KYB verification for an Israeli business takes 2–7 business days — **start the KYB today**
but keep `BILLING_ENABLED=false` and invoice the first pilots by hand.

When the keys exist, follow `STRIPE_RUNBOOK.md` (already in this repo). Summary:
- Create 3 recurring ILS prices: Starter ₪299 / Pro ₪899 / Agency ₪1999.
- Set `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_PRICE_{STARTER,PRO,AGENCY}`,
  and `STRIPE_WEBHOOK_SECRET` (webhook endpoint `https://app.posting-autopilot.com/billing/webhook`,
  events: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`).
- Flip `BILLING_ENABLED=true`, restart web/worker. Test with card `4242 4242 4242 4242` in test
  mode first, then swap to `sk_live_…`.
- The cancellation handler is already correct (cancelled subs lose access on next paywall check).

---

## 2. Ban-safety — residential/mobile proxy + secondary FB account (MANDATORY before any FB post)

**The #1 launch risk:** posting Facebook from the Hetzner datacenter IP (AS24940) under the
founder's personal FB account → **permanent ban of an irreplaceable personal asset**. Bans key on
IP reputation + behaviour, NOT user volume, so "small pilot" does **not** protect you. The capture
script's own comment admits the posting IP should be the operator's home IP — the server pivot
silently dropped that safety property.

**Hard sequence — do ALL of these before the first FB login (Blocker B):**

1. **Buy a residential or mobile proxy** ($5–15/mo). Both the FB **capture** and the FB **poster**
   must egress through the **same** sticky residential IP. Code insertion points (proxy is not yet
   wired — add it env-gated/additively): `common/fb_browser_poster.py` `p.chromium.launch(...)`
   (lines ~86, ~234, ~437) take a `proxy={"server": ..., "username": ..., "password": ...}` arg;
   the capture launcher must use the same. Gate behind an env var, e.g. `FB_PROXY_URL`.
2. **Use a secondary / business FB account**, never the founder's personal one. Watch ban behaviour
   for 1–2 weeks before trusting it.
3. **Posting-failure alert:** wire a same-day alert to the owner (reuse the leads-notify plumbing)
   so a re-auth / checkpoint / captcha is caught immediately.
4. **Conservative caps** (already enforced in code, keep them): char-by-char typing with jitter,
   30 s–2 min between TG posts (max 10/hr), 5–10 min between FB groups, daily cap ≤50, **no posting
   23:00–07:00**, auto-pause 30 min on block/captcha.

**Abort criteria — do not launch (even the pilot) if any is true:**
- `encryption_active()` is `False` while real tenant data is present. (Currently **True** — OK.)
- No **proven** off-box backup restore once a paying tenant exists.
- FB posting from the bare datacenter IP / personal account. (Gate FB behind §2.)

> Telegram has **no** equivalent datacenter-IP ban risk for the bot API, which is the other reason
> the pilot is TG-first.

---

## 3. Pricing — pilot recommendation

Current ladder (live on landing + `/pricing`): **Starter ₪299 · Pro ₪899 (popular) · Agency ₪1999**,
all `/mo`, with a free trial. Recommendation for the pilot:

- **Set `TRIAL_DAYS=14`** in `.env.prod` (the code default is 3; prod should be 14 — confirm it is).
  14 days gives a real "first hot lead" win inside the trial.
- **Bill the 1–3 pilot partners manually** (bank transfer / invoice) until Stripe KYB clears.
  Keep `BILLING_ENABLED=false` so nobody hits a dead self-serve checkout.
- **Anchor the pilot on the Pro tier (₪899)** — it's the only tier that includes Facebook + 50
  channels + scheduler + analytics, and it frames the value. For a TG-only pilot you can offer a
  **founder discount** (e.g. first 3 partners at ₪299–₪499/mo locked for 6 months) in exchange for
  a testimonial + weekly feedback. Do this as a manual invoice, not a code change.
- Do **not** invent customer counts or fake testimonials anywhere. The landing uses product
  capabilities (50+ groups, 3 languages, 70% less screening) — keep claims to capabilities, not
  customer stats, until real pilot numbers exist.

---

## 4. Go / No-Go pre-flight checklist (TG-only pilot)

Run top-to-bottom. Every line must be ✅ before onboarding a partner.

**Infra / health**
- [ ] `https://app.posting-autopilot.com/health` and `/ready` return 200.
- [ ] Containers web/worker/scheduler/caddy/postgres/redis all **healthy**.
- [ ] `encryption_active()` is **True** (`DATA_ENCRYPTION_KEY` set).
- [ ] Off-box backup of `pg_dump` + `data/fb_sessions` + `data/tg_sessions` exists, and a
      **restore has been proven once**. (CRIT before the first paying tenant.)
- [ ] UptimeRobot / dead-man monitor pings the app.

**Telegram path (the actual pilot)**
- [ ] Bot token set (both mirrored keys), `bot` container up, AI key OR stub fallback set.
- [ ] A test listing posts to a test TG channel with human-like pacing (verify in posting logs).
- [ ] A test reply reaches the bot, gets screened, and produces a 🔥 hot-lead alert.
- [ ] (Optional) listener up with the owner's TG account if catching group replies.

**Cabinet onboarding**
- [ ] New partner can register → reach `/dashboard` → see the **"Telegram alone is enough to
      start"** signpost → Facebook card reads **Optional**.
- [ ] Setup progress shows **/5** (not /6) and never sticks below 100% on a TG-only setup.
- [ ] Languages render correctly in HE (RTL), RU, EN on landing, pricing, and cabinet.

**Facebook (only if a partner explicitly wants FB this pilot)**
- [ ] Residential/mobile proxy bought and wired (capture + poster on the SAME egress IP).
- [ ] FB login done on a **secondary** account via cabinet → Каналы → FB cloud capture.
- [ ] Posting-failure alert wired to the owner.
- [ ] If proxy is NOT ready → **keep FB off**, ship TG-only. This is the default for pilot #1.

**Billing**
- [ ] `BILLING_ENABLED=false` (manual invoicing) OR full Stripe block set + test-mode checkout
      verified end-to-end.
- [ ] `TRIAL_DAYS=14` confirmed.

**Legal (before first paying tenant)**
- [ ] Bilingual HE/EN Terms + `/privacy` live with the real legal entity name.

If every box above is ✅ → **GO** for the TG-only pilot. Any unchecked CRIT box → **NO-GO**.

---

## 5. Restart cheat-sheet (server)

```
ssh -i ~/.ssh/posting_autopilot_hetzner root@167.233.98.210
cd /opt/posting-autopilot
export APP_ENV_FILE=.env.prod APP_RUNTIME_ENV_FILE=.env.runtime
C="docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml"
$C build web          # only when templates/code changed
$C up -d web worker scheduler caddy
$C up -d bot          # after Telegram token is set
$C up -d listener     # after the owner's TG account login (optional)
```
Rollback artifacts live in `/opt/posting-autopilot/backups/` (`LAST_BACKUP_TS` holds the timestamp).
Do **not** run `deploy-hetzner.sh` as-is — it waits on bot+listener which need secrets and fails.

---

## 6. Conversion & SEO layer (wave 2 — landing + cabinet polish)

Branch-only, additive, no prod redeploy. All changes verified locally on SQLite
(app boots, `/` + `/dashboard` return 200 in EN/RU/HE, i18n keys resolve, JSON-LD parses).

**Landing (`app/templates/landing.html`):**
- **Objection-handling FAQ** (new `#faq` section + nav link) — 5 trilingual Q&A, `<details>`
  accordion reusing landing card styling: *is it safe / ban risk · do I need Facebook ·
  pricing & trial · data privacy · cancel anytime*. First item open by default.
- **SEO/social head**: trilingual-aware `<title>` + `meta description`, canonical, full
  OpenGraph + Twitter Card tags, `og:locale` per language (`he_IL`/`ru_RU`/`en_US`),
  `theme-color`, and a **JSON-LD `SoftwareApplication`** block with 3 `Offer`s
  (Starter ₪299 / Pro ₪899 / Agency ₪1999, ILS). `og:image` + canonical use
  `PUBLIC_MARKETING_URL` (falls back to `https://posting-autopilot.com`).
  - *Note:* the `og:image` currently points at `logo-mark.svg`. For best social previews,
    the owner may later add a 1200×630 PNG share image and swap that one URL.
- "How it works" (4 steps) and "manual vs Autopilot" before/after comparison were already
  present from earlier work — wave 2 did **not** duplicate them; it added the missing FAQ.

**Cabinet i18n stage-2:**
- Routed the last inline-conditional strings through `ui()` / `common/i18n.py` so every
  cabinet label has a single RU/HE/EN source of truth:
  - dashboard "See how it works" card → `see_how_title` / `see_how_desc` / `see_how_btn`.
  - top-nav `Proof` / `Experiment` / `Story` / `Autopilot` → `nav_proof` / `nav_experiment`
    / `nav_story` / `nav_autopilot`.
- The TG-only first-run path (profile → listing → connect Telegram → campaign → run) was
  already fully `ui()`-driven from wave 1; no hardcoded English remained on it.

**Trial reminder still stands:** keep **`TRIAL_DAYS=14`** in `.env.prod` (code default is 3).
The landing trial copy and the JSON-LD/FAQ all read `trial_days` dynamically, so this single
env var drives every "14-day free trial" mention on the site — no hardcoded numbers.
