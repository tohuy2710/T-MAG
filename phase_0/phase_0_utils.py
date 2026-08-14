"""Phase 0 utility functions for loading templates and saving results."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timezone

from phase_0_config import (
    TEMPLATES_DIR, PHASE_0_RESULTS_FILE, PHASE_0_OUTPUT_DIR,
    INDIVIDUAL_RESULTS_DIR, SAVE_INDIVIDUAL_RESULTS,
    LOG_LEVEL, LOG_FORMAT
)

logger = logging.getLogger(__name__)

# Setup logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)


def setup_logger(name: str) -> logging.Logger:
    """Create logger for module."""
    return logging.getLogger(name)


def load_templates() -> List[Dict[str, Any]]:
    """Load all templates from templates directory."""
    templates = []
    
    if not TEMPLATES_DIR.exists():
        logger.warning(f"Templates directory not found: {TEMPLATES_DIR}")
        return templates
    
    for template_file in sorted(TEMPLATES_DIR.glob("*.json")):
        try:
            data = json.loads(template_file.read_text(encoding="utf-8"))
            template_id = data.get("template_id", template_file.stem)
            data["_file"] = str(template_file)
            templates.append(data)
            logger.info(f"Loaded template: {template_id} from {template_file.name}")
        except Exception as e:
            logger.error(f"Failed to load template {template_file.name}: {e}")
    
    logger.info(f"Total templates loaded: {len(templates)}")
    return templates


def load_template_by_id(template_id: str) -> Dict[str, Any] | None:
    """Load specific template by ID."""
    templates = load_templates()
    for t in templates:
        if t.get("template_id") == template_id:
            return t
    return None


def save_simulation_results(results: List[Dict[str, Any]]) -> None:
    """Save simulation results to JSON file."""
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_simulated": len(results),
        "passed": sum(1 for r in results if r.get("status") == "COMPLETE"),
        "failed": sum(1 for r in results if r.get("status") != "COMPLETE"),
        "results": results,
    }
    
    PHASE_0_RESULTS_FILE.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    logger.info(f"Saved results to {PHASE_0_RESULTS_FILE}")


def save_individual_result(result: Dict[str, Any]) -> None:
    """Save individual simulation result."""
    if not SAVE_INDIVIDUAL_RESULTS:
        return
    
    INDIVIDUAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    alpha_id = result.get("alpha_id", "unknown")
    filename = INDIVIDUAL_RESULTS_DIR / f"{alpha_id}.json"
    
    filename.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    logger.debug(f"Saved individual result: {filename}")


def get_summary_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute summary statistics from results."""
    if not results:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "avg_sharpe": 0,
            "avg_fitness": 0,
            "avg_turnover": 0,
        }
    
    complete = [r for r in results if r.get("status") == "COMPLETE"]
    
    if not complete:
        return {
            "total": len(results),
            "passed": 0,
            "failed": len(results),
            "avg_sharpe": 0,
            "avg_fitness": 0,
            "avg_turnover": 0,
        }
    
    sharpes = [r.get("sim_data", {}).get("is", {}).get("sharpe", 0) for r in complete]
    fitnesses = [r.get("sim_data", {}).get("is", {}).get("fitness", 0) for r in complete]
    turnovers = [r.get("sim_data", {}).get("is", {}).get("turnover", 0) for r in complete]
    
    return {
        "total": len(results),
        "passed": len(complete),
        "failed": len(results) - len(complete),
        "avg_sharpe": sum(sharpes) / len(sharpes) if sharpes else 0,
        "avg_fitness": sum(fitnesses) / len(fitnesses) if fitnesses else 0,
        "avg_turnover": sum(turnovers) / len(turnovers) if turnovers else 0,
    }


def print_summary(results: List[Dict[str, Any]]) -> None:
    """Print summary of results."""
    stats = get_summary_stats(results)
    
    print("\n" + "=" * 70)
    print("  Phase 0 — Simulation Summary")
    print("=" * 70)
    print(f"  Total simulated: {stats['total']}")
    print(f"  Completed: {stats['passed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Success rate: {stats['passed']/stats['total']*100:.1f}%" if stats['total'] > 0 else "  N/A")
    print(f"\n  Average Sharpe: {stats['avg_sharpe']:.2f}")
    print(f"  Average Fitness: {stats['avg_fitness']:.2f}")
    print(f"  Average Turnover: {stats['avg_turnover']:.4f}")
    print("=" * 70 + "\n")
