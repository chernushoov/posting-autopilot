# CLAUDE_FIX_ALL.md — Posting Autopilot: полный фикс перед пилотом

## КОНТЕКСТ

Ты работаешь в репо `posting-autopilot` (GitHub: chernushoov/posting-autopilot).
Стек: Python 3.11, Flask, SQLAlchemy, PostgreSQL 16, Redis+RQ, aiogram 3.4, Telethon, Docker Compose (6 сервисов: web, bot, worker, scheduler, postgres, redis).
Продакшен доступен через Cloudflare tunnel.
Цель: довести продукт до состояния "первый пилотный клиент может зарегистрироваться, подключить Telegram, создать объявление, запустить постинг и получить горячий лид с телефоном".

## ПРИОРИТЕТ ЗАДАЧ

Выполняй строго по порядку. Каждый блок — отдельный коммит с осмысленным сообщением.

---

### БЛОК 1: AUTH — Единая система входа (КРИТИЧНО)

**Проблема:** Два логина — `/login` (admin, username+password) и `/user-login` (self-service, email+password). Protected routes редиректят на `/login`, но self-service юзеры логинятся через `/user-login`. Результат: после регистрации пользователь не может войти в dashboard.

**Что сделать:**

1. Найди в `app/routes/` все `@login_required` декораторы и роуты `/login`.
2. Объедини логику: `/login` должен принимать И username И email. Или полностью мигрируй на email-based auth.
3. Все `redirect(url_for('login'))` замени на `redirect(url_for('user_login'))` или единый `/login`.
4. Убедись что после успешного логина — redirect на `/dashboard`.
5. Убедись что `/register` создаёт пользователя с `email` + `password_hash` (bcrypt или werkzeug).
6. После регистрации — автоматический логин и redirect на `/dashboard`.

**Проверка:** зарегистрировать нового пользователя → автоматически попадает в dashboard → logout → login по email → dashboard.

```
Коммит: fix: unify auth — single login flow via email, auto-login after register
```

---

### БЛОК 2: SIDEBAR GUARD — Скрыть навигацию для гостей (КРИТИЧНО)

**Проблема:** На страницах `/register`, `/user-login`, `/terms` видна полная sidebar навигация дашборда (Dashboard, Telegram, Facebook, Vacancies...) + кнопка "יציאה" (logout) — даже для неаутентифицированных пользователей.

**Что сделать:**

1. Найди base template (вероятно `app/templates/base.html` или `_layout.html`).
2. Оберни sidebar/nav в проверку: `{% if session.get('is_admin') or session.get('user_id') %}`.
3. Для публичных страниц (landing, register, login, terms, pricing) sidebar НЕ должен рендериться.
4. Кнопку logout показывай только аутентифицированным.

**Проверка:** открой `/register` в incognito — sidebar не виден, только форма.

```
Коммит: fix: hide sidebar navigation for unauthenticated users
```

---

### БЛОК 3: i18n — Языки на ВСЕХ страницах (КРИТИЧНО)

**Проблема:** Landing переведён на 3 языка (HE/RU/EN). Но register, user-login, pricing, terms — смесь EN и HE.

**Что сделать:**

1. Найди `common/i18n.py` — там ~150+ ключей в словаре `UI`.
2. Добавь недостающие ключи для register, login, pricing FAQ, terms — все 3 языка (HE/RU/EN).
3. В шаблонах замени хардкод текст на `{{ ui('key') }}`.
4. Sidebar навигация тоже должна использовать i18n (ключи `nav_dashboard`, `nav_listings`, `nav_leads` и т.д.).

**Проверка:** переключи на RU → зайди на register, pricing, login — всё на русском.

```
Коммит: feat: full i18n coverage for register, login, pricing, terms, sidebar
```

---

### БЛОК 4: ТЕРМИНОЛОГИЯ — "Универсальный" вместо "Рекрутинг" (КРИТИЧНО)

**Проблема:** Landing продаёт универсальный продукт (авто, квартиры, услуги). Но dashboard использует рекрутинговую терминологию: "משרה" (vacancy), "מועמדים" (candidates).

**Что сделать:**

1. **В UI (templates + i18n):** замени:
   - "Vacancy" / "משרה" / "Вакансия" → "Listing" / "מודעה" / "Объявление"
   - "Candidate" / "מועמד" / "Кандидат" → "Lead" / "ליד" / "Лид"
2. **В URL-роутах** — алиасы для обратной совместимости: `/vacancies/` → redirect на `/listings/`
3. **НЕ переименовывай таблицы/колонки в БД** — только UI-слой.

```
Коммит: refactor: universal terminology — listings/leads instead of vacancies/candidates
```

---

### БЛОК 5: DEMO секция на Landing (ВАЖНО)

**Проблема:** Кнопка "Смотреть демо" ведёт на `#demo` — якорь не существует.

**Что сделать:**

1. Добавь `<section id="demo">` с анимированным чат-примером бота на 3 языках.
2. Покажи реалистичный диалог: пользователь пишет → бот задаёт вопросы → собирает телефон → уведомление "🔥 HOT LEAD".

```
Коммит: feat: add interactive demo chat section on landing page
```

---

### БЛОК 6: TELETHON POSTING — campaign_tick (БЛОКЕР)

**Проблема:** Telethon auth+sync работают. Но `campaign_tick` в `worker/tasks.py` не отправляет реальные сообщения.

**Что сделать:**

1. В `worker/tasks.py` — `campaign_tick()`: для каждого source в кампании вызови `post_to_group()` из `common/tg_client.py`.
2. `post_to_group()` уже реализован с anti-spam (задержки 3-10 мин, rate limit 10/час, 50/день, ночной режим, FloodWait обработка).
3. Убедись что `campaign_tick` получает `api_id` и `api_hash` из Company model.
4. Обнови статус PostingAttempt после каждой отправки.

**Проверка:** запусти кампанию → worker постит в TG группу → PostingAttempt логируется.

```
Коммит: feat: wire Telethon posting into campaign_tick
```

---

### БЛОК 7: PHONE COLLECTION в боте (ВАЖНО)

**Проблема:** Бот должен собирать телефон лида после скрининга.

**Что сделать:**

1. В `bot/run_bot.py` после скрининговых вопросов — добавь шаг "Отправьте телефон".
2. Обработай текст с номером и `content_type=CONTACT`.
3. Сохрани в `Candidate.phone` (добавь поле через schema.py если нет).

```
Коммит: feat: phone collection in bot — text and contact share
```

---

### БЛОК 8: HOT LEAD NOTIFICATION (ВАЖНО)

**Проблема:** HOT лид должен мгновенно уведомлять владельца бизнеса.

**Что сделать:**

1. После классификации HOT — отправить TG-сообщение владельцу с именем, телефоном, WhatsApp линком.
2. Добавь поле `owner_telegram_id` в Company model.
3. В дашборде профиля — поле "Telegram ID для уведомлений".

```
Коммит: feat: instant Telegram notification to business owner on HOT lead
```

---

### БЛОК 9: МЕЛКИЕ ФИКСЫ

1. Redirect `/login` → `/user-login` если оба существуют.
2. Pricing "כניסה" link → на правильный login.
3. CSRF protection во все формы.
4. Meta tags: og:title, og:description для шаринга.
5. Все URL — HTTPS.

```
Коммит: fix: misc — redirect cleanup, CSRF, meta tags
```

---

## ПОРЯДОК ВЫПОЛНЕНИЯ

```
1. БЛОК 2 (sidebar guard)     — минимальный риск
2. БЛОК 1 (auth unification)  — критический путь
3. БЛОК 3 (i18n)              — качество
4. БЛОК 4 (терминология)      — messaging fix
5. БЛОК 9 (мелочи)            — cleanup
6. БЛОК 5 (demo секция)       — конверсия
7. БЛОК 6 (Telethon posting)  — core feature
8. БЛОК 7 (phone collection)  — core feature
9. БЛОК 8 (HOT notification)  — core feature
```

## ПРАВИЛА

- Один блок = один коммит. Не смешивай.
- После каждого блока — `docker compose up --build` и smoke test.
- НЕ трогай структуру БД без миграции. Новые колонки — через `app/schema.py` (`_ensure_columns`).
- НЕ трогай `.env`, секреты, Telethon session strings.
- Все тексты — через i18n систему (`common/i18n.py`), никакого хардкода.
- Тестируй в трёх языках: HE, RU, EN.

## SMOKE TEST ПОСЛЕ ВСЕХ БЛОКОВ

```
1. Открой landing (/) в RU → всё на русском
2. Нажми "Начать" → register на русском, без sidebar
3. Зарегистрируйся → автоматический вход → dashboard
4. Sidebar на русском: Панель, Объявления, Лиды, Telegram...
5. Подключи Telegram → success
6. Создай объявление (listing) → сохранено
7. Создай кампанию → запусти
8. Worker постит в TG группу
9. Кто-то пишет боту → бот ведёт скрининг → собирает телефон
10. Лид HOT → владелец получает TG уведомление с телефоном
11. Logout → login по email → dashboard
```
