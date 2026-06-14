# posting-autopilot — Launch Prep Roadmap
_Built overnight 2026-06-15 from the Flight Readiness Review verdict (GO-FOR-PILOT-WITH-CONDITIONS). I work the engineer items; you clear the owner holds in the morning._

## Verdict recap
- 6/6 stations GO-WITH-CONDITIONS. Launch = controlled **TG-only pilot**, 1–3 hand-onboarded partners, manual billing. Not public GA.
- RED's 3 "criticals" verified against the live tree: **2 stale** (encryption IS active on prod; trial-gate IS sound), **1 real → FIXED+deployed** (cancellation now revokes access, main `0b182cf`).
- **#1 risk:** FB posting from the Hetzner datacenter IP under a personal FB account → ban. Mitigation = proxy + secondary account BEFORE any FB login.

## OWNER HOLDS (morning — only you can do these)
| # | Item | Why only you | Time |
|---|---|---|---|
| O1 | **Start Stripe KYB** | IL business verification, 2–7 days (longest pole). Bill first pilots manually meanwhile. | start ASAP |
| O2 | **Telegram phone + SMS code** | code is real-time to your phone | ~15 min |
| O3 | **Buy residential/mobile proxy** ($5–15/mo) | payment | 10 min |
| O4 | **FB login on a SECONDARY account** (after O3) | your credentials + FB checkpoint | ~5 min |
| O5 | Object Storage for off-box backup (~2€/mo) + give creds | payment | 10 min |
| O6 | Legal entity name + support email for ToS/privacy | legal identity | 2 min |

## ENGINEERING (I do these overnight — status updated as I go)
| # | Item | Sev | Status |
|---|---|---|---|
| E1 | FB proxy-readiness (capture + poster, same egress IP, env-gated) | CRIT | ⏳ |
| E2 | DB+sessions backup script + PROVEN restore on throwaway pg | CRIT | ⏳ |
| E3 | Posting-failure alert to owner (not_logged_in/banned/captcha) | HIGH | ⏳ |
| E4 | Worker-paywall (stop posting after trial expiry) | HIGH | ⏳ |
| E5 | Harden TG/FB session files (chmod 0700) | HIGH | ⏳ |
| E6 | Bilingual ToS + /privacy drafts (placeholders for O6) | HIGH | ⏳ |
| E7 | Pre-run session health-check + short-circuit | MED | ⏳ |
| E8 | RAM mem_limits + swap (2vCPU/4GB box runs chromium+Xvfb) | MED | ⏳ |
| E9 | PII-at-rest: encrypt Candidate.phone/chat_log_json | MED | ⏳ |

## VERIFIED ALREADY (don't redo)
- App e2e 19/19, tenant isolation (no IDOR), mobile 0px, EN/HE 0 RU-leak, CSRF.
- FB server-capture (noVNC) live, tenant-isolated, bulletproof teardown, cross-tenant 403.
- Encryption active on prod. Trial-gate sound. Cancellation fixed.

## ABORT CRITERIA (don't launch even pilot if)
1. `encryption_active()`==False with real tenant data (currently True ✓).
2. No PROVEN backup restore once a paying tenant exists.
3. FB posting from bare datacenter IP on a personal account.
