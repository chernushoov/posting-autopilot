# Security — pre-launch audit + status (2026-06-14)

Full code-grounded audit run on the whole app. **Headline: multi-tenant isolation is solid — NO exploitable IDOR.** Every list/detail/mutation route scopes by `company_id`. Below = findings + fix status.

## Fixed in this branch (redesign/hitech-2026-06-14)
- **H1 — FB App Secret leaked to browser** ✅ FIXED. `connect_facebook.html` pre-filled `value="{{ fb_app_secret }}"` into an input → any logged-in tenant could read the deployment's FB App Secret from page source. Removed the prefill (field now blank, like the TG api_hash field).
- **M8 — no `.dockerignore`** ✅ FIXED. Added `.dockerignore` excluding `data/`, `.env*`, `*.db`, `*.session`, `.venv*`, etc. so secrets/runtime data never bake into the image.

## TOP remaining — do as the next dedicated pass (NOT rushed overnight; touches auth/connect flows)
- **C1 — TG session files plaintext at rest.** `data/tg_sessions/company_<id>.session` (Telethon auth key = full takeover of the user's personal Telegram) + `tg_api_id/tg_api_hash` (models.py) stored plaintext. Fix: encrypt at app layer with a `DATA_ENCRYPTION_KEY` (Fernet) from env; lock `data/` perms `0700`; or volume encryption. *No real-tenant sessions at rest yet — fix before onboarding real recruiters.*
- **C2 — FB access tokens plaintext in DB.** `Company.fb_access_token` (scopes incl. `pages_manage_posts`). Same Fernet-encrypt at write (`auth_routes.py:713`) / decrypt at read. Plan: one `common/crypto.py` (`enc()/dec()`), apply to `fb_access_token` + `tg_api_hash`, migrate existing (none yet).
- **H2 — shared FB browser session across tenants.** `worker/fb_auto_post.py` falls back to one shared `floordsgn` FB session unless `FB_BROWSER_SESSION_COMPANY_<id>` set → identity bleed. Fix: fail closed if no per-company session.

## Medium (hardening, schedule after C1/C2)
- **M1** — `is_admin=True` set for every registered user (currently NOT an escalation — operator is the magic `owner_id=="admin_owner"`; no route grants power from `is_admin` alone). Rename login marker to `logged_in`; add explicit `is_operator`. Footgun to fix before adding any admin gate.
- **M3** — `/demo/*` (hot-lead simulator, can fire real bot DMs) gated only by `@login_required`. Owner uses it for demos now → keep enabled, but restrict to operator/`DEMO_ENABLED` before public multi-tenant launch.
- **M4** — bump `Werkzeug 3.0.1→≥3.0.6` (CVE-2024-49767 multipart DoS), `Flask→3.0.3`, `Jinja2→3.1.5`; add `pip-audit` to CI. *(Deferred from this cutover to avoid an untested dep-bump in the big redesign deploy; do with local test.)*
- **M5** — creatives/logo upload validates extension only (no MIME). Allowed set is non-executable images + `secure_filename`+UUID, so no XSS today; mirror the vacancy validator (extension+MIME+magic-byte) before widening the allow-list.
- **M6** — login rate-limit is in-memory/per-process (resets on restart, ×workers); `/register` has none; password min is only 6. Move limiter to Redis covering `/login`+`/user-login`+`/register`; raise password policy.
- **M7** — trial gate uses broad path-prefix allow-list in `before_request`; tighten to exact matches; add a test that an expired trial can't reach `/vacancies`/`/campaigns`/`/api/*`.

## Verified OK (don't re-audit)
Multi-tenant scoping on all routes; `/uploads/<basename>` ownership-checked + traversal-safe; Stripe webhook signature verified; CSRF on (exemptions safe); Jinja autoescape, no `|safe`; OAuth `state` random+verified; prod cookies HttpOnly+SameSite=Lax+Secure; `env_guard` fail-closed in prod; no secrets committed.

**Order to fix:** C1+C2 (encrypt creds at rest) → H2 → M4 → M6 → M1/M3/M5/M7.
