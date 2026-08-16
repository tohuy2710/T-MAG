#!/usr/bin/env python3
"""Phase 1: Quarterly Return Reversal batch simulation.

This phase focuses on simulating the quarterly_return_reversal template
with comprehensive parameter combinations for GLB/TOPDIV3000/Delay1.

Usage:
  python3 phase_1_sim.py                          # Simulate quarterly_return_reversal template
  python3 phase_1_sim.py --batch-size 15          # Custom batch size
  python3 phase_1_sim.py --max-per-template 30    # Generate more candidates
  python3 phase_1_sim.py --max-concurrent 5       # Higher concurrency
  python3 phase_1_sim.py --show-top 15            # Show top 15 performers
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timezone

# Add parent and phase_1 to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from phase_1_config import (
    BATCH_SIZE, MAX_CANDIDATES_PER_TEMPLATE, MAX_CONCURRENT,
    SIMULATION_TIMEOUT, PHASE_1_OUTPUT_DIR, DEFAULT_TEMPLATE, AUTO_SUBMIT
)
from phase_1_utils import (
    setup_logger, load_templates, load_template_by_id,
    save_simulation_results, save_individual_result,
    print_summary, get_summary_stats, print_top_performers
)

from brain_api import BrainClient
from generate_candidates import expand_template, FieldValidator
from research_target import load_target

logger = setup_logger(__name__)


def generate_candidates_from_templates(
    templates: List[Dict[str, Any]],
    max_per_template: int = 20,
) -> List[Dict[str, Any]]:
    """Generate candidates from templates.
    
    Args:
        templates: List of template dictionaries
        max_per_template: Maximum candidates per template
        
    Returns:
        List of candidate expressions with metadata
    """
    candidates = []
    target = load_target()
    
    # Load field validator if available
    try:
        fields_path = target.require_fields_reference()
        validator = FieldValidator(fields_path, target.excluded_dataset_ids)
        logger.info(f"Loaded field validator with {len(validator.field_list)} fields")
    except Exception as e:
        logger.warning(f"Field validator not available: {e}")
        validator = None
    
    for template in templates:
        tid = template.get("template_id", "unknown")
        logger.info(f"Expanding template: {tid}")
        
        try:
            cands = expand_template(
                template,
                max_candidates=max_per_template,
                validator=validator,
                target=target,
            )
            candidates.extend(cands)
            logger.info(f"  Generated {len(cands)} candidates from {tid}")
        except Exception as e:
            logger.error(f"  Failed to expand {tid}: {e}")
    
    logger.info(f"Total candidates generated: {len(candidates)}")
    return candidates


def batch_simulate(
    candidates: List[Dict[str, Any]],
    batch_size: int = 10,
    max_concurrent: int = 3,
) -> List[Dict[str, Any]]:
    """Batch simulate candidates using BRAIN API.
    
    Args:
        candidates: List of candidate expressions
        batch_size: Number of candidates per batch
        max_concurrent: Maximum concurrent simulations
        
    Returns:
        List of simulation results
    """
    
    print(f"\n[sim] Starting batch simulation: {len(candidates)} candidates")
    print(f"      Batch size: {batch_size}")
    print(f"      Max concurrent: {max_concurrent}\n")
    
    client = BrainClient(max_concurrent=max_concurrent)
    client.connect()
    logger.info("Connected to BRAIN API")
    
    all_results = []
    
    # Process in batches
    for batch_idx, i in enumerate(range(0, len(candidates), batch_size)):
        batch = candidates[i:i+batch_size]
        batch_num = batch_idx + 1
        total_batches = (len(candidates) + batch_size - 1) // batch_size
        
        print(f"[batch {batch_num}/{total_batches}] Simulating {len(batch)} candidates...")
        
        try:
            # Use streaming simulate
            batch_results = []
            for result in client.batch_simulate_stream(batch, max_concurrent=max_concurrent):
                sim = result.get("sim_result", {})
                status = sim.get("status", "ERROR")
                
                alpha_id = sim.get("alpha_id")
                sharpe = sim.get("sim_data", {}).get("is", {}).get("sharpe", 0)
                fitness = sim.get("sim_data", {}).get("is", {}).get("fitness", 0)
                turnover = sim.get("sim_data", {}).get("is", {}).get("turnover", 0)
                
                output = {
                    "expression": result.get("expression"),
                    "template_id": result.get("template_id"),
                    "status": status,
                    "alpha_id": alpha_id,
                    "sim_data": sim.get("sim_data"),
                    "simulated_at": datetime.now(timezone.utc).isoformat(),
                }
                
                batch_results.append(output)
                save_individual_result(output)
                
                if status == "COMPLETE":
                    print(f"  ✓ {alpha_id} sharpe={sharpe:.2f} fitness={fitness:.2f} turnover={turnover:.4f}")
                else:
                    error_msg = sim.get("message", "unknown error")
                    print(f"  ✗ {status}: {error_msg}")
            
            all_results.extend(batch_results)
            
        except Exception as e:
            logger.error(f"Batch {batch_num} failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Phase 1: Quarterly Return Reversal simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 phase_1_sim.py                          # Default simulation
  python3 phase_1_sim.py --batch-size 15          # Larger batches
  python3 phase_1_sim.py --max-per-template 50    # More candidates
  python3 phase_1_sim.py --show-top 20            # Show top 20 performers
        """
    )
    
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, 
                       help=f"Template ID to simulate (default: {DEFAULT_TEMPLATE})")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, 
                       help=f"Batch size (default: {BATCH_SIZE})")
    parser.add_argument("--max-per-template", type=int, default=MAX_CANDIDATES_PER_TEMPLATE,
                       help=f"Max candidates per template (default: {MAX_CANDIDATES_PER_TEMPLATE})")
    parser.add_argument("--max-concurrent", type=int, default=MAX_CONCURRENT,
                       help=f"Max concurrent simulations (default: {MAX_CONCURRENT})")
    parser.add_argument("--output", help="Output file (default: phase_1/output/simulation_results.json)")
    parser.add_argument("--show-top", type=int, default=10,
                       help="Number of top performers to display (default: 10)")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("  Phase 1 — Quarterly Return Reversal Simulation")
    print("=" * 70)
    print(f"\n  Environment: GLB / TOPDIV3000 / Delay 1")
    print(f"  Template: {args.template}")
    print(f"  Auto-submit: {AUTO_SUBMIT}")
    print()
    
    # Load template
    logger.info(f"Loading template: {args.template}")
    tmpl = load_template_by_id(args.template)
    if not tmpl:
        print(f"✗ Template not found: {args.template}")
        print(f"  Available templates in templates/ directory")
        return 1
    
    templates = [tmpl]
    print(f"[load] Loaded template: {args.template}\n")
    
    # Generate candidates
    print(f"[gen] Generating candidates (max {args.max_per_template} per template)...")
    candidates = generate_candidates_from_templates(
        templates,
        max_per_template=args.max_per_template
    )
    print(f"[gen] Generated {len(candidates)} candidates\n")
    
    if not candidates:
        print("✗ No candidates generated")
        return 1
    
    # Show sample candidates
    print("Sample candidates:")
    for i, cand in enumerate(candidates[:3], 1):
        expr = cand.get("expression", "")
        if len(expr) > 100:
            expr = expr[:97] + "..."
        print(f"  {i}. {expr}")
    if len(candidates) > 3:
        print(f"  ... and {len(candidates) - 3} more")
    print()
    
    # Simulate
    results = batch_simulate(
        candidates,
        batch_size=args.batch_size,
        max_concurrent=args.max_concurrent
    )
    
    # Save results
    save_simulation_results(results)
    
    # Print summaries
    print_summary(results)
    print_top_performers(results, top_n=args.show_top)
    
    # Statistics
    stats = get_summary_stats(results)
    print(f"[save] Results saved to {PHASE_1_OUTPUT_DIR}")
    print(f"       Individual results: {PHASE_1_OUTPUT_DIR}/individual/\n")
    
    # Final message
    if AUTO_SUBMIT:
        print("Note: Auto-submit is ENABLED. Top performers will be submitted automatically.")
    else:
        print("Note: Auto-submit is DISABLED. Review results and submit manually if desired.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
