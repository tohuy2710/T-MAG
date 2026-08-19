#!/bin/bash

# Wrapper to run analyzer with proper venv activation

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PHASE_1_PLUS_DIR="${PROJECT_ROOT}/phase_1_plus"

# Activate venv
source "${PROJECT_ROOT}/.venv/bin/activate"

# Run analyzer
cd "${PHASE_1_PLUS_DIR}"
python3 cmf_wyckoff_analyzer.py "$@"
