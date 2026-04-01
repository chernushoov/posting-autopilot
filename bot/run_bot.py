import os, json, re
from datetime import datetime, timedelta, timezone
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.db import db_session
from app.models import Candidate, CandidateStatus, Company, Vacancy
from common.ai import build_system_prompt, score_candidate
from common.i18n import detect_language, t, get_questions
from common.runtime_env import get_recruitbot_token
from common.email_notify import send_hot_lead_email

BOT_TOKEN = get_recruitbot_token()
SCREENING_TIMEOUT_MINUTES = 30
PASS_SCORE_THRESHOLD = 40

# Phone number pattern: Israeli 05X-XXXXXXX or international
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?0?\d{1,3}\)?[-.\s]?\d{3}[-.\s]?\d{3,4}")

dp = Dispatcher()


def lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="🇮🇱 עברית", callback_data="lang:he"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
        ]
    ])


def vacancy_keyboard(vacancies, lang, bot_username):
    rows = []
    for v in vacancies[:5]:
        label = f"📝 {v.title}" + (f" — {v.city}" if v.city else "")
        rows.append([InlineKeyboardButton(text=label, callback_data=f"apply:{v.id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_candidate_lang(candidate) -> str:
    return candidate.language or "ru"


def resume_keyboard(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("resume_button", lang), callback_data="screening:resume"),
        InlineKeyboardButton(text=t("restart_button", lang), callback_data="screening:restart"),
    ]])


def reapply_keyboard(vacancy_id: int, lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("reapply_button", lang), callback_data=f"reapply:{vacancy_id}"),
    ]])


def is_screening_expired(candidate) -> bool:
    try:
        log = json.loads(candidate.chat_log_json or "[]")
    except Exception:
        return False
    if not log:
        return False
    for entry in reversed(log):
        ts = entry.get("ts", "")
        if ts:
            try:
                last_ts = datetime.fromisoformat(ts)
                if last_ts.tzinfo is None:
                    last_ts = last_ts.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                return (now - last_ts) > timedelta(minutes=SCREENING_TIMEOUT_MINUTES)
            except (ValueError, TypeError):
                continue
    return False


def count_answered(log: list) -> int:
    return sum(1 for m in log if m.get("role") == "assistant" and m.get("type") == "question")


def extract_phone(text: str) -> str | None:
    """Extract phone number from text. Returns cleaned number or None."""
    match = PHONE_RE.search(text)
    if match:
        # Clean: keep only digits and leading +
        raw = match.group()
        cleaned = re.sub(r"[^\d+]", "", raw)
        if len(cleaned) >= 9:
            return cleaned
    return None


def get_screening_questions(vacancy, lang: str) -> list[str]:
    """Get screening questions: bot_qualifying_questions > interview_questions_json > defaults."""
    # Priority 1: Universal bot qualifying questions (Task 1.2)
    if vacancy and vacancy.bot_qualifying_questions:
        try:
            custom = json.loads(vacancy.bot_qualifying_questions)
            if custom and isinstance(custom, list) and len(custom) > 0:
                return custom
        except Exception:
            pass
    # Priority 2: Legacy interview questions
    if vacancy and vacancy.interview_questions_json:
        try:
            custom = json.loads(vacancy.interview_questions_json)
            if custom and isinstance(custom, list) and len(custom) > 0:
                return custom
        except Exception:
            pass
    return get_questions(lang)


def build_bot_greeting(vacancy, lang: str) -> str:
    """Build greeting from bot_introduction or default screening_start."""
    if vacancy and vacancy.bot_introduction:
        return vacancy.bot_introduction
    return t("screening_start", lang, title=vacancy.title if vacancy else "")


def classify_candidate(vacancy, candidate, questions: list, answers: list) -> str:
    """Classify as hot/warm/cold based on vacancy criteria and scoring."""
    # If we have hot/cold criteria from the listing, use AI score + heuristics
    score = candidate.score or 0

    # Cold: very low score or matches cold criteria
    if score < 20:
        return "cold"

    # Hot: high score + phone collected
    if score >= PASS_SCORE_THRESHOLD and candidate.phone:
        return "hot"

    # Hot without phone: warm (need phone to be hot)
    if score >= PASS_SCORE_THRESHOLD:
        return "warm"

    # Medium score: warm
    if score >= 20:
        return "warm"

    return "cold"


async def send_hot_lead_notification(bot: Bot, company: Company, candidate: Candidate, vacancy: Vacancy):
    """Send Telegram notification to business owner about a HOT lead."""
    if not company.owner_id or not company.owner_id.strip():
        return
    # Only send to numeric Telegram user IDs
    if not company.owner_id.replace("_", "").replace("admin", "").strip().isdigit():
        return

    name = candidate.full_name or candidate.tg_username or "Unknown"
    phone = candidate.phone or "not provided"
    summary = candidate.summary or "No summary"
    listing = vacancy.title if vacancy else "Unknown"

    text = (
        f"🔥 HOT LEAD!\n\n"
        f"📋 Listing: {listing}\n"
        f"👤 Name: {name}\n"
        f"📞 Phone: {phone}\n"
        f"📊 Score: {candidate.score}\n"
        f"📝 Summary: {summary}\n"
    )
    if candidate.tg_username:
        text += f"💬 Telegram: @{candidate.tg_username}\n"
    # WhatsApp quick-contact link for the lead
    if candidate.phone:
        wa_num = candidate.phone.lstrip('+').replace('-', '').replace(' ', '')
        if not wa_num.startswith('972') and wa_num.startswith('0'):
            wa_num = '972' + wa_num[1:]
        text += f"📲 WhatsApp: https://wa.me/{wa_num}\n"

    try:
        await bot.send_message(chat_id=company.owner_id, text=text)
    except Exception as e:
        print(f"[bot] Failed to send hot lead notification to {company.owner_id}: {e}")

    # Task 2.4: Email notification (async-safe — runs in thread)
    try:
        # Check if owner_id looks like email for User-based accounts
        from app.db import db_session as _db
        from app.models import User
        db = _db()
        user = db.query(User).filter(User.company_id == company.id, User.is_active == True).first()
        if user and user.email:
            send_hot_lead_email(
                to_email=user.email,
                listing_title=vacancy.title if vacancy else "Unknown",
                lead_name=name,
                lead_phone=phone,
                lead_score=candidate.score or 0,
                lead_summary=summary,
                lead_telegram=candidate.tg_username or "",
            )
        db.close()
    except Exception as e:
        print(f"[bot] Email notification error: {e}")


# --- /start handler ---

@dp.message(F.text.startswith("/start"))
async def cmd_start(message: Message):
    db = db_session()
    try:
        comp = db.query(Company).filter(Company.is_active == True).order_by(Company.id.asc()).first()
        if not comp:
            await message.answer(t("not_configured", "en"))
            return

        tg_user_id = str(message.from_user.id) if message.from_user else None

        args = message.text.split(maxsplit=1)
        deep_link = args[1] if len(args) > 1 else None

        c = None
        if tg_user_id:
            c = db.query(Candidate).filter(
                Candidate.company_id == comp.id,
                Candidate.tg_user_id == tg_user_id
            ).first()

        if not c:
            tg_lang = message.from_user.language_code if message.from_user else None
            detected = detect_language(tg_lang)
            c = Candidate(
                company_id=comp.id,
                tg_user_id=tg_user_id,
                tg_username=message.from_user.username if message.from_user else None,
                full_name=f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip() if message.from_user else None,
                status=CandidateStatus.new,
                language=detected,
                chat_log_json="[]",
            )
            db.add(c)
            db.commit()

        lang = get_candidate_lang(c)

        if deep_link and deep_link.startswith("apply_"):
            try:
                vacancy_id = int(deep_link.split("_", 1)[1])
                vacancy = db.query(Vacancy).filter(
                    Vacancy.id == vacancy_id,
                    Vacancy.is_active == True
                ).first()
                if vacancy:
                    c.vacancy_id = vacancy.id
                    c.status = CandidateStatus.qualifying
                    c.chat_log_json = "[]"
                    db.commit()
                    await start_screening(message, c, vacancy, lang, db)
                    return
            except (ValueError, IndexError):
                pass

        if not c.language:
            await message.answer(t("welcome", lang), reply_markup=lang_keyboard())
        else:
            await show_vacancies(message, comp, lang, db)
    finally:
        db.close()


# --- Language selection ---

@dp.callback_query(F.data.startswith("lang:"))
async def on_lang_select(callback: CallbackQuery):
    lang = callback.data.split(":")[1]
    if lang not in ("ru", "he", "en"):
        lang = "ru"

    db = db_session()
    try:
        comp = db.query(Company).filter(Company.is_active == True).order_by(Company.id.asc()).first()
        if not comp:
            await callback.answer()
            return

        tg_user_id = str(callback.from_user.id)
        c = db.query(Candidate).filter(
            Candidate.company_id == comp.id,
            Candidate.tg_user_id == tg_user_id
        ).first()

        if c:
            c.language = lang
            db.commit()

        await callback.message.edit_text(t("language_set", lang))
        await callback.answer()
        await show_vacancies(callback.message, comp, lang, db)
    finally:
        db.close()


# --- Apply ---

@dp.callback_query(F.data.startswith("apply:"))
async def on_apply(callback: CallbackQuery):
    try:
        vacancy_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer()
        return

    db = db_session()
    try:
        comp = db.query(Company).filter(Company.is_active == True).order_by(Company.id.asc()).first()
        if not comp:
            await callback.answer()
            return

        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id, Vacancy.is_active == True).first()
        if not vacancy:
            await callback.answer()
            return

        tg_user_id = str(callback.from_user.id)
        c = db.query(Candidate).filter(
            Candidate.company_id == comp.id,
            Candidate.tg_user_id == tg_user_id
        ).first()
        if not c:
            await callback.answer()
            return

        lang = get_candidate_lang(c)

        if c.vacancy_id == vacancy.id and c.status in (CandidateStatus.passed, CandidateStatus.rejected):
            await callback.answer()
            await callback.message.answer(
                t("already_applied", lang),
                reply_markup=reapply_keyboard(vacancy.id, lang),
            )
            return

        c.vacancy_id = vacancy.id
        c.status = CandidateStatus.qualifying
        c.chat_log_json = "[]"
        c.phone = None
        c.classification = None
        db.commit()

        await callback.answer()
        await start_screening(callback.message, c, vacancy, lang, db)
    finally:
        db.close()


# --- Re-apply ---

@dp.callback_query(F.data.startswith("reapply:"))
async def on_reapply(callback: CallbackQuery):
    try:
        vacancy_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer()
        return

    db = db_session()
    try:
        comp = db.query(Company).filter(Company.is_active == True).order_by(Company.id.asc()).first()
        if not comp:
            await callback.answer()
            return

        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id, Vacancy.is_active == True).first()
        if not vacancy:
            await callback.answer()
            return

        tg_user_id = str(callback.from_user.id)
        c = db.query(Candidate).filter(
            Candidate.company_id == comp.id,
            Candidate.tg_user_id == tg_user_id
        ).first()
        if not c:
            await callback.answer()
            return

        c.vacancy_id = vacancy.id
        c.status = CandidateStatus.qualifying
        c.chat_log_json = "[]"
        c.score = None
        c.summary = ""
        c.phone = None
        c.classification = None
        db.commit()

        lang = get_candidate_lang(c)
        await callback.answer()
        await start_screening(callback.message, c, vacancy, lang, db)
    finally:
        db.close()


# --- Resume/Restart ---

@dp.callback_query(F.data.startswith("screening:"))
async def on_screening_action(callback: CallbackQuery):
    action = callback.data.split(":")[1]

    db = db_session()
    try:
        comp = db.query(Company).filter(Company.is_active == True).order_by(Company.id.asc()).first()
        if not comp:
            await callback.answer()
            return

        tg_user_id = str(callback.from_user.id)
        c = db.query(Candidate).filter(
            Candidate.company_id == comp.id,
            Candidate.tg_user_id == tg_user_id
        ).first()
        if not c or not c.vacancy_id:
            await callback.answer()
            return

        vacancy = db.query(Vacancy).filter(Vacancy.id == c.vacancy_id).first()
        if not vacancy:
            await callback.answer()
            return

        lang = get_candidate_lang(c)

        if action == "restart":
            c.status = CandidateStatus.qualifying
            c.chat_log_json = "[]"
            c.phone = None
            c.classification = None
            db.commit()
            await callback.answer()
            await start_screening(callback.message, c, vacancy, lang, db)
        elif action == "resume":
            questions = get_screening_questions(vacancy, lang)
            try:
                log = json.loads(c.chat_log_json or "[]")
            except Exception:
                log = []
            asked = count_answered(log)
            if asked < len(questions):
                progress = t("screening_progress", lang, current=asked + 1, total=len(questions))
                reply = f"{progress}\n{questions[asked]}"
                log.append({"role": "assistant", "text": questions[asked], "type": "question", "ts": ""})
                c.chat_log_json = json.dumps(log, ensure_ascii=False)
                db.commit()
                await callback.answer()
                await callback.message.answer(reply)
            else:
                await callback.answer()
        else:
            await callback.answer()
    finally:
        db.close()


# --- Free text messages (screening answers + phone collection) ---

@dp.message(F.text)
async def on_message(message: Message):
    db = db_session()
    try:
        comp = db.query(Company).filter(Company.is_active == True).order_by(Company.id.asc()).first()
        if not comp:
            await message.answer(t("not_configured", "en"))
            return

        tg_user_id = str(message.from_user.id) if message.from_user else None
        c = None
        if tg_user_id:
            c = db.query(Candidate).filter(
                Candidate.company_id == comp.id,
                Candidate.tg_user_id == tg_user_id
            ).first()

        if not c:
            tg_lang = message.from_user.language_code if message.from_user else None
            lang = detect_language(tg_lang)
            await message.answer(t("no_active_conversation", lang))
            return

        lang = get_candidate_lang(c)

        # --- Phone collection state: interviewing = waiting for phone ---
        if c.status == CandidateStatus.interviewing:
            phone = extract_phone(message.text)
            if phone:
                c.phone = phone
                try:
                    log = json.loads(c.chat_log_json or "[]")
                except Exception:
                    log = []
                log.append({"role": "user", "text": message.text, "ts": message.date.isoformat() if message.date else "", "type": "phone"})

                # Score and classify
                vacancy = db.query(Vacancy).filter(Vacancy.id == c.vacancy_id).first() if c.vacancy_id else None
                questions = get_screening_questions(vacancy, lang)
                user_answers = [m["text"] for m in log if m.get("role") == "user" and m.get("type") != "phone"]

                if not c.score:
                    v_title = vacancy.title if vacancy else "Unknown"
                    result = score_candidate(v_title, questions, user_answers, lang)
                    c.score = result["score"]
                    c.summary = result["summary"]

                classification = classify_candidate(vacancy, c, questions, user_answers)
                c.classification = classification
                c.status = CandidateStatus.passed if classification == "hot" else CandidateStatus.passed

                reply = t("phone_accepted", lang)
                log.append({"role": "assistant", "text": reply, "type": "result", "ts": "", "classification": classification, "phone": phone})
                c.chat_log_json = json.dumps(log, ensure_ascii=False)
                db.commit()

                await message.answer(reply)

                # HOT lead notification (Task 1.5)
                if classification == "hot":
                    await send_hot_lead_notification(message.bot, comp, c, vacancy)

                return
            else:
                await message.answer(t("phone_invalid", lang))
                return

        # Not in screening mode
        if c.status not in (CandidateStatus.qualifying,):
            await message.answer(t("no_active_conversation", lang))
            return

        # Check timeout
        if is_screening_expired(c):
            try:
                log = json.loads(c.chat_log_json or "[]")
            except Exception:
                log = []
            vacancy = db.query(Vacancy).filter(Vacancy.id == c.vacancy_id).first() if c.vacancy_id else None
            questions = get_screening_questions(vacancy, lang)
            answered = count_answered(log)
            if answered > 0:
                await message.answer(
                    t("screening_resume", lang, answered=answered, total=len(questions)),
                    reply_markup=resume_keyboard(lang),
                )
            else:
                await message.answer(
                    t("screening_expired", lang),
                    reply_markup=resume_keyboard(lang),
                )
            return

        # Active screening — process answer
        vacancy = db.query(Vacancy).filter(Vacancy.id == c.vacancy_id).first() if c.vacancy_id else None
        questions = get_screening_questions(vacancy, lang)

        try:
            log = json.loads(c.chat_log_json or "[]")
        except Exception:
            log = []

        # Save user answer
        log.append({"role": "user", "text": message.text, "ts": message.date.isoformat() if message.date else ""})

        asked = count_answered(log)

        if asked < len(questions):
            # More questions to ask
            progress = t("screening_progress", lang, current=asked + 1, total=len(questions))
            reply = f"{t('answer_accepted', lang)}\n\n{progress}\n{questions[asked]}"
            log.append({"role": "assistant", "text": questions[asked], "type": "question", "ts": ""})
        else:
            # All questions answered → score → ask for phone
            user_answers = [m["text"] for m in log if m.get("role") == "user"]
            v_title = vacancy.title if vacancy else "Unknown"

            result = score_candidate(v_title, questions, user_answers, lang)
            c.score = result["score"]
            c.summary = result["summary"]

            # Preliminary classification (before phone)
            if c.score < 20:
                # COLD — close politely, no phone ask
                c.status = CandidateStatus.rejected
                c.classification = "cold"
                reply = t("classification_cold_close", lang)
                log.append({"role": "assistant", "text": reply, "type": "result", "ts": "",
                            "score": c.score, "classification": "cold", "provider": result.get("provider", "unknown")})
            else:
                # WARM/HOT potential — ask for phone
                c.status = CandidateStatus.interviewing  # = waiting for phone
                reply = t("ask_phone", lang)
                log.append({"role": "assistant", "text": reply, "type": "phone_request", "ts": "",
                            "score": c.score, "provider": result.get("provider", "unknown")})

        c.chat_log_json = json.dumps(log, ensure_ascii=False)
        db.commit()

        await message.answer(reply)
    finally:
        db.close()


# --- Contact share handler (Telegram contact button) ---

@dp.message(F.contact)
async def on_contact(message: Message):
    """Handle shared contact for phone collection."""
    db = db_session()
    try:
        comp = db.query(Company).filter(Company.is_active == True).order_by(Company.id.asc()).first()
        if not comp:
            return

        tg_user_id = str(message.from_user.id) if message.from_user else None
        if not tg_user_id:
            return

        c = db.query(Candidate).filter(
            Candidate.company_id == comp.id,
            Candidate.tg_user_id == tg_user_id
        ).first()

        if not c or c.status != CandidateStatus.interviewing:
            return

        phone = message.contact.phone_number
        if not phone:
            return

        lang = get_candidate_lang(c)
        c.phone = phone

        try:
            log = json.loads(c.chat_log_json or "[]")
        except Exception:
            log = []

        log.append({"role": "user", "text": f"[contact shared: {phone}]", "ts": message.date.isoformat() if message.date else "", "type": "phone"})

        vacancy = db.query(Vacancy).filter(Vacancy.id == c.vacancy_id).first() if c.vacancy_id else None
        questions = get_screening_questions(vacancy, lang)
        user_answers = [m["text"] for m in log if m.get("role") == "user" and m.get("type") != "phone"]

        if not c.score:
            v_title = vacancy.title if vacancy else "Unknown"
            result = score_candidate(v_title, questions, user_answers, lang)
            c.score = result["score"]
            c.summary = result["summary"]

        classification = classify_candidate(vacancy, c, questions, user_answers)
        c.classification = classification
        c.status = CandidateStatus.passed

        reply = t("phone_accepted", lang)
        log.append({"role": "assistant", "text": reply, "type": "result", "ts": "", "classification": classification, "phone": phone})
        c.chat_log_json = json.dumps(log, ensure_ascii=False)
        db.commit()

        await message.answer(reply)

        if classification == "hot":
            await send_hot_lead_notification(message.bot, comp, c, vacancy)
    finally:
        db.close()


# --- Helpers ---

async def show_vacancies(message: Message, company, lang: str, db):
    vacancies = db.query(Vacancy).filter(
        Vacancy.company_id == company.id,
        Vacancy.is_active == True
    ).order_by(Vacancy.created_at.desc()).limit(5).all()

    if not vacancies:
        await message.answer(t("no_vacancies", lang))
        return

    text = t("vacancies_header", lang)
    for v in vacancies:
        text += f"\n\n🔹 **{v.title}**"
        if v.city:
            text += f" — {v.city}"
        if v.body:
            body_short = v.body[:100] + ("..." if len(v.body) > 100 else "")
            text += f"\n{body_short}"

    kb = vacancy_keyboard(vacancies, lang, None)
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


async def start_screening(message: Message, candidate, vacancy, lang: str, db):
    """Start screening: use bot_introduction if available, then first question."""
    questions = get_screening_questions(vacancy, lang)
    if not questions:
        questions = get_questions(lang)

    # Use universal bot introduction or default greeting
    greeting = build_bot_greeting(vacancy, lang)
    progress = t("screening_progress", lang, current=1, total=len(questions))
    reply = f"{greeting}\n\n{progress}\n{questions[0]}"

    log = [{"role": "assistant", "text": questions[0], "type": "question", "ts": ""}]
    candidate.chat_log_json = json.dumps(log, ensure_ascii=False)
    db.commit()

    await message.answer(reply)


def main():
    if not BOT_TOKEN:
        raise SystemExit("RECRUITBOT_TELEGRAM_BOT_TOKEN/TELEGRAM_BOT_TOKEN missing")

    import asyncio
    import time

    max_retries = 12
    for attempt in range(max_retries):
        try:
            bot = Bot(BOT_TOKEN)
            loop = asyncio.new_event_loop()
            me = loop.run_until_complete(bot.get_me())
            print(f"[bot] Connected as @{me.username} (attempt {attempt + 1})")
            loop.run_until_complete(bot.session.close())
            loop.close()
            break
        except Exception as e:
            print(f"[bot] Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(10)
            else:
                raise SystemExit(f"[bot] Could not connect after {max_retries} attempts")

    bot = Bot(BOT_TOKEN)
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
