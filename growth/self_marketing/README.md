# Posting Autopilot — self-marketing pack

The product markets itself: Posting Autopilot publishes posts *about* Posting Autopilot,
which is both the ad and the live proof it works.

| File | What |
|------|------|
| `creatives/` | 7 branded creatives — HE/RU/EN × square (feed) / wide (link) / portrait (story). Crisp text, on-brand (navy `#1a1a2e` + green `#4ade80`). |
| `POST_COPY.md` | Honest post copy HE/RU/EN (short + long). No invented numbers. |
| `seed_self_promo.py` | Idempotent seed: creates the "Posting Autopilot" self-promo tenant + marketing listing + destination placeholder + daily campaign (OFF by default). `python -m growth.self_marketing.seed_self_promo` |
| `FB_CONNECT_OWNER_STEP.md` | The one owner step (FB login) + the real ban-risk guidance. Telegram works first with no risk. |
| `creatives/_creative-template.html` | The parametric HTML used to render the creatives (change copy/colors, re-render). |

## Status
- ✅ Creatives, copy, seed script — **done, staged, verified** (seed py-compiles, all model
  fields exist).
- ⏳ Connect a channel + toggle the campaign ON — owner step. Telegram first (no ban
  risk), Facebook after a dedicated promo account + proxy are ready.

## Guardrails
- Nothing here connects a channel or publishes anything. Publishing stays a deliberate
  owner action (see repo posting-guard rules).
- Prod server + deploy are Codex's domain — this pack is repo content only, not a deploy.
- Honesty: keep claims to what the product verifiably does. The "this post published
  itself" hook only holds while the self-promo campaign is what's posting it.
