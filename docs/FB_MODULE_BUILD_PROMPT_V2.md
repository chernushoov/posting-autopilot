# CLAUDE COMMANDER — Posting Autopilot: FB Auto-Posting Module (v2, merged)

Version: v2 (merged operator v1 + assistant 2026-05-08 review)
Repo: `recruit-autopilot-core/`
Stack: Python 3.11, Flask, SQLAlchemy, PostgreSQL 16, Redis+RQ, aiogram 3.4, Telethon, Docker Compose (web/bot/worker/scheduler/postgres/redis). Existing Apple-style CSS, i18n in he/ru/en/ar.

---

## CRITICAL CHANGES FROM v1 (read first)

1. **Terminology decision (MVP):** repo currently has `Vacancy/Candidate` in `app/models.py:176/282`. FB module FKs to **`Vacancy.id`** as `listing_id` *foreign key only*. UI surface labels FB pages as "Listing/Lead" via i18n keys (`fb.terminology.listing` / `fb.terminology.lead`). Full DB rename = P1 follow-up after first paying pilot. **Do not rename existing tables.**
2. **Alembic adoption** is required Batch 0 prerequisite — repo has no migrations infra (`init_db.py` is current schema source).
3. **Risk acknowledgement** UX is mandatory before `/fb/connect` — clients must accept FB ban risk in writing.
4. **Sentry-with-redaction** required from day one to debug live FB issues without leaking cookies.
5. **Shadowban detection**, **per-group min_interval**, **content variation**, **pre-flight content policy**, **disaster recovery** added as anti-block hardening.

---

## MISSION

Build an additive Facebook auto-posting module that mirrors EZPost (`ezpost.co.il`) on top of existing Vacancy model. Ship MVP for live pilot clients within 2 weeks. **Treat FB posting as inherently risky** — clients accept that FB may rate-limit, shadowban, or block their account; product mitigates with anti-block + monitoring + transparent disclosure but does not guarantee zero impact.

FB Groups API has been dead since Apr 2024. Use server-side Playwright headless browser automation with stored user cookies.

---

## DO NOT TOUCH

- Existing Telegram/Telethon code paths
- Existing AI lead screening (aiogram bot, HOT/WARM/COLD)
- Existing `init_db.py` schema as it stands today (you'll wrap it with alembic stamp, not rewrite)
- Existing terminology in DB (Vacancy/Candidate) — UI label "Listing/Lead" via i18n only

FB module is purely additive. Match existing Apple CSS, layout, i18n pattern.

---

## ARCHITECTURE

### New files

```
common/fb_session.py              # Fernet cookie encryption + redaction filter helpers
common/fb_client.py               # Playwright async wrapper
common/fb_anti_block.py           # delays, caps, warmup, per-group spacing
common/fb_content_policy.py       # NEW v2: pre-flight regex/keyword content validator
common/fb_post_verifier.py        # NEW v2: 5-min visibility check (shadowban detection)
common/fb_rephrase.py             # NEW v2: AI-driven copy variation per group
worker/fb_tasks.py                # RQ tasks (post, verify, refresh, validate)
worker/fb_disaster.py             # NEW v2: auto-pause when N blocks/hour exceeded
worker/Dockerfile.fb              # Playwright deps
app/routes/fb_auth.py             # /fb/connect, /fb/cookies, /fb/disconnect, /fb/disclaimer
app/routes/fb_groups.py           # /fb/groups list/refresh, listing-group binding
app/routes/fb_admin.py            # NEW v2: super-admin dashboard
app/templates/fb/disclaimer.html  # NEW v2: risk acknowledgment UX
app/templates/fb/connect.html     # cookie paste UI
app/templates/fb/groups.html      # group picker
app/templates/fb/admin.html       # NEW v2: all-accounts overview for super-admin
migrations/                       # NEW: alembic migrations dir (Batch 0)
migrations/versions/0001_baseline.py    # Batch 0
migrations/versions/0002_add_fb_models.py    # Batch 1
common/sentry_init.py             # NEW v2: sentry with cookie redaction
```

### Models (append to `app/models.py` — Batch 1)

```python
class FBAccount(Base):
    __tablename__ = "fb_accounts"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    fb_user_id = Column(String(64))
    display_name = Column(String(255))
    cookies_encrypted = Column(Text, nullable=False)
    user_agent = Column(Text)
    fingerprint_json = Column(JSON)         # viewport, locale, tz, languages
    status = Column(String(32), default="active")  # active|blocked|expired|checkpoint|paused|disconnected
    last_check_at = Column(DateTime)
    last_error = Column(Text)
    posts_today = Column(Integer, default=0)
    posts_this_hour = Column(Integer, default=0)
    counter_hour_anchor = Column(DateTime)
    counter_day_anchor = Column(Date)
    hourly_cap = Column(Integer, default=8)
    daily_cap = Column(Integer, default=40)
    warmup_until = Column(DateTime)         # halve caps until this datetime
    risk_acknowledged_at = Column(DateTime, nullable=False)  # NEW v2 — set on /fb/connect
    consecutive_blocks_today = Column(Integer, default=0)    # NEW v2
    last_block_at = Column(DateTime)                          # NEW v2
    created_at = Column(DateTime, default=datetime.utcnow)

class FBGroup(Base):
    __tablename__ = "fb_groups"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    fb_account_id = Column(UUID, ForeignKey("fb_accounts.id"), nullable=False)
    fb_group_id = Column(String(64), nullable=False)
    name = Column(String(512))
    members_count = Column(Integer)
    privacy = Column(String(32))
    last_posted_at = Column(DateTime)
    post_count_total = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    min_interval_hours = Column(Integer, default=24)   # NEW v2: per-group spacing rule
    shadowban_strikes = Column(Integer, default=0)     # NEW v2
    rules_text = Column(Text)                          # NEW v2: operator notes about group rules
    __table_args__ = (UniqueConstraint("fb_account_id", "fb_group_id"),)

class FBListingGroup(Base):
    __tablename__ = "fb_listing_groups"
    listing_id = Column(UUID, ForeignKey("vacancies.id"), primary_key=True)  # NOTE: vacancies.id (DB), labeled "listing" in UI
    fb_group_id = Column(UUID, ForeignKey("fb_groups.id"), primary_key=True)

class FBPostJob(Base):
    __tablename__ = "fb_post_jobs"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID, ForeignKey("vacancies.id"), nullable=False)  # NOTE: vacancies.id
    fb_account_id = Column(UUID, ForeignKey("fb_accounts.id"), nullable=False)
    fb_group_id = Column(UUID, ForeignKey("fb_groups.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    posted_at = Column(DateTime)
    fb_post_url = Column(String(1024))
    status = Column(String(32), default="pending", index=True)  # pending|running|posted|verified|shadowbanned|failed|blocked|skipped
    error = Column(Text)
    retry_count = Column(Integer, default=0)
    text_used = Column(Text)            # NEW v2: actual variant text used
    verified_at = Column(DateTime)      # NEW v2: when post-flight verifier ran
    created_at = Column(DateTime, default=datetime.utcnow)

class FBDisasterEvent(Base):  # NEW v2
    __tablename__ = "fb_disaster_events"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    reason = Column(String(255))
    blocks_in_hour = Column(Integer)
    accounts_paused = Column(Integer)
    resolved_at = Column(DateTime)
    resolved_by_user_id = Column(UUID, ForeignKey("users.id"))
```

Indexes: `(status, scheduled_at)`, `(fb_account_id)`, `(fb_account_id, fb_group_id)` on FBPostJob.

### `common/fb_session.py`

- Fernet key from env `FB_COOKIE_KEY`. If missing on startup — raise loud error with generation instructions.
- `encrypt_cookies(cookies: list[dict]) -> str` → JSON dump → Fernet → base64 string
- `decrypt_cookies(blob: str) -> list[dict]` → reverse
- Cookie schema (Playwright-compatible): `{name, value, domain, path, expires, httpOnly, secure, sameSite}`
- Validator: ensure required FB cookies present (`c_user`, `xs`, `datr`)
- **NEW v2:** `redact_for_logging(payload: Any) -> Any` — strips any `cookies_encrypted`, `c_user`, `xs`, `datr`, `b`, `fr` keys from any dict/string before logging or sentry submission.

### `common/sentry_init.py` (Batch 0)

```python
import sentry_sdk
from common.fb_session import redact_for_logging

def init_sentry():
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=0.1,
        before_send=lambda event, hint: redact_for_logging(event),
    )
```

### `common/fb_client.py` (async, Playwright)

```python
class FBClient:
    def __init__(self, account: FBAccount): ...
    async def __aenter__(self):
        # chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        # context with stored UA, viewport (1366x768 or 1920x1080), locale, tz from fingerprint_json
        # restore cookies
        # eval init script: navigator.webdriver=undefined, fix permissions, plugins
        ...
    async def __aexit__(self, *exc): ...

    async def validate_session(self) -> bool: ...
    async def list_groups(self) -> list[dict]: ...
    async def post_to_group(self, fb_group_id: str, text: str, media_paths: list[str] = None) -> dict: ...
    async def detect_block(self) -> str | None: ...
```

CRITICAL: realistic UA matching installed Chromium version, override `navigator.webdriver`, realistic viewport, locale, timezone. NO Selenium.

### `common/fb_content_policy.py` (NEW v2, Batch 3)

```python
import re

BANNED_KEYWORDS = [...]  # configurable list of FB-trigger words
PHONE_RE = re.compile(r'\+?\d[\d\s\-()]{7,}')
EXTERNAL_LINK_RE = re.compile(r'https?://(?!facebook\.com)[^\s]+')

def validate(text: str) -> tuple[bool, str]:
    """Returns (allowed, reason). Pre-flight check before enqueue."""
    # phone numbers in body
    if PHONE_RE.search(text):
        return False, "phone_number_in_body"
    # external links other than fb
    if len(EXTERNAL_LINK_RE.findall(text)) > 1:
        return False, "too_many_external_links"
    # banned keywords
    for kw in BANNED_KEYWORDS:
        if kw.lower() in text.lower():
            return False, f"banned_keyword:{kw}"
    return True, ""
```

### `common/fb_post_verifier.py` (NEW v2, Batch 4)

```python
async def verify_post_visible(post_url: str) -> bool:
    """Open in fresh anonymous Playwright context. Return True if post visible."""
    # New Chromium context, no cookies
    # Goto post_url with 10s timeout
    # If status == 404 or redirect to login -> False
    # If post composer text not found in DOM -> False
    # Else True
```

### `common/fb_rephrase.py` (NEW v2, Batch 4)

```python
def variant_for(base_text: str, group_id: str, listing_id: str) -> str:
    """Return a deterministic-per-(listing,group) text variant.
    
    On first call for a listing, generate 5 AI rephrases via existing
    LLM service (same that handles screening). Cache them in Redis 
    `fb_variants:{listing_id}:[0..4]`. Hash group_id to pick variant 
    index → ensures same listing in different groups gets different 
    text, but same listing+group always gets same text on retry.
    """
```

### `common/fb_anti_block.py`

```python
DELAY_MIN_S = 45
DELAY_MAX_S = 180
HOURLY_CAP_DEFAULT = 8
DAILY_CAP_DEFAULT = 40
WARMUP_DAYS = 3
WARMUP_MULT = 0.5

def can_post(account: FBAccount, group: FBGroup) -> tuple[bool, str]:
    # 1. account.status == 'active'
    # 2. NEW v2: account.consecutive_blocks_today < 3 (else system-wide pause via disaster)
    # 3. account hourly + daily caps (existing logic, with warmup multiplier)
    # 4. NEW v2: per-group min interval — group.last_posted_at + group.min_interval_hours <= now
    # 5. NEW v2: group.shadowban_strikes < 3 (else mark group disabled)
    # returns (True, "") or (False, reason)
```

### `worker/fb_tasks.py` (RQ)

```python
def fb_post_job(job_id: str):
    # 1. Load FBPostJob, FBAccount, FBGroup, Vacancy (labeled listing)
    # 2. Acquire Redis lock fb_lock:{fb_account_id} (TTL 600s)
    # 3. anti_block.can_post(account, group) -> if False, reschedule +1h, return
    # 4. NEW v2: build text via fb_rephrase.variant_for(...)
    # 5. NEW v2: fb_content_policy.validate(text) -> if False, mark failed
    # 6. Mark job running, save text_used
    # 7. asyncio.run(FBClient(account).__aenter__ ... post_to_group)
    # 8. On checkpoint: account.status='checkpoint', notify user via aiogram bot, 
    #    mark all pending jobs of account as skipped, increment account.consecutive_blocks_today
    # 9. On success: posted_at, fb_post_url, increment_counters, group.last_posted_at, post_count_total++
    #    NEW v2: enqueue fb_post_verify(job_id) with delay=300s
    # 10. On transient error: retry_count++, reschedule +30min, max 3 retries -> failed
    # 11. time.sleep(next_delay())
    # 12. release lock

def fb_post_verify(post_job_id: str):  # NEW v2
    # Run 5 min after fb_post_job success
    # Use a SECOND playwright context (fresh, no cookies)
    # Goto fb_post_url; expect 200 + composer text matches
    # If 404/redirect/empty: increment shadowban_strikes on group, mark job status=shadowbanned
    # If 3+ shadowban strikes on a group → group.enabled = False, alert via aiogram

def refresh_fb_groups(account_id: str): ...

def validate_fb_sessions_periodic(): ...
```

Separate RQ queue `fb_queue`. Concurrency=1 per account guaranteed by Redis lock.

### `worker/fb_disaster.py` (NEW v2)

```python
def check_disaster():
    """Called every 5 min by scheduler.
    
    Counts FBAccount.consecutive_blocks_today aggregated last 1h.
    If > 3 in a single hour:
    - Set ALL active FBAccounts.status = 'paused'
    - Insert FBDisasterEvent
    - Notify owner via aiogram bot (owner-channel)
    - Manual unpause only via fb_admin route
    """
```

### Scheduler integration

In existing scheduler service, add:
- Every 1 min: SELECT FBPostJob WHERE status='pending' AND scheduled_at <= now() — enqueue `fb_post_job` to `fb_queue`
- Every 5 min: enqueue `fb_disaster.check_disaster` (NEW v2)
- Every 6h: enqueue `validate_fb_sessions_periodic`
- Every 24h per active account: enqueue `refresh_fb_groups`

### Routes

`app/routes/fb_auth.py`:
- `GET /fb/disclaimer` — risk text in he/ru/en/ar with mandatory checkbox; on submit set session cookie `fb_risk_acknowledged=1`
- `GET /fb/connect` — requires `fb_risk_acknowledged` cookie else redirect to `/fb/disclaimer`. Render status + cookie paste form + instructions (link to "Cookie-Editor" extension)
- `POST /fb/cookies` — accept JSON paste, validate format, run validate_session synchronously (10s timeout), if OK encrypt+save FBAccount with `risk_acknowledged_at = now`, redirect to `/fb/groups?refresh=1`
- `POST /fb/disconnect` — wipe `cookies_encrypted`, set status='disconnected'

`app/routes/fb_groups.py`:
- `GET /fb/groups` — list groups for current user's account, search/filter UI
- `POST /fb/groups/refresh` — enqueue `refresh_fb_groups`, redirect back
- `POST /listings/<id>/fb-groups` — save FBListingGroup associations (replace all). NOTE: `<id>` is a vacancy id; templates label it "listing".
- `POST /fb/groups/<id>/min-interval` — NEW v2: operator can override per-group min_interval_hours

`app/routes/fb_admin.py` (NEW v2, super-admin role only):
- `GET /fb/admin` — all FBAccounts overview: status, daily/hourly post counts, last block, shadowban strikes
- `POST /fb/admin/<account_id>/pause` — manual pause
- `POST /fb/admin/<account_id>/unpause` — manual unpause (clears consecutive_blocks_today)
- `POST /fb/admin/disaster/<event_id>/resolve` — clear disaster event, unpause all accounts

### Templates (Apple CSS, RTL aware, i18n keys under `fb.*` and `fb.terminology.*`)

`fb/disclaimer.html` (NEW v2):
- 4-language risk text (he/ru/en/ar)
- Bullet list: FB ToS prohibits automation; FB may rate-limit, restrict, or block; FloorDSGN is not liable for FB-imposed actions; we mitigate with anti-block but cannot guarantee zero impact
- Mandatory checkbox: "I have read and accept the risks above"
- Continue button enabled only after checkbox

`fb/connect.html`:
- Status card: connected/disconnected, last_check_at, status badge
- Step-by-step: install Cookie-Editor → open facebook.com (logged in) → export JSON → paste → Validate
- Large textarea + Validate button
- Error display

`fb/groups.html`:
- Refresh button (POST)
- Search filter (client-side)
- Checkbox list: name, members, privacy, last_posted_at, **min_interval_hours editable input** (NEW v2)
- Bulk select-all
- For listing context (`?listing_id=...`): bound checkboxes save FBListingGroup on submit

`fb/admin.html` (NEW v2):
- All FBAccounts table
- Active disaster events list with resolve button
- Per-account: pause / unpause buttons

### Listing form integration

Add to existing **Vacancy** edit form (only when user has active FBAccount): "Facebook groups" multi-select. Add "FB recurrence" — reuse existing TG campaign recurrence widget (cron or "every X hours"). On campaign tick for FB: create FBPostJob rows for each (listing, group) pair, scheduled now or jittered +0–10 min apart. UI label is "Listing" via i18n.

### `.env.example` additions

```
FB_COOKIE_KEY=                # Fernet: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FB_HEADLESS=true
FB_PROXY=                     # optional residential proxy URL per-account
PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
SENTRY_DSN=                   # NEW v2 — required if you want production observability
```

### `worker/Dockerfile.fb`

Base on existing worker image, add:
```dockerfile
RUN pip install playwright==1.48.0 sentry-sdk
RUN playwright install --with-deps chromium
```
Memory ≥ 1GB.

### `docker-compose.yml`

Add service `fb_worker`:
- build from `worker/Dockerfile.fb`
- env: `RQ_QUEUES=fb_queue`, `FB_COOKIE_KEY`, `SENTRY_DSN`
- depends_on: redis, postgres
- shm_size: '2gb'
- mem_limit: 1500m

### Migrations (Batch 0 + 1)

Batch 0 — adopt alembic:
- `pip install alembic` in worker + web Dockerfiles
- `alembic init migrations/`
- `env.py` uses `Base.metadata` from `app/models.py`
- `alembic stamp head` against existing DB schema
- First "baseline" migration is empty (records current state)

Batch 1 migration:
- `alembic revision --autogenerate -m "add fb models"` creates `0002_add_fb_models.py`
- Test `alembic upgrade head` and `alembic downgrade -1`

### i18n

Add namespace `fb.*` to all 4 locale files (he/ru/en/ar). Stub Arabic with English values. Keys needed: `fb.terminology.listing`, `fb.terminology.lead`, `fb.disclaimer.title`, `fb.disclaimer.bullets.*`, `fb.disclaimer.accept`, `fb.connect.title`, `fb.connect.steps.*`, `fb.connect.paste`, `fb.connect.validate`, `fb.connect.success`, `fb.connect.error`, `fb.groups.title`, `fb.groups.refresh`, `fb.groups.search`, `fb.groups.empty`, `fb.groups.members`, `fb.groups.last_posted`, `fb.groups.min_interval`, `fb.status.active`, `fb.status.blocked`, `fb.status.checkpoint`, `fb.status.expired`, `fb.status.paused`, `fb.listing.groups_label`, `fb.listing.recurrence_label`, `fb.admin.title`, `fb.admin.disasters`.

---

## ANTI-BLOCK RULES (NEVER BYPASS)

- Random delay 45–180s between posts per account
- Hourly cap 8, daily cap 40 (defaults; halved during 3-day warmup)
- Single Redis lock per account = serialized posting
- Abort account on checkpoint detection, notify user via aiogram bot, mark pending jobs skipped
- **NEW v2:** per-group min_interval_hours = 24 default (configurable per group)
- **NEW v2:** content variation (no two groups get identical text)
- **NEW v2:** pre-flight content policy validation
- **NEW v2:** post-flight visibility verification (5 min after success)
- **NEW v2:** disaster recovery (≥3 blocks/hour → pause all)
- No 2captcha integration in MVP — manual recovery only
- Single FBAccount per user in MVP

## SECURITY RULES

- Cookies always Fernet-encrypted at rest
- `FB_COOKIE_KEY` required at boot; refuse to start without it
- Never log cookies, never log decrypted values
- **NEW v2:** Sentry redaction filter strips cookie fields from all events before send
- Disconnect endpoint must wipe `cookies_encrypted`
- **NEW v2:** Risk acknowledgment required before account creation

---

## EXECUTION PLAN

Build in **6 ordered batches**. After each batch run:

```bash
docker compose build web worker fb_worker
docker compose up -d
docker compose exec web alembic upgrade head
docker compose logs -f fb_worker
```

Confirm green before next batch. Output complete files only — no diffs, no fragments, no comments unless required.

### Batch 0 — Pre-requisites (NEW v2)

- `pip install alembic` in `web/` and `worker/` Dockerfiles
- `alembic init migrations/`
- `env.py` uses `Base.metadata` from `app/models.py`
- `alembic stamp head` against current DB
- `migrations/versions/0001_baseline.py` empty migration recording current schema state
- Add `MIGRATIONS.md` documenting: "Vacancy/Candidate kept in DB for MVP; UI labels via i18n only"
- `app/templates/fb/disclaimer.html` with risk text he/ru/en/ar
- `common/sentry_init.py` with `before_send` redaction filter
- Wire `init_sentry()` into web + worker startup
- `.env.example` updated
- **Verify:** `alembic current` returns 0001; `/fb/disclaimer` renders in 4 languages; sentry test event arrives without leaking cookies

### Batch 1 — FB Foundation

- Models in `app/models.py` (with FK to `vacancies.id`)
- Alembic migration `0002_add_fb_models.py`
- `common/fb_session.py` with `redact_for_logging`
- `app/routes/fb_auth.py` (`/fb/connect` requires acknowledged cookie; `/fb/cookies`)
- `app/templates/fb/connect.html`
- i18n keys (connect-related, terminology)
- `.env.example` `FB_COOKIE_KEY` documented
- Register blueprint in app factory
- **Verify:** cookie paste validates and saves FBAccount with `risk_acknowledged_at`

### Batch 2 — Group discovery

- `common/fb_client.py`: `__aenter__`, `__aexit__`, `validate_session`, `list_groups`, `detect_block`
- `worker/Dockerfile.fb`
- `docker-compose.yml` `fb_worker` service
- `worker/fb_tasks.py`: `refresh_fb_groups`, `validate_fb_sessions_periodic`
- `app/routes/fb_groups.py` (list + refresh + min-interval)
- `app/templates/fb/groups.html`
- i18n keys (groups-related)
- **Verify:** real FB account → groups parsed and displayed with editable min_interval

### Batch 3 — Posting engine + content policy

- `common/fb_client.py`: `post_to_group` with media upload + human-like typing
- `common/fb_anti_block.py` (incl per-group min_interval, shadowban strikes)
- `common/fb_content_policy.py` (NEW v2)
- `worker/fb_tasks.py`: `fb_post_job` (uses content_policy + variant)
- **Verify:** manually enqueue 1 job → posts successfully → URL captured; verify content policy rejects 5 banned-keyword test payloads

### Batch 4 — Variation + verifier + scheduler

- `common/fb_rephrase.py` (NEW v2) using existing LLM service
- `common/fb_post_verifier.py` (NEW v2)
- `worker/fb_tasks.py`: `fb_post_verify`
- Scheduler additions (poll pending, validate, refresh, disaster)
- Listing form changes (FB groups multi-select + recurrence + i18n label "Listing")
- Job creation logic on FB campaign tick (creates FBPostJob rows)
- Dashboard counts: pending/running/posted/verified/shadowbanned/failed
- **Verify:** vacancy with 3 groups → 3 jobs created → posted with delays → 3 different texts → 5 min later 3 verifier jobs run

### Batch 5 — Disaster recovery + admin

- `worker/fb_disaster.py` (NEW v2)
- `app/routes/fb_admin.py` (NEW v2, super-admin role)
- `app/templates/fb/admin.html`
- aiogram bot disaster notification handler
- **Verify:** simulate 4 fake blocks in 1h → all accounts pause → admin route shows event → manual resolve unpauses

### Batch 6 — Live readiness + production hardening

- E2E live FB account, 5 real groups, 1 vacancy/listing, full cycle
- Block/checkpoint flow tested (simulate by clearing cookies)
- Aiogram bot notification on block
- Disconnect flow wipes cookies
- Sentry events arriving without leaked cookies (manual smoke)
- Per-group min interval tested with same listing → same group within 24h (must be skipped with reason)
- Content policy + variation working end-to-end
- Operator runbook `RECRUIT_FB_OPS_RUNBOOK.md`
- Pricing/SLA/disclaimer signed off by operator
- **Deploy production** (not preview)

---

## ACCESS

- Login: `operator / HBIKEGMS5nd7GNXP`
- Reference existing patterns: `common/tg_client.py`, `worker/tasks.py::campaign_tick`, `app/models.py` (Vacancy with 5 bot_* fields)

## COMPLIANCE NOTE FOR OPERATOR (READ TO BUYER)

> Facebook ToS prohibits automated posting via cookies. We mitigate with anti-block guardrails (per-account caps, per-group spacing, content variation, shadowban detection, automatic disaster pause), but FB may rate-limit, shadowban, or block your account anyway. Pricing is per-active-account-month + per-1000-posts; you accept the platform risk. We don't refund FB-imposed bans.

## START

Begin **Batch 0** (alembic + disclaimer + sentry). Stop after Batch 0 verification before Batch 1. Output every file complete.
