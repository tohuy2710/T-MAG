"""Phase 0 configuration and constants."""

import os
from pathlib import Path

# Paths
WORKSPACE_ROOT = Path(__file__).parent.parent
PHASE_0_ROOT = WORKSPACE_ROOT / "phase_0"
TEMPLATES_DIR = WORKSPACE_ROOT / "templates"
PHASE_0_OUTPUT_DIR = PHASE_0_ROOT / "output"
PHASE_0_RESULTS_FILE = PHASE_0_OUTPUT_DIR / "simulation_results.json"
PHASE_0_LOG_FILE = PHASE_0_OUTPUT_DIR / "phase_0.log"

# Create output directory if needed
PHASE_0_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Simulation parameters
BATCH_SIZE = int(os.getenv("PHASE_0_BATCH_SIZE", "10"))
MAX_CANDIDATES_PER_TEMPLATE = int(os.getenv("PHASE_0_MAX_PER_TEMPLATE", "8"))
SIMULATION_TIMEOUT = int(os.getenv("PHASE_0_SIM_TIMEOUT", "600"))  # seconds
MAX_CONCURRENT = int(os.getenv("PHASE_0_MAX_CONCURRENT", "2"))

# Template filtering
EXCLUDED_TEMPLATES = set(os.getenv("PHASE_0_EXCLUDED", "").split(",")) if os.getenv("PHASE_0_EXCLUDED") else set()
INCLUDED_TEMPLATES = set(os.getenv("PHASE_0_INCLUDED", "").split(",")) if os.getenv("PHASE_0_INCLUDED") else set()

# Logging
LOG_LEVEL = os.getenv("PHASE_0_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s %(message)s"

# Candidate generation
FIELD_VALIDATOR_ENABLED = os.getenv("PHASE_0_VALIDATE_FIELDS", "true").lower() == "true"

# Output format
SAVE_INDIVIDUAL_RESULTS = os.getenv("PHASE_0_SAVE_INDIVIDUAL", "true").lower() == "true"
INDIVIDUAL_RESULTS_DIR = PHASE_0_OUTPUT_DIR / "individual"

print(f"""
Phase 0 Configuration
=====================
Templates dir: {TEMPLATES_DIR}
Output dir: {PHASE_0_OUTPUT_DIR}
Batch size: {BATCH_SIZE}
Max per template: {MAX_CANDIDATES_PER_TEMPLATE}
Max concurrent: {MAX_CONCURRENT}
Timeout: {SIMULATION_TIMEOUT}s
""")
