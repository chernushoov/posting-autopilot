"""Inbound Telegram listener (Phase 2 — stop losing group replies).

Problem this fixes: ads go out to TG groups, candidates reply IN the group, but
nothing was listening — every "I'm interested" was silently lost. The DM
apply-link funnel only catches people who click it. This adds the missing
inbound side.

What it does (SAFE v1):
  - For each company with a connected Telegram account (Telethon session), run a
    userbot listener.
  - Capture a message when it is a REPLY to one of OUR OWN posts in a group we
    posted to (high precision attribution — no false positives from unrelated
    group chatter), or a private DM to our account.
  - Attribute it to the most recent vacancy we posted in that chat, create/update
    a Candidate lead, and NOTIFY THE OPERATOR (via the bot) with the message.

What it deliberately does NOT do: it never auto-replies in the group and never
auto-DMs the candidate. Mass auto-messaging from a personal account is a ban
risk and a "send on the user's behalf" action — that stays a human decision.

Run:  python -m worker.tg_listener   (needs at least one company with TG connected)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime

from app.db import db_session
from app.models import Candidate, CandidateStatus, Company, PostingAttempt, Source, Vacancy
from common.tg_client import _session_path

logger = logging.getLogger("tg_listener")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [tg_listener] %(message)s")


def _companies_with_telegram() -> list[dict]:
    """Return [{id, api_id, api_hash}] for companies that have connected TG."""
    db = db_session()
    try:
        rows = (
            db.query(Company)
            .filter(Company.is_active == True, Company.tg_api_id.isnot(None), Company.tg_api_hash.isnot(None))
            .all()
        )
        return [{"id": c.id, "api_id": int(c.tg_api_id), "api_hash": c.tg_api_hash} for c in rows]
    finally:
        db.close()


def _recent_vacancy_for_source(db, company_id: int, source_id: int) -> int | None:
    """Most recent vacancy we actually posted into this source."""
    pa = (
        db.query(PostingAttempt)
        .filter(
            PostingAttempt.company_id == company_id,
            PostingAttempt.source_id == source_id,
            PostingAttempt.result_status == "posted",
        )
        .order_by(PostingAttempt.created_at.desc())
        .first()
    )
    return pa.vacancy_id if pa else None


def _notify_operator(company_id: int, text: str) -> None:
    """Notify the operator about a captured lead via the Bot API (sync, best-effort).

    Targets resolve through the shared helper so the company profile's
    owner_telegram_id (set in /profile) is honoured first, then env overrides, then
    the legacy owner_id. This is the same resolution the demo + /profile test button
    use, so what the user configures is exactly what receives live hot-lead alerts.
    """
    from common.notify_targets import resolve_recruit_notify_targets

    db = db_session()
    try:
        comp = db.query(Company).filter(Company.id == company_id).first()
        targets = resolve_recruit_notify_targets(comp) if comp else []
    finally:
        db.close()
    if not targets:
        logger.info("captured lead for company %s but no operator notify chat configured", company_id)
        return
    try:
        from bot.tg import tg_send_message_safe

        for chat_id in targets:
            tg_send_message_safe(chat_id, text)
    except Exception as e:
        logger.warning("operator notify failed: %s", e)


def _capture_lead(company_id: int, source_id: int | None, tg_user_id: str | None,
                  username: str | None, full_name: str | None, message_text: str,
                  context: str) -> None:
    """Create/update a Candidate lead from an inbound reply and notify the operator."""
    db = db_session()
    try:
        vacancy_id = _recent_vacancy_for_source(db, company_id, source_id) if source_id else None
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first() if vacancy_id else None

        cand = None
        if tg_user_id:
            cand = (
                db.query(Candidate)
                .filter(Candidate.company_id == company_id, Candidate.tg_user_id == tg_user_id)
                .order_by(Candidate.id.desc())
                .first()
            )
        is_new = cand is None
        if is_new:
            cand = Candidate(
                company_id=company_id,
                vacancy_id=vacancy_id,
                tg_user_id=tg_user_id,
                tg_username=username,
                full_name=full_name,
                status=CandidateStatus.qualifying,
                chat_log_json="[]",
            )
            db.add(cand)
        # append the inbound message to the conversation log
        try:
            log = json.loads(cand.chat_log_json or "[]")
        except Exception:
            log = []
        log.append({"role": "user", "text": message_text, "type": "inbound_reply",
                    "channel": context, "ts": datetime.utcnow().isoformat()})
        cand.chat_log_json = json.dumps(log, ensure_ascii=False)
        if not cand.summary:
            cand.summary = f"Ответ(а) {context}: {message_text[:160]}"
        db.commit()
        cand_id = cand.id
        v_title = vacancy.title if vacancy else "(не определена)"
    finally:
        db.close()

    who = full_name or (f"@{username}" if username else f"id {tg_user_id}")
    note = (
        f"📨 Новый отклик ({context})\n"
        f"👤 {who}\n"
        f"📋 Вакансия: {v_title}\n"
        f"💬 Сообщение: {message_text[:400]}\n"
        f"— ответьте человеку лично (лид #{cand_id})."
    )
    _notify_operator(company_id, note)
    logger.info("captured lead #%s for company %s (%s)", cand_id, company_id, context)


async def _run_company_listener(company: dict) -> None:
    """Start one Telethon userbot listener for a company and run until disconnected."""
    from telethon import TelegramClient, events
    from telethon import utils as tl_utils

    company_id = company["id"]
    client = TelegramClient(_session_path(company_id), company["api_id"], company["api_hash"])
    await client.connect()
    if not await client.is_user_authorized():
        logger.info("company %s has TG creds but no authorized session — skipping", company_id)
        await client.disconnect()
        return

    me = await client.get_me()
    my_id = me.id

    # Map marked chat_id -> source_id for the groups we have posted into.
    watched: dict[int, int] = {}
    db = db_session()
    try:
        sources = db.query(Source).filter(
            Source.company_id == company_id,
            Source.platform == "telegram",
            Source.is_active == True,
        ).all()
    finally:
        db.close()
    for s in sources:
        try:
            entity = await client.get_entity(s.tg_ref)
            watched[tl_utils.get_peer_id(entity)] = s.id
        except Exception as e:
            logger.info("company %s: could not resolve source %s (%s)", company_id, s.tg_ref, e)
    logger.info("company %s listening — me=%s, watching %s chats", company_id, my_id, len(watched))

    @client.on(events.NewMessage)
    async def handler(event):  # noqa: ANN001
        try:
            if event.out:
                return  # ignore our own messages
            sender = await event.get_sender()
            if getattr(sender, "bot", False):
                return  # ignore other bots
            text = (event.raw_text or "").strip()
            if not text:
                return

            username = getattr(sender, "username", None)
            full_name = " ".join(filter(None, [getattr(sender, "first_name", None), getattr(sender, "last_name", None)])) or None
            uid = str(getattr(sender, "id", "")) or None

            if event.is_private:
                # Direct DM to our account — a response, vacancy unknown.
                _capture_lead(company_id, None, uid, username, full_name, text, "в личке")
                return

            chat_id = event.chat_id
            if chat_id not in watched:
                return  # not a group we posted to → ignore the noise
            if not event.is_reply:
                return  # only count replies (high precision)
            replied = await event.get_reply_message()
            if not replied or replied.sender_id != my_id:
                return  # only replies to OUR posts
            _capture_lead(company_id, watched[chat_id], uid, username, full_name, text, "в группе")
        except Exception as e:
            logger.warning("company %s handler error: %s", company_id, e)

    await client.run_until_disconnected()


async def _main_async() -> None:
    companies = _companies_with_telegram()
    if not companies:
        logger.info("no companies with a connected Telegram account — nothing to listen to. Exiting.")
        return
    logger.info("starting inbound listeners for %s companies", len(companies))
    await asyncio.gather(*[_run_company_listener(c) for c in companies])


def main() -> None:
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
