"""Phase 1 configuration and constants."""

import os
from pathlib import Path

# Paths
WORKSPACE_ROOT = Path(__file__).parent.parent
PHASE_1_ROOT = WORKSPACE_ROOT / "phase_1"
TEMPLATES_DIR = WORKSPACE_ROOT / "templates"
PHASE_1_OUTPUT_DIR = PHASE_1_ROOT / "output"
PHASE_1_RESULTS_FILE = PHASE_1_OUTPUT_DIR / "simulation_results.json"
PHASE_1_LOG_FILE = PHASE_1_OUTPUT_DIR / "phase_1.log"

# Create output directory if needed
PHASE_1_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Simulation parameters
BATCH_SIZE = int(os.getenv("PHASE_1_BATCH_SIZE", "10"))
MAX_CANDIDATES_PER_TEMPLATE = int(os.getenv("PHASE_1_MAX_PER_TEMPLATE", "20"))
SIMULATION_TIMEOUT = int(os.getenv("PHASE_1_SIM_TIMEOUT", "600"))  # seconds
MAX_CONCURRENT = int(os.getenv("PHASE_1_MAX_CONCURRENT", "3"))

# Template filtering for phase 1
# By default, focus on quarterly_return_reversal template
DEFAULT_TEMPLATE = "quarterly_return_reversal"
EXCLUDED_TEMPLATES = set(os.getenv("PHASE_1_EXCLUDED", "").split(",")) if os.getenv("PHASE_1_EXCLUDED") else set()
INCLUDED_TEMPLATES = set(os.getenv("PHASE_1_INCLUDED", DEFAULT_TEMPLATE).split(","))

# Logging
LOG_LEVEL = os.getenv("PHASE_1_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s %(message)s"

# Candidate generation
FIELD_VALIDATOR_ENABLED = os.getenv("PHASE_1_VALIDATE_FIELDS", "true").lower() == "true"

# Output format
SAVE_INDIVIDUAL_RESULTS = os.getenv("PHASE_1_SAVE_INDIVIDUAL", "true").lower() == "true"
INDIVIDUAL_RESULTS_DIR = PHASE_1_OUTPUT_DIR / "individual"

# Auto-submit disabled for phase 1
AUTO_SUBMIT = False  # Phase 1 is simulation only, no auto-submit

print(f"""
Phase 1 Configuration
=====================
Template: {DEFAULT_TEMPLATE}
Templates dir: {TEMPLATES_DIR}
Output dir: {PHASE_1_OUTPUT_DIR}
Batch size: {BATCH_SIZE}
Max per template: {MAX_CANDIDATES_PER_TEMPLATE}
Max concurrent: {MAX_CONCURRENT}
Timeout: {SIMULATION_TIMEOUT}s
Auto-submit: {AUTO_SUBMIT}
""")
