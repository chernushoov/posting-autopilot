# TASK — выкатить аудит-фиксы бэкенда (от MacBook, 2026-06-15)

Ветка УЖЕ локально: `fix/backend-audit-hardening` (head aa0caf6, запушена на origin).
Содержит фикс всех 71 находок аудита (3 CRITICAL / 16 HIGH / 29 MEDIUM), 9 коммитов по подсистемам.

## Шаги
1. `git checkout fix/backend-audit-hardening`
2. Прогнать: `python -m compileall app common worker bot` + `scripts/test_phase{1,2,3}.py`
   (ожидаемые ПРЕДнаследованные падения, НЕ регрессии: Postgres-only information_schema, landing /register).
3. Смержить в боевую (рекомендация: `main`, НЕ в `fix/double-click-post-guard` — там живой WIP landing.html).
4. ⚠️ ПЕРЕД деплоем убедиться, что на VPS в .env.prod есть:
   - `FLASK_SECRET_KEY=<сильный рандом>`  ← КРИТИЧНО: фикс C1 теперь ЖЁСТКО падает на старте без него
   - `OUTREACH_PHYSICAL_ADDRESS=...`, `OUTREACH_SENDER_IDENTITY=...`  (CAN-SPAM)
   Сгенерить ключ: python -c "import secrets;print(secrets.token_urlsafe(48))"
5. Деплой: Hetzner root@167.233.98.210 через git archive + rebuild, APP_ENV_FILE=.env.prod.
6. Проверить /health=200, что worker+scheduler поднялись. При фейле — откат.
7. Отчитаться: что смержено/задеплоено + health.

## НЕ делать
- НЕ мержить в fix/double-click-post-guard (затрёт незакоммиченный landing.html).
- НЕ деплоить, пока FLASK_SECRET_KEY не в .env.prod (иначе мгновенный краш старта).
