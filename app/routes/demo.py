"""
Demo aid routes — visible at /demo.

Goal: a one-click "fire a hot lead" button so the operator can prove the
end-to-end candidate flow during a live observer walkthrough WITHOUT dropping
to a terminal. Click the button → an AI-scored "hot" candidate row is created,
classify_candidate runs, send_hot_lead_notification fires, the operator's
Telegram chat receives a real "🔥 HOT LEAD!" message within seconds.

Cleanup helper too — wipe DEMO_FB_* and DEMO_HOT_* candidates between
walkthroughs so the dashboard counters don't keep growing.
"""
from __future__ import annotations

import asyncio
import json
import os
import time

from flask import Blueprint, jsonify, render_template_string, request, session

from ..auth import login_required
from ..db import db_session
from ..models import Candidate, CandidateStatus, Company, Vacancy

bp = Blueprint("demo", __name__, url_prefix="/demo")


PAGE_HTML = """<!doctype html>
<html lang="ru" dir="ltr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Demo · Hot Lead Simulator</title>
  <link rel="stylesheet" href="/static/app.css">
  <style>
    body { background: #0d0d0d; color: #f5f5f5; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; padding: 32px; max-width: 720px; margin: 0 auto; }
    h1 { color: #ff6b6b; font-size: 28px; margin-bottom: 8px; letter-spacing: -0.02em; }
    .lead { color: #c0c0c0; font-size: 14px; margin-bottom: 28px; line-height: 1.5; }
    .vacancy-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
    .vacancy-title { font-weight: 600; font-size: 14px; flex: 1; padding-right: 16px; }
    .vacancy-meta { color: #777; font-size: 11px; margin-top: 4px; }
    .btn-fire { background: #ff6b6b; color: white; border: 0; padding: 10px 16px; border-radius: 8px; font-weight: 600; font-size: 13px; cursor: pointer; transition: 0.2s; }
    .btn-fire:hover { background: #ff5252; }
    .btn-fire[disabled] { opacity: 0.5; cursor: wait; }
    .btn-cleanup { background: transparent; border: 1px solid #444; color: #ccc; padding: 10px 18px; border-radius: 8px; font-weight: 500; font-size: 12px; cursor: pointer; margin-top: 24px; }
    .btn-cleanup:hover { border-color: #ff6b6b; color: #ff6b6b; }
    .toast { background: #0a4a2a; border: 1px solid #1a8a4a; border-radius: 8px; padding: 12px 16px; margin: 16px 0; font-size: 13px; line-height: 1.6; }
    .toast.error { background: #4a0a0a; border-color: #8a1a1a; }
    .toast pre { background: rgba(0,0,0,0.4); padding: 8px; border-radius: 4px; margin: 8px 0; overflow-x: auto; font-size: 11px; }
    .target { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 14px 18px; margin: 0 0 24px; font-size: 12px; line-height: 1.6; color: #aaa; }
    .target b { color: #f5f5f5; }
    a { color: #ff6b6b; }
  </style>
</head>
<body>
  <h1>🔥 Hot Lead Simulator</h1>
  <p class="lead">
    Тебе на демо. Нажми "Fire" по любой вакансии — бот создаёт реалистичного кандидата с ответами,
    AI скорит, send_hot_lead_notification отправляет тебе уведомление в Telegram.
    Используй чтоб показать наблюдателю end-to-end screening flow.
  </p>

  <div class="target">
    <b>Notify chat:</b> {{ notify_chat or 'NOT CONFIGURED — set RECRUIT_OPERATOR_NOTIFY_CHAT in .env' }}<br>
    <b>Bot:</b> @AutopillotRecruit_bot<br>
    <b>Company:</b> {{ company_name }} (id={{ company_id }})
  </div>

  {% if vacancies %}
    {% for v in vacancies %}
    <div class="vacancy-card">
      <div>
        <div class="vacancy-title">{{ v.title }}</div>
        <div class="vacancy-meta">id={{ v.id }} · lang={{ v.language }} · bot_qs={{ 'yes' if v.bot_qualifying_questions else 'no' }}</div>
      </div>
      <button class="btn-fire" data-vacancy-id="{{ v.id }}">Fire ▶</button>
    </div>
    {% endfor %}
  {% else %}
    <div class="toast error">No active vacancies for this company. Add a vacancy in /vacancies/ first.</div>
  {% endif %}

  <button class="btn-cleanup" id="cleanupBtn">↺ Wipe demo candidates (DEMO_FB_* / DEMO_HOT_*)</button>

  <div id="resultArea"></div>

  <script>
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    function csrf() {
      // Demo page is intentionally minimal — Flask-WTF CSRF skipped on /api/demo/*
      // by virtue of the demo blueprint being CSRF-exempt. Header still nice if available.
      return csrfMeta ? csrfMeta.content : '';
    }
    function appendToast(html, isError) {
      const div = document.createElement('div');
      div.className = 'toast' + (isError ? ' error' : '');
      div.innerHTML = html;
      document.getElementById('resultArea').prepend(div);
    }
    document.querySelectorAll('.btn-fire').forEach(btn => {
      btn.onclick = async () => {
        const vid = btn.dataset.vacancyId;
        btn.disabled = true; btn.textContent = 'Firing…';
        try {
          const r = await fetch(`/demo/api/simulate-hot-lead?vacancy_id=${vid}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf() },
          });
          const data = await r.json();
          if (r.ok) {
            appendToast(
              `<b>✓ Hot lead fired for vacancy ${vid}</b><br>` +
              `score=${data.score} · classification=${data.classification} · candidate_id=${data.candidate_id}<br>` +
              `Provider: ${data.scoring_provider}<br>` +
              `<i>Check your Telegram chat with @AutopillotRecruit_bot — message should arrive within 3 seconds.</i><pre>${data.summary || ''}</pre>` +
              `Notification sent → ${data.notification_targets.join(', ') || '(no targets configured)'}`
            );
          } else {
            appendToast(`<b>Error:</b> ${data.error || JSON.stringify(data)}`, true);
          }
        } catch (e) {
          appendToast(`<b>Network error:</b> ${e.message}`, true);
        } finally {
          btn.disabled = false; btn.textContent = 'Fire ▶';
        }
      };
    });
    document.getElementById('cleanupBtn').onclick = async () => {
      if (!confirm('Удалить всех DEMO_FB_* и DEMO_HOT_* кандидатов?')) return;
      const r = await fetch('/demo/api/cleanup', { method: 'POST', headers: { 'X-CSRF-Token': csrf() } });
      const data = await r.json();
      if (r.ok) {
        appendToast(`✓ Удалено ${data.deleted} demo-кандидатов.`);
      } else {
        appendToast(`<b>Error:</b> ${data.error}`, true);
      }
    };
  </script>
</body>
</html>"""


@bp.get("/")
@login_required
def index():
    if not session.get("current_company_id"):
        return "<p>Сначала выбери компанию в /companies/</p>", 400
    db = db_session()
    company_id = session["current_company_id"]
    company = db.query(Company).filter(Company.id == company_id).first()
    vacancies = (
        db.query(Vacancy)
        .filter(Vacancy.company_id == company_id, Vacancy.is_active == True)
        .order_by(Vacancy.id.asc())
        .all()
    )
    db.close()
    return render_template_string(
        PAGE_HTML,
        vacancies=vacancies,
        company_name=company.name if company else "?",
        company_id=company_id,
        notify_chat=os.environ.get("RECRUIT_OPERATOR_NOTIFY_CHAT") or os.environ.get(f"RECRUIT_OPERATOR_NOTIFY_CHAT_{company_id}", ""),
    )


@bp.post("/api/simulate-hot-lead")
@login_required
def api_simulate():
    """Fire a synthetic hot-lead candidate for the requested vacancy.

    Body / query: vacancy_id (required). Mirrors scripts/simulate_hot_lead.py
    but runs in-process inside the web container; calls into the bot's
    score_candidate, classify_candidate, send_hot_lead_notification.
    """
    if not session.get("current_company_id"):
        return jsonify({"error": "no current company"}), 400
    company_id = session["current_company_id"]

    vacancy_id = request.args.get("vacancy_id", type=int) or (request.get_json(silent=True) or {}).get("vacancy_id")
    if not vacancy_id:
        return jsonify({"error": "vacancy_id required"}), 400

    db = db_session()
    try:
        vacancy = db.query(Vacancy).filter(
            Vacancy.id == vacancy_id, Vacancy.company_id == company_id, Vacancy.is_active == True
        ).first()
        if not vacancy:
            return jsonify({"error": f"vacancy {vacancy_id} not found in company {company_id}"}), 404
        company = db.query(Company).filter(Company.id == company_id).first()

        from common.ai import score_candidate
        from bot.run_bot import classify_candidate, get_screening_questions, send_hot_lead_notification

        lang = (vacancy.language or "ru").lower()
        questions = get_screening_questions(vacancy, lang)

        canned_by_lang = {
            "ru": [
                "5 лет опыта на промышленных бетонных полах, работал на крупных складах и паркингах",
                "Тель-Авив, готов ездить по всей стране, у меня есть машина",
                "Документы в порядке, виза работника",
                "Готов выйти на следующей неделе",
                "Готов уточнить остальные детали на интервью",
            ],
            "he": [
                "5 שנות ניסיון בבטון תעשייתי, עבדתי במחסנים גדולים ובחניונים",
                "תל אביב, מוכן לעבוד בכל הארץ, יש לי רכב",
                "מסמכים בסדר, ויזת עובד",
                "מוכן להתחיל בשבוע הבא",
                "מוכן להבהיר פרטים נוספים בריאיון",
            ],
            "en": [
                "5 years experience on industrial concrete floors, large warehouses and parking lots",
                "Tel Aviv, ready to travel anywhere in the country, I have a car",
                "Documents in order, work visa",
                "Ready to start next week",
                "Happy to clarify in interview",
            ],
        }
        answers = list(canned_by_lang.get(lang, canned_by_lang["ru"]))[: max(len(questions), 1)]
        while len(answers) < len(questions):
            answers.append("Готов уточнить на интервью")

        chat_log = []
        for q, a in zip(questions, answers):
            chat_log.append({"role": "bot", "text": q, "ts": int(time.time())})
            chat_log.append({"role": "user", "text": a, "ts": int(time.time())})

        candidate = Candidate(
            company_id=company_id,
            vacancy_id=vacancy_id,
            tg_user_id=f"DEMO_HOT_{int(time.time())}",
            tg_username="demo_hot_candidate",
            full_name="Demo Candidate (E2E)",
            language=lang,
            status=CandidateStatus.passed,
            phone="+972-50-555-0001",
            chat_log_json=json.dumps(chat_log, ensure_ascii=False),
            red_flags="[]",
        )
        db.add(candidate)
        db.flush()

        scoring = score_candidate(vacancy.title, questions, answers, lang)
        candidate.score = int(scoring.get("score", 0))
        candidate.summary = scoring.get("summary") or ""
        candidate.classification = classify_candidate(vacancy, candidate, questions, answers)
        db.commit()
        db.refresh(candidate)

        # Build notification destinations preview
        notification_targets: list[str] = []
        if company.owner_id and company.owner_id.replace("_", "").replace("admin", "").strip().isdigit():
            notification_targets.append(company.owner_id)
        per_company = os.environ.get(f"RECRUIT_OPERATOR_NOTIFY_CHAT_{company_id}")
        if per_company and per_company.strip().isdigit() and per_company not in notification_targets:
            notification_targets.append(per_company.strip())
        fallback = os.environ.get("RECRUIT_OPERATOR_NOTIFY_CHAT")
        if fallback and fallback.strip().isdigit() and fallback not in notification_targets:
            notification_targets.append(fallback.strip())

        # Fire the actual TG DM via aiogram in a fresh event loop
        token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("RECRUITBOT_TELEGRAM_BOT_TOKEN")
        notify_status = "skipped (no token)"
        if token and notification_targets:
            from aiogram import Bot

            async def _fire():
                bot = Bot(token=token)
                try:
                    await send_hot_lead_notification(bot, company, candidate, vacancy)
                finally:
                    await bot.session.close()

            try:
                asyncio.run(_fire())
                notify_status = "sent"
            except Exception as exc:
                notify_status = f"failed: {exc!r}"

        return jsonify({
            "ok": True,
            "candidate_id": candidate.id,
            "score": candidate.score,
            "classification": candidate.classification,
            "summary": candidate.summary,
            "scoring_provider": scoring.get("provider", "unknown"),
            "language": lang,
            "notification_targets": notification_targets,
            "notification_status": notify_status,
        })
    except Exception as exc:
        db.rollback()
        return jsonify({"error": f"unexpected: {exc!r}"}), 500
    finally:
        db.close()


@bp.post("/api/cleanup")
@login_required
def api_cleanup():
    """Wipe demo-marker candidates for the current company."""
    if not session.get("current_company_id"):
        return jsonify({"error": "no current company"}), 400
    company_id = session["current_company_id"]
    db = db_session()
    try:
        from sqlalchemy import or_
        # Delete candidates whose tg_user_id starts with DEMO_HOT_ or DEMO_FB_
        deleted = (
            db.query(Candidate)
            .filter(Candidate.company_id == company_id)
            .filter(or_(
                Candidate.tg_user_id.like("DEMO_HOT_%"),
                Candidate.tg_user_id.like("DEMO_FB_%"),
                Candidate.full_name == "Demo Candidate (E2E)",
                Candidate.full_name == "Demo Candidate (E2E simulation)",
            ))
            .delete(synchronize_session=False)
        )
        db.commit()
        return jsonify({"ok": True, "deleted": deleted})
    except Exception as exc:
        db.rollback()
        return jsonify({"error": str(exc)}), 500
    finally:
        db.close()
