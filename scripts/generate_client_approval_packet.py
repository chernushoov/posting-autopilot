#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops" / "live_vacancy_4_hires"
INTAKE_PATH = OPS_DIR / "vacancy_intake_template.json"
GENERATED_DIR = OPS_DIR / "generated"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def clean(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def main() -> int:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    intake = load_json(INTAKE_PATH)

    role = clean(intake.get("vacancy_title")) or "[ROLE TITLE]"
    city = clean(intake.get("location", {}).get("city")) or "[CITY]"
    area = clean(intake.get("location", {}).get("area_or_site"))
    pay = clean(intake.get("compensation", {}).get("salary_or_pay")) or "[PAY]"
    schedule = " / ".join(
        part for part in [
            clean(intake.get("schedule", {}).get("shift_type")),
            clean(intake.get("schedule", {}).get("days")),
            clean(intake.get("schedule", {}).get("hours")),
        ] if part
    ) or "[SCHEDULE]"
    reqs = [str(item).strip() for item in intake.get("requirements", {}).get("must_have", []) if str(item).strip()]
    apply_path = clean(intake.get("response_path", {}).get("primary_apply_path")) or "[APPLY PATH]"

    location = city + (f" / {area}" if area else "")
    reqs_text = ", ".join(reqs[:3]) if reqs else "[REQ 1], [REQ 2], [REQ 3]"

    message = (
        "Собрали финальную вакансию для запуска.\n\n"
        "Проверьте, пожалуйста, что всё верно:\n"
        f"- Вакансия: {role}\n"
        f"- Город / локация: {location}\n"
        f"- Оплата: {pay}\n"
        f"- График: {schedule}\n"
        f"- Главные требования: {reqs_text}\n"
        f"- Путь отклика: {apply_path}\n\n"
        "Если всё верно, подтвердите одним сообщением:\n"
        "`Подтверждаю, можно запускать`\n\n"
        "Если нужно исправить, пришлите только конкретные правки.\n"
    )

    packet = (
        "# Client Approval Packet\n\n"
        f"- Role: {role}\n"
        f"- Location: {location}\n"
        f"- Pay: {pay}\n"
        f"- Schedule: {schedule}\n"
        f"- Requirements: {reqs_text}\n"
        f"- Apply path: {apply_path}\n\n"
        "## Message to send\n\n"
        f"{message}"
    )

    (GENERATED_DIR / "client_approval_message.txt").write_text(message, encoding="utf-8")
    (GENERATED_DIR / "client_approval_packet.md").write_text(packet, encoding="utf-8")
    print(str(GENERATED_DIR / "client_approval_packet.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
