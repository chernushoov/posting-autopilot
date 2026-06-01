# Demo readiness — Posting Autopilot, 2026-06-01

A 16-agent audit + persona simulation (6 personas: recruiter / car dealer / landlord /
services / reseller / shop owner, across iPhone+Android, RU/HE/EN) confirmed the real
problem and fixed the dead-ends. **The pay-wall fear is unfounded:** registration is
payment-free, gives a 14-day trial, never asks for a card; prices (₪299/899/1999/mo —
nowhere near 15000) only appear if you deliberately open /pricing. The actual issue was
broken steps *during* the trial. Those are now fixed.

## Fixed (verified)
- **Toggle "Start pilot run" → HTTP 500** (DetachedInstanceError) — fixed.
- **Manually-added Telegram group could never become "ready"** → Run dead-ended — now ready on add.
- **"Send test hot lead" lied "Sent!"** while your phone got nothing → now sends only to YOUR
  Telegram, and if the bot was never started it says "press Start in the bot" with a link.
- **No way to add a Facebook group on a server** → manual "add group/Marketplace by URL" form
  is now the primary, always-visible path.
- **/pricing "Try free" buttons dead-ended anonymous users at the login page** → now go to /register.
- **English "Pay:/Apply:" on car/apartment ads** → labels are now niche-aware + translated.
- **Scary "Redis / ALLOW_INLINE_POSTING" error text** → friendly "try again in a moment".
- **Tables clipped on phones** → scroll horizontally on mobile.
- **Mobile landing**: hamburger menu + EN/RU/HE switcher; all WhatsApp CTAs → register.

## The happy path for the video (every step works today)
1. Open the site on a phone → tap **"14 Days Free"** → lands on **/register** ✅
2. Register (email + password + business name) → **dashboard, 14-day trial, NO card** ✅
3. Tap **"Get a sample hot lead"** → a scored 🔥 lead appears on the dashboard (zero setup) ✅ — *safest value moment to film*
4. Create a listing (**use a Jobs listing** — labels are perfect there) ✅
5. Connect Telegram → **phone + SMS** ⚠️ needs the one-time env keys below (or use your already-connected account)
6. Add a group, set your Telegram notify ID → **"Send test hot lead"** arrives ✅ (press Start in the bot first)
7. **"Run now"** → real post ⚠️ needs the two steps below

## What only YOU can flip (2 minutes), and the safety note
- **Phone-only Telegram for new users (step 5):** register ONE app at my.telegram.org and set
  `RECRUITBOT_TG_API_ID` + `RECRUITBOT_TG_API_HASH` in the env, restart. Without it, new users
  see the API-ID/Hash fields (your own account is already connected, so YOUR demo still works).
- **"Run now" actually posts (step 7):** add `ALLOW_INLINE_POSTING=1` to `.env` and restart.
  ⚠️ **SAFETY:** your account has ~79 real groups linked — "Run now" posts to **all linked
  groups**. Before filming step 7, link the demo campaign to **one throwaway group only**, or
  film step 3 (sample hot lead) as the value moment instead. I deliberately did NOT enable
  real posting to avoid an accidental 79-group blast while you test.

## Status
Everything above is committed locally (held for your "push"). Live server restarted on the
fixed code at http://localhost:8000 — refresh and poke around.
