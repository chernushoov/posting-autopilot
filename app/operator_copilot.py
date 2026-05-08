from __future__ import annotations

from pathlib import Path

from .db import db_session
from .models import Campaign, Candidate, Company, PostingAttempt, Source, Vacancy


def _t(lang: str, *, en: str, ru: str, he: str) -> str:
    return {"ru": ru, "he": he}.get(lang, en)


def _page_label(path: str, lang: str) -> str:
    mapping = (
        ("/dashboard", _t(lang, en="Dashboard", ru="Панель", he="לוח בקרה")),
        ("/connect/telegram", _t(lang, en="Telegram connect", ru="Подключение Telegram", he="חיבור טלגרם")),
        ("/connect/facebook", _t(lang, en="Facebook connect", ru="Подключение Facebook", he="חיבור פייסבוק")),
        ("/vacancies", _t(lang, en="Vacancies", ru="Вакансии", he="משרות")),
        ("/sources", _t(lang, en="Destinations", ru="Каналы", he="יעדים")),
        ("/campaigns", _t(lang, en="Campaigns", ru="Кампании", he="קמפיינים")),
        ("/candidates", _t(lang, en="Candidates", ru="Кандидаты", he="מועמדים")),
        ("/profile", _t(lang, en="Company profile", ru="Профиль компании", he="פרופיל חברה")),
        ("/companies", _t(lang, en="Companies", ru="Компании", he="חברות")),
    )
    for prefix, label in mapping:
        if path.startswith(prefix):
            return label
    return _t(lang, en="Workspace", ru="Рабочее пространство", he="סביבת עבודה")


def _session_file_exists(company_id: int) -> bool:
    return Path(__file__).resolve().parents[1].joinpath("data", "tg_sessions", f"company_{company_id}.session").exists()


def build_operator_copilot(session_data, path: str, lang: str = "en"):
    if not (session_data.get("is_admin") or session_data.get("user_id")):
        return None

    owner_id = session_data.get("owner_id")
    company_id = session_data.get("current_company_id")

    if not company_id or not owner_id:
        return {
            "title": _t(lang, en="Operator Copilot", ru="Operator Copilot", he="Operator Copilot"),
            "summary": _t(
                lang,
                en="No company is selected. Choose the company you want to operate before changing vacancies or campaigns.",
                ru="Компания не выбрана. Сначала выбери компанию, с которой хочешь работать.",
                he="לא נבחרה חברה. בחר קודם את החברה שאיתה תרצה לעבוד.",
            ),
            "state_label": _t(lang, en="setup", ru="настройка", he="הגדרה"),
            "state_tone": "manual_action_required",
            "page_label": _page_label(path, lang),
            "context_label": _t(lang, en="Context", ru="Контекст", he="הקשר"),
            "warnings_label": _t(lang, en="Attention", ru="Внимание", he="תשומת לב"),
            "facts": [],
            "warnings": [],
            "actions": [
                {
                    "label": _t(lang, en="Open companies", ru="Открыть компании", he="פתח חברות"),
                    "href": "/companies/",
                    "primary": True,
                }
            ],
        }

    db = db_session()
    try:
        company = (
            db.query(Company)
            .filter(Company.id == company_id, Company.owner_id == owner_id, Company.is_active == True)
            .first()
        )
        if not company:
            return {
                "title": _t(lang, en="Operator Copilot", ru="Operator Copilot", he="Operator Copilot"),
                "summary": _t(
                    lang,
                    en="The selected company is no longer available. Re-select the active company and continue.",
                    ru="Выбранная компания недоступна. Выбери активную компанию заново.",
                    he="החברה שנבחרה אינה זמינה. בחר מחדש חברה פעילה.",
                ),
                "state_label": _t(lang, en="attention", ru="внимание", he="תשומת לב"),
                "state_tone": "failed",
                "page_label": _page_label(path, lang),
                "context_label": _t(lang, en="Context", ru="Контекст", he="הקשר"),
                "warnings_label": _t(lang, en="Attention", ru="Внимание", he="תשומת לב"),
                "facts": [],
                "warnings": [],
                "actions": [
                    {
                        "label": _t(lang, en="Open companies", ru="Открыть компании", he="פתח חברות"),
                        "href": "/companies/",
                        "primary": True,
                    }
                ],
            }

        vacancy_count = db.query(Vacancy).filter(Vacancy.company_id == company_id, Vacancy.is_active == True).count()
        telegram_sources = (
            db.query(Source)
            .filter(Source.company_id == company_id, Source.platform == "telegram", Source.is_active == True)
            .all()
        )
        facebook_sources = (
            db.query(Source)
            .filter(Source.company_id == company_id, Source.platform == "facebook", Source.is_active == True)
            .all()
        )
        campaigns = db.query(Campaign).filter(Campaign.company_id == company_id).all()
        running_campaigns = [c for c in campaigns if c.is_running]
        candidate_count = db.query(Candidate).filter(Candidate.company_id == company_id).count()
        recent_attempt = (
            db.query(PostingAttempt)
            .filter(PostingAttempt.company_id == company_id)
            .order_by(PostingAttempt.id.desc())
            .first()
        )
        recent_telegram_attempt = (
            db.query(PostingAttempt)
            .filter(PostingAttempt.company_id == company_id, PostingAttempt.platform == "telegram")
            .order_by(PostingAttempt.id.desc())
            .first()
        )
        latest_failed_attempt = (
            db.query(PostingAttempt)
            .filter(PostingAttempt.company_id == company_id, PostingAttempt.result_status.in_(["failed", "blocked_or_suspected"]))
            .order_by(PostingAttempt.id.desc())
            .first()
        )

        telegram_ready_count = sum(1 for s in telegram_sources if s.last_check_ok)
        facebook_manual_count = sum(1 for s in facebook_sources if (s.posting_mode or "") == "assisted_manual")
        telegram_credentials = bool(company.tg_api_id and company.tg_api_hash)
        telegram_session_present = _session_file_exists(company_id)
        telegram_authorized = False
        if telegram_credentials:
            try:
                from common.tg_client import is_authorized

                telegram_authorized = is_authorized(int(company.tg_api_id), company.tg_api_hash, company_id)
            except Exception:
                telegram_authorized = False
        ordered_campaigns = sorted(campaigns, key=lambda item: item.id, reverse=True)
        primary_campaign = (sorted(running_campaigns, key=lambda item: item.id, reverse=True) or ordered_campaigns or [None])[0]
        first_telegram_source = next((source for source in telegram_sources if source.is_active), None)
        latest_tg_error = ""
        for source in telegram_sources:
            if (source.last_check_message or "").strip():
                latest_tg_error = source.last_check_message.strip()
                if latest_tg_error == "NOT_AUTHORIZED":
                    break
        if recent_telegram_attempt and recent_telegram_attempt.error_message:
            latest_tg_error = recent_telegram_attempt.error_message.strip()

        facts = [
            _t(
                lang,
                en=f"Current page: {_page_label(path, lang)}",
                ru=f"Текущая страница: {_page_label(path, lang)}",
                he=f"עמוד נוכחי: {_page_label(path, lang)}",
            ),
            _t(
                lang,
                en=f"Company: {company.name}",
                ru=f"Компания: {company.name}",
                he=f"חברה: {company.name}",
            ),
            _t(
                lang,
                en=f"Active vacancies: {vacancy_count}",
                ru=f"Активные вакансии: {vacancy_count}",
                he=f"משרות פעילות: {vacancy_count}",
            ),
            _t(
                lang,
                en=f"Telegram destinations ready: {telegram_ready_count}/{len(telegram_sources)}",
                ru=f"Telegram-каналы готовы: {telegram_ready_count}/{len(telegram_sources)}",
                he=f"יעדי טלגרם מוכנים: {telegram_ready_count}/{len(telegram_sources)}",
            ),
            _t(
                lang,
                en=f"Telegram account authorized: {'yes' if telegram_authorized else 'no'}",
                ru=f"Telegram-аккаунт авторизован: {'да' if telegram_authorized else 'нет'}",
                he=f"חשבון Telegram מאומת: {'כן' if telegram_authorized else 'לא'}",
            ),
            _t(
                lang,
                en=f"Facebook destinations: {len(facebook_sources)}",
                ru=f"Facebook-каналы: {len(facebook_sources)}",
                he=f"יעדי פייסבוק: {len(facebook_sources)}",
            ),
            _t(
                lang,
                en=f"Campaigns running: {len(running_campaigns)}/{len(campaigns)}",
                ru=f"Кампаний запущено: {len(running_campaigns)}/{len(campaigns)}",
                he=f"קמפיינים פעילים: {len(running_campaigns)}/{len(campaigns)}",
            ),
            _t(
                lang,
                en=f"Worker responses: {candidate_count}",
                ru=f"Отклики работников: {candidate_count}",
                he=f"תגובות עובדים: {candidate_count}",
            ),
        ]

        warnings = []
        if latest_tg_error:
            warnings.append(
                _t(
                    lang,
                    en=f"Latest Telegram issue: {latest_tg_error}",
                    ru=f"Последняя проблема Telegram: {latest_tg_error}",
                    he=f"בעיית טלגרם אחרונה: {latest_tg_error}",
                )
            )
        if facebook_manual_count:
            warnings.append(
                _t(
                    lang,
                    en="Facebook stays assisted/manual in pilot mode. The operator must confirm the final result.",
                    ru="Facebook в пилоте остаётся assisted/manual. Финальный результат должен подтвердить оператор.",
                    he="פייסבוק נשאר במצב מלווה/ידני בפיילוט. המפעיל צריך לאשר את התוצאה הסופית.",
                )
            )

        state_tone = "posted"
        state_label = _t(lang, en="ready", ru="готово", he="מוכן")
        summary = _t(
            lang,
            en="Pilot flow is assembled. Keep watching destinations, attempts, and candidate responses.",
            ru="Пилотный контур собран. Дальше следи за каналами, попытками постинга и откликами.",
            he="נתיב הפיילוט מורכב. עקוב אחרי היעדים, ניסיונות הפרסום ותגובות המועמדים.",
        )
        actions = []

        def add_action(
            label_en: str,
            label_ru: str,
            label_he: str,
            href: str,
            primary: bool = False,
            method: str = "GET",
            confirm_en: str | None = None,
            confirm_ru: str | None = None,
            confirm_he: str | None = None,
        ):
            key = (href, method.upper())
            if key not in {(action["href"], action.get("method", "GET").upper()) for action in actions}:
                action_obj = {
                    "label": _t(lang, en=label_en, ru=label_ru, he=label_he),
                    "href": href,
                    "primary": primary,
                    "method": method.upper(),
                }
                if confirm_en or confirm_ru or confirm_he:
                    action_obj["confirm"] = _t(
                        lang,
                        en=confirm_en or confirm_ru or confirm_he or "Confirm?",
                        ru=confirm_ru or confirm_en or "Подтвердить?",
                        he=confirm_he or confirm_en or "אישור?",
                    )
                actions.append(action_obj)

        if vacancy_count == 0:
            state_tone = "manual_action_required"
            state_label = _t(lang, en="setup", ru="настройка", he="הגדרה")
            summary = _t(
                lang,
                en="No live vacancy exists yet. Create one pilot vacancy before connecting destinations or campaigns.",
                ru="Пока нет живой вакансии. Сначала создай одну пилотную вакансию.",
                he="עדיין אין משרה חיה. צור קודם משרת פיילוט אחת.",
            )
            add_action("Create vacancy", "Создать вакансию", "צור משרה", "/vacancies/new", True)
            add_action("Open vacancies", "Открыть вакансии", "פתח משרות", "/vacancies/")
        elif not telegram_credentials:
            state_tone = "manual_action_required"
            state_label = _t(lang, en="setup", ru="настройка", he="הגדרה")
            summary = _t(
                lang,
                en="Telegram credentials are missing for this company. Connect the Telegram account that is already inside the target groups.",
                ru="Для этой компании не настроены Telegram credentials. Подключи Telegram-аккаунт, который уже состоит в нужных группах.",
                he="חסרים פרטי Telegram לחברה הזו. חבר את חשבון הטלגרם שכבר נמצא בקבוצות היעד.",
            )
            add_action("Connect Telegram", "Подключить Telegram", "חבר טלגרם", "/connect/telegram", True)
        elif (not telegram_authorized and latest_tg_error == "NOT_AUTHORIZED") or (
            telegram_session_present and telegram_ready_count == 0 and path.startswith("/connect/telegram") and not telegram_authorized
        ):
            state_tone = "failed"
            state_label = _t(lang, en="attention", ru="внимание", he="תשומת לב")
            summary = _t(
                lang,
                en="Telegram is linked by credentials, but the current company is not authorized for posting yet. Re-open Telegram connect, verify the account, then sync groups.",
                ru="Telegram credentials есть, но текущая компания ещё не авторизована для постинга. Открой Telegram connect, пройди verify и потом sync groups.",
                he="יש פרטי Telegram, אבל החברה הנוכחית עדיין לא מורשית לפרסום. פתח שוב את חיבור Telegram, בצע אימות ואז סנכרון קבוצות.",
            )
            add_action("Open Telegram connect", "Открыть Telegram connect", "פתח חיבור טלגרם", "/connect/telegram", True)
            add_action("Open campaigns", "Открыть кампании", "פתח קמפיינים", "/campaigns/")
        elif telegram_ready_count == 0:
            state_tone = "manual_action_required"
            state_label = _t(lang, en="setup", ru="настройка", he="הגדרה")
            summary = _t(
                lang,
                en="Telegram is connected, but no READY destination exists yet. Sync groups or add the target group manually.",
                ru="Telegram подключён, но пока нет ни одного READY-канала. Сделай sync groups или добавь целевую группу вручную.",
                he="טלגרם מחובר, אבל עדיין אין יעד READY. בצע סנכרון קבוצות או הוסף את קבוצת היעד ידנית.",
            )
            add_action(
                "Sync Telegram groups",
                "Синхронизировать группы Telegram",
                "סנכרן קבוצות טלגרם",
                "/connect/telegram/sync",
                True,
                method="POST",
            )
            add_action("Open Telegram connect", "Открыть Telegram connect", "פתח חיבור טלגרם", "/connect/telegram")
            add_action("Open destinations", "Открыть каналы", "פתח יעדים", "/sources/")
        elif len(campaigns) == 0:
            state_tone = "manual_action_required"
            state_label = _t(lang, en="setup", ru="настройка", he="הגדרה")
            summary = _t(
                lang,
                en="Destinations are ready, but no campaign exists yet. Create one pilot campaign and attach the ready destinations.",
                ru="Каналы уже готовы, но кампании ещё нет. Создай одну пилотную кампанию и привяжи к ней готовые каналы.",
                he="היעדים כבר מוכנים, אבל עדיין אין קמפיין. צור קמפיין פיילוט אחד וחבר אליו את היעדים המוכנים.",
            )
            add_action("Create campaign", "Создать кампанию", "צור קמפיין", "/campaigns/new", True)
            add_action("Open campaigns", "Открыть кампании", "פתח קמפיינים", "/campaigns/")
        elif not running_campaigns:
            state_tone = "manual_action_required"
            state_label = _t(lang, en="attention", ru="внимание", he="תשומת לב")
            summary = _t(
                lang,
                en="Campaigns exist, but none is running. Open the campaigns page and start the pilot campaign.",
                ru="Кампании есть, но ни одна не запущена. Открой кампании и включи пилотную.",
                he="יש קמפיינים, אבל אף אחד מהם לא פעיל. פתח את הקמפיינים והפעל את קמפיין הפיילוט.",
            )
            if primary_campaign:
                # Compute destination count for confirm message — operator should
                # know how many real groups will receive auto-posts before flipping.
                campaign_dest_count = (
                    db.query(Campaign).filter(Campaign.id == primary_campaign.id).first()
                )
                from .models import CampaignSource as _CS
                dest_count = db.query(_CS).filter(_CS.campaign_id == primary_campaign.id).count()
                add_action(
                    "Activate campaign — auto-posting starts",
                    "Активировать кампанию — начнётся автопостинг",
                    "הפעל קמפיין — פרסום אוטומטי יתחיל",
                    f"/campaigns/toggle/{primary_campaign.id}",
                    True,
                    method="POST",
                    confirm_en=f"Activate '{primary_campaign.name}'? It will auto-post to {dest_count} destinations during the active hours window. You can pause anytime.",
                    confirm_ru=f"Активировать '{primary_campaign.name}'? Бот начнёт автопост в {dest_count} каналов в активные часы. Поставить на паузу можно в любой момент.",
                    confirm_he=f"להפעיל את '{primary_campaign.name}'? הבוט יתחיל לפרסם אוטומטית ל-{dest_count} יעדים בשעות הפעילות. אפשר להשהות בכל עת.",
                )
            add_action("Review campaign first", "Сначала проверь кампанию", "בדוק קמפיין קודם", "/campaigns/")
        elif recent_attempt and recent_attempt.result_status == "failed":
            state_tone = "failed"
            state_label = _t(lang, en="attention", ru="внимание", he="תשומת לב")
            summary = _t(
                lang,
                en="The latest posting attempt failed. Open campaigns and the destination log, then fix the blocking issue before retrying.",
                ru="Последняя попытка постинга завершилась ошибкой. Открой кампании и лог destination, потом исправь блокирующую проблему перед повтором.",
                he="ניסיון הפרסום האחרון נכשל. פתח את הקמפיינים ואת לוג היעד, ואז תקן את הבעיה החוסמת לפני ניסיון נוסף.",
            )
            if recent_attempt.platform == "telegram" and recent_attempt.error_message != "NOT_AUTHORIZED" and recent_attempt.source_id:
                add_action(
                    "Re-check destination",
                    "Перепроверить канал",
                    "בדוק שוב יעד",
                    f"/sources/check/{recent_attempt.source_id}",
                    True,
                    method="POST",
                )
            elif primary_campaign:
                add_action(
                    "Run campaign now",
                    "Запустить кампанию сейчас",
                    "הפעל קמפיין עכשיו",
                    f"/campaigns/run/{primary_campaign.id}",
                    True,
                    method="POST",
                )
            add_action("Open campaigns", "Открыть кампании", "פתח קמפיינים", "/campaigns/")
            add_action("Open Telegram connect", "Открыть Telegram connect", "פתח חיבור טלגרם", "/connect/telegram")
        elif candidate_count > 0:
            state_tone = "posted"
            state_label = _t(lang, en="live", ru="в работе", he="חי")
            summary = _t(
                lang,
                en="The system is live and candidates are already coming in. Review fresh responses and keep the campaign stable.",
                ru="Система уже в работе и кандидаты приходят. Просматривай свежие отклики и держи кампанию стабильной.",
                he="המערכת כבר חיה ומועמדים נכנסים. בדוק תגובות חדשות ושמור על יציבות הקמפיין.",
            )
            add_action("Open candidates", "Открыть кандидатов", "פתח מועמדים", "/candidates/", True)
            add_action("Open campaigns", "Открыть кампании", "פתח קמפיינים", "/campaigns/")
        else:
            if primary_campaign:
                add_action(
                    "Run campaign now",
                    "Запустить кампанию сейчас",
                    "הפעל קמפיין עכשיו",
                    f"/campaigns/run/{primary_campaign.id}",
                    True,
                    method="POST",
                )
            add_action("Open campaigns", "Открыть кампании", "פתח קמפיינים", "/campaigns/")
            add_action("Open candidates", "Открыть кандидатов", "פתח מועמדים", "/candidates/")
            add_action("Open destinations", "Открыть каналы", "פתח יעדים", "/sources/")

        if first_telegram_source and latest_tg_error and latest_tg_error not in {"NOT_AUTHORIZED"}:
            add_action(
                "Check Telegram destination",
                "Проверить Telegram-канал",
                "בדוק יעד טלגרם",
                f"/sources/check/{first_telegram_source.id}",
                False,
                method="POST",
            )
        if latest_failed_attempt:
            add_action(
                "Open latest failed attempt",
                "Открыть последнюю ошибку",
                "פתח את הכשל האחרון",
                f"/campaigns/?focus_attempt={latest_failed_attempt.id}#attempt-{latest_failed_attempt.id}",
            )
            add_action(
                "Open failed destination",
                "Открыть проблемный канал",
                "פתח את היעד הבעייתי",
                f"/sources/?focus_source={latest_failed_attempt.source_id}#source-{latest_failed_attempt.source_id}",
            )

        if recent_attempt:
            facts.append(
                _t(
                    lang,
                    en=f"Latest posting attempt: {recent_attempt.result_status}",
                    ru=f"Последняя попытка постинга: {recent_attempt.result_status}",
                    he=f"ניסיון הפרסום האחרון: {recent_attempt.result_status}",
                )
            )

        return {
            "title": _t(lang, en="Operator Copilot", ru="Operator Copilot", he="Operator Copilot"),
            "summary": summary,
            "state_label": state_label,
            "state_tone": state_tone,
            "page_label": _page_label(path, lang),
            "context_label": _t(lang, en="Context", ru="Контекст", he="הקשר"),
            "warnings_label": _t(lang, en="Attention", ru="Внимание", he="תשומת לב"),
            "facts": facts,
            "warnings": warnings,
            "actions": actions,
        }
    finally:
        db.close()
