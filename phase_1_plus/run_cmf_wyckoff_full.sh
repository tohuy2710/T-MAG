#!/bin/bash

# ============================================================================
# CMF Wyckoff Full Test Suite
# Chạy toàn bộ workflow: parse → simulate → analyze → report
# ============================================================================

set -e

PHASE_1_PLUS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${PHASE_1_PLUS_DIR}/output/cmf_wyckoff"

echo ""
echo "=========================================================================="
echo "  CMF WYCKOFF ALPHA FULL TEST SUITE"
echo "=========================================================================="
echo ""
echo "  Working directory: ${PHASE_1_PLUS_DIR}"
echo "  Output directory: ${OUTPUT_DIR}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Parse options
LEVEL=""
DRY_RUN=""
BATCH_SIZE="10"
MAX_CONCURRENT="3"

while [[ $# -gt 0 ]]; do
  case $1 in
    --level)
      LEVEL="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="--dry-run"
      shift
      ;;
    --batch-size)
      BATCH_SIZE="$2"
      shift 2
      ;;
    --max-concurrent)
      MAX_CONCURRENT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# ============================================================================
# Step 1: Verify template file exists
# ============================================================================

TEMPLATE_FILE="${PHASE_1_PLUS_DIR}/alphas_cmf_wyckoff_template.txt"

if [ ! -f "${TEMPLATE_FILE}" ]; then
  echo "✗ Template file not found: ${TEMPLATE_FILE}"
  exit 1
fi

ALPHA_COUNT=$(grep -c "^rank\|^group\|^sign\|-" "${TEMPLATE_FILE}" || true)
echo "[step 1] ✓ Template file found (contains ~${ALPHA_COUNT} expressions)"
echo ""

# ============================================================================
# Step 2: Run simulator
# ============================================================================

echo "[step 2] Running simulator..."
echo "         Batch size: ${BATCH_SIZE}"
echo "         Max concurrent: ${MAX_CONCURRENT}"

if [ -n "${LEVEL}" ]; then
  echo "         Level filter: L${LEVEL}"
fi

if [ -n "${DRY_RUN}" ]; then
  echo "         Mode: DRY RUN (no API calls)"
fi

echo ""

cd "${PHASE_1_PLUS_DIR}"

# Activate venv
PROJECT_ROOT="$(cd "${PHASE_1_PLUS_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/.venv/bin/activate"

if [ -n "${LEVEL}" ]; then
  python3 cmf_wyckoff_simulator.py \
    --level "${LEVEL}" \
    --batch-size "${BATCH_SIZE}" \
    --max-concurrent "${MAX_CONCURRENT}" \
    ${DRY_RUN}
else
  python3 cmf_wyckoff_simulator.py \
    --batch-size "${BATCH_SIZE}" \
    --max-concurrent "${MAX_CONCURRENT}" \
    ${DRY_RUN}
fi

if [ $? -ne 0 ]; then
  echo "✗ Simulator failed"
  exit 1
fi

echo ""

# ============================================================================
# Step 3: Run analyzer
# ============================================================================

echo "[step 3] Running analyzer..."
echo ""

python3 cmf_wyckoff_analyzer.py

if [ $? -ne 0 ]; then
  echo "✗ Analyzer failed"
  exit 1
fi

echo ""

# ============================================================================
# Step 4: Summary
# ============================================================================

RESULTS_JSON="${OUTPUT_DIR}/results.json"
RESULTS_CSV="${OUTPUT_DIR}/results.csv"
REPORT_MD="${OUTPUT_DIR}/CMF_WYCKOFF_REPORT.md"

echo "=========================================================================="
echo "  ✓ COMPLETE"
echo "=========================================================================="
echo ""
echo "Output files:"
echo "  JSON:   ${RESULTS_JSON}"
echo "  CSV:    ${RESULTS_CSV}"
echo "  Report: ${REPORT_MD}"
echo ""

if [ -f "${RESULTS_CSV}" ]; then
  LINE_COUNT=$(wc -l < "${RESULTS_CSV}")
  echo "CSV contains $(( ${LINE_COUNT} - 1 )) results"
fi

if [ -f "${REPORT_MD}" ]; then
  echo "✓ Markdown report generated"
  echo ""
  echo "To view the report:"
  echo "  cat ${REPORT_MD}"
fi

echo ""
