# LAUNCH TOMORROW — 2026-05-10

Полный аудит стека выполнен 2026-05-09. Состояние: **готов к запуску** с двумя
блокерами оператора (FB session, реальная клиентская кампания) и одним только что
исправленным багом (RQ timeout). Ниже — что есть, что чинили сегодня, что делать
утром, и в каком порядке.

---

## Состояние стека (snapshot 2026-05-09)

| Компонент | Статус | Заметка |
|---|---|---|
| `web` (Flask, :8080) | running | все 11 ключевых роутов 200/302 OK |
| `bot` (@AutopillotRecruit_bot) | running | getMe 200, оператор chat 8175553706 настроен |
| `worker` (RQ default/low/high) | running | 0 pending / 0 started, 10 failed (исторические Apr 22) |
| `scheduler` (APScheduler) | running | 9 ч uptime, тики кампаний идут |
| `redis` | running | ping OK |
| `postgres` | running | 26 ч uptime |

**DB cтейт:** 6 активных компаний, 15 активных вакансий (10 recruitment + 5 realestate),
23 кандидата (10 hot, 2 warm, 1 cold, 10 NULL — старые мартовские тестовые),
11 каналов постинга, все `last_check_ok=true`. 5 успешных posting_attempts, 38
исторических failures (33 — гейт «destination not ready», корректное поведение).

---

## Что починено сегодня (Sprint 8 + аудит)

1. **AI date-grounding** (`common/ai.py`) — в скоринговый промпт инжектится `TODAY: <iso>`,
   gpt-4o-mini больше не округляет «1 июня 2026» в «через 2.5 года».
2. **Per-vacancy funnel cards** на `/vacancies/` — total/hot/warm/cold/avg_score
   прямо в списке без захода в деталку.
3. **RQ campaign_tick timeout 180s → 1800s** (`worker/queue.py`). Найден через
   разбор failed-job registry: 30-120s anti-spam delay × 5-6 групп легко
   перебивал старый дефолт. Без фикса любой реальный «Run Now» на 5+ групп
   терял 2-3 поста посередине.

---

## Что нужно сделать утром (по приоритету)

### P0 — обязательно перед первым реальным выстрелом

1. **FB session capture** (5 мин, оператор на Mac).
   `python scripts/fb_capture_session.py` — открывает headed Chromium,
   вы логинитесь в FB один раз, storage_state сохраняется в
   `data/fb_sessions/<name>.json`. Без этого FB-постинг работает только в
   очереди для ручной публикации (16 pending items уже ждут).

2. **Smoke pre-flight**: `curl -sf http://localhost:8080/health` должен
   вернуть 200 + `make smoke` (если есть) либо `python scripts/runtime_check.py`.
   Должны пройти оба: connect/telegram, campaigns/, vacancies/, demo/.

3. **Подтвердить кампанию для боевого огня.** Сейчас `posting_runs`:
   2 in_progress, 4 ready. Решить какую кампанию (FloorDSGN найм или
   Floor.DSGN Properties аренда) запускать первой и подтвердить словом «fire»
   — sandbox требует явного approval.

### P1 — желательно до запуска кампании

4. **SMTP** для daily digest (5 мин). Сейчас `SMTP_HOST/USER/PASSWORD` пустые —
   email-уведомления о горячих лидах НЕ идут (только Telegram DM работает).
   Если планируется email-канал — заполнить в `.env` и `docker compose restart web bot worker`.

5. **Cleanup 10 NULL classification candidates** (косметика). Старые мартовские
   тестовые без классификации, не ломают UI но засоряют статистику.
   `UPDATE candidates SET classification='cold' WHERE classification IS NULL AND created_at < '2026-04-01';`

6. **Прогнать /demo/ симулятор по 1 разу на каждой вакансии** перед клиентом —
   убедиться что AI-скоринг и hot-lead notification идут на оператора.

### P2 — после успешного первого огня

7. **Реальный клиент real estate**: получить от агентства имя, FB-группы,
   реальные данные квартир. Сейчас работаем под Floor.DSGN Properties +
   FloorDSGN телефонами (по согласованию).

8. **Production hosting**: решить Mac+Cloudflare vs Hetzner $5/mo. Сейчас
   tunnel: `basement-inner-extra-tyler.trycloudflare.com` — эфемерный URL,
   ломается при ребуте.

9. **Stripe billing wiring** для revenue-share с RE-агентством (~4-6 ч).

10. **Cars vertical (Boris)** — отложен на 3+ месяца, ждём BD-путь к Yad2.

---

## Чек-лист запуска (минимально)

```
[ ] docker compose ps  → все 6 running
[ ] curl http://localhost:8080/health → 200
[ ] FB session captured (если планируем FB postинг)
[ ] cloudflare tunnel up (или решено что без tunnel)
[ ] /vacancies/ показывает funnel-цифры
[ ] /demo/ → 1 fire → hot-lead DM пришёл оператору
[ ] оператор подтвердил какую кампанию fire
[ ] /campaigns/run/<id> → posting_attempts заполнились
[ ] через 5-10 мин: result_status='posted' хотя бы для одного
```

---

## Известные ограничения (осознанные, не блокеры)

- **Anti-spam**: 30-120s между постами + 10/час + 50/день + ночной mode 23:00-07:00.
  Это by design.
- **FB Graph API postинг убит в 2024** — поэтому FB-канал работает через
  Playwright (manual или automated с captured session).
- **Telethon vs aiogram**: TG-юзер аккаунт (Telethon) для постинга в группы,
  bot-API (aiogram) для DM кандидатам и оператору. Сессии Telethon в
  `data/tg_sessions/`, требуют 1.43+ (в requirements.txt запинено).
- **Tunnel URL эфемерный** — пока не на Hetzner, после ребута меняется.
