import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Tone(str, enum.Enum):
    professional = "professional"
    friendly = "friendly"
    strict = "strict"

class Language(str, enum.Enum):
    ru = "ru"
    en = "en"
    he = "he"
    auto = "auto"

class CandidateStatus(str, enum.Enum):
    new = "new"
    qualifying = "qualifying"
    interviewing = "interviewing"
    passed = "passed"
    rejected = "rejected"
    hired = "hired"


class FacebookGroupStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    archived = "archived"
    blocked = "blocked"
    needs_review = "needs_review"


class FacebookGroupSourceType(str, enum.Enum):
    seed_csv = "seed_csv"
    seed_json = "seed_json"
    manual_entry = "manual_entry"
    customer_import = "customer_import"
    ops_review = "ops_review"


class FacebookGroupVerificationStatus(str, enum.Enum):
    unverified = "unverified"
    verified = "verified"
    stale = "stale"
    rejected = "rejected"


class FacebookPostVariantStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    archived = "archived"


class FacebookPostTone(str, enum.Enum):
    professional = "professional"
    casual = "casual"
    urgent = "urgent"


class FacebookPostLengthMode(str, enum.Enum):
    short = "short"
    medium = "medium"
    long = "long"


class FacebookPostGenerationSource(str, enum.Enum):
    ai = "ai"
    manual = "manual"
    ai_then_edited = "ai_then_edited"


class FacebookPostingRunStatus(str, enum.Enum):
    draft = "draft"
    ready = "ready"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class FacebookPostingQueueItemStatus(str, enum.Enum):
    pending = "pending"
    current = "current"
    opened = "opened"
    posted = "posted"
    skipped = "skipped"
    failed = "failed"


class FacebookPostingResultStatus(str, enum.Enum):
    posted = "posted"
    got_responses = "got_responses"
    got_cvs = "got_cvs"
    interview_scheduled = "interview_scheduled"
    hired = "hired"
    rejected_by_group = "rejected_by_group"
    no_signal = "no_signal"

class UserRole(str, enum.Enum):
    admin = "admin"
    owner = "owner"
    member = "member"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(300), nullable=False, unique=True, index=True)
    password_hash = Column(String(256), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.owner)
    is_active = Column(Boolean, nullable=False, default=True)
    trial_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    company = relationship("Company", backref="users")


class BusinessType(str, enum.Enum):
    company = "company"
    individual = "individual"


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    owner_id = Column(String(64), nullable=False)  # telegram user_id or internal user id
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Hot-lead notification targets (set on Profile page)
    notify_telegram_chat_id = Column(String(32), nullable=True)
    notify_email = Column(String(300), nullable=True)

    # Billing — plan tier drives feature limits (see app/plans.py)
    plan_tier = Column(String(20), nullable=False, default="trial")
    # Indexed + unique so webhook lookups by Stripe id are fast and unambiguous
    # (one Stripe customer/subscription maps to exactly one Company). NULLs allowed
    # (multiple un-subscribed companies) on both SQLite and Postgres.
    stripe_customer_id = Column(String(64), nullable=True, index=True, unique=True)
    stripe_subscription_id = Column(String(64), nullable=True, index=True, unique=True)

    # Profile fields
    business_type = Column(String(20), nullable=False, default="company")
    contact_person = Column(String(200), nullable=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(300), nullable=True)
    website = Column(String(500), nullable=True)
    logo_emoji = Column(String(10), nullable=True)  # simple emoji avatar

    # AI settings
    ai_positive_prompt = Column(Text, nullable=False, default="")
    ai_negative_prompt = Column(Text, nullable=False, default="")
    ai_tone = Column(Enum(Tone), nullable=False, default=Tone.professional)
    ai_language = Column(Enum(Language), nullable=False, default=Language.ru)

    ai_greeting_template = Column(Text, nullable=False, default="")
    ai_rejection_template = Column(Text, nullable=False, default="")
    ai_success_template = Column(Text, nullable=False, default="")

    # Telegram Client (Telethon) credentials for auto-posting
    tg_api_id = Column(String(20), nullable=True)
    tg_api_hash = Column(String(64), nullable=True)

    # Facebook OAuth
    fb_access_token = Column(Text, nullable=True)
    fb_user_id = Column(String(64), nullable=True)
    fb_user_name = Column(String(200), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    vacancies = relationship("Vacancy", back_populates="company")
    sources = relationship("Source", back_populates="company")
    campaigns = relationship("Campaign", back_populates="company")
    candidates = relationship("Candidate", back_populates="company")
    fb_group_sources = relationship("FacebookGroupSource", back_populates="company")
    fb_groups = relationship("FacebookGroup", back_populates="company")
    fb_post_variants = relationship("FacebookPostVariant", back_populates="company")
    fb_posting_runs = relationship("FacebookPostingRun", back_populates="company")
    fb_posting_queue_items = relationship("FacebookPostingQueueItem", back_populates="company")
    fb_posting_results = relationship("FacebookPostingResult", back_populates="company")

class Vacancy(Base):
    __tablename__ = "vacancies"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False, default="")
    city = Column(String(120), nullable=True)
    language = Column(Enum(Language), nullable=False, default=Language.ru)
    salary_text = Column(String(200), nullable=True)
    schedule_text = Column(String(200), nullable=True)
    contact_text = Column(String(200), nullable=True)
    apply_url = Column(String(500), nullable=True)
    final_post_title = Column(String(200), nullable=True)
    final_post_body = Column(Text, nullable=True)

    # interview configuration (simple MVP)
    interview_questions_json = Column(Text, nullable=False, default="[]")

    # Universal listing fields (Task 1.2)
    listing_type = Column(String(40), nullable=False, default="recruitment")
    bot_introduction = Column(Text, nullable=True)
    bot_faq_knowledge = Column(Text, nullable=True)
    bot_qualifying_questions = Column(Text, nullable=True)  # JSON array of strings
    bot_hot_criteria = Column(Text, nullable=True)
    bot_cold_criteria = Column(Text, nullable=True)
    whatsapp_number = Column(String(20), nullable=True)  # Task 2.3: WhatsApp click-to-chat
    image_path = Column(String(500), nullable=True)  # legacy single primary photo path
    images_json = Column(Text, nullable=True)  # JSON array of upload paths for carousel (real estate / cars)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    company = relationship("Company", back_populates="vacancies")
    campaigns = relationship("Campaign", back_populates="vacancy")
    candidates = relationship("Candidate", back_populates="vacancy")
    posting_attempts = relationship("PostingAttempt", back_populates="vacancy")
    fb_post_variants = relationship("FacebookPostVariant", back_populates="vacancy")
    fb_posting_runs = relationship("FacebookPostingRun", back_populates="vacancy")

class SourceType(str, enum.Enum):
    group = "group"
    channel = "channel"
    chat = "chat"

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    tg_ref = Column(String(200), nullable=False)  # @username or numeric id
    label = Column(String(200), nullable=True)
    source_type = Column(Enum(SourceType), nullable=False, default=SourceType.group)
    platform = Column(String(20), nullable=False, default="telegram")
    destination_kind = Column(String(20), nullable=False, default="group")
    posting_mode = Column(String(30), nullable=False, default="auto")
    destination_url = Column(String(500), nullable=True)

    folder = Column(String(100), nullable=True)  # user-defined folder/group name

    # integration status (MVP fields)
    last_check_ok = Column(Boolean, nullable=False, default=False)
    last_check_message = Column(String(300), nullable=True)
    last_post_at = Column(DateTime, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    company = relationship("Company", back_populates="sources")
    campaign_sources = relationship("CampaignSource", back_populates="source")
    posting_attempts = relationship("PostingAttempt", back_populates="source")

    __table_args__ = (
        UniqueConstraint("company_id", "tg_ref", name="uq_source_company_tgref"),
    )

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(200), nullable=False, default="")
    interval_minutes = Column(Integer, nullable=False, default=180)
    active_hours_json = Column(Text, nullable=False, default='{"start":9,"end":19}')  # local hours
    days_of_week_json = Column(Text, nullable=False, default='[0,1,2,3,4,5]')  # 0=Mon
    max_posts_per_day = Column(Integer, nullable=False, default=10)

    is_running = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    company = relationship("Company", back_populates="campaigns")
    vacancy = relationship("Vacancy", back_populates="campaigns")
    sources = relationship("CampaignSource", back_populates="campaign")
    posting_attempts = relationship("PostingAttempt", back_populates="campaign")

class CampaignSource(Base):
    __tablename__ = "campaign_sources"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)

    campaign = relationship("Campaign", back_populates="sources")
    source = relationship("Source", back_populates="campaign_sources")

    __table_args__ = (
        UniqueConstraint("campaign_id", "source_id", name="uq_campaign_source"),
    )

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id", ondelete="SET NULL"), nullable=True, index=True)

    tg_user_id = Column(String(64), nullable=True, index=True)
    tg_username = Column(String(200), nullable=True)
    full_name = Column(String(200), nullable=True)

    status = Column(Enum(CandidateStatus), nullable=False, default=CandidateStatus.new)
    score = Column(Integer, nullable=True)
    summary = Column(Text, nullable=False, default="")
    red_flags = Column(Text, nullable=False, default="[]")

    phone = Column(String(30), nullable=True)
    language = Column(String(10), nullable=True)  # detected candidate language (ru/he/en)
    classification = Column(String(10), nullable=True)  # hot/warm/cold
    chat_log_json = Column(Text, nullable=False, default="[]")  # [{role,text,ts}]
    next_action_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    company = relationship("Company", back_populates="candidates")
    vacancy = relationship("Vacancy", back_populates="candidates")


class PostingAttempt(Base):
    __tablename__ = "posting_attempts"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    run_key = Column(String(120), nullable=False, index=True)

    platform = Column(String(20), nullable=False, default="telegram")
    destination = Column(String(200), nullable=False, default="")
    destination_ref = Column(String(500), nullable=False, default="")
    asset_title = Column(String(200), nullable=False, default="")
    asset_body = Column(Text, nullable=False, default="")

    action_taken = Column(String(80), nullable=False, default="pending")
    result_status = Column(String(40), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    operator_notes = Column(Text, nullable=False, default="")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    campaign = relationship("Campaign", back_populates="posting_attempts")
    vacancy = relationship("Vacancy", back_populates="posting_attempts")
    source = relationship("Source", back_populates="posting_attempts")

    # One logical post per (posting cycle, destination): guards against a retried
    # or double-fired tick recording/posting the same content to the same source.
    __table_args__ = (
        UniqueConstraint("run_key", "source_id", name="uq_posting_attempt_runkey_source"),
    )


class FacebookGroupSource(Base):
    __tablename__ = "fb_group_sources"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(Enum(FacebookGroupSourceType), nullable=False, default=FacebookGroupSourceType.seed_csv)
    source_label = Column(String(120), nullable=False)
    import_batch_key = Column(String(120), nullable=False)
    collected_by = Column(String(120), nullable=True)
    collected_at = Column(DateTime, nullable=True)
    verification_status = Column(
        Enum(FacebookGroupVerificationStatus),
        nullable=False,
        default=FacebookGroupVerificationStatus.unverified,
    )
    last_verified_at = Column(DateTime, nullable=True)
    raw_source_url = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    company = relationship("Company", back_populates="fb_group_sources")
    groups = relationship("FacebookGroup", back_populates="seed_source")

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "source_type",
            "source_label",
            "import_batch_key",
            name="uq_fb_group_source_batch",
        ),
    )


class FacebookGroup(Base):
    __tablename__ = "fb_groups"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    seed_source_id = Column(Integer, ForeignKey("fb_group_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    facebook_url = Column(Text, nullable=False)
    facebook_url_normalized = Column(String(255), nullable=False)
    facebook_slug = Column(String(160), nullable=True, index=True)
    primary_category = Column(String(64), nullable=False)
    secondary_tags_json = Column(Text, nullable=False, default="[]")
    country_code = Column(String(8), nullable=False, default="IL")
    language_code = Column(String(16), nullable=False, default="he")
    city = Column(String(120), nullable=True)
    region = Column(String(120), nullable=True)
    audience_type = Column(String(64), nullable=True)
    member_count_estimate = Column(Integer, nullable=True)
    activity_rating = Column(Integer, nullable=True)
    posting_rules_summary = Column(Text, nullable=True)
    requires_membership = Column(Boolean, nullable=False, default=False)
    requires_admin_approval = Column(Boolean, nullable=False, default=False)
    performance_score = Column(Integer, nullable=True)
    status = Column(Enum(FacebookGroupStatus), nullable=False, default=FacebookGroupStatus.active)
    is_active = Column(Boolean, nullable=False, default=True)
    last_verified_at = Column(DateTime, nullable=True)
    last_posted_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="fb_groups")
    seed_source = relationship("FacebookGroupSource", back_populates="groups")
    queue_items = relationship("FacebookPostingQueueItem", back_populates="group")

    __table_args__ = (
        UniqueConstraint("company_id", "facebook_url_normalized", name="uq_fb_group_company_url"),
        CheckConstraint("activity_rating >= 1 AND activity_rating <= 5", name="ck_fb_groups_activity_rating"),
        CheckConstraint("member_count_estimate >= 0", name="ck_fb_groups_member_count"),
    )


class FacebookPostVariant(Base):
    __tablename__ = "fb_post_variants"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_label = Column(String(80), nullable=False)
    tone = Column(Enum(FacebookPostTone), nullable=False)
    length_mode = Column(Enum(FacebookPostLengthMode), nullable=False)
    language_code = Column(String(16), nullable=False, default="he")
    headline = Column(String(160), nullable=True)
    cta_text = Column(String(160), nullable=True)
    full_text = Column(Text, nullable=False)
    char_count = Column(Integer, nullable=True)
    status = Column(Enum(FacebookPostVariantStatus), nullable=False, default=FacebookPostVariantStatus.draft)
    generation_source = Column(Enum(FacebookPostGenerationSource), nullable=False)
    prompt_version = Column(String(40), nullable=True)
    input_payload_json = Column(Text, nullable=True)
    edited_by_user = Column(Boolean, nullable=False, default=False)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(120), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    company = relationship("Company", back_populates="fb_post_variants")
    vacancy = relationship("Vacancy", back_populates="fb_post_variants")
    posting_runs = relationship("FacebookPostingRun", back_populates="post_variant")


class FacebookPostingRun(Base):
    __tablename__ = "fb_posting_runs"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False, index=True)
    post_variant_id = Column(Integer, ForeignKey("fb_post_variants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(160), nullable=True)
    status = Column(Enum(FacebookPostingRunStatus), nullable=False, default=FacebookPostingRunStatus.draft)
    group_count = Column(Integer, nullable=False, default=0)
    created_by = Column(String(120), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_action_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    company = relationship("Company", back_populates="fb_posting_runs")
    vacancy = relationship("Vacancy", back_populates="fb_posting_runs")
    post_variant = relationship("FacebookPostVariant", back_populates="posting_runs")
    queue_items = relationship("FacebookPostingQueueItem", back_populates="run")


class FacebookPostingQueueItem(Base):
    __tablename__ = "fb_posting_queue_items"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id = Column(Integer, ForeignKey("fb_posting_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("fb_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    status = Column(Enum(FacebookPostingQueueItemStatus), nullable=False, default=FacebookPostingQueueItemStatus.pending)
    opened_at = Column(DateTime, nullable=True)
    copied_at = Column(DateTime, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    skipped_at = Column(DateTime, nullable=True)
    completed_by = Column(String(120), nullable=True)
    skip_reason = Column(String(160), nullable=True)
    group_note = Column(Text, nullable=True)
    post_url_manual = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    company = relationship("Company", back_populates="fb_posting_queue_items")
    run = relationship("FacebookPostingRun", back_populates="queue_items")
    group = relationship("FacebookGroup", back_populates="queue_items")
    result = relationship("FacebookPostingResult", back_populates="queue_item", uselist=False)

    __table_args__ = (
        UniqueConstraint("run_id", "group_id", name="uq_fb_queue_run_group"),
        UniqueConstraint("run_id", "position", name="uq_fb_queue_run_position"),
    )


class FacebookPostingResult(Base):
    __tablename__ = "fb_posting_results"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    queue_item_id = Column(Integer, ForeignKey("fb_posting_queue_items.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    result_status = Column(Enum(FacebookPostingResultStatus), nullable=False, default=FacebookPostingResultStatus.posted)
    response_count = Column(Integer, nullable=True)
    cv_count = Column(Integer, nullable=True)
    interview_count = Column(Integer, nullable=True)
    hire_count = Column(Integer, nullable=True)
    quality_score = Column(Integer, nullable=True)
    last_checked_at = Column(DateTime, nullable=True)
    owner_note = Column(Text, nullable=True)
    result_note = Column(Text, nullable=True)
    updated_by = Column(String(120), nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="fb_posting_results")
    queue_item = relationship("FacebookPostingQueueItem", back_populates="result")

    __table_args__ = (
        CheckConstraint("response_count >= 0", name="ck_fb_results_response_count"),
        CheckConstraint("cv_count >= 0", name="ck_fb_results_cv_count"),
        CheckConstraint("interview_count >= 0", name="ck_fb_results_interview_count"),
        CheckConstraint("hire_count >= 0", name="ck_fb_results_hire_count"),
        CheckConstraint("quality_score >= 1 AND quality_score <= 5", name="ck_fb_results_quality_score"),
    )


class StripeWebhookEvent(Base):
    """Idempotency ledger for Stripe webhooks. Stripe delivers at-least-once and
    retries on any non-2xx/timeout, so we record each event id and skip replays."""
    __tablename__ = "stripe_webhook_events"
    id = Column(Integer, primary_key=True)
    event_id = Column(String(80), nullable=False, unique=True, index=True)
    event_type = Column(String(80), nullable=True)
    processed_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ── Prospecting ────────────────────────────────────────────────────────────────

class ProspectStatus(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    replied = "replied"
    converted = "converted"
    rejected = "rejected"
    unsubscribed = "unsubscribed"

class OutreachStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    bounced = "bounced"
    replied = "replied"
    failed = "failed"

class Prospect(Base):
    __tablename__ = "prospects"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    category = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(Text, nullable=True)
    email = Column(String(300), nullable=True)
    rating = Column(String(10), nullable=True)
    review_count = Column(Integer, nullable=True)
    city = Column(String(100), nullable=True)
    source_query = Column(String(500), nullable=True)
    status = Column(Enum(ProspectStatus), nullable=False, default=ProspectStatus.new)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    contacted_at = Column(DateTime, nullable=True)

    company = relationship("Company")
    outreach_attempts = relationship("OutreachAttempt", back_populates="prospect")

class OutreachAttempt(Base):
    __tablename__ = "outreach_attempts"
    id = Column(Integer, primary_key=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(500), nullable=True)
    body_preview = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    status = Column(Enum(OutreachStatus), nullable=False, default=OutreachStatus.pending)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    prospect = relationship("Prospect", back_populates="outreach_attempts")
    company = relationship("Company")
