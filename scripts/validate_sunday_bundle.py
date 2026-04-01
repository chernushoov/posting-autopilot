#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "ops" / "live_vacancy_4_hires"

REQUIRED_FILES = [
    "README.md",
    "vacancy_intake_client.md",
    "CLIENT_MESSAGE_TEMPLATES.md",
    "CLIENT_APPROVAL_TEMPLATE.md",
    "vacancy_intake_template.json",
    "POSTING_COPY_PACK.md",
    "SCREENING_PACK.md",
    "SOURCE_OWNER_MESSAGE_TEMPLATES.md",
    "source_execution_plan.csv",
    "first_wave_source_roster.csv",
    "candidate_pipeline.csv",
    "CANDIDATE_PIPELINE_GUIDE.md",
    "CANDIDATE_MESSAGE_TEMPLATES.md",
    "CANDIDATE_FOLLOWUP_TEMPLATES.md",
    "RECRUITER_HANDOFF_TEMPLATE.md",
    "interview_followup_log.csv",
    "pilot_metrics.csv",
    "case_study_capture.json",
    "END_OF_DAY_REPORT_TEMPLATE.md",
    "READINESS_MATRIX.md",
]


def load_json(path: Path) -> None:
    with path.open("r", encoding="utf-8") as handle:
        json.load(handle)


def main() -> int:
    missing = [name for name in REQUIRED_FILES if not (OPS / name).exists()]
    load_json(OPS / "vacancy_intake_template.json")
    load_json(OPS / "case_study_capture.json")
    contract_check = subprocess.run(
        ["python3", str(ROOT / "scripts" / "validate_ops_contracts.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    contract_status = "error"
    contract_payload = {}
    if contract_check.stdout.strip():
        contract_payload = json.loads(contract_check.stdout)
        contract_status = contract_payload.get("status", "error")
    generated_dir = OPS / "generated"
    generated = sorted(p.name for p in generated_dir.iterdir()) if generated_dir.exists() else []
    print(json.dumps({
        "ops_dir": str(OPS),
        "missing_files": missing,
        "generated_files": generated,
        "required_count": len(REQUIRED_FILES),
        "contract_status": contract_status,
        "contract_checks": contract_payload.get("checks", []),
        "status": "ok" if not missing and contract_status == "ok" else "missing_files" if missing else "contract_error",
    }, ensure_ascii=False, indent=2))
    return 0 if not missing and contract_status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
