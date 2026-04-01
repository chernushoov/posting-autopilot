#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/17] Build vacancy pack"
python3 "${ROOT_DIR}/scripts/build_live_vacancy_pack.py"

echo
echo "[2/17] Validate Sunday bundle"
python3 "${ROOT_DIR}/scripts/validate_sunday_bundle.py"

echo
echo "[3/17] Validate ops contracts"
python3 "${ROOT_DIR}/scripts/validate_ops_contracts.py"

echo
echo "[4/17] Prepare first-wave source roster"
python3 "${ROOT_DIR}/scripts/prepare_first_wave_roster.py"

echo
echo "[5/17] Readiness check"
python3 "${ROOT_DIR}/scripts/sunday_readiness_check.py"

echo
echo "[6/17] Ingest raw responses"
python3 "${ROOT_DIR}/scripts/ingest_raw_responses.py"

echo
echo "[7/17] Sync screening to pipeline"
python3 "${ROOT_DIR}/scripts/sync_screening_to_pipeline.py"

echo
echo "[8/17] Refresh shortlist"
python3 "${ROOT_DIR}/scripts/promote_shortlist_from_pipeline.py"

echo
echo "[9/17] Generate execution board"
python3 "${ROOT_DIR}/scripts/generate_execution_board.py"

echo
echo "[10/17] Generate posting evidence summary"
python3 "${ROOT_DIR}/scripts/generate_posting_evidence_summary.py"

echo
echo "[11/17] Generate client progress update"
python3 "${ROOT_DIR}/scripts/generate_client_progress_update.py"

echo
echo "[12/17] Generate recruiter handoff batch"
python3 "${ROOT_DIR}/scripts/generate_recruiter_handoff_batch.py"

echo
echo "[13/17] Update case-study rollup"
python3 "${ROOT_DIR}/scripts/update_case_study_from_tracking.py"

echo
echo "[14/17] Generate Sunday ops report"
python3 "${ROOT_DIR}/scripts/generate_sunday_ops_report.py"

echo
echo "[15/17] Generate launch status snapshot"
python3 "${ROOT_DIR}/scripts/generate_launch_status_snapshot.py"

echo
echo "[16/17] Generate end-of-day report"
python3 "${ROOT_DIR}/scripts/generate_end_of_day_report.py"

echo
echo "[17/17] Generate day-close packet"
python3 "${ROOT_DIR}/scripts/generate_day_close_packet.py"

echo
echo "Sunday launch control complete."
