#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ["RECRUITBOT_AI_PROVIDER"] = "stub"
os.environ.pop("RECRUITBOT_AI_API_KEY", None)
os.environ.pop("AI_API_KEY", None)

from common.ai import build_system_prompt, score_candidate
from common.i18n import DEFAULT_QUESTIONS, LANG_MAP, MESSAGES, detect_language, get_questions, t


@dataclass
class DummyCompany:
    ai_tone: str = "professional"
    ai_positive_prompt: str = "Ask only the next screening question."
    ai_negative_prompt: str = "Do not promise a hire."


@dataclass
class DummyVacancy:
    title: str
    interview_questions_json: str = ""


LANGS = ("ru", "he", "en")
FORMAT_CASES = {
    "screening_start": {"title": "Warehouse Worker"},
    "screening_progress": {"current": 1, "total": 3},
    "screening_resume": {"answered": 1, "total": 3},
}

POSITIVE_ANSWERS = {
    "ru": ["Да, есть опыт работы на складе", "Сейчас в Тель-Авиве", "Есть разрешение и могу начать сразу"],
    "he": ["כן, יש לי ניסיון במחסן", "אני נמצא בתל אביב", "יש לי אישור עבודה ואני יכול להתחיל מיד"],
    "en": ["Yes, I have warehouse experience", "I am in Tel Aviv", "I have a work permit and can start immediately"],
}

NEGATIVE_ANSWERS = {
    "ru": ["Нет опыта", "Сейчас далеко", "Нет документов и не готов"],
    "he": ["אין ניסיון", "אני רחוק", "אין לי מסמכים ואני לא זמין"],
    "en": ["No experience", "I am far away", "No documents and not available"],
}


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def assert_message_coverage() -> list[dict]:
    issues = []
    for key, translations in MESSAGES.items():
        for lang in LANGS:
            text = translations.get(lang, "")
            if not text or not text.strip():
                issues.append({"type": "missing_translation", "key": key, "lang": lang})
                continue
            if key in FORMAT_CASES:
                try:
                    _ = text.format(**FORMAT_CASES[key])
                except Exception as exc:
                    issues.append({"type": "format_error", "key": key, "lang": lang, "error": str(exc)})
    return issues


def language_mapping_results() -> list[dict]:
    checks = [
        ("ru", "ru"),
        ("uk", "ru"),
        ("be", "ru"),
        ("he", "he"),
        ("iw", "he"),
        ("en", "en"),
        ("en-US", "en"),
        ("fr", "ru"),
        (None, "ru"),
    ]
    results = []
    for incoming, expected in checks:
        actual = detect_language(incoming)
        results.append({"incoming": incoming, "expected": expected, "actual": actual, "passed": actual == expected})
    return results


def run_language_case(lang: str) -> dict:
    company = DummyCompany()
    prompt = build_system_prompt(company, vacancy_title="Warehouse Worker", lang=lang)
    questions = get_questions(lang)
    positive = score_candidate("Warehouse Worker", questions, POSITIVE_ANSWERS[lang], lang)
    negative = score_candidate("Warehouse Worker", questions, NEGATIVE_ANSWERS[lang], lang)
    custom_questions = json.dumps([f"Custom Q1 {lang}", f"Custom Q2 {lang}"], ensure_ascii=False)
    custom_vacancy = DummyVacancy(title="Warehouse Worker", interview_questions_json=custom_questions)
    custom_loaded = json.loads(custom_vacancy.interview_questions_json)

    return {
        "lang": lang,
        "welcome": t("welcome", lang),
        "language_set": t("language_set", lang),
        "default_questions": questions,
        "custom_questions": custom_loaded,
        "prompt_contains_language": lang in prompt.lower() or {
            "ru": "russian",
            "he": "hebrew",
            "en": "english",
        }[lang] in prompt.lower(),
        "positive_score": positive["score"],
        "negative_score": negative["score"],
        "positive_provider": positive["provider"],
        "negative_provider": negative["provider"],
        "positive_beats_negative": positive["score"] > negative["score"],
    }


def main() -> int:
    out_dir = ROOT_DIR / "ops" / "prelaunch_artifacts" / "multilingual_pilot"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = now_stamp()

    translation_issues = assert_message_coverage()
    lang_map = language_mapping_results()
    cases = [run_language_case(lang) for lang in LANGS]

    overall_ok = (
        not translation_issues
        and all(item["passed"] for item in lang_map)
        and all(item["default_questions"] and len(item["default_questions"]) >= 3 for item in cases)
        and all(item["positive_beats_negative"] for item in cases)
        and all(item["prompt_contains_language"] for item in cases)
    )

    report = {
        "checked_at": stamp,
        "overall_ok": overall_ok,
        "translation_issues": translation_issues,
        "language_map_checks": lang_map,
        "cases": cases,
    }

    json_path = out_dir / f"multilingual_pilot_{stamp}.json"
    latest_path = out_dir / "latest.json"
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    json_path.write_text(text, encoding="utf-8")
    latest_path.write_text(text, encoding="utf-8")
    print(text)
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
