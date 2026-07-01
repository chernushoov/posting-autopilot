# Facebook connect — the ONE owner step (staged, not automatable)

Everything for self-marketing is ready in this folder (creatives, copy, seed). The only
thing an autonomous agent cannot do is **log into a real Facebook account** — that
requires the owner's credentials and a live human login. This is that step, written so
it takes ~5 minutes.

## Why this needs the owner (and can't be done for you)
- FB posting works by driving a real logged-in browser session (Playwright), not a
  public API. The session is *your* FB account state — cookies + localStorage.
  See `common/fb_browser_poster.py` (reads `data/fb_sessions/<name>.json`).
- No one but the account owner can complete the login (password + 2FA/checkpoint).

## Ban risk — read before you connect (documented, real)
- **Prod runs on a Hetzner datacenter IP (167.233.98.210).** Facebook flags "personal
  account + datacenter IP + automation" hard. Using your **personal** FB account here
  risks a checkpoint or ban.
- **Do this first:** use a **dedicated business/secondary FB account** for posting, and
  ideally route it through a residential/mobile proxy or post from a residential IP.
  The product already types char-by-char with human-like delays and staggers groups to
  reduce footprint, but IP + account reputation is the dominant factor.
- Historical note in `docs/FB_SAFE_WORKFLOW_DEMO.md`: competitor tools got accounts
  banned. Treat the posting account as disposable, not your main profile.

## Steps
1. On a machine with a browser (locally is safest — residential IP), from the repo root:
   ```bash
   # one-time: create the FB browser venv if not present (see docs), then:
   .venv-fb/bin/python scripts/fb_capture_session.py pa_promo
   ```
   A real Chrome window opens. Log into the **dedicated promo FB account**, pass any
   checkpoint, land on your feed, then return to the terminal and press Enter.
   → saves `data/fb_sessions/pa_promo.json`.
2. Move that session file to wherever the worker runs (prod volume is owned by Codex —
   coordinate; do not hand-edit the prod server).
3. In the app UI, open company **"Posting Autopilot"** → connect Facebook / add the
   promo group(s) as destinations for the **"PA self-promo"** campaign.
4. Attach the creative `creatives/PA-he-sq.png` (or per-channel variant) and paste the
   body from `POST_COPY.md`.
5. Toggle the campaign **ON**. It posts once/day by default (tune interval in UI).

## What's already staged for you (no owner needed, done)
- `creatives/` — 7 branded creatives (HE/RU/EN × square/wide/portrait), crisp text.
- `POST_COPY.md` — honest post copy in HE/RU/EN (short + long).
- `seed_self_promo.py` — idempotent seed that creates the "Posting Autopilot" self-promo
  tenant + marketing listing + destination placeholder + a daily campaign (OFF by
  default). Run: `python -m growth.self_marketing.seed_self_promo`.

## Telegram alternative (lower risk, connect this first)
Telegram auto-posting has none of the FB ban risk. You can run the **"PA self-promo"**
campaign to a Telegram promo channel today: point the seeded destination
`@REPLACE_WITH_YOUR_PROMO_CHANNEL` at a real channel, connect Telegram, toggle ON.
Prove the self-marketing loop on Telegram, then add Facebook once the promo account +
proxy are in place.
