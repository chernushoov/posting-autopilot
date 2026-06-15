# DO NOT — anti-patterns & traps (read before changing things)
_What doesn't work / isn't needed. Hard-won; ignoring these costs hours or breaks prod._

## Deploy / infra
- **DON'T recreate prod containers with a bare `docker compose ... up -d`.** The container env comes from `env_file: ${APP_ENV_FILE:-.env}`, NOT from `--env-file .env.prod` (that flag only feeds `${VAR}` interpolation for caddy/compose). You MUST export `APP_ENV_FILE=.env.prod` — exactly as `deploy-hetzner.sh:145` does — or the container silently loads the STALE `.env` and you get a cascade: web won't boot (env_guard: `PUBLIC_MARKETING_URL`/`PUBLIC_APP_URL` required → 502), `DATA_ENCRYPTION_KEY` missing (breaks PII encrypt/decrypt — and a *different* key per service means cross-service ciphertext can't be read), `TRIAL_DAYS` reverts 14→3, `BILLING_ENABLED` flips, and wrong TG/FB tokens. Canonical recreate: `APP_ENV_FILE=.env.prod docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate <svc>`. (2026-06-15: hardened by making `.env` a copy of `.env.prod` on the box so the default path is also safe — but still export `APP_ENV_FILE` to be explicit. Cost a prod 502 during launch prep to learn.)
- **DON'T expect `git push` to deploy.** App code is BAKED into the Docker image. You MUST `git archive HEAD app … | ssh … tar -x` then `docker compose … build web && up -d web`. Only `web` for app/template changes.
- **DON'T `caddy reload` via `exec` for Caddyfile changes — it silently doesn't apply.** Use `docker compose restart caddy` (cost a 404→403 debug loop to learn).
- **DON'T forget non-`app/` files.** Proxy code lives in `common/` + `scripts/` — ship those too or changes don't land.
- **DON'T assume `build web` updates the worker.** Each service builds its OWN image (`build: .` shared base → `posting-autopilot-web`, `-worker`, `-scheduler`, `-bot`, `-listener`). A change in `worker/`, `bot/`, or shared `app/` code used by them needs `docker compose build worker scheduler bot && up -d --force-recreate …` — else the worker silently runs stale code (this hid a Sentry-init + worker-paywall change until caught). For web-only changes, `build web` is enough.
- **DON'T edit GLB/build artifacts to fix a bug** (general rule): fix at the source/runtime layer.

## Facebook (critical)
- **DON'T log into a personal FB from the Hetzner datacenter IP.** Permanent ban of a personal asset. Proxy (residential) FIRST, then a SECONDARY/business account, watch ban behavior 1–2 weeks. Bans key on IP+behavior, not user volume — a "small pilot" does NOT protect you.
- **DON'T rely on Meta API for groups/Marketplace** — it can't post there at all. Browser automation is the only path.
- **DON'T leave the noVNC capture ungated** — it's single-slot, forward_auth-gated, one-time password, /proc-sweep teardown. Keep it that way.

## Security / data
- **DON'T read `company_id` from request input.** Always `current_company_id()` from the session + `scoped()`. This is the entire isolation guarantee.
- **DON'T put secrets in repo or chat.** `.env.prod` on the server only. Give scoped/revocable API tokens, never passwords/bank/KYC.
- **DON'T enable a third-party script without adding its domain to the Caddyfile CSP** (`script-src`/`connect-src`) — it'll be silently blocked.
- **DON'T ship Clarity/session-recording without a privacy-policy disclosure.**

## Process (learned the hard way)
- **DON'T trust multi-agent audit findings without verifying against the LIVE tree.** The FRR raised 3 "criticals"; 2 were STALE (encryption was active; trial-gate was sound). Always re-check on prod before acting.
- **DON'T rush flow-changing features (post-login questionnaire, group-sync routing) the night before launch.** Additive/visible only when unattended; do core-flow changes with the owner awake.
- **DON'T `git add -A` blindly** — it pulled in node_modules + scratch files. Stage explicitly; keep `.gitignore` honest.

## Frontend
- **DON'T use `overflow:hidden` on the landing body** to kill horizontal scroll — it breaks the sticky scroll-story. Use `overflow-x:clip`.
- **DON'T redirect CRUD form pages (`/vacancies/new`, `/connect/*`, `/profile`) to the SPA** — only pure read-duplicate lists (`/analytics`, `/candidates`) redirect. Redirecting forms breaks create/edit.
- **DON'T blanket-translate cabinet labels via PA_LOC** — array order ≠ mock, it mislabels. Use the `cb.*` i18n keys.
- **DON'T reintroduce `© 2026` / AI dates** — product is 2025, attributed to the owner.

## Don't-bother (not needed now)
- No Kubernetes / horizontal scale before paying customers — one box is fine for the pilot.
- No GA4 unless you accept a cookie-consent banner (CF Web Analytics is cookieless).
- No self-hosted analytics on the 2vCPU/4GB box — it's already running chromium+Xvfb.
- Don't touch etalon tag `etalon-prelaunch-2026-06-15` as a "just edit it" — it's the rollback point.
