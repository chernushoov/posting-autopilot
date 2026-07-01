"""
Seed the SELF-MARKETING tenant: Posting Autopilot posts about Posting Autopilot.

Idempotent (find-or-create), same pattern as scripts/seed.py. Creates:
  - Company  "Posting Autopilot" (owner_id="pa_self")   — the self-promo tenant
  - Vacancy  marketing listing (listing_type="marketing") — the product offer + copy
             with the creative attached and app.posting-autopilot.com as the apply URL
  - Source   the promo destination(s) — placeholders the OWNER points at real channels
  - Campaign links listing -> destinations, NOT running by default (owner flips it on)

The post claim "this post published itself" only stays honest if this campaign is the
thing publishing it. Copy lives in POST_COPY.md; creatives in creatives/.

Run (once DB is reachable):
    python -m growth.self_marketing.seed_self_promo
    # then in the UI: Company "Posting Autopilot" -> point the destination(s) at your
    # real promo channel(s), connect Telegram/Facebook, and toggle the campaign ON.

This script does NOT connect any channel and does NOT start posting. It only stages
ready-to-run content. Publishing remains a deliberate owner action.
"""
import json
from app.db import engine, db_session
from app.models import (
    Base, Company, Vacancy, Source, Campaign, CampaignSource,
    Language, SourceType,
)

CREATIVE_REL = "growth/self_marketing/creatives/PA-he-sq.png"  # primary (IL); swap per channel
LANDING = "https://app.posting-autopilot.com"

# Kept in sync with POST_COPY.md (HE primary). Honest claims only — no invented numbers.
POST_BODY_HE = (
    "את הפוסט הזה פרסמתי לבד 🤖\n\n"
    "Posting Autopilot מפרסם את המשרות והמבצעים שלך בטלגרם ובקבוצות פייסבוק — "
    "אוטומטית, בזמנים שאתה בוחר, ומסנן את התשובות ב-AI כדי שתקבל רק את הרלוונטיים.\n\n"
    "14 יום ניסיון חינם 👇\n"
    "app.posting-autopilot.com"
)
POST_BODY_RU = (
    "Этот пост я опубликовал сам 🤖\n\n"
    "Posting Autopilot постит ваши вакансии и офферы в Telegram и группы Facebook — "
    "автоматически, в выбранное вами время, и фильтрует отклики через AI, чтобы к вам "
    "приходили только релевантные.\n\n"
    "14 дней бесплатно 👇\n"
    "app.posting-autopilot.com"
)


def _get_or_create_company(db):
    c = (
        db.query(Company)
        .filter(Company.owner_id == "pa_self", Company.name == "Posting Autopilot")
        .first()
    )
    if c:
        return c, False
    c = Company(
        owner_id="pa_self",
        name="Posting Autopilot",
        description="Self-marketing tenant — the product posts about itself.",
        business_type="company",
        website=LANDING,
        logo_emoji="🤖",
        ai_language=Language.he,
        ai_positive_prompt=(
            "Ответь дружелюбно и коротко. Объясни, что продукт постит вакансии/офферы "
            "в Telegram и группы Facebook автоматически и фильтрует отклики через AI. "
            "Дай ссылку на app.posting-autopilot.com и 14-дневный бесплатный триал."
        ),
        ai_negative_prompt=(
            "Не выдумывай цифры, кейсы и отзывы. Не обещай гарантированных результатов. "
            "Не называй конкурентов."
        ),
    )
    db.add(c)
    db.commit()
    return c, True


def _get_or_create_listing(db, company):
    v = (
        db.query(Vacancy)
        .filter(Vacancy.company_id == company.id, Vacancy.title == "Posting Autopilot")
        .first()
    )
    if v:
        return v, False
    v = Vacancy(
        company_id=company.id,
        title="Posting Autopilot",
        city=None,
        language=Language.he,
        listing_type="marketing",  # not a recruitment vacancy — a product offer
        body=POST_BODY_HE,
        final_post_title="Posting Autopilot",
        final_post_body=POST_BODY_HE,
        apply_url=LANDING,
        image_path=CREATIVE_REL,
        bot_introduction=(
            "אני העוזר של Posting Autopilot. הכלי מפרסם משרות ומבצעים בטלגרם ובקבוצות "
            "פייסבוק אוטומטית ומסנן תשובות ב-AI. 14 יום ניסיון חינם: app.posting-autopilot.com"
        ),
        interview_questions_json=json.dumps([], ensure_ascii=False),
    )
    db.add(v)
    db.commit()
    return v, True


def _get_or_create_destination(db, company):
    # Placeholder the OWNER repoints at a real promo channel/group before turning the
    # campaign on. posting_mode stays "auto"; nothing posts until a channel is connected.
    s = (
        db.query(Source)
        .filter(Source.company_id == company.id, Source.tg_ref == "@REPLACE_WITH_YOUR_PROMO_CHANNEL")
        .first()
    )
    if s:
        return s, False
    s = Source(
        company_id=company.id,
        tg_ref="@REPLACE_WITH_YOUR_PROMO_CHANNEL",
        label="PA promo channel (set me)",
        source_type=SourceType.channel,
        platform="telegram",
        destination_kind="channel",
        posting_mode="auto",
    )
    db.add(s)
    db.commit()
    return s, True


def _get_or_create_campaign(db, company, listing, dest):
    camp = (
        db.query(Campaign)
        .filter(Campaign.company_id == company.id, Campaign.name == "PA self-promo")
        .first()
    )
    created = False
    if not camp:
        camp = Campaign(
            company_id=company.id,
            vacancy_id=listing.id,
            name="PA self-promo",
            interval_minutes=1440,   # once a day by default — tune in UI
            max_posts_per_day=1,
            is_running=False,        # owner turns this on after connecting a channel
        )
        db.add(camp)
        db.commit()
        created = True
    link = (
        db.query(CampaignSource)
        .filter(CampaignSource.campaign_id == camp.id, CampaignSource.source_id == dest.id)
        .first()
    )
    if not link:
        db.add(CampaignSource(campaign_id=camp.id, source_id=dest.id))
        db.commit()
    return camp, created


def main():
    Base.metadata.create_all(bind=engine)
    db = db_session()
    try:
        company, c_new = _get_or_create_company(db)
        listing, l_new = _get_or_create_listing(db, company)
        dest, d_new = _get_or_create_destination(db, company)
        camp, camp_new = _get_or_create_campaign(db, company, listing, dest)
        print("Self-promo seed done.")
        print(f"  company  id={company.id}  ({'created' if c_new else 'exists'})")
        print(f"  listing  id={listing.id}  ({'created' if l_new else 'exists'})")
        print(f"  dest     id={dest.id}  tg_ref={dest.tg_ref}  ({'created' if d_new else 'exists'})")
        print(f"  campaign id={camp.id}  running={camp.is_running}  ({'created' if camp_new else 'exists'})")
        print("\nNext (owner): point the destination at a real channel, connect")
        print("Telegram/Facebook, then toggle campaign 'PA self-promo' ON in the UI.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
