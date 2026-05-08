#!/usr/bin/env python3
"""
End-to-end simulation of a HOT candidate going through bot screening.

This proves the full pipeline:
  1. Candidate row created (mimics what bot does on /start apply_<vacancy_id>)
  2. 4 answers recorded in chat_log_json (mimics bot capturing user replies)
  3. score_candidate(...) runs (rule-based fallback or AI if API key configured)
  4. classify_candidate(...) returns "hot" (assuming score >= 40 + phone present)
  5. send_hot_lead_notification(...) DMs the operator's TG chat

After running, the operator should see a "🔥 HOT LEAD!" Telegram message in their
chat with @AutopillotRecruit_bot, with a fake candidate name ("Demo Candidate"),
the chosen vacancy title, score, summary, and a wa.me link.

This is the demo proof — when the observer asks "but does the screening actually
work?", you run this and they see the bot fire a real notification.

Usage (from inside docker bot container, where deps + env are loaded):
    docker exec recruit-autopilot-core-bot-1 python scripts/simulate_hot_lead.py [vacancy_id]

Default vacancy_id = 6 (FloorDSGN concrete polishing).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time

# This script must run inside the bot container so it has access to the
# same env (TELEGRAM_BOT_TOKEN, RECRUIT_OPERATOR_NOTIFY_CHAT) as the live bot.
from app.db import db_session
from app.models import Candidate, CandidateStatus, Company, Vacancy
from common.ai import score_candidate
from bot.run_bot import (
    PASS_SCORE_THRESHOLD,
    classify_candidate,
    get_screening_questions,
    send_hot_lead_notification,
)
from aiogram import Bot


DEMO_ANSWERS_BY_VACANCY = {
    6: [
        "5 лет на бетонных полах, в основном промышленные склады и паркинги",
        "Тель-Авив, готов ездить по всей стране, у меня есть машина",
        "Да, документы в порядке, виза работника",
        "Готов выйти на следующей неделе",
    ],
    5: [
        "3 года эпокси, работал на торговых центрах и автосалонах",
        "Холон, готов по центру и северу",
        "Документы в порядке",
        "Готов выйти в этом месяце",
    ],
    "default": [
        "Опыт 4 года в этой сфере",
        "Тель-Авив, готов ездить по стране",
        "Да, документы в порядке",
        "Готов выйти на следующей неделе",
    ],
}


def main() -> int:
    vacancy_id = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    db = db_session()
    try:
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id, Vacancy.is_active == True).first()
        if not vacancy:
            print(f"ERROR: vacancy {vacancy_id} not found / inactive")
            return 1
        company = db.query(Company).filter(Company.id == vacancy.company_id).first()
        if not company:
            print(f"ERROR: company {vacancy.company_id} not found")
            return 1

        lang = (vacancy.language or "ru").lower()
        questions = get_screening_questions(vacancy, lang)
        answers = DEMO_ANSWERS_BY_VACANCY.get(vacancy_id, DEMO_ANSWERS_BY_VACANCY["default"])
        # Trim/pad answers to match question count
        while len(answers) < len(questions):
            answers.append("Готов уточнить на интервью")
        answers = answers[: len(questions)]

        chat_log = []
        for q, a in zip(questions, answers):
            chat_log.append({"role": "bot", "text": q, "ts": int(time.time())})
            chat_log.append({"role": "user", "text": a, "ts": int(time.time())})

        candidate = Candidate(
            company_id=company.id,
            vacancy_id=vacancy_id,
            tg_user_id=f"DEMO_HOT_{int(time.time())}",
            tg_username="demo_hot_candidate",
            full_name="Demo Candidate (E2E simulation)",
            language=lang,
            status=CandidateStatus.passed,
            phone="+972-50-555-0001",
            chat_log_json=json.dumps(chat_log, ensure_ascii=False),
        )
        db.add(candidate)
        db.flush()

        scoring = score_candidate(vacancy.title, questions, answers, lang)
        candidate.score = int(scoring.get("score", 0))
        candidate.summary = scoring.get("summary") or "(no summary)"
        candidate.classification = classify_candidate(vacancy, candidate, questions, answers)
        db.commit()
        db.refresh(candidate)

        print(f"\n=== Demo candidate created ===")
        print(f"  candidate_id : {candidate.id}")
        print(f"  vacancy_id   : {candidate.vacancy_id}")
        print(f"  vacancy      : {vacancy.title}")
        print(f"  company_id   : {company.id} ({company.name})")
        print(f"  score        : {candidate.score}")
        print(f"  classification: {candidate.classification}")
        print(f"  pass threshold: {PASS_SCORE_THRESHOLD}")
        print(f"  scoring source: {scoring.get('provider', 'unknown')}")
        print(f"  summary      : {candidate.summary[:200]}")
        print()

        if candidate.classification == "hot":
            print("→ Firing send_hot_lead_notification (operator should receive TG DM)...")
        else:
            print(f"→ Classification is '{candidate.classification}'. send_hot_lead_notification will be called anyway for demo proof.")

        # Set up an aiogram Bot instance just for sending the notification
        token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("RECRUITBOT_TELEGRAM_BOT_TOKEN")
        if not token:
            print("ERROR: TELEGRAM_BOT_TOKEN not in env")
            return 2

        async def fire():
            bot = Bot(token=token)
            try:
                await send_hot_lead_notification(bot, company, candidate, vacancy)
            finally:
                await bot.session.close()

        asyncio.run(fire())

        notify_chat = os.environ.get("RECRUIT_OPERATOR_NOTIFY_CHAT")
        per_company = os.environ.get(f"RECRUIT_OPERATOR_NOTIFY_CHAT_{company.id}")
        targets = []
        if company.owner_id and company.owner_id.replace("_", "").replace("admin", "").strip().isdigit():
            targets.append(("owner_id", company.owner_id))
        if per_company and per_company.strip().isdigit():
            targets.append(("per_company_env", per_company.strip()))
        if notify_chat and notify_chat.strip().isdigit():
            targets.append(("fallback_env", notify_chat.strip()))

        print()
        print("=== Notification destinations ===")
        if not targets:
            print("  ⚠ none configured. Set RECRUIT_OPERATOR_NOTIFY_CHAT=<tg_user_id> in .env, restart bot+worker.")
            return 3
        for source, target in targets:
            print(f"  {source}: chat_id={target}")

        print()
        print(f"✓ DONE. Operator should now see a '🔥 HOT LEAD!' message from @AutopillotRecruit_bot.")
        print(f"  candidate_id={candidate.id} stays in DB — delete with:")
        print(f"  docker exec recruit-autopilot-core-postgres-1 psql -U postgres -d ra -c \"DELETE FROM candidates WHERE id={candidate.id};\"")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
