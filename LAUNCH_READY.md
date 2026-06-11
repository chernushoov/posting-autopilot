# LAUNCH READY — что осталось до живого продукта (обновлено 2026-06-11)

Код готов принимать деньги. Всё, что ниже — конфигурация и инфраструктура, кода больше не требуется.
Состояние кода: trial-гейт работает, plan-лимиты enforced, Stripe checkout/webhook безопасны (fail-closed), CSRF-exempt починен, тенант-изоляция закрыта.

## Шаг 1 — Stripe (≈1 час, нужен аккаунт Алексея)

1. Создать аккаунт stripe.com (Израиль, ILS).
2. Products → создать 3 recurring-цены: Starter ₪299/мес, Pro ₪899/мес, Agency ₪1999/мес.
3. Developers → API keys → взять `sk_live_...` (или `sk_test_...` для прогона).
4. Developers → Webhooks → endpoint `https://<домен>/billing/webhook`, события:
   `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`.
   Взять `whsec_...`.
5. Прописать env (см. шаг 3). Без `STRIPE_WEBHOOK_SECRET` вебхук отвергает всё (fail-closed, так задумано).

## Шаг 2 — VPS (≈0.5 дня)

1. Hetzner CX22 (€4.5/мес) или DO. Docker + docker compose.
2. Домен → A-запись на VPS. Caddy/Traefik для HTTPS (Caddyfile из 3 строк достаточно).
3. `git clone` репо, заполнить `.env.runtime` (шаг 3), `bash scripts/compose_with_runtime.sh up -d --build`.
4. Проверить `/health` и что 6 сервисов поднялись (web, bot, worker, scheduler, postgres, redis).
5. В compose поставить у `bot` `restart: unless-stopped` (сейчас "no" — упавший бот молча останавливает скрининг).

## Шаг 3 — Env-переменные (.env.runtime на VPS)

```
DATABASE_URL=postgresql://ra:ra@postgres:5432/ra
REDIS_URL=redis://redis:6379/0
FLASK_SECRET_KEY=<openssl rand -hex 32>
ADMIN_LOGIN=operator
ADMIN_PASSWORD=<НОВЫЙ! старый засвечен в git-истории>
RECRUITBOT_TELEGRAM_BOT_TOKEN=<токен @AutopillotRecruit_bot>
RECRUITBOT_AI_PROVIDER=openai
RECRUITBOT_AI_API_KEY=<ключ>
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_AGENCY=price_...
SUPPORT_CONTACT_URL=https://wa.me/<номер Алексея>   # кнопка «Связаться» на /pricing
FORCE_HTTPS=1
```

## Шаг 4 — Смоук на проде (15 минут)

1. /register → новый аккаунт → дашборд.
2. Создать вакансию → подключить Telegram (API ID/Hash оператора) → синк групп → кампания → Run now на тестовой группе.
3. Кликнуть тариф → дойти до карты Stripe (тестовая карта 4242…) → вернуться → проверить, что plan_tier записан и лимиты изменились.
4. Прислать боту /start с телефона → пройти анкету → убедиться, что 🔥-лид прилетел.

## Известные границы продукта (продавать честно)

- Постит в Telegram автоматически; Facebook — ассистированный ручной режим. Instagram НЕТ.
- Отклики ловятся через apply-ссылку в посте (личка бота). Ответы «в группе» не собираются.
- «ИИ-скрининг» = анкета по сценарию + AI-скоринг и выжимка в конце. Свободного диалога нет.
- Юзербот-постинг с личного аккаунта — капы стоят, но риск ограничений TG остаётся; не гнать сотни групп с новых аккаунтов.

## Тарифные лимиты (enforced в коде, app/plans.py)

| План | Активные объявления | Каналы |
|---|---|---|
| Trial (14 дн) | 5 | 50 |
| Starter ₪299 | 1 | 10 |
| Pro ₪899 | 5 | 50 |
| Agency ₪1999 | без лимита | без лимита |
