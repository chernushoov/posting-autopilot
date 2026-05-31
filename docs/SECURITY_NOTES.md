# Security & data-handling notes

Status as of 2026-06-01. Tracks what is done and the follow-ups that need an owner
decision before going live.

## Done
- **Passwords**: bcrypt with transparent upgrade from the old SHA-256 hashes
  (`common/passwords.py`, used by registration + login).
- **Flask secret key**: weak/dev keys are rejected; a strong 32+ char `FLASK_SECRET_KEY`
  is required in production. Local throwaway runs must opt in with
  `ALLOW_INSECURE_DEV_SECRET=1` (`app/config.py`).
- **Login rate-limiting**: shared limiter across user-login and admin-login.
- **Secure cookies**: `SESSION_COOKIE_SECURE` on in prod/staging or with `FORCE_HTTPS`.
- **Secrets out of git**: `.gitignore` now blocks `*.cookies.txt`, `data/fb_sessions/*.json`,
  `data/fb_screenshots/`, `.openclaw/`, and the venvs. The four committed
  `ops/**/live_settings_probe/*/cookies.txt` (a *demo* Vercel session token — "Demo
  Founder", not a real user) were removed from tracking.

## Follow-ups (need owner decision / a focused change)
1. **History rewrite + token rotation (low urgency)**: the demo session cookie above
   still exists in git *history*. Rewriting shared history (filter-repo) is destructive
   and the repo is pushed, so it's deliberately NOT done autonomously. If that Vercel
   deployment is still live, rotate its `SECRET_KEY` and, if desired, scrub history.
2. **Encrypt sessions + lead PII at rest**: `data/fb_sessions/*.json`,
   `data/tg_sessions/*`, and candidate phone/PII are currently plaintext on disk. Add an
   app-level encryption layer (e.g. Fernet keyed by an env secret) around session
   read/write and sensitive Candidate columns. Deferred because it touches the live
   session-loading path and must be done with a migration + tested decrypt, not at night.
3. **Data-handling & refund statements**: publish where data is stored/hosted, how FB
   sessions are used, retention, and a refund policy. These are business/legal copy the
   owner must author — placeholders intentionally not invented here.
4. **Stripe webhook hardening**: webhook already rejects when `STRIPE_WEBHOOK_SECRET`
   is unset; confirm the secret is set in production before enabling billing.
