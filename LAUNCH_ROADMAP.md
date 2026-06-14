# posting-autopilot — Launch Prep Roadmap & Night Report
_Updated overnight 2026-06-15. main = `bb196ce`, all 7 containers healthy, full e2e 19/19 PASS after every deploy._

## OVERALL GRADE
- **TG-only pilot readiness: 8.5/10** — engine works end-to-end, isolation/i18n/mobile verified; gated only by 3 owner actions.
- **Public GA readiness: 6/10** — needs live payments, off-box backup, FB proxy, ToS/privacy, failure alerting.
- **Verdict:** the rocket is built & test-fired. Two of your logins + Stripe arm the engines. Do NOT light FB from a bare datacenter IP (see O3/O4).

## DONE & VERIFIED TONIGHT
- ✅ Cancellation now revokes access (was a no-op) — `0b182cf`.
- ✅ FB **proxy-readiness** (E1): `FB_PROXY_*` wired into capture + poster (same egress IP). Env-gated, off until set — `8eb0517`.
- ✅ Landing (he/ru/en): **"apps coming soon"** App Store + Google Play badges in hero; footer **© 2025 + "created by Alexey Chernushoov"** (was 2026); terms year → 2025 — `8eb0517`.
- ✅ Landing **mobile horizontal overflow → 0px** (was 56px from scroll-reveal), content not clipped, verified by screenshot — `bb196ce`.
- ✅ Encryption verified ACTIVE on prod; trial-gate verified sound (RED's claims were stale).
- ✅ Full regression re-run after all deploys: cabinet 11/11 screens 0 console errors, EN/HE no RU-leak + RTL, mobile 0px, TG pipe live.

## OWNER HOLDS (morning — only you)
| # | Item | Time |
|---|---|---|
| O1 | **Start Stripe KYB** (2–7 days; bill first pilots manually meanwhile) | ASAP |
| O2 | **Telegram phone + SMS code** — send me the number, I trigger the code, you paste 5 digits | ~5 min |
| O3 | **Buy residential/mobile proxy** → give me `FB_PROXY_SERVER/USERNAME/PASSWORD` | 10 min |
| O4 | **FB login on a SECONDARY account** (only after O3) | ~5 min |
| O5 | Object Storage creds for off-box backup (~2€/mo) | 10 min |
| O6 | Legal entity name + support email (for ToS/privacy) | 2 min |
| O7 | **Social links** (you said the MacBook has them — I couldn't fetch via `ssh m1`; paste them and I wire the footer) | 2 min |

## ENGINEERING — REMAINING (prioritized, I build on your go / morning)
| # | Item | Sev | Status |
|---|---|---|---|
| E1 | FB proxy-readiness | CRIT | ✅ done |
| E2 | DB+sessions backup + PROVEN restore (off-box needs O5) | CRIT | ⏳ next |
| E3 | Posting-failure alert to owner (banned/captcha/session dead) | HIGH | ⏳ |
| E4 | Worker-paywall (stop posting after trial expiry) | HIGH | ⏳ |
| E5 | chmod 0700 + encrypt TG/FB session files | HIGH | ⏳ |
| E6 | Bilingual ToS + /privacy (needs O6) | HIGH | ⏳ |
| F1 | **Auto-folder TG/FB groups by theme** (categorizer on sync + UI grouping; `Source.folder`/`FacebookGroup.primary_category` exist) | HIGH | 📋 specced |
| F2 | **Post-login segmentation questionnaire** (company size / # hires / time spent / need → funnel + upsell; small biz → nurture on ₪299). New table via create_all, gated+skippable+fail-safe. Build with you awake since it changes the login→cabinet flow | HIGH | 📋 specced |
| E7 | Pre-run session health-check + short-circuit | MED | ⏳ |
| E8 | RAM mem_limits + swap (chromium+Xvfb on 2vCPU/4GB) | MED | ⏳ |
| E9 | PII-at-rest: encrypt Candidate.phone/chat_log_json | MED | ⏳ |

## Why F1/F2 are specced, not shipped tonight
They change core flows (group sync routing; the post-login path). Per "additive only / don't break the live app the night before launch," I built the safe/visible items and verified them, and left these two for a careful pass with you awake to eyeball the new flow. Both are designed (storage exists / new table via create_all), so they're fast to land once greenlit.

## ABORT CRITERIA (don't launch even pilot if)
1. `encryption_active()`==False with real tenant data (currently True ✓).
2. No PROVEN backup restore once a paying tenant exists.
3. FB posting from bare datacenter IP on a personal account.
