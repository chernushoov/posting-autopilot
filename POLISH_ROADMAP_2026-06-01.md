# Polish roadmap — synthesized from 5 new-user simulations (2026-06-01)
# Personas: Tamar (recruiter), Igor (car dealer), Rina (landlord, non-tech),
# Dani (skeptical buyer), First-15-min (onboarding funnel).
# Strong convergence. Ordered by impact (P0 = blocks value/money for everyone).

## P0 — ONBOARDING KILLERS (almost nobody reaches first value)
1. TELEGRAM api_id/api_hash WALL (~65% quit here; #1 unanimous). Users must visit
   my.telegram.org, create an app, copy 2 secrets, + phone + SMS + maybe 2FA.
   FIX: use ONE shared/managed app credential (env RECRUITBOT_TG_API_ID/HASH — api_id
   identifies the APP not the user, so many accounts share it). User enters ONLY phone
   + SMS code. Hide the words API/Hash/token entirely (move BYO-credential to Advanced).
   Files: app/templates/connect_telegram.html, app/routes/auth_routes.py (~251/302), i18n tg_credentials_desc.
2. FACEBOOK App ID/Secret WALL + the WORKING browser-login has NO BUTTON (terminal only).
   FIX: a real "Connect Facebook" button that runs the session capture; drop App ID/Secret
   from the default flow (Advanced only). Files: connect_facebook.html, auth_routes.py ~441.
3. FACEBOOK page tells 3 contradictory stories: banner "auto, reads your groups" vs panels
   "white-hat, manual-assisted only, paste yourself" vs the real auto-poster (now works) with
   no UI trigger. FIX: ONE honest story (browser-session auto), wire the auto-fire button,
   delete the manual/white-hat/App-ID confusion. Files: connect_facebook.html, fb_posting_queue.html (line 7), fb_safe_workflow.py auto-fire.
4. CAN'T PAY: Stripe not configured (checkout dead-loops) + not deployed live.
   FIX: configure Stripe + deploy (owner accounts — runbooks ready).
5. PATH-TO-VALUE is 8 steps + Redis dep + "campaign" concept. FIX: collapse to
   "connect Telegram by phone → Post now → see a lead". Auto-create campaign; never show
   raw "Redis offline". Promote the /demo instant-hot-lead as the onboarding AHA (it exists,
   buried in a Russian "Демо-симулятор" card). Files: dashboard.html wizard, campaigns.py:349, demo.py.

## P1 — CONVERSION / TRUST
6. RECRUITING-ONLY LABELS (Vacancy/Candidate/CV/Hired/RecruitBot) → car & apartment users
   feel they're in the wrong app. FIX: category-aware labels (job→vacancy/candidate;
   car→listing/buyer/test-drive/sold; apartment→listing/renter). Files: i18n, dashboard.html, vacancy_new.html, fb_posting_queue.html result options.
7. LANGUAGE INCONSISTENCY: register.html English-only; dashboard hardcoded EN "Worker
   Responses" + RU "Демо-симулятор"; pricing FAQ English + recruiter-only; default lang
   hardcoded Hebrew-RTL (RU/EN ad traffic bounces). FIX: full i18n + detect lang from
   Accept-Language/geo; prominent switcher. Files: register.html, dashboard.html, pricing.html, factory.py:155/186.
8. SCARY red "Демо-симулятор / open /demo" card on a real customer's dashboard → "am I in a
   test?" distrust. FIX: hide from customers (gate behind owner/demo flag).
9. BAN-SAFETY hidden + "no bans" claim contradicts terms.html §6. FIX: visible Ban-Safety
   panel (per-day cap, human pacing, "use a secondary FB account", live block/captcha status);
   change copy to honest "ban-minimizing". The anti-ban code already exists (tg_client limits, fb stagger).
10. HOT-LEAD notification gated behind "paste your numeric Telegram chat ID" → silently does
    nothing (the headline feature!). FIX: "Connect my Telegram for alerts" button + "Send me a
    test hot lead" button. Files: profile.html:55, notify_targets.py.

## P2 — MARKET FIT / PROOF
11. WhatsApp — IL market lives there. Hot leads go to Telegram only; no WA posting/delivery.
12. Marketplace doesn't actually POST (just saves bookmark URLs). Build category→Marketplace post.
13. FB-side reply capture missing (buyers reply on FB, not TG). Only TG replies are captured.
14. ROI receipt: "posted X groups, Y responses, Z hot leads, ~N hours saved" (data already in DB).
15. TRUST hygiene: purge committed ops/**/cookies.txt from git; encrypt FB sessions + lead PII
    at rest; publish data/hosting + refund statements.

## GOOD PARTS TO PROTECT (personas praised these)
- Landing page + ROI calculator (Tamar's favorite). AI screening/scoring + phone-dedup +
  hot/warm/cold + FAQ-answer (Dani: "tells me a real recruiter used this"). Category folders
  on FB groups (just shipped). The car buyer-scoring + apartment-applicant scoring already in common/ai.py.

## EXECUTION ORDER (this session)
- [x] feedback synthesized (this file)
- [x] Q1 hide scary Демо card from customers (#8) — done in 5c46909
- [x] Q2 FB page: one honest story (#3 copy) — done in 5c46909 + ban-safety panel 408f57e
- [x] BIG-1 Telegram phone-only connect via shared credential (#1) — d59bfef
- [x] BIG-2 FB connect button (#2) — 813a1ad (gated, no auto-fire of real posts)
- [x] category-aware labels (#6) — already mostly present (listing_type, niche-neutral nav,
      category-aware hot-lead in bot/run_bot.py); finished pricing FAQ + headings 21cfa5b
- [x] language consistency (#7) — Accept-Language detect + register/dashboard i18n f83283b
- [x] #5 path-to-value (auto-campaign + inline posting) — 9d37aa9
- [x] #9 ban-safety panel + honest landing — 408f57e
- [x] #10 hot-lead test button + owner_telegram_id fix — c2aba95
- [x] #11 WhatsApp click-to-chat — already in bot; sample made consistent e402b1c
- [x] #14 ROI receipt — 0296dbc
- [x] #15 untrack cookies + SECURITY_NOTES — 1c135f2
- [x] landing verticals strip — 5822e73

## OWNER ACTION ITEMS / DEFERRED — see NIGHT_REPORT_2026-06-01.md
Still needs owner: push, RECRUITBOT_TG_API_ID/HASH, deploy+Stripe, FB_ALLOW_LOCAL_CAPTURE,
ALLOW_INLINE_POSTING. Deferred (risk/size): at-rest encryption, git-history rewrite,
data/refund statements, FB Marketplace posting (#12), FB-side reply capture (#13).
