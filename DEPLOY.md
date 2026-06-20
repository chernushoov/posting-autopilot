# Posting Autopilot — Canonical Repo & Safe Deploy

_Established 2026-06-20 to end the multi-codebase drift. Read before touching prod._

## Source of truth

- **Canonical git repo:** `chernushoov/posting-autopilot` → branch **`main`**
  (synced 2026-06-20 to equal exact production runtime + security fixes).
- **Canonical local working copy:** `~/Desktop/posting-autopilot-canonical`
  (fresh clone + production overlay; the only local copy you should deploy from).
- **Production server:** Hetzner CPX22 `167.233.98.210`, path `/opt/posting-autopilot`.
  SSH: `ssh -i ~/.ssh/posting_autopilot_hetzner root@167.233.98.210`.
  The box has **NO git**; code is baked into the image via `Dockerfile: COPY . /app`.

## DO NOT deploy from these (stale / corrupt — non-canonical)

- `~/Desktop/recruit-autopilot-core` — **CORRUPT working tree**: committed files
  (crypto.py, cabinet_data.py, cabinet.html, privacy.html …) are MISSING from the
  checkout. An rsync `--delete` from here would DESTROY production. Kept only for
  git history reference.
- `~/Desktop/сережа-posting-autopilot`, `~/Work/02-Projects/posting-autopilot`,
  `~/Desktop/_archive-2026/recruit-autopilot-core1` — old divergent copies.
- `~/Desktop/PostingAutopilot*` — these are the **mobile apps** (iOS/Android/StoreKit),
  not the server; separate repos.

## Secrets — NEVER in git

Live only in the server `/opt/posting-autopilot/.env.prod`. Current state (2026-06-20):
- `TELEGRAM_BOT_TOKEN` set (bot @AutopillotRecruit_bot live), `DATA_ENCRYPTION_KEY` set
  (encryption active), `TRIAL_DAYS=14`, `BILLING_ENABLED=false` (manual invoicing).
- AI: provider must be `openai` + `RECRUITBOT_AI_API_KEY=sk-...` for real lead scoring
  (currently `stub`/keyword until the key is added). Model: `gpt-4o-mini`.
- Stripe keys empty (pilot bills manually until KYB clears).

## Safe deploy procedure (no --delete, ever)

```bash
# 1. Make the change in the CANONICAL copy, commit, push.
cd ~/Desktop/posting-autopilot-canonical
#    ... edit ... ; git add -p ; git commit ; git push

# 2. Back up prod first (code + DB).
ssh -i ~/.ssh/posting_autopilot_hetzner root@167.233.98.210 \
  'cd /opt/posting-autopilot && ts=$(date +%Y%m%d-%H%M%S) && tar czf backups/code-$ts.tar.gz app common'
#    (an automated daily pg_dump already lands in backups/db-*.sql.gz)

# 3. Copy ONLY changed source files to prod (scp or rsync WITHOUT --delete).
scp -i ~/.ssh/posting_autopilot_hetzner app/routes/foo.py \
  root@167.233.98.210:/opt/posting-autopilot/app/routes/foo.py

# 4. Rebuild + recreate (code is baked into the image).
ssh -i ~/.ssh/posting_autopilot_hetzner root@167.233.98.210 'cd /opt/posting-autopilot &&
  export APP_ENV_FILE=.env.prod APP_RUNTIME_ENV_FILE=.env.runtime &&
  C="docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml" &&
  $C build web && $C up -d web worker scheduler caddy'
#    add `$C up -d bot` only if bot/ code changed.

# 5. Verify before walking away.
curl -s -o /dev/null -w "%{http_code}\n" https://app.posting-autopilot.com/health   # 200
curl -s -o /dev/null -w "%{http_code}\n" https://app.posting-autopilot.com/ready    # 200
```

- **Never** run `deploy-hetzner.sh` as-is (waits on bot+listener which need secrets).
- **Never** `rsync --delete` from a local copy onto prod (prod has files a partial
  local checkout lacks → silent destruction).
- **Rollback:** restore from `backups/code-*.tar.gz` (+ `db-*.sql.gz`) and rebuild.

## What "canonical = prod" reconciliation did (2026-06-20)

- Base = `origin/main` (complete: tests, scripts, ops tooling, all modules).
- Overlaid the live production runtime (Stripe billing migration, lang-switch
  `/?lang=`, today's onboarding fix = Facebook optional / `steps_total=5`).
- Kept `main`'s `_safe_apply_url()` over prod's regressed copy (prod had a stored-XSS
  hole in vacancies.py via apply_url) — and **deployed that fix to prod**.
- Dropped macOS `._*` junk. Secrets/data never tracked.
