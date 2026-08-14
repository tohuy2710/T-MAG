#!/usr/bin/env python3
"""Phase 0: Simple batch simulation of paper-extracted templates.

Usage:
  python3 phase_0_sim.py                                    # Simulate all templates
  python3 phase_0_sim.py --template alpha1                  # Specific template
  python3 phase_0_sim.py --extraction extraction_src_002.json  # Paper-specific templates
  python3 phase_0_sim.py --batch-size 20                    # Custom batch size
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timezone

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from phase_0_config import (
    BATCH_SIZE, MAX_CANDIDATES_PER_TEMPLATE, MAX_CONCURRENT,
    SIMULATION_TIMEOUT, PHASE_0_OUTPUT_DIR
)
from phase_0_utils import (
    setup_logger, load_templates, load_template_by_id,
    save_simulation_results, save_individual_result,
    print_summary, get_summary_stats
)

from brain_api import BrainClient
from generate_candidates import expand_template, FieldValidator
from research_target import load_target

logger = setup_logger(__name__)


def generate_candidates_from_templates(
    templates: List[Dict[str, Any]],
    max_per_template: int = 8,
) -> List[Dict[str, Any]]:
    """Generate candidates from templates."""
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
    max_concurrent: int = 2,
) -> List[Dict[str, Any]]:
    """Batch simulate candidates."""
    
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
                sharpe = sim.get("sim_data", {}).get("is", {}).get("sharpe")
                fitness = sim.get("sim_data", {}).get("is", {}).get("fitness")
                turnover = sim.get("sim_data", {}).get("is", {}).get("turnover")
                
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
                    print(f"  ✗ {status} (expr_len={len(result.get('expression', ''))})")
            
            all_results.extend(batch_results)
            
        except Exception as e:
            logger.error(f"Batch {batch_num} failed: {e}")
    
    return all_results


def main():
    parser = argparse.ArgumentParser(description="Phase 0: Batch simulate templates")
    parser.add_argument("--template", help="Specific template ID to simulate")
    parser.add_argument("--extraction", help="extraction_src_XXX.json file for paper-specific templates")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Batch size")
    parser.add_argument("--max-per-template", type=int, default=MAX_CANDIDATES_PER_TEMPLATE)
    parser.add_argument("--max-concurrent", type=int, default=MAX_CONCURRENT)
    parser.add_argument("--output", help="Output file (default: phase_0/output/simulation_results.json)")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("  Phase 0 — Batch Simulation")
    print("=" * 70 + "\n")
    
    # Load templates
    if args.template:
        logger.info(f"Loading specific template: {args.template}")
        tmpl = load_template_by_id(args.template)
        if not tmpl:
            print(f"✗ Template not found: {args.template}")
            return 1
        templates = [tmpl]
    elif args.extraction:
        # Load from extraction JSON (paper-specific templates)
        logger.info(f"Loading templates from extraction file: {args.extraction}")
        extraction_file = Path(args.extraction)
        if not extraction_file.exists():
            # Try in workspace root
            extraction_file = Path(__file__).parent.parent / args.extraction
        
        if not extraction_file.exists():
            print(f"✗ Extraction file not found: {args.extraction}")
            return 1
        
        try:
            extraction_data = json.loads(extraction_file.read_text(encoding="utf-8"))
            if isinstance(extraction_data, list):
                templates = extraction_data
            elif isinstance(extraction_data, dict) and "templates" in extraction_data:
                templates = extraction_data["templates"]
            else:
                templates = extraction_data
            
            print(f"[load] Loaded {len(templates)} template(s) from {extraction_file.name}\n")
        except Exception as e:
            logger.error(f"Failed to load extraction file: {e}")
            return 1
    else:
        templates = load_templates()
    
    if not templates:
        print("✗ No templates found")
        return 1
    
    print(f"[load] Loaded {len(templates)} template(s)\n")
    
    # Generate candidates
    print("[gen] Generating candidates...")
    candidates = generate_candidates_from_templates(
        templates,
        max_per_template=args.max_per_template
    )
    print(f"[gen] Generated {len(candidates)} candidates\n")
    
    if not candidates:
        print("✗ No candidates generated")
        return 1
    
    # Simulate
    results = batch_simulate(
        candidates,
        batch_size=args.batch_size,
        max_concurrent=args.max_concurrent
    )
    
    # Save results
    save_simulation_results(results)
    print_summary(results)
    
    # Statistics
    stats = get_summary_stats(results)
    print(f"[save] Results saved to {PHASE_0_OUTPUT_DIR}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
