#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/8] Ingest raw responses"
python3 "${ROOT_DIR}/scripts/ingest_raw_responses.py"

echo
echo "[2/8] Sync screening to pipeline"
python3 "${ROOT_DIR}/scripts/sync_screening_to_pipeline.py"

echo
echo "[3/8] Refresh shortlist"
python3 "${ROOT_DIR}/scripts/promote_shortlist_from_pipeline.py"

echo
echo "[4/8] Generate recruiter handoff batch"
python3 "${ROOT_DIR}/scripts/generate_recruiter_handoff_batch.py"

echo
echo "[5/8] Generate client progress update"
python3 "${ROOT_DIR}/scripts/generate_client_progress_update.py"

echo
echo "[6/8] Generate execution board"
python3 "${ROOT_DIR}/scripts/generate_execution_board.py"

echo
echo "[7/8] Generate posting evidence summary"
python3 "${ROOT_DIR}/scripts/generate_posting_evidence_summary.py"

echo
echo "[8/8] Update case-study rollup"
python3 "${ROOT_DIR}/scripts/update_case_study_from_tracking.py"

echo
echo "Ops refresh complete."
