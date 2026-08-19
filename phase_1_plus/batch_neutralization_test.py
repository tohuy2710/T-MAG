#!/usr/bin/env python3
"""
Batch Neutralization Test
Kiểm định một hoặc nhiều alphas với các neutralization settings khác nhau.
Tạo comparison matrix: alphas x neutralization settings.

Usage:
  python3 batch_neutralization_test.py --alphas alphas_4steps_cmf.txt
  python3 batch_neutralization_test.py --alphas alphas_4steps_cmf.txt --step 4
  python3 batch_neutralization_test.py --limit 5  # Test top 5 alphas
  python3 batch_neutralization_test.py --settings SLOW FAST SUBINDUSTRY
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone
from collections import defaultdict

# Add parent scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from brain_api import BrainClient


# ============================================================================
# CONFIGURATION
# ============================================================================

PHASE_1_PLUS_ROOT = Path(__file__).parent
OUTPUT_DIR = PHASE_1_PLUS_ROOT / "output"
BATCH_TEST_OUTPUT_DIR = OUTPUT_DIR / "neutralization_robustness"

NEUTRALIZATION_SETTINGS = [
    "SLOW",
    "FAST",
    "SLOW_AND_FAST",
    "SUBINDUSTRY",
    "CROWDING"
]

REGIONS = {
    "APAC": "glbApac",
    "EMEA": "glbEmea",
    "AMER": "glbAmer",
}

# Create output directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BATCH_TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SETTINGS_TEMPLATE = {
    "region": "GLB",
    "universe": "TOPDIV3000",
    "delay": 1,
    "decay": 10,
    "truncation": 0.08,
    "pasteurization": "ON",
    "unit_handling": "VERIFY",
    "nan_handling": "OFF",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_alphas_from_file(filepath: str, step_filter: int = None, limit: int = None) -> List[Dict[str, Any]]:
    """Load alphas from file."""
    candidates = []
    
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    current_desc = None
    for line in lines:
        line = line.strip()
        
        if not line or line.startswith("#"):
            if line.startswith("#"):
                current_desc = line[1:].strip()
            continue
        
        expr = line
        
        # Extract step
        step_num = None
        if current_desc:
            if "Step3" in current_desc or "BƯỚC 3" in current_desc:
                step_num = 3
            elif "Step4" in current_desc or "BƯỚC 4" in current_desc:
                step_num = 4
            elif "Step2" in current_desc or "Param:" in current_desc or "BƯỚC 2" in current_desc:
                step_num = 2
        
        if step_filter is not None and step_num != step_filter:
            current_desc = None
            continue
        
        candidate = {
            "expression": expr,
            "description": current_desc or f"Alpha",
            "step": step_num,
        }
        
        candidates.append(candidate)
        current_desc = None
        
        if limit and len(candidates) >= limit:
            break
    
    return candidates


def extract_metrics(sim_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extract metrics for overall + regions."""
    metrics = {}
    
    is_data = sim_data.get("is", {})
    
    # Overall
    metrics["OVERALL"] = {
        "sharpe": is_data.get("sharpe", 0),
        "returns": is_data.get("returns", 0),
        "turnover": is_data.get("turnover", 0),
        "fitness": is_data.get("fitness", 0),
    }
    
    # Regions
    for region_name, region_key in REGIONS.items():
        region_data = is_data.get(region_key, {})
        metrics[region_name] = {
            "sharpe": region_data.get("sharpe", 0),
            "returns": region_data.get("returns", 0),
            "turnover": region_data.get("turnover", 0),
            "fitness": region_data.get("fitness", 0),
        }
    
    return metrics


def simulate_batch(
    alphas: List[Dict[str, Any]],
    neutralizations: List[str],
    client: BrainClient,
    max_concurrent: int = 3
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Simulate alphas with different neutralization settings.
    
    Returns:
        {
            "alpha_1_expr": [
                {"neutralization": "SLOW", "status": "COMPLETE", "metrics": {...}},
                {"neutralization": "FAST", "status": "COMPLETE", "metrics": {...}},
                ...
            ],
            ...
        }
    """
    
    results_matrix = {}
    total_sims = len(alphas) * len(neutralizations)
    current_sim = 0
    
    print(f"\n⏳ Running {total_sims} simulations ({len(alphas)} alphas × {len(neutralizations)} settings)...\n")
    
    # Build candidate list with neutralization variants
    candidates_to_sim = []
    alpha_mapping = {}  # Track which candidate corresponds to which alpha
    
    for alpha in alphas:
        expr = alpha.get("expression", "")
        
        for neut in neutralizations:
            # Only create candidates if alpha has <neut> placeholder or is generic
            candidate_expr = expr
            if "<neut>" in expr:
                candidate_expr = expr.replace("<neut>", neut)
            
            settings = DEFAULT_SETTINGS_TEMPLATE.copy()
            settings["neutralization"] = neut
            
            candidate = {
                "expression": candidate_expr,
                "description": f"{alpha.get('description', '')} | {neut}",
                "settings": settings,
                "alpha_idx": len([c for c in candidates_to_sim if c.get("alpha_id") == id(alpha)]),
                "neutralization": neut,
                "alpha_id": id(alpha),
            }
            
            candidates_to_sim.append(candidate)
            
            if expr not in alpha_mapping:
                alpha_mapping[expr] = []
            alpha_mapping[expr].append((neut, candidate))
    
    # Simulate in batches
    sim_results_flat = []
    
    for i in range(0, len(candidates_to_sim), max_concurrent):
        batch = candidates_to_sim[i:i+max_concurrent]
        batch_num = i // max_concurrent + 1
        total_batches = (len(candidates_to_sim) + max_concurrent - 1) // max_concurrent
        
        print(f"[{batch_num}/{total_batches}] Simulating {len(batch)} candidates...")
        
        try:
            for result in client.batch_simulate_stream(batch, max_concurrent=max_concurrent):
                current_sim += 1
                
                sim = result.get("sim_result", {})
                status = sim.get("status", "ERROR")
                
                expr = result.get("expression", "")
                neut = result.get("neutralization", "")
                alpha_idx = result.get("alpha_idx", 0)
                
                sim_result = {
                    "expression": expr,
                    "neutralization": neut,
                    "status": status,
                    "alpha_id": sim.get("alpha_id"),
                    "metrics": extract_metrics(sim.get("sim_data", {})) if status == "COMPLETE" else {},
                    "error": sim.get("message") if status != "COMPLETE" else None,
                }
                
                sim_results_flat.append(sim_result)
                
                # Pretty print progress
                if status == "COMPLETE":
                    metrics = sim_result.get("metrics", {})
                    overall = metrics.get("OVERALL", {})
                    sharpe = overall.get("sharpe", 0)
                    returns = overall.get("returns", 0)
                    print(f"     [{current_sim}/{total_sims}] ✓ {neut:<15} "
                          f"sharpe={sharpe:>7.3f} returns={returns:>8.4f}")
                else:
                    error = sim.get("message", "unknown")[:30]
                    print(f"     [{current_sim}/{total_sims}] ✗ {neut:<15} {error}")
        
        except Exception as e:
            print(f"     ✗ Batch error: {e}")
            import traceback
            traceback.print_exc()
    
    # Reorganize results by alpha expression
    for expr, mapping in alpha_mapping.items():
        results_matrix[expr] = []
        
        for neut, candidate in mapping:
            # Find corresponding sim result
            matching = [r for r in sim_results_flat if r.get("neutralization") == neut and r.get("expression") == candidate.get("expression")]
            
            if matching:
                results_matrix[expr].append(matching[0])
    
    return results_matrix


def save_results_json(results_matrix: Dict[str, List[Dict[str, Any]]]):
    """Save matrix results to JSON."""
    output_file = BATCH_TEST_OUTPUT_DIR / "batch_neutralization_matrix.json"
    
    output_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_alphas": len(results_matrix),
        "total_results": sum(len(v) for v in results_matrix.values()),
        "results": results_matrix,
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved matrix results to: {output_file}")


def save_results_csv(results_matrix: Dict[str, List[Dict[str, Any]]]):
    """Save matrix in CSV format."""
    import csv
    
    output_file = BATCH_TEST_OUTPUT_DIR / "batch_neutralization_matrix.csv"
    
    # Collect all neutralizations
    all_neutralizations = set()
    for alpha_results in results_matrix.values():
        for r in alpha_results:
            all_neutralizations.add(r.get("neutralization", ""))
    all_neutralizations = sorted(list(all_neutralizations))
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        # Build headers: Alpha | Neut1_Sharpe | Neut1_Returns | Neut1_Turnover | Neut2_Sharpe | ...
        headers = ["Alpha_Expr"]
        for neut in all_neutralizations:
            headers.extend([f"{neut}_Sharpe", f"{neut}_Returns", f"{neut}_Turnover", f"{neut}_Fitness"])
        writer.writerow(headers)
        
        # Write data rows
        for expr, alpha_results in results_matrix.items():
            expr_short = expr[:80] if len(expr) > 80 else expr
            row = [expr_short]
            
            # Create lookup map
            neut_map = {r.get("neutralization"): r for r in alpha_results}
            
            for neut in all_neutralizations:
                result = neut_map.get(neut, {})
                
                if result.get("status") == "COMPLETE":
                    metrics = result.get("metrics", {}).get("OVERALL", {})
                    row.extend([
                        metrics.get("sharpe", ""),
                        metrics.get("returns", ""),
                        metrics.get("turnover", ""),
                        metrics.get("fitness", ""),
                    ])
                else:
                    row.extend(["ERROR", "ERROR", "ERROR", "ERROR"])
            
            writer.writerow(row)
    
    print(f"✓ Saved CSV matrix to: {output_file}")


def print_matrix_comparison(results_matrix: Dict[str, List[Dict[str, Any]]]):
    """Print comparison matrix."""
    print("\n" + "=" * 150)
    print("  NEUTRALIZATION SETTINGS COMPARISON MATRIX")
    print("=" * 150)
    
    # Collect all neutralizations
    all_neutralizations = set()
    for alpha_results in results_matrix.values():
        for r in alpha_results:
            all_neutralizations.add(r.get("neutralization", ""))
    all_neutralizations = sorted(list(all_neutralizations))
    
    print(f"\nTesting {len(results_matrix)} alphas × {len(all_neutralizations)} settings:")
    print(f"Settings: {', '.join(all_neutralizations)}\n")
    
    # Print matrix: each row is alpha, columns are neutralizations
    print("SHARPE RATIO COMPARISON")
    print("-" * 150)
    print(f"{'Alpha':<40}", end="")
    for neut in all_neutralizations:
        print(f" {neut:<12}", end="")
    print()
    print("-" * 150)
    
    for i, (expr, alpha_results) in enumerate(results_matrix.items(), 1):
        expr_short = expr[:39] if len(expr) > 39 else expr
        print(f"{expr_short:<40}", end="")
        
        neut_map = {r.get("neutralization"): r for r in alpha_results}
        
        for neut in all_neutralizations:
            result = neut_map.get(neut, {})
            
            if result.get("status") == "COMPLETE":
                sharpe = result.get("metrics", {}).get("OVERALL", {}).get("sharpe", 0)
                print(f" {sharpe:>11.3f}", end="")
            else:
                print(f" {'ERROR':>11}", end="")
        
        print()
    
    # Print regional breakdown for best performers
    print("\n" + "=" * 150)
    print("  REGIONAL BREAKDOWN - TOP PERFORMERS")
    print("=" * 150)
    
    for neut in all_neutralizations:
        print(f"\n🌍 {neut}")
        print("-" * 100)
        print(f"{'Alpha':<40} {'APAC':<12} {'EMEA':<12} {'AMER':<12} {'Overall':<12}")
        print("-" * 100)
        
        # Find top 5 for this neutralization
        top_alphas = []
        for expr, alpha_results in results_matrix.items():
            matching = [r for r in alpha_results if r.get("neutralization") == neut]
            if matching and matching[0].get("status") == "COMPLETE":
                sharpe = matching[0].get("metrics", {}).get("OVERALL", {}).get("sharpe", 0)
                top_alphas.append((expr, matching[0], sharpe))
        
        top_alphas.sort(key=lambda x: x[2], reverse=True)
        
        for expr, result, _ in top_alphas[:5]:
            expr_short = expr[:39] if len(expr) > 39 else expr
            metrics = result.get("metrics", {})
            
            apac_s = metrics.get("APAC", {}).get("sharpe", 0)
            emea_s = metrics.get("EMEA", {}).get("sharpe", 0)
            amer_s = metrics.get("AMER", {}).get("sharpe", 0)
            overall_s = metrics.get("OVERALL", {}).get("sharpe", 0)
            
            print(f"{expr_short:<40} {apac_s:>11.3f}  {emea_s:>11.3f}  {amer_s:>11.3f}  {overall_s:>11.3f}")
    
    print("\n" + "=" * 150)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Batch Test Multiple Alphas with Different Neutralization Settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 batch_neutralization_test.py --alphas alphas_4steps_cmf.txt
  python3 batch_neutralization_test.py --alphas alphas_4steps_cmf.txt --step 4
  python3 batch_neutralization_test.py --alphas alphas_4steps_cmf.txt --limit 3
  python3 batch_neutralization_test.py --settings SLOW FAST SUBINDUSTRY
        """
    )
    
    parser.add_argument("--alphas", required=True,
                       help="File containing alpha expressions")
    parser.add_argument("--step", type=int, choices=[2, 3, 4],
                       help="Filter alphas by step")
    parser.add_argument("--limit", type=int, default=None,
                       help="Limit number of alphas to test")
    parser.add_argument("--settings", nargs="+",
                       default=NEUTRALIZATION_SETTINGS,
                       help="Neutralization settings to test")
    parser.add_argument("--max-concurrent", type=int, default=3,
                       help="Max concurrent simulations")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 150)
    print("  BATCH NEUTRALIZATION TEST - REGIONAL ANALYSIS")
    print("=" * 150)
    
    # Load alphas
    alpha_file = PHASE_1_PLUS_ROOT / args.alphas
    
    if not alpha_file.exists():
        print(f"\n✗ File not found: {alpha_file}")
        return 1
    
    print(f"\n📄 Loading alphas from: {alpha_file}")
    alphas = load_alphas_from_file(str(alpha_file), step_filter=args.step, limit=args.limit)
    print(f"✓ Loaded {len(alphas)} alphas")
    
    if not alphas:
        print("✗ No alphas loaded")
        return 1
    
    print(f"✓ Testing with {len(args.settings)} neutralization settings: {', '.join(args.settings)}")
    
    # Show sample
    print(f"\nSample alphas:")
    for i, alpha in enumerate(alphas[:2], 1):
        desc = alpha.get("description", "")[:50]
        print(f"  {i}. {desc}")
    if len(alphas) > 2:
        print(f"  ... and {len(alphas) - 2} more")
    
    # Connect to BRAIN API
    print(f"\n🔗 Connecting to BRAIN API...")
    client = BrainClient(max_concurrent=args.max_concurrent)
    client.connect()
    print("✓ Connected!\n")
    
    # Run batch simulation
    results_matrix = simulate_batch(alphas, args.settings, client, max_concurrent=args.max_concurrent)
    
    # Save results
    print("\n💾 Saving results...")
    save_results_json(results_matrix)
    save_results_csv(results_matrix)
    
    # Print comparison
    print_matrix_comparison(results_matrix)
    
    print("✓ Batch test completed!\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
