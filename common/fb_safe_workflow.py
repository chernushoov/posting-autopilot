from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import or_

from app.config import Config
from app.models import (
    Company,
    FacebookGroup,
    FacebookGroupSource,
    FacebookGroupSourceType,
    FacebookGroupStatus,
    FacebookGroupVerificationStatus,
    FacebookPostGenerationSource,
    FacebookPostLengthMode,
    FacebookPostTone,
    FacebookPostVariant,
    FacebookPostVariantStatus,
    FacebookPostingQueueItem,
    FacebookPostingQueueItemStatus,
    FacebookPostingResult,
    FacebookPostingResultStatus,
    FacebookPostingRun,
    FacebookPostingRunStatus,
    Language,
    Vacancy,
)

PROMPT_VERSION = "fb_safe_workflow_v1"

BASE_SYSTEM_PROMPT = """You write Hebrew Facebook job posts for Israeli recruiters.

Your job is to turn one vacancy into one clear, high-converting, compliance-safe Facebook group post.

Rules:
1. Write in natural modern Hebrew.
2. Keep the post suitable for manual posting in Facebook groups.
3. Mention the role, location, and key offer clearly.
4. Use a strong first line that works in feed preview.
5. Keep the structure easy to scan on mobile.
6. Do not invent facts that are not in the input.
7. Do not mention the client company unless allow_company_name=true.
8. Do not promise guaranteed salary, visa, relocation, or conditions not provided.
9. Do not use manipulative or spammy claims.
10. Do not output hashtags unless explicitly requested.
11. Do not output Markdown code fences.
12. Return exactly the requested JSON structure."""

STYLE_ADDONS = {
    FacebookPostTone.professional: "Write in polished recruiter Hebrew. Keep the structure clean and credible.",
    FacebookPostTone.casual: "Write in friendly everyday Hebrew. Keep the post easy to scan and human.",
    FacebookPostTone.urgent: "Write in direct urgent Hebrew. Open with immediate hiring energy.",
}

LENGTH_TARGETS: dict[FacebookPostLengthMode, tuple[int, int]] = {
    FacebookPostLengthMode.short: (160, 260),
    FacebookPostLengthMode.medium: (260, 420),
    FacebookPostLengthMode.long: (420, 560),
}

ALLOWED_CTA_MODES = {"dm_cv", "comment_interested", "whatsapp", "apply_link"}


def _enum_value(value: Any) -> str:
    return getattr(value, "value", str(value))


def humanize_status(value: str | None) -> str:
    if not value:
        return "-"
    return value.replace("_", " ").capitalize()


def humanize_datetime(value: datetime | None, now: datetime | None = None) -> str:
    if not value:
        return "never"
    now = now or datetime.utcnow()
    delta = now - value
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    if seconds < 604800:
        return f"{seconds // 86400}d ago"
    return value.strftime("%Y-%m-%d")


def summarize_text(value: str | None, limit: int = 120) -> str | None:
    text = normalize_whitespace(value)
    if not text:
        return None
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def build_group_warning_chips(group: FacebookGroup, now: datetime | None = None) -> list[str]:
    now = now or datetime.utcnow()
    chips: list[str] = []
    if group.last_posted_at:
        age = now - group.last_posted_at
        if age <= timedelta(hours=24):
            chips.append("recently posted here")
        elif age <= timedelta(days=3):
            chips.append("repost risk")
    if group.requires_admin_approval:
        chips.append("approval likely")
    if group.activity_rating is not None and group.activity_rating <= 2:
        chips.append("low activity")
    return chips


def normalize_whitespace(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def parse_bool(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def parse_optional_date(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    return datetime.fromisoformat(text)


def parse_tags(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [normalize_whitespace(str(item)) for item in value if normalize_whitespace(str(item))]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("["):
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [normalize_whitespace(str(item)) for item in parsed if normalize_whitespace(str(item))]
    raw_parts = re.split(r"[|,]", text)
    return [normalize_whitespace(part) for part in raw_parts if normalize_whitespace(part)]


def normalize_facebook_url(url: str) -> str:
    raw = normalize_whitespace(url)
    if not raw:
        raise ValueError("facebook_url is required")
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    if "facebook.com" not in parsed.netloc.lower():
        raise ValueError("facebook_url must be a Facebook URL")
    netloc = parsed.netloc.lower()
    for prefix in ("m.", "mobile.", "mbasic."):
        if netloc.startswith(prefix):
            netloc = netloc[len(prefix):]
    if not netloc.startswith("www."):
        netloc = f"www.{netloc}"
    path = re.sub(r"/+", "/", parsed.path or "/").rstrip("/")
    if not path:
        path = "/"
    return f"https://{netloc}{path}"


def extract_facebook_slug(normalized_url: str) -> str | None:
    parsed = urlparse(normalized_url)
    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        return None
    if len(parts) >= 2 and parts[0] == "groups":
        return parts[1]
    return parts[-1]


def build_fb_prompt_payload(company: Company, vacancy: Vacancy, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    tone = FacebookPostTone(payload.get("tone", FacebookPostTone.professional))
    length_mode = FacebookPostLengthMode(payload.get("length_mode", FacebookPostLengthMode.medium))
    cta_mode = payload.get("cta_mode") or "dm_cv"
    if cta_mode not in ALLOWED_CTA_MODES:
        cta_mode = "dm_cv"
    requirements = payload.get("requirements")
    if not isinstance(requirements, list):
        requirements = []
    benefits = payload.get("benefits")
    if not isinstance(benefits, list):
        benefits = []

    return {
        "vacancy_title": normalize_whitespace(payload.get("vacancy_title") or vacancy.title),
        "vacancy_body": normalize_whitespace(payload.get("vacancy_body") or vacancy.body),
        "city": normalize_whitespace(payload.get("city") or vacancy.city),
        "salary_hint": normalize_whitespace(payload.get("salary_hint")),
        "employment_type": normalize_whitespace(payload.get("employment_type")),
        "requirements": [normalize_whitespace(item) for item in requirements if normalize_whitespace(item)],
        "benefits": [normalize_whitespace(item) for item in benefits if normalize_whitespace(item)],
        "cta_mode": cta_mode,
        "cta_value": normalize_whitespace(payload.get("cta_value")),
        "tone": tone.value,
        "length_mode": length_mode.value,
        "allow_company_name": parse_bool(payload.get("allow_company_name"), default=False),
        "company_name": normalize_whitespace(payload.get("company_name") or company.name),
        "notes": normalize_whitespace(payload.get("notes")),
        "language_code": "he",
    }


def build_generation_prompt(prompt_payload: dict[str, Any]) -> dict[str, str]:
    tone = FacebookPostTone(prompt_payload["tone"])
    user_prompt = (
        "Generate one Hebrew Facebook job post.\n\n"
        f"Use:\n- tone={prompt_payload['tone']}\n- length_mode={prompt_payload['length_mode']}\n"
        f"- cta_mode={prompt_payload['cta_mode']}\n\nVacancy input:\n"
        f"{json.dumps(prompt_payload, ensure_ascii=False, indent=2)}"
    )
    return {
        "system_prompt": BASE_SYSTEM_PROMPT,
        "style_addon": STYLE_ADDONS[tone],
        "user_prompt": user_prompt,
    }


def _build_cta(cta_mode: str, cta_value: str | None) -> str:
    if cta_mode == "comment_interested":
        return 'מעוניינים? כתבו "מעוניין/ת" בתגובות ונחזור אליכם.'
    if cta_mode == "whatsapp" and cta_value:
        return f"לשליחת פרטים או קורות חיים אפשר לפנות בוואטסאפ: {cta_value}"
    if cta_mode == "apply_link" and cta_value:
        return f"להגשת מועמדות: {cta_value}"
    return "לשליחת קורות חיים אפשר לפנות בפרטי."


def _title_with_prefix(title: str) -> str:
    stripped = normalize_whitespace(title)
    if stripped.startswith("ל"):
        return stripped
    return f"ל{stripped}"


def _truncate_sentence(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    truncated = text[: max_chars - 1].rsplit(" ", 1)[0].rstrip(" ,.-")
    return f"{truncated}."


def _compose_stub_post(prompt_payload: dict[str, Any]) -> dict[str, Any]:
    tone = FacebookPostTone(prompt_payload["tone"])
    length_mode = FacebookPostLengthMode(prompt_payload["length_mode"])
    title = prompt_payload["vacancy_title"]
    city = prompt_payload["city"]
    salary_hint = prompt_payload["salary_hint"]
    employment_type = prompt_payload["employment_type"]
    requirements = prompt_payload["requirements"][:5]
    benefits = prompt_payload["benefits"][:3]
    vacancy_body = prompt_payload["vacancy_body"]
    cta = _build_cta(prompt_payload["cta_mode"], prompt_payload.get("cta_value"))

    location_text = f" ב{city}" if city else ""
    if tone == FacebookPostTone.professional:
        headline = f"מגייסים {title}{location_text}"
        intro = f"דרוש/ה {_title_with_prefix(title)}{location_text}."
    elif tone == FacebookPostTone.casual:
        headline = f"מחפשים {title}{location_text}"
        intro = f"מחפשים {_title_with_prefix(title)}{location_text}."
    else:
        headline = f"גיוס מיידי{location_text}" if city else f"גיוס מיידי ל{title}"
        intro = f"מחפשים {_title_with_prefix(title)}{location_text} להתחלה מהירה."

    details: list[str] = [intro]
    if employment_type:
        details.append(f"מדובר ב{employment_type}.")

    if requirements:
        req_count = 2 if length_mode == FacebookPostLengthMode.short else 3
        req_text = ", ".join(requirements[:req_count])
        details.append(f"מתאים למועמדים עם ניסיון ב{req_text}.")

    if salary_hint:
        details.append(f"טווח ההצעה: {salary_hint}.")

    if benefits and length_mode != FacebookPostLengthMode.short:
        details.append(f"יתרונות בולטים: {', '.join(benefits[:2])}.")

    if vacancy_body and length_mode == FacebookPostLengthMode.long:
        details.append(_truncate_sentence(vacancy_body, 120))

    body = " ".join(details)
    if tone == FacebookPostTone.urgent and len(body) > 260:
        body = _truncate_sentence(body, 220)
    if tone == FacebookPostTone.casual:
        body = body.replace("מועמדים", "אנשים")

    full_post = f"{headline}\n\n{body}\n\n{cta}"
    min_chars, max_chars = LENGTH_TARGETS[length_mode]
    if len(full_post) > max_chars:
        overflow = len(full_post) - max_chars
        body = _truncate_sentence(body, max(80, len(body) - overflow - 10))
        full_post = f"{headline}\n\n{body}\n\n{cta}"

    warnings = []
    if prompt_payload.get("company_name") and not prompt_payload.get("allow_company_name"):
        warnings.append("company_name_hidden")
    if len(full_post) < min_chars:
        warnings.append("below_target_length")
    if len(full_post) > max_chars:
        warnings.append("above_target_length")

    return {
        "headline": headline,
        "body": body,
        "cta": cta,
        "full_post": full_post,
        "character_count": len(full_post),
        "warnings": warnings,
    }


def generate_hebrew_post(company: Company, vacancy: Vacancy, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    prompt_payload = build_fb_prompt_payload(company=company, vacancy=vacancy, payload=payload)
    prompt_bundle = build_generation_prompt(prompt_payload)
    result = _compose_stub_post(prompt_payload)
    provider = Config.AI_PROVIDER or "stub"
    meta_warnings = list(result["warnings"])
    if provider != "stub":
        meta_warnings.append("provider_not_connected_in_repo_using_stub_generation")
    return {
        "prompt_payload": prompt_payload,
        "prompt_bundle": prompt_bundle,
        "prompt_version": PROMPT_VERSION,
        "provider": provider,
        "output": {**result, "warnings": meta_warnings},
    }


def _variant_label(tone: FacebookPostTone, length_mode: FacebookPostLengthMode) -> str:
    return f"{tone.value}_{length_mode.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"


def save_post_variant(
    db,
    *,
    company_id: int,
    vacancy_id: int,
    actor_id: str,
    generation_payload: dict[str, Any],
    generated_output: dict[str, Any],
    status: FacebookPostVariantStatus = FacebookPostVariantStatus.draft,
    notes: str | None = None,
) -> FacebookPostVariant:
    tone = FacebookPostTone(generation_payload["tone"])
    length_mode = FacebookPostLengthMode(generation_payload["length_mode"])
    variant = FacebookPostVariant(
        company_id=company_id,
        vacancy_id=vacancy_id,
        variant_label=_variant_label(tone, length_mode),
        tone=tone,
        length_mode=length_mode,
        language_code="he",
        headline=generated_output.get("headline"),
        cta_text=generated_output.get("cta"),
        full_text=generated_output["full_post"],
        char_count=generated_output.get("character_count"),
        status=status,
        generation_source=FacebookPostGenerationSource.ai,
        prompt_version=PROMPT_VERSION,
        input_payload_json=json.dumps(generation_payload, ensure_ascii=False),
        notes=notes,
    )
    if status == FacebookPostVariantStatus.approved:
        variant.approved_at = datetime.utcnow()
        variant.approved_by = actor_id
    db.add(variant)
    db.flush()
    return variant


def approve_post_variant(
    variant: FacebookPostVariant,
    *,
    actor_id: str,
    full_text: str | None = None,
    headline: str | None = None,
    cta_text: str | None = None,
    notes: str | None = None,
) -> FacebookPostVariant:
    original_full_text = variant.full_text
    if full_text:
        variant.full_text = full_text.strip()
    if headline is not None:
        variant.headline = normalize_whitespace(headline) or None
    if cta_text is not None:
        variant.cta_text = normalize_whitespace(cta_text) or None
    if notes is not None:
        variant.notes = notes.strip() or None
    variant.char_count = len(variant.full_text or "")
    if variant.full_text != original_full_text:
        variant.edited_by_user = True
        if variant.generation_source == FacebookPostGenerationSource.ai:
            variant.generation_source = FacebookPostGenerationSource.ai_then_edited
    variant.status = FacebookPostVariantStatus.approved
    variant.approved_at = datetime.utcnow()
    variant.approved_by = actor_id
    return variant


def _serialize_group(group: FacebookGroup) -> dict[str, Any]:
    return {
        "id": group.id,
        "name": group.name,
        "facebook_url": group.facebook_url,
        "facebook_url_normalized": group.facebook_url_normalized,
        "facebook_slug": group.facebook_slug,
        "primary_category": group.primary_category,
        "secondary_tags": json.loads(group.secondary_tags_json or "[]"),
        "country_code": group.country_code,
        "language_code": group.language_code,
        "city": group.city,
        "region": group.region,
        "audience_type": group.audience_type,
        "member_count_estimate": group.member_count_estimate,
        "activity_rating": group.activity_rating,
        "posting_rules_summary": group.posting_rules_summary,
        "requires_membership": group.requires_membership,
        "requires_admin_approval": group.requires_admin_approval,
        "performance_score": group.performance_score,
        "status": _enum_value(group.status),
        "is_active": group.is_active,
        "last_verified_at": group.last_verified_at.isoformat() if group.last_verified_at else None,
        "last_posted_at": group.last_posted_at.isoformat() if group.last_posted_at else None,
        "last_verified_label": humanize_datetime(group.last_verified_at),
        "last_posted_label": humanize_datetime(group.last_posted_at),
        "warning_chips": build_group_warning_chips(group),
        "notes": group.notes,
    }


def serialize_post_variant(variant: FacebookPostVariant) -> dict[str, Any]:
    return {
        "id": variant.id,
        "vacancy_id": variant.vacancy_id,
        "variant_label": variant.variant_label,
        "tone": _enum_value(variant.tone),
        "length_mode": _enum_value(variant.length_mode),
        "headline": variant.headline,
        "cta_text": variant.cta_text,
        "full_text": variant.full_text,
        "char_count": variant.char_count,
        "status": _enum_value(variant.status),
        "generation_source": _enum_value(variant.generation_source),
        "prompt_version": variant.prompt_version,
        "edited_by_user": variant.edited_by_user,
        "approved_at": variant.approved_at.isoformat() if variant.approved_at else None,
        "approved_at_label": humanize_datetime(variant.approved_at),
        "approved_by": variant.approved_by,
        "notes": variant.notes,
        "created_at": variant.created_at.isoformat() if variant.created_at else None,
        "created_at_label": humanize_datetime(variant.created_at),
    }


def serialize_posting_run(run: FacebookPostingRun) -> dict[str, Any]:
    queue_items = []
    counts = {"total": 0, "posted": 0, "skipped": 0, "pending": 0, "current": 0, "opened": 0, "failed": 0}
    latest_signal: dict[str, Any] | None = None
    for item in sorted(run.queue_items, key=lambda row: row.position):
        counts["total"] += 1
        counts[_enum_value(item.status)] += 1
        result_payload = serialize_posting_result(item.result) if item.result else None
        signal_dt = None
        signal_label = None
        signal_note = None
        if result_payload:
            signal_dt = item.result.updated_at
            signal_label = humanize_status(result_payload["result_status"])
            signal_note = summarize_text(result_payload.get("result_note") or result_payload.get("owner_note"))
        elif item.group_note:
            signal_dt = item.posted_at or item.skipped_at or item.opened_at or item.created_at
            signal_label = humanize_status(item.status.value if hasattr(item.status, "value") else str(item.status))
            signal_note = summarize_text(item.group_note)
        if signal_dt and (
            latest_signal is None or signal_dt > latest_signal["sort_dt"]
        ):
            latest_signal = {
                "status": result_payload["result_status"] if result_payload else _enum_value(item.status),
                "label": signal_label,
                "note": signal_note,
                "updated_at": _iso_or_none(signal_dt),
                "updated_label": humanize_datetime(signal_dt),
                "sort_dt": signal_dt,
            }
        queue_items.append(
            {
                "id": item.id,
                "group_id": item.group_id,
                "position": item.position,
                "status": _enum_value(item.status),
                "status_label": humanize_status(_enum_value(item.status)),
                "opened_at": item.opened_at.isoformat() if item.opened_at else None,
                "copied_at": item.copied_at.isoformat() if item.copied_at else None,
                "posted_at": item.posted_at.isoformat() if item.posted_at else None,
                "skipped_at": item.skipped_at.isoformat() if item.skipped_at else None,
                "opened_at_label": humanize_datetime(item.opened_at),
                "posted_at_label": humanize_datetime(item.posted_at),
                "skipped_at_label": humanize_datetime(item.skipped_at),
                "completed_by": item.completed_by,
                "skip_reason": item.skip_reason,
                "group_note": item.group_note,
                "post_url_manual": item.post_url_manual,
                "group": _serialize_group(item.group),
                "result": result_payload,
            }
        )
    active_count = counts["pending"] + counts["current"] + counts["opened"]
    return {
        "id": run.id,
        "vacancy_id": run.vacancy_id,
        "post_variant_id": run.post_variant_id,
        "name": run.name,
        "status": _enum_value(run.status),
        "status_label": humanize_status(_enum_value(run.status)),
        "group_count": run.group_count,
        "created_by": run.created_by,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "last_action_at": run.last_action_at.isoformat() if run.last_action_at else None,
        "created_at_label": humanize_datetime(run.created_at),
        "started_at_label": humanize_datetime(run.started_at),
        "completed_at_label": humanize_datetime(run.completed_at),
        "last_action_at_label": humanize_datetime(run.last_action_at or run.created_at),
        "notes": run.notes,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "post_variant": serialize_post_variant(run.post_variant),
        "counts": counts,
        "attention_label": "Needs attention" if active_count else "Run complete",
        "latest_signal": {key: value for key, value in latest_signal.items() if key != "sort_dt"} if latest_signal else None,
        "queue_items": queue_items,
    }


def _iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def serialize_posting_result(result: FacebookPostingResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "queue_item_id": result.queue_item_id,
        "result_status": _enum_value(result.result_status),
        "result_status_label": humanize_status(_enum_value(result.result_status)),
        "response_count": result.response_count,
        "cv_count": result.cv_count,
        "interview_count": result.interview_count,
        "hire_count": result.hire_count,
        "quality_score": result.quality_score,
        "last_checked_at": result.last_checked_at.isoformat() if result.last_checked_at else None,
        "last_checked_at_label": humanize_datetime(result.last_checked_at),
        "owner_note": result.owner_note,
        "result_note": result.result_note,
        "updated_by": result.updated_by,
        "updated_at": result.updated_at.isoformat() if result.updated_at else None,
        "updated_at_label": humanize_datetime(result.updated_at),
    }


def build_vacancy_fb_continuity_map(db, company_id: int, vacancy_ids: list[int]) -> dict[int, dict[str, Any]]:
    if not vacancy_ids:
        return {}

    variants = (
        db.query(FacebookPostVariant)
        .filter(FacebookPostVariant.company_id == company_id, FacebookPostVariant.vacancy_id.in_(vacancy_ids))
        .order_by(FacebookPostVariant.vacancy_id.asc(), FacebookPostVariant.created_at.desc(), FacebookPostVariant.id.desc())
        .all()
    )
    runs = (
        db.query(FacebookPostingRun)
        .filter(FacebookPostingRun.company_id == company_id, FacebookPostingRun.vacancy_id.in_(vacancy_ids))
        .order_by(FacebookPostingRun.vacancy_id.asc(), FacebookPostingRun.created_at.desc(), FacebookPostingRun.id.desc())
        .all()
    )

    variants_by_vacancy: dict[int, list[FacebookPostVariant]] = {vacancy_id: [] for vacancy_id in vacancy_ids}
    for variant in variants:
        variants_by_vacancy.setdefault(variant.vacancy_id, []).append(variant)

    runs_by_vacancy: dict[int, list[FacebookPostingRun]] = {vacancy_id: [] for vacancy_id in vacancy_ids}
    for run in runs:
        runs_by_vacancy.setdefault(run.vacancy_id, []).append(run)

    latest_run_ids = [run_list[0].id for run_list in runs_by_vacancy.values() if run_list]
    queue_counts_by_run: dict[int, dict[str, int]] = {}
    queue_items_by_run: dict[int, list[FacebookPostingQueueItem]] = {}
    if latest_run_ids:
        queue_items = (
            db.query(FacebookPostingQueueItem)
            .filter(FacebookPostingQueueItem.run_id.in_(latest_run_ids))
            .order_by(FacebookPostingQueueItem.run_id.asc(), FacebookPostingQueueItem.position.asc())
            .all()
        )
        for item in queue_items:
            bucket = queue_counts_by_run.setdefault(
                item.run_id,
                {"total": 0, "posted": 0, "skipped": 0, "pending": 0, "current": 0, "opened": 0, "failed": 0},
            )
            bucket["total"] += 1
            bucket[_enum_value(item.status)] += 1
            queue_items_by_run.setdefault(item.run_id, []).append(item)

    latest_result_by_run: dict[int, dict[str, Any]] = {}
    if latest_run_ids:
        latest_results = (
            db.query(FacebookPostingResult, FacebookPostingQueueItem.run_id)
            .join(FacebookPostingQueueItem, FacebookPostingResult.queue_item_id == FacebookPostingQueueItem.id)
            .filter(FacebookPostingQueueItem.run_id.in_(latest_run_ids))
            .order_by(FacebookPostingQueueItem.run_id.asc(), FacebookPostingResult.updated_at.desc())
            .all()
        )
        for result, run_id in latest_results:
            if run_id in latest_result_by_run:
                continue
            latest_result_by_run[run_id] = {
                "status": _enum_value(result.result_status),
                "label": humanize_status(_enum_value(result.result_status)),
                "updated_at": _iso_or_none(result.updated_at),
                "updated_label": humanize_datetime(result.updated_at),
                "note": summarize_text(result.result_note or result.owner_note),
            }

    continuity_map: dict[int, dict[str, Any]] = {}
    unfinished_statuses = {
        FacebookPostingRunStatus.draft,
        FacebookPostingRunStatus.ready,
        FacebookPostingRunStatus.in_progress,
    }

    for vacancy_id in vacancy_ids:
        vacancy_variants = variants_by_vacancy.get(vacancy_id, [])
        vacancy_runs = runs_by_vacancy.get(vacancy_id, [])
        latest_variant = vacancy_variants[0] if vacancy_variants else None
        latest_approved_variant = next(
            (variant for variant in vacancy_variants if variant.status == FacebookPostVariantStatus.approved),
            None,
        )
        latest_run = vacancy_runs[0] if vacancy_runs else None
        unfinished_run = next((run for run in vacancy_runs if run.status in unfinished_statuses), None)
        queue_counts = queue_counts_by_run.get(latest_run.id if latest_run else -1, {})
        latest_result = latest_result_by_run.get(latest_run.id if latest_run else -1)
        latest_queue_items = queue_items_by_run.get(latest_run.id if latest_run else -1, [])
        active_count = (queue_counts.get("pending", 0) + queue_counts.get("current", 0) + queue_counts.get("opened", 0))
        latest_note = None
        for item in latest_queue_items:
            latest_note = summarize_text(item.group_note or item.skip_reason)
            if latest_note:
                break

        if unfinished_run and unfinished_run.status == FacebookPostingRunStatus.in_progress:
            status_key = "run_in_progress"
            status_label = "Run in progress"
        elif unfinished_run:
            status_key = "action_needed"
            status_label = "Action needed"
        elif latest_run and latest_run.status == FacebookPostingRunStatus.completed:
            status_key = "last_run_completed"
            status_label = "Last run completed"
        elif latest_approved_variant:
            status_key = "approved_variant_ready"
            status_label = "Approved variant ready"
        elif latest_variant:
            status_key = "draft_generated"
            status_label = "Draft generated"
        else:
            status_key = "no_fb_flow"
            status_label = "No FB flow started"

        continuity_map[vacancy_id] = {
            "status_key": status_key,
            "status_label": status_label,
            "latest_variant": serialize_post_variant(latest_variant) if latest_variant else None,
            "latest_approved_variant": serialize_post_variant(latest_approved_variant) if latest_approved_variant else None,
            "latest_run": {
                "id": latest_run.id,
                "status": _enum_value(latest_run.status),
                "group_count": latest_run.group_count,
                "created_at": _iso_or_none(latest_run.created_at),
                "last_action_at": _iso_or_none(latest_run.last_action_at),
                "started_at": _iso_or_none(latest_run.started_at),
                "completed_at": _iso_or_none(latest_run.completed_at),
                "created_at_label": humanize_datetime(latest_run.created_at),
                "last_action_at_label": humanize_datetime(latest_run.last_action_at or latest_run.created_at),
                "completed_at_label": humanize_datetime(latest_run.completed_at),
                "counts": queue_counts,
                "attention_label": "Needs attention" if active_count else "Complete",
                "attention_key": "needs_attention" if active_count else "complete",
                "latest_signal": latest_result,
                "latest_note": latest_result["note"] if latest_result and latest_result.get("note") else latest_note,
            }
            if latest_run
            else None,
            "unfinished_run_id": unfinished_run.id if unfinished_run else None,
            "resume_target": (
                f"/facebook/posting-runs/{unfinished_run.id}/queue"
                if unfinished_run
                else (
                    f"/facebook/vacancies/{vacancy_id}/groups?variant_id={latest_approved_variant.id}"
                    if latest_approved_variant
                    else (
                        f"/facebook/vacancies/{vacancy_id}/post-generator?variant_id={latest_variant.id}"
                        if latest_variant
                        else f"/facebook/vacancies/{vacancy_id}/post-generator"
                    )
                )
            ),
        }
    return continuity_map


def _apply_group_filters(query, company_id: int, filters: dict[str, Any]):
    query = query.filter(FacebookGroup.company_id == company_id)
    status = filters.get("status")
    if status:
        query = query.filter(FacebookGroup.status == FacebookGroupStatus(status))
    if "is_active" in filters and filters.get("is_active") not in (None, ""):
        query = query.filter(FacebookGroup.is_active == parse_bool(filters.get("is_active")))
    if filters.get("primary_category"):
        query = query.filter(FacebookGroup.primary_category == normalize_whitespace(filters["primary_category"]))
    if filters.get("city"):
        query = query.filter(FacebookGroup.city == normalize_whitespace(filters["city"]))
    if filters.get("audience_type"):
        query = query.filter(FacebookGroup.audience_type == normalize_whitespace(filters["audience_type"]))
    if filters.get("min_activity"):
        query = query.filter(FacebookGroup.activity_rating >= int(filters["min_activity"]))
    if filters.get("search"):
        search = f"%{normalize_whitespace(filters['search'])}%"
        query = query.filter(
            or_(
                FacebookGroup.name.ilike(search),
                FacebookGroup.city.ilike(search),
                FacebookGroup.region.ilike(search),
                FacebookGroup.facebook_slug.ilike(search),
            )
        )
    return query


def list_groups(db, company_id: int, filters: dict[str, Any]) -> list[dict[str, Any]]:
    query = db.query(FacebookGroup)
    query = _apply_group_filters(query, company_id, filters)
    rows = (
        query.order_by(
            FacebookGroup.activity_rating.desc(),
            FacebookGroup.last_posted_at.asc(),
            FacebookGroup.id.asc(),
        )
        .all()
    )
    return [_serialize_group(row) for row in rows]


def _ensure_same_company(row_company_id: int, company_id: int, label: str) -> None:
    if row_company_id != company_id:
        raise ValueError(f"{label} does not belong to current company")


def create_posting_run(
    db,
    *,
    company_id: int,
    vacancy_id: int,
    post_variant_id: int,
    group_ids: list[int],
    created_by: str,
    name: str | None = None,
    notes: str | None = None,
) -> FacebookPostingRun:
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id, Vacancy.company_id == company_id).first()
    if not vacancy:
        raise ValueError("vacancy not found")
    variant = (
        db.query(FacebookPostVariant)
        .filter(FacebookPostVariant.id == post_variant_id, FacebookPostVariant.company_id == company_id)
        .first()
    )
    if not variant:
        raise ValueError("post variant not found")
    if variant.status != FacebookPostVariantStatus.approved:
        raise ValueError("post variant must be approved before queue creation")

    ordered_ids: list[int] = []
    for group_id in group_ids:
        if group_id not in ordered_ids:
            ordered_ids.append(int(group_id))
    if not ordered_ids:
        raise ValueError("at least one group_id is required")

    groups = (
        db.query(FacebookGroup)
        .filter(FacebookGroup.company_id == company_id, FacebookGroup.id.in_(ordered_ids), FacebookGroup.is_active == True)
        .all()
    )
    groups_by_id = {group.id: group for group in groups}
    if len(groups_by_id) != len(ordered_ids):
        raise ValueError("one or more groups are missing or inactive")

    run = FacebookPostingRun(
        company_id=company_id,
        vacancy_id=vacancy_id,
        post_variant_id=post_variant_id,
        name=normalize_whitespace(name) or None,
        status=FacebookPostingRunStatus.ready,
        group_count=len(ordered_ids),
        created_by=created_by,
        notes=(notes or "").strip() or None,
    )
    db.add(run)
    db.flush()

    for index, group_id in enumerate(ordered_ids, start=1):
        item_status = FacebookPostingQueueItemStatus.current if index == 1 else FacebookPostingQueueItemStatus.pending
        db.add(
            FacebookPostingQueueItem(
                company_id=company_id,
                run_id=run.id,
                group_id=group_id,
                position=index,
                status=item_status,
            )
        )
    db.flush()
    db.refresh(run)
    return run


def _advance_run_state(run: FacebookPostingRun) -> None:
    items = sorted(run.queue_items, key=lambda row: row.position)
    pending_items = [item for item in items if item.status == FacebookPostingQueueItemStatus.pending]
    live_items = [
        item
        for item in items
        if item.status in {FacebookPostingQueueItemStatus.current, FacebookPostingQueueItemStatus.opened}
    ]

    if not live_items and pending_items:
        pending_items[0].status = FacebookPostingQueueItemStatus.current

    terminal_statuses = {
        FacebookPostingQueueItemStatus.posted,
        FacebookPostingQueueItemStatus.skipped,
        FacebookPostingQueueItemStatus.failed,
    }
    if items and all(item.status in terminal_statuses for item in items):
        run.status = FacebookPostingRunStatus.completed
        if not run.completed_at:
            run.completed_at = datetime.utcnow()
    elif any(item.status != FacebookPostingQueueItemStatus.pending for item in items):
        run.status = FacebookPostingRunStatus.in_progress
        if not run.started_at:
            run.started_at = datetime.utcnow()
    else:
        run.status = FacebookPostingRunStatus.ready
    run.last_action_at = datetime.utcnow()


def mark_queue_item_opened(queue_item: FacebookPostingQueueItem) -> FacebookPostingQueueItem:
    queue_item.status = FacebookPostingQueueItemStatus.opened
    queue_item.opened_at = datetime.utcnow()
    return queue_item


def mark_queue_item_copied(queue_item: FacebookPostingQueueItem) -> FacebookPostingQueueItem:
    queue_item.copied_at = datetime.utcnow()
    return queue_item


def mark_queue_item_posted(
    queue_item: FacebookPostingQueueItem,
    *,
    actor_id: str,
    group_note: str | None = None,
    post_url_manual: str | None = None,
) -> FacebookPostingQueueItem:
    queue_item.status = FacebookPostingQueueItemStatus.posted
    queue_item.posted_at = datetime.utcnow()
    queue_item.completed_by = actor_id
    queue_item.group_note = (group_note or "").strip() or None
    queue_item.post_url_manual = normalize_whitespace(post_url_manual) or None
    queue_item.group.last_posted_at = queue_item.posted_at
    return queue_item


def skip_queue_item(
    queue_item: FacebookPostingQueueItem,
    *,
    actor_id: str,
    skip_reason: str | None = None,
    group_note: str | None = None,
) -> FacebookPostingQueueItem:
    queue_item.status = FacebookPostingQueueItemStatus.skipped
    queue_item.skipped_at = datetime.utcnow()
    queue_item.completed_by = actor_id
    queue_item.skip_reason = normalize_whitespace(skip_reason) or None
    queue_item.group_note = (group_note or "").strip() or None
    return queue_item


def fail_queue_item(
    queue_item: FacebookPostingQueueItem,
    *,
    actor_id: str,
    group_note: str | None = None,
) -> FacebookPostingQueueItem:
    queue_item.status = FacebookPostingQueueItemStatus.failed
    queue_item.completed_by = actor_id
    queue_item.group_note = (group_note or "").strip() or None
    return queue_item


def update_queue_item_action(
    db,
    *,
    company_id: int,
    queue_item_id: int,
    action: str,
    actor_id: str,
    payload: dict[str, Any] | None = None,
) -> FacebookPostingQueueItem:
    payload = payload or {}
    queue_item = (
        db.query(FacebookPostingQueueItem)
        .filter(FacebookPostingQueueItem.id == queue_item_id, FacebookPostingQueueItem.company_id == company_id)
        .first()
    )
    if not queue_item:
        raise ValueError("queue item not found")
    _ensure_same_company(queue_item.run.company_id, company_id, "run")

    if action == "opened":
        mark_queue_item_opened(queue_item)
    elif action == "copied":
        mark_queue_item_copied(queue_item)
    elif action == "posted":
        mark_queue_item_posted(
            queue_item,
            actor_id=actor_id,
            group_note=payload.get("group_note"),
            post_url_manual=payload.get("post_url_manual"),
        )
    elif action == "skipped":
        skip_queue_item(
            queue_item,
            actor_id=actor_id,
            skip_reason=payload.get("skip_reason"),
            group_note=payload.get("group_note"),
        )
    elif action == "failed":
        fail_queue_item(queue_item, actor_id=actor_id, group_note=payload.get("group_note"))
    else:
        raise ValueError("unsupported action")

    _advance_run_state(queue_item.run)
    db.flush()
    return queue_item


def upsert_posting_result(
    db,
    *,
    company_id: int,
    queue_item_id: int,
    actor_id: str,
    payload: dict[str, Any],
) -> FacebookPostingResult:
    queue_item = (
        db.query(FacebookPostingQueueItem)
        .filter(FacebookPostingQueueItem.id == queue_item_id, FacebookPostingQueueItem.company_id == company_id)
        .first()
    )
    if not queue_item:
        raise ValueError("queue item not found")

    result = (
        db.query(FacebookPostingResult)
        .filter(FacebookPostingResult.queue_item_id == queue_item_id, FacebookPostingResult.company_id == company_id)
        .first()
    )
    if not result:
        result = FacebookPostingResult(company_id=company_id, queue_item_id=queue_item_id)
        db.add(result)

    result.result_status = FacebookPostingResultStatus(payload.get("result_status", FacebookPostingResultStatus.posted))
    result.response_count = parse_optional_int(payload.get("response_count"))
    result.cv_count = parse_optional_int(payload.get("cv_count"))
    result.interview_count = parse_optional_int(payload.get("interview_count"))
    result.hire_count = parse_optional_int(payload.get("hire_count"))
    result.quality_score = parse_optional_int(payload.get("quality_score"))
    result.last_checked_at = parse_optional_date(payload.get("last_checked_at")) or datetime.utcnow()
    result.owner_note = (payload.get("owner_note") or "").strip() or None
    result.result_note = (payload.get("result_note") or "").strip() or None
    result.updated_by = actor_id
    result.updated_at = datetime.utcnow()
    db.flush()
    return result


def _merge_optional_text(existing: str | None, incoming: str | None) -> str | None:
    incoming = normalize_whitespace(incoming)
    if incoming:
        return incoming
    return existing


def _merge_optional_int(existing: int | None, incoming: int | None) -> int | None:
    if incoming is not None:
        return incoming
    return existing


def _merge_optional_dt(existing: datetime | None, incoming: datetime | None) -> datetime | None:
    if existing and incoming:
        return max(existing, incoming)
    return incoming or existing


def validate_group_seed_row(row: dict[str, Any], default_source_type: str | None = None) -> dict[str, Any]:
    group_name = normalize_whitespace(row.get("group_name") or row.get("name"))
    facebook_url = normalize_whitespace(row.get("facebook_url"))
    primary_category = normalize_whitespace(row.get("primary_category"))
    if not group_name:
        raise ValueError("group_name is required")
    if not facebook_url:
        raise ValueError("facebook_url is required")
    if not primary_category:
        raise ValueError("primary_category is required")

    normalized_url = normalize_facebook_url(facebook_url)
    source_type = row.get("source_type") or default_source_type or FacebookGroupSourceType.seed_csv.value
    verification_status = row.get("verification_status") or FacebookGroupVerificationStatus.unverified.value
    cleaned = {
        "group_name": group_name,
        "facebook_url": facebook_url,
        "facebook_url_normalized": normalized_url,
        "facebook_slug": normalize_whitespace(row.get("facebook_slug")) or extract_facebook_slug(normalized_url),
        "primary_category": primary_category,
        "secondary_tags": parse_tags(row.get("secondary_tags") or row.get("secondary_tags_json")),
        "country_code": normalize_whitespace(row.get("country_code")) or "IL",
        "language_code": normalize_whitespace(row.get("language_code")) or "he",
        "city": normalize_whitespace(row.get("city")) or None,
        "region": normalize_whitespace(row.get("region")) or None,
        "audience_type": normalize_whitespace(row.get("audience_type")) or None,
        "member_count_estimate": parse_optional_int(row.get("member_count_estimate")),
        "activity_rating": parse_optional_int(row.get("activity_rating")),
        "posting_rules_summary": normalize_whitespace(row.get("posting_rules_summary")) or None,
        "requires_membership": parse_bool(row.get("requires_membership"), default=False),
        "requires_admin_approval": parse_bool(row.get("requires_admin_approval"), default=False),
        "status": row.get("status") or FacebookGroupStatus.active.value,
        "is_active": parse_bool(row.get("is_active"), default=True),
        "last_verified_at": parse_optional_date(row.get("last_verified_at")),
        "notes": (row.get("notes") or "").strip() or None,
        "source_type": FacebookGroupSourceType(source_type),
        "verification_status": FacebookGroupVerificationStatus(verification_status),
        "import_batch_key": normalize_whitespace(row.get("import_batch_key")),
        "raw_source_url": normalize_whitespace(row.get("raw_source_url")) or None,
    }
    if cleaned["activity_rating"] is not None and not 1 <= cleaned["activity_rating"] <= 5:
        raise ValueError("activity_rating must be between 1 and 5")
    if cleaned["member_count_estimate"] is not None and cleaned["member_count_estimate"] < 0:
        raise ValueError("member_count_estimate must be >= 0")
    if not cleaned["import_batch_key"]:
        raise ValueError("import_batch_key is required")
    return cleaned


def _load_seed_rows(path: str) -> list[dict[str, Any]]:
    suffix = Path(path).suffix.lower()
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        if suffix == ".csv":
            return list(csv.DictReader(handle))
        if suffix == ".json":
            loaded = json.load(handle)
            if isinstance(loaded, list):
                return loaded
            raise ValueError("JSON seed file must be a list of objects")
    raise ValueError("seed file must be .csv or .json")


def import_group_seed_file(
    db,
    *,
    company_id: int,
    path: str,
    source_label: str | None = None,
    collected_by: str | None = None,
    default_source_type: str | None = None,
) -> dict[str, Any]:
    rows = _load_seed_rows(path)
    source_label = source_label or Path(path).name
    sources_cache: dict[tuple[str, str], FacebookGroupSource] = {}
    report = {
        "path": path,
        "rows_seen": 0,
        "created": 0,
        "updated": 0,
        "errors": 0,
        "error_rows": [],
    }

    for index, raw_row in enumerate(rows, start=1):
        report["rows_seen"] += 1
        try:
            row = validate_group_seed_row(raw_row, default_source_type=default_source_type)
            cache_key = (row["source_type"].value, row["import_batch_key"])
            source = sources_cache.get(cache_key)
            if not source:
                source = (
                    db.query(FacebookGroupSource)
                    .filter(
                        FacebookGroupSource.company_id == company_id,
                        FacebookGroupSource.source_type == row["source_type"],
                        FacebookGroupSource.source_label == source_label,
                        FacebookGroupSource.import_batch_key == row["import_batch_key"],
                    )
                    .first()
                )
                if not source:
                    source = FacebookGroupSource(
                        company_id=company_id,
                        source_type=row["source_type"],
                        source_label=source_label,
                        import_batch_key=row["import_batch_key"],
                        collected_by=collected_by,
                        collected_at=datetime.utcnow(),
                        verification_status=row["verification_status"],
                        last_verified_at=row["last_verified_at"],
                        raw_source_url=row["raw_source_url"],
                    )
                    db.add(source)
                    db.flush()
                sources_cache[cache_key] = source

            existing = (
                db.query(FacebookGroup)
                .filter(
                    FacebookGroup.company_id == company_id,
                    FacebookGroup.facebook_url_normalized == row["facebook_url_normalized"],
                )
                .first()
            )
            if not existing and row["facebook_slug"]:
                existing = (
                    db.query(FacebookGroup)
                    .filter(
                        FacebookGroup.company_id == company_id,
                        FacebookGroup.facebook_slug == row["facebook_slug"],
                    )
                    .first()
                )
            if not existing:
                existing = (
                    db.query(FacebookGroup)
                    .filter(
                        FacebookGroup.company_id == company_id,
                        FacebookGroup.name == row["group_name"],
                        FacebookGroup.primary_category == row["primary_category"],
                        FacebookGroup.city == row["city"],
                        FacebookGroup.region == row["region"],
                    )
                    .first()
                )

            if existing:
                existing.seed_source_id = source.id
                existing.name = row["group_name"]
                existing.facebook_url = row["facebook_url"]
                existing.facebook_url_normalized = row["facebook_url_normalized"]
                existing.facebook_slug = _merge_optional_text(existing.facebook_slug, row["facebook_slug"])
                existing.primary_category = row["primary_category"]
                existing.secondary_tags_json = json.dumps(row["secondary_tags"], ensure_ascii=False)
                existing.country_code = row["country_code"]
                existing.language_code = row["language_code"]
                existing.city = _merge_optional_text(existing.city, row["city"])
                existing.region = _merge_optional_text(existing.region, row["region"])
                existing.audience_type = _merge_optional_text(existing.audience_type, row["audience_type"])
                existing.member_count_estimate = _merge_optional_int(existing.member_count_estimate, row["member_count_estimate"])
                existing.activity_rating = _merge_optional_int(existing.activity_rating, row["activity_rating"])
                existing.posting_rules_summary = _merge_optional_text(existing.posting_rules_summary, row["posting_rules_summary"])
                existing.requires_membership = row["requires_membership"]
                existing.requires_admin_approval = row["requires_admin_approval"]
                existing.status = FacebookGroupStatus(row["status"])
                existing.is_active = row["is_active"]
                existing.last_verified_at = _merge_optional_dt(existing.last_verified_at, row["last_verified_at"])
                existing.notes = _merge_optional_text(existing.notes, row["notes"])
                existing.updated_at = datetime.utcnow()
                report["updated"] += 1
            else:
                db.add(
                    FacebookGroup(
                        company_id=company_id,
                        seed_source_id=source.id,
                        name=row["group_name"],
                        facebook_url=row["facebook_url"],
                        facebook_url_normalized=row["facebook_url_normalized"],
                        facebook_slug=row["facebook_slug"],
                        primary_category=row["primary_category"],
                        secondary_tags_json=json.dumps(row["secondary_tags"], ensure_ascii=False),
                        country_code=row["country_code"],
                        language_code=row["language_code"],
                        city=row["city"],
                        region=row["region"],
                        audience_type=row["audience_type"],
                        member_count_estimate=row["member_count_estimate"],
                        activity_rating=row["activity_rating"],
                        posting_rules_summary=row["posting_rules_summary"],
                        requires_membership=row["requires_membership"],
                        requires_admin_approval=row["requires_admin_approval"],
                        status=FacebookGroupStatus(row["status"]),
                        is_active=row["is_active"],
                        last_verified_at=row["last_verified_at"],
                        notes=row["notes"],
                    )
                )
                report["created"] += 1
            db.flush()
        except Exception as exc:
            report["errors"] += 1
            report["error_rows"].append({"row": index, "error": str(exc), "input": raw_row})

    return report


def ensure_all_tables(engine, base_metadata) -> dict[str, Any]:
    before = set(base_metadata.tables.keys())
    base_metadata.create_all(bind=engine)
    return {
        "status": "ok",
        "tables_known": sorted(before),
        "fb_tables": sorted([name for name in before if name.startswith("fb_")]),
    }


def ensure_company_for_seed(db, owner_id: str = "admin_owner", name: str = "Default Company") -> Company:
    company = db.query(Company).filter(Company.owner_id == owner_id, Company.name == name).first()
    if not company:
        company = Company(owner_id=owner_id, name=name, description="Seeded company", is_active=True)
        db.add(company)
        db.flush()
    elif not company.is_active:
        company.is_active = True
        db.flush()
    return company


def ensure_vacancy_for_company(db, company_id: int, title: str = "Senior Recruiter") -> Vacancy:
    vacancy = db.query(Vacancy).filter(Vacancy.company_id == company_id, Vacancy.title == title).first()
    if not vacancy:
        vacancy = Vacancy(
            company_id=company_id,
            title=title,
            city="תל אביב",
            body="משרה מלאה בחברת גיוס עם עבודה מול לקוחות, ניסוח פרסומים וניהול תהליך גיוס.",
            language=Language.auto,
            interview_questions_json="[]",
        )
        db.add(vacancy)
        db.flush()
    return vacancy


def write_sample_seed_file(path: str) -> str:
    rows = [
        {
            "group_name": "משרות הייטק תל אביב",
            "facebook_url": "https://www.facebook.com/groups/tech.jobs.tlv",
            "primary_category": "tech",
            "country_code": "IL",
            "language_code": "he",
            "source_type": "seed_csv",
            "import_batch_key": "il_fb_seed_2026_q2",
            "verification_status": "verified",
            "city": "Tel Aviv",
            "region": "Center",
            "member_count_estimate": 85000,
            "activity_rating": 5,
            "audience_type": "mixed",
            "secondary_tags": "hebrew|startup|tel_aviv",
            "posting_rules_summary": "מותר לפרסם משרות בלי כפילויות יומיות",
            "requires_membership": "true",
            "requires_admin_approval": "false",
            "last_verified_at": "2026-03-30",
            "notes": "קבוצה פעילה מאוד",
        },
        {
            "group_name": "דרושים חיפה והצפון",
            "facebook_url": "https://www.facebook.com/groups/jobs.haifa.north",
            "primary_category": "city_jobs",
            "country_code": "IL",
            "language_code": "he",
            "source_type": "seed_csv",
            "import_batch_key": "il_fb_seed_2026_q2",
            "verification_status": "verified",
            "city": "Haifa",
            "region": "North",
            "member_count_estimate": 42000,
            "activity_rating": 4,
            "audience_type": "job_seekers",
            "secondary_tags": "hebrew|haifa|north",
            "posting_rules_summary": "משרות מקומיות בלבד",
            "requires_membership": "true",
            "requires_admin_approval": "true",
            "last_verified_at": "2026-03-30",
            "notes": "טובה לתפקידי שירות ותפעול",
        },
    ]
    fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path
