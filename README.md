# Recruit Autopilot Core (Telegram-first)

Это базовый каркас платформы: мульти-компании (profiles), вакансии, источники (телеграм-группы/каналы), кампании постинга, кандидаты, AI-настройки, очередь задач и Telegram-бот.

## Быстрый старт (Docker)

1) Скопируй env:
```bash
cp .env.example .env
# optional: keep real runtime secrets out of .env
cp .env.runtime.example .env.runtime
```

Заполни как минимум:
- `RECRUITBOT_TELEGRAM_BOT_TOKEN` — отдельный токен именно для этого бота
- `.env.runtime` — optional local override file for real runtime secrets
- не используй токен главного MoltBot/OpenClaw бота, иначе получишь polling conflict
- `RECRUITBOT_AI_PROVIDER` / `RECRUITBOT_AI_API_KEY` можно не задавать на старте, если достаточно `stub`

2) Подними:
```bash
docker compose up --build
```

3) Инициализируй БД:
```bash
docker compose exec web python -m scripts.seed
```

4) Открой панель:
- http://localhost:8080
- login/password берутся из `ADMIN_LOGIN` / `ADMIN_PASSWORD`
- значения из `.env.example` подходят только для локального старта и должны быть заменены до пилота

5) Проверь runtime:
```bash
bash scripts/runtime_check_with_env.sh
bash scripts/runtime_check_with_env.sh --json
python3 scripts/runtime_env_status.py --json
python3 scripts/bootstrap_check.py
```

6) Прогони prelaunch front:
```bash
bash scripts/run_prelaunch_front.sh
python3 scripts/final_launch_gate.py
bash scripts/run_launch_release_pack.sh
python3 scripts/live_settings_matrix_probe.py
python3 scripts/multilingual_pilot_check.py
bash scripts/run_detailed_pilot_pack.sh
```

## Архитектура (кратко)
- `web` — Flask + Jinja (панель)
- `bot` — aiogram (кандидаты/интервью/ответы)
- `worker` — RQ worker + scheduler (posting/inbound/interview/digest)
- `postgres` — общая БД
- `redis` — очереди задач

## Что уже есть в каркасе
- Multi-tenant через Company/Profile (изоляция по `company_id`)
- Company switcher в navbar
- CRUD: companies / vacancies / sources / campaigns / candidates
- AI settings (positive/negative prompt + tone/language/templates)
- Job queue интерфейсы (enqueue + примеры задач)
- Telegram bot skeleton: входящий кандидат -> state machine -> сохранение

## Что дальше докручивать (в Meltbot/Claude)
- Реальные интеграции Telegram API для проверки админства/поста в группы
- Реальный AI провайдер (Anthropic/OpenAI/локальная модель)
- Автодискавери групп (каталог источников)
- Платежи/тарифы

## Runtime note
- `web`, `worker`, `scheduler` и `bot` читают сначала `RECRUITBOT_*` переменные окружения
- старые общие `TELEGRAM_BOT_TOKEN` / `AI_PROVIDER` / `AI_API_KEY` остаются как fallback
- runtime precedence now is: exported env / `.env.runtime` / `.env`
- keychain bootstrap helper: `bash scripts/bootstrap_runtime_secrets.sh --help`
- это сделано, чтобы RecruitBot мог жить рядом с основной MoltBot/OpenClaw системой без конфликта секретов
- безопасный порядок запуска и типовые поломки описаны в [RUNTIME_RUNBOOK.md](./RUNTIME_RUNBOOK.md)
- финальная launch-проверка описана в [POSTING_AUTOPILOT_FINAL_VERIFICATION_RUNBOOK.md](./POSTING_AUTOPILOT_FINAL_VERIFICATION_RUNBOOK.md)
- текущий launch verdict зафиксирован в [POSTING_AUTOPILOT_LAUNCH_GATE_STATUS_2026-03-30.md](./POSTING_AUTOPILOT_LAUNCH_GATE_STATUS_2026-03-30.md)
