#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
INTAKE_PATH = OPS_DIR / "vacancy_intake_template.json"
SCREENING_PACK_PATH = OPS_DIR / "SCREENING_PACK.md"
ROSTER_PATH = OPS_DIR / "first_wave_source_roster.csv"
OUT_DIR = OPS_DIR / "generated"


def load_intake() -> dict:
    with INTAKE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def clean(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def missing_fields(data: dict) -> list[str]:
    checks = {
        "vacancy_title": clean(data.get("vacancy_title")),
        "location.city": clean(data.get("location", {}).get("city")),
        "compensation.salary_or_pay": clean(data.get("compensation", {}).get("salary_or_pay")),
        "schedule.shift_type": clean(data.get("schedule", {}).get("shift_type")),
        "schedule.days": clean(data.get("schedule", {}).get("days")),
        "schedule.hours": clean(data.get("schedule", {}).get("hours")),
        "schedule.start_date_or_urgency": clean(data.get("schedule", {}).get("start_date_or_urgency")),
        "requirements.must_have": clean(data.get("requirements", {}).get("must_have", [])),
        "response_path.primary_apply_path": clean(data.get("response_path", {}).get("primary_apply_path")),
        "recruiter_owner": clean(data.get("recruiter_owner")),
    }
    return [key for key, value in checks.items() if not value]


def build_context(data: dict) -> dict:
    requirements = [str(item).strip() for item in data.get("requirements", {}).get("must_have", []) if str(item).strip()]
    benefits = [str(item).strip() for item in data.get("benefits", []) if str(item).strip()]
    return {
        "client_name": clean(data.get("client_name")) or "[CLIENT NAME]",
        "role": clean(data.get("vacancy_title")) or "[ROLE TITLE]",
        "city": clean(data.get("location", {}).get("city")) or "[CITY]",
        "area": clean(data.get("location", {}).get("area_or_site")),
        "pay": clean(data.get("compensation", {}).get("salary_or_pay")) or "[PAY]",
        "pay_period": clean(data.get("compensation", {}).get("pay_period")),
        "schedule": " / ".join(
            part for part in [
                clean(data.get("schedule", {}).get("shift_type")),
                clean(data.get("schedule", {}).get("days")),
                clean(data.get("schedule", {}).get("hours")),
            ] if part
        ) or "[SCHEDULE]",
        "urgency": clean(data.get("schedule", {}).get("start_date_or_urgency")) or "[URGENCY]",
        "requirements": requirements[:3] or ["[REQ 1]", "[REQ 2]", "[REQ 3]"],
        "benefits": benefits[:2] or ["[BENEFIT 1]", "[BENEFIT 2]"],
        "contact": clean(data.get("response_path", {}).get("primary_apply_path")) or "[APPLY LINK OR CONTACT]",
        "recruiter_owner": clean(data.get("recruiter_owner")) or "[RECRUITER OWNER]",
        "language_requirements": clean(data.get("language_requirements", {}).get("candidate_languages", [])) or "[LANGUAGE REQUIREMENT]",
        "legal": clean(data.get("documents_and_legal", {}).get("work_permit_required")) or "[LEGAL / DOCUMENT REQUIREMENT]",
    }


def read_roster_preview(limit: int = 5) -> list[str]:
    if not ROSTER_PATH.exists():
        return []
    with ROSTER_PATH.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    preview: list[str] = []
    for row in rows:
        source_name = clean(row.get("source_name"))
        status = clean(row.get("status"))
        if not source_name:
            continue
        preview.append(f"- {source_name} [{status or 'unknown'}]")
        if len(preview) >= limit:
            break
    return preview


def read_screening_pack_excerpt() -> str:
    if not SCREENING_PACK_PATH.exists():
        return "- Screening pack file is missing."
    lines = SCREENING_PACK_PATH.read_text(encoding="utf-8").splitlines()
    bullets = [line for line in lines if line.strip().startswith("- ")]
    excerpt = bullets[:7]
    return "\n".join(excerpt) if excerpt else "- Screening pack ready."


def render_posts(ctx: dict) -> dict[str, str]:
    role_line = ctx["role"]
    if ctx["area"]:
        role_line = f"{ctx['role']} | {ctx['city']} / {ctx['area']}"
    else:
        role_line = f"{ctx['role']} | {ctx['city']}"

    requirements = "\n".join(f"- {item}" for item in ctx["requirements"])
    benefits = "\n".join(f"- {item}" for item in ctx["benefits"])

    telegram = (
        f"{role_line}\n\n"
        f"Нужны 4 человека на {ctx['role']}.\n"
        f"Локация: {ctx['city']}" + (f" / {ctx['area']}" if ctx["area"] else "") + "\n"
        f"Оплата: {ctx['pay']}\n"
        f"График: {ctx['schedule']}\n\n"
        f"Требования:\n{requirements}\n\n"
        f"Преимущества:\n{benefits}\n\n"
        f"Старт: {ctx['urgency']}\n"
        f"Отклик: {ctx['contact']}\n"
    )

    facebook = (
        f"Ищем 4 сотрудников на позицию {ctx['role']} в {ctx['city']}" + (f" / {ctx['area']}" if ctx["area"] else "") + ".\n\n"
        f"Что предлагаем:\n"
        f"- Оплата: {ctx['pay']}\n"
        f"- График: {ctx['schedule']}\n"
        f"- Старт: {ctx['urgency']}\n"
        f"- Условия:\n{benefits}\n\n"
        f"Кого ищем:\n{requirements}\n\n"
        f"Отклик: {ctx['contact']}\n"
        f"Нужно закрыть 4 позиции, поэтому быстрый отклик важен.\n"
    )

    compact = (
        f"Нужны 4 человека на {ctx['role']}, {ctx['city']}" + (f" / {ctx['area']}" if ctx["area"] else "") + ".\n"
        f"Оплата: {ctx['pay']}\n"
        f"График: {ctx['schedule']}\n"
        f"Требования: {', '.join(ctx['requirements'])}\n"
        f"Старт: {ctx['urgency']}\n"
        f"Отклик: {ctx['contact']}\n"
    )

    return {
        "telegram_short.txt": telegram,
        "facebook_standard.txt": facebook,
        "facebook_groups_compact.txt": compact,
    }


def render_vacancy_card(ctx: dict) -> str:
    area = f" / {ctx['area']}" if ctx["area"] else ""
    pay = ctx["pay"] + (f" ({ctx['pay_period']})" if ctx["pay_period"] else "")
    requirements = "\n".join(f"- {item}" for item in ctx["requirements"])
    benefits = "\n".join(f"- {item}" for item in ctx["benefits"])
    return (
        "# Final Vacancy Card\n\n"
        f"- Client: {ctx['client_name']}\n"
        f"- Role: {ctx['role']}\n"
        f"- Location: {ctx['city']}{area}\n"
        f"- Pay: {pay}\n"
        f"- Schedule: {ctx['schedule']}\n"
        f"- Urgency: {ctx['urgency']}\n"
        f"- Language requirement: {ctx['language_requirements']}\n"
        f"- Legal / documents: {ctx['legal']}\n"
        f"- Recruiter owner: {ctx['recruiter_owner']}\n"
        f"- Apply path: {ctx['contact']}\n\n"
        "## Must-have requirements\n"
        f"{requirements}\n\n"
        "## Benefits\n"
        f"{benefits}\n"
    )


FIELD_LABELS = {
    "vacancy_title": "Название вакансии / role title",
    "location.city": "Город / location city",
    "compensation.salary_or_pay": "Оплата / salary or pay",
    "schedule.shift_type": "Тип смены / shift type",
    "schedule.days": "Дни работы / working days",
    "schedule.hours": "Часы работы / working hours",
    "schedule.start_date_or_urgency": "Дата старта или срочность / start date or urgency",
    "requirements.must_have": "Ключевые требования / must-have requirements",
    "response_path.primary_apply_path": "Основной путь отклика / primary apply path",
    "recruiter_owner": "Ответственный рекрутер / recruiter owner",
}


def render_missing_fields_message(missing: list[str]) -> str:
    if not missing:
        return "Все критичные поля уже заполнены. Можно переходить к финализации вакансии и запуску первой волны."
    labels = [FIELD_LABELS.get(field, field) for field in missing]
    bullets = "\n".join(f"- {label}" for label in labels)
    return (
        "Нам не хватает нескольких полей, чтобы запустить вакансию без задержек:\n\n"
        f"{bullets}\n\n"
        "Как только пришлёте это, я сразу финализирую тексты и подготовлю запуск."
    )


def render_operator_start_brief(ctx: dict, missing: list[str], roster_preview: list[str]) -> str:
    roster_block = "\n".join(roster_preview) if roster_preview else "- First-wave roster not prepared yet."
    missing_block = "\n".join(f"- {FIELD_LABELS.get(field, field)}" for field in missing) if missing else "- No critical input gaps."
    return (
        "# Operator Start Brief\n\n"
        f"- Role: {ctx['role']}\n"
        f"- City: {ctx['city']}" + (f" / {ctx['area']}" if ctx["area"] else "") + "\n"
        f"- Pay: {ctx['pay']}\n"
        f"- Schedule: {ctx['schedule']}\n"
        f"- Apply path: {ctx['contact']}\n"
        f"- Recruiter owner: {ctx['recruiter_owner']}\n\n"
        "## Missing fields to close first\n"
        f"{missing_block}\n\n"
        "## First-wave source preview\n"
        f"{roster_block}\n"
    )


def render_launch_packet(ctx: dict, posts: dict[str, str], vacancy_card: str, missing_message: str, screening_excerpt: str, roster_preview: list[str]) -> str:
    roster_block = "\n".join(roster_preview) if roster_preview else "- First-wave roster not prepared yet."
    return (
        "# Final Launch Packet\n\n"
        f"{vacancy_card.strip()}\n\n"
        "## Missing fields client message\n"
        f"{missing_message}\n\n"
        "## Telegram Short Post\n"
        f"```text\n{posts['telegram_short.txt'].strip()}\n```\n\n"
        "## Facebook Standard Post\n"
        f"```text\n{posts['facebook_standard.txt'].strip()}\n```\n\n"
        "## Facebook Groups Compact Post\n"
        f"```text\n{posts['facebook_groups_compact.txt'].strip()}\n```\n\n"
        "## Screening Pack Excerpt\n"
        f"{screening_excerpt}\n\n"
        "## First-Wave Source Preview\n"
        f"{roster_block}\n"
    )


def write_outputs(posts: dict[str, str], vacancy_card: str, missing: list[str], missing_message: str, operator_brief: str, launch_packet: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in posts.items():
        (OUT_DIR / name).write_text(content, encoding="utf-8")
    (OUT_DIR / "final_vacancy_card.md").write_text(vacancy_card, encoding="utf-8")
    (OUT_DIR / "missing_fields_message.txt").write_text(missing_message + "\n", encoding="utf-8")
    (OUT_DIR / "operator_start_brief.md").write_text(operator_brief, encoding="utf-8")
    (OUT_DIR / "final_launch_packet.md").write_text(launch_packet, encoding="utf-8")

    readiness = {
        "status": "ready_to_finalize_copy" if not missing else "needs_input",
        "missing_fields": missing,
        "generated_files": sorted([*posts.keys(), "final_vacancy_card.md", "missing_fields_message.txt", "operator_start_brief.md", "final_launch_packet.md"]),
    }
    (OUT_DIR / "launch_readiness.json").write_text(
        json.dumps(readiness, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    data = load_intake()
    missing = missing_fields(data)
    context = build_context(data)
    posts = render_posts(context)
    vacancy_card = render_vacancy_card(context)
    roster_preview = read_roster_preview()
    screening_excerpt = read_screening_pack_excerpt()
    missing_message = render_missing_fields_message(missing)
    operator_brief = render_operator_start_brief(context, missing, roster_preview)
    launch_packet = render_launch_packet(context, posts, vacancy_card, missing_message, screening_excerpt, roster_preview)
    write_outputs(posts, vacancy_card, missing, missing_message, operator_brief, launch_packet)
    status = "READY" if not missing else "NEEDS_INPUT"
    print(f"{status}: generated posting files in {OUT_DIR}")
    if missing:
      print("Missing fields:")
      for field in missing:
          print(f"- {field}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
