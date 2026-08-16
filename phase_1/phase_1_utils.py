"""Phase 1 utility functions for loading templates and saving results."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timezone

from pathlib import Path
import sys

# Add phase_1 directory to path
sys.path.insert(0, str(Path(__file__).parent))

from phase_1_config import (
    TEMPLATES_DIR, PHASE_1_RESULTS_FILE, PHASE_1_OUTPUT_DIR,
    INDIVIDUAL_RESULTS_DIR, SAVE_INDIVIDUAL_RESULTS,
    LOG_LEVEL, LOG_FORMAT, INCLUDED_TEMPLATES, EXCLUDED_TEMPLATES
)

logger = logging.getLogger(__name__)

# Setup logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)


def setup_logger(name: str) -> logging.Logger:
    """Create logger for module."""
    return logging.getLogger(name)


def load_templates(template_id: str = None) -> List[Dict[str, Any]]:
    """Load templates from templates directory.
    
    Args:
        template_id: If provided, load only this template. Otherwise load based on INCLUDED_TEMPLATES.
    """
    templates = []
    
    if not TEMPLATES_DIR.exists():
        logger.warning(f"Templates directory not found: {TEMPLATES_DIR}")
        return templates
    
    # Determine which templates to load
    if template_id:
        target_templates = {template_id}
    elif INCLUDED_TEMPLATES:
        target_templates = INCLUDED_TEMPLATES
    else:
        # Load all if no filter specified
        target_templates = None
    
    for template_file in sorted(TEMPLATES_DIR.glob("*.json")):
        try:
            data = json.loads(template_file.read_text(encoding="utf-8"))
            tid = data.get("template_id", template_file.stem)
            
            # Filter logic
            if target_templates and tid not in target_templates:
                continue
            if tid in EXCLUDED_TEMPLATES:
                continue
            
            data["_file"] = str(template_file)
            templates.append(data)
            logger.info(f"Loaded template: {tid} from {template_file.name}")
        except Exception as e:
            logger.error(f"Failed to load template {template_file.name}: {e}")
    
    logger.info(f"Total templates loaded: {len(templates)}")
    return templates


def load_template_by_id(template_id: str) -> Dict[str, Any] | None:
    """Load specific template by ID."""
    templates = load_templates(template_id=template_id)
    for t in templates:
        if t.get("template_id") == template_id:
            return t
    return None


def save_simulation_results(results: List[Dict[str, Any]]) -> None:
    """Save simulation results to JSON file."""
    output = {
        "phase": "phase_1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_simulated": len(results),
        "passed": sum(1 for r in results if r.get("status") == "COMPLETE"),
        "failed": sum(1 for r in results if r.get("status") != "COMPLETE"),
        "results": results,
    }
    
    PHASE_1_RESULTS_FILE.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    logger.info(f"Saved results to {PHASE_1_RESULTS_FILE}")


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
            "max_sharpe": 0,
            "min_sharpe": 0,
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
            "max_sharpe": 0,
            "min_sharpe": 0,
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
        "max_sharpe": max(sharpes) if sharpes else 0,
        "min_sharpe": min(sharpes) if sharpes else 0,
    }


def print_summary(results: List[Dict[str, Any]]) -> None:
    """Print summary of results."""
    stats = get_summary_stats(results)
    
    print("\n" + "=" * 70)
    print("  Phase 1 — Quarterly Return Reversal — Simulation Summary")
    print("=" * 70)
    print(f"  Total simulated: {stats['total']}")
    print(f"  Completed: {stats['passed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Success rate: {stats['passed']/stats['total']*100:.1f}%" if stats['total'] > 0 else "  N/A")
    print(f"\n  Sharpe Statistics:")
    print(f"    Average: {stats['avg_sharpe']:.2f}")
    print(f"    Maximum: {stats['max_sharpe']:.2f}")
    print(f"    Minimum: {stats['min_sharpe']:.2f}")
    print(f"\n  Average Fitness: {stats['avg_fitness']:.2f}")
    print(f"  Average Turnover: {stats['avg_turnover']:.4f}")
    print("=" * 70 + "\n")


def print_top_performers(results: List[Dict[str, Any]], top_n: int = 10) -> None:
    """Print top performing alphas by Sharpe ratio."""
    complete = [r for r in results if r.get("status") == "COMPLETE"]
    
    if not complete:
        print("No completed simulations to rank.\n")
        return
    
    # Sort by Sharpe descending
    sorted_results = sorted(
        complete,
        key=lambda r: r.get("sim_data", {}).get("is", {}).get("sharpe", 0),
        reverse=True
    )
    
    print("\n" + "=" * 70)
    print(f"  Top {top_n} Performers (by Sharpe)")
    print("=" * 70)
    
    for i, result in enumerate(sorted_results[:top_n], 1):
        sim_data = result.get("sim_data", {}).get("is", {})
        sharpe = sim_data.get("sharpe", 0)
        fitness = sim_data.get("fitness", 0)
        turnover = sim_data.get("turnover", 0)
        alpha_id = result.get("alpha_id", "unknown")
        expr = result.get("expression", "")
        
        # Truncate expression if too long
        if len(expr) > 80:
            expr = expr[:77] + "..."
        
        print(f"\n  {i}. {alpha_id}")
        print(f"     Sharpe: {sharpe:.2f} | Fitness: {fitness:.2f} | Turnover: {turnover:.4f}")
        print(f"     {expr}")
    
    print("\n" + "=" * 70 + "\n")
