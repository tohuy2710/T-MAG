#!/bin/bash

# Wrapper to run simulation with proper venv activation

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PHASE_1_PLUS_DIR="${PROJECT_ROOT}/phase_1_plus"

# Activate venv
source "${PROJECT_ROOT}/.venv/bin/activate"

# Run simulator with all arguments passed through
cd "${PHASE_1_PLUS_DIR}"
python3 cmf_wyckoff_simulator.py "$@"
