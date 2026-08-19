#!/usr/bin/env python3
"""
Test Multiple Neutralization Settings - Regional Analysis
Kiểm định công thức alpha với nhiều neutralization settings khác nhau.
Tính Sharpe, return, turnover cho overall + các region (APAC, EMEA, AMER).

Usage:
  python3 test_neutralization_settings.py
  python3 test_neutralization_settings.py --alpha "rank(group_neutralize(...))"
  python3 test_neutralization_settings.py --expr-file my_expr.txt
  python3 test_neutralization_settings.py --settings SLOW FAST SUBINDUSTRY
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
NEUTRALIZATION_OUTPUT_DIR = OUTPUT_DIR / "neutralization_robustness"

# Neutralization settings to test
NEUTRALIZATION_SETTINGS = [
    "SLOW",
    "FAST",
    "SLOW_AND_FAST",
    "SUBINDUSTRY",
    "CROWDING"
]

# Regional keys in sim_data.is
REGIONS = {
    "APAC": "glbApac",
    "EMEA": "glbEmea",
    "AMER": "glbAmer",
}

# Create output directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
NEUTRALIZATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# DEFAULT ALPHA FORMULA (from user requirement)
# ============================================================================

DEFAULT_ALPHA = """rank(group_neutralize(rank(ts_rank(sign(short_term_price_change_2 - short_term_price_change), 2)) * (1 - ts_rank(returns, 10)), <neut>))"""

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

def extract_regional_metrics(sim_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract metrics for overall and each region.
    
    Returns:
        {
            "OVERALL": {"sharpe": ..., "returns": ..., "turnover": ..., ...},
            "APAC": {...},
            "EMEA": {...},
            "AMER": {...}
        }
    """
    is_data = sim_data.get("is", {})
    
    metrics = {}
    
    # Overall metrics
    metrics["OVERALL"] = {
        "sharpe": is_data.get("sharpe", 0),
        "returns": is_data.get("returns", 0),
        "turnover": is_data.get("turnover", 0),
        "fitness": is_data.get("fitness", 0),
        "drawdown": is_data.get("drawdown", 0),
        "pnl": is_data.get("pnl", 0),
        "bookSize": is_data.get("bookSize", 0),
        "longCount": is_data.get("longCount", 0),
        "shortCount": is_data.get("shortCount", 0),
        "margin": is_data.get("margin", 0),
    }
    
    # Regional metrics
    for region_name, region_key in REGIONS.items():
        region_data = is_data.get(region_key, {})
        metrics[region_name] = {
            "sharpe": region_data.get("sharpe", 0),
            "returns": region_data.get("returns", 0),
            "turnover": region_data.get("turnover", 0),
            "fitness": region_data.get("fitness", 0),
            "drawdown": region_data.get("drawdown", 0),
            "pnl": region_data.get("pnl", 0),
            "bookSize": region_data.get("bookSize", 0),
            "longCount": region_data.get("longCount", 0),
            "shortCount": region_data.get("shortCount", 0),
            "margin": region_data.get("margin", 0),
        }
    
    return metrics


def simulate_with_setting(
    alpha_expr: str,
    neutralization: str,
    client: BrainClient
) -> Dict[str, Any]:
    """
    Simulate alpha with specific neutralization setting.
    
    Args:
        alpha_expr: Alpha expression (with <neut> placeholder)
        neutralization: Neutralization setting (SLOW, FAST, etc.)
        client: BRAIN API client
        
    Returns:
        Simulation result with metrics
    """
    
    # Replace neutralization placeholder
    expr = alpha_expr.replace("<neut>", neutralization)
    
    # Create settings
    settings = DEFAULT_SETTINGS_TEMPLATE.copy()
    settings["neutralization"] = neutralization
    
    # Create candidate
    candidate = {
        "expression": expr,
        "description": f"Testing {neutralization} neutralization",
        "settings": settings,
    }
    
    try:
        # Simulate (single)
        results = list(client.batch_simulate_stream([candidate], max_concurrent=1))
        
        if results:
            result = results[0]
            sim = result.get("sim_result", {})
            
            return {
                "neutralization": neutralization,
                "status": sim.get("status", "ERROR"),
                "alpha_id": sim.get("alpha_id"),
                "sim_data": sim.get("sim_data"),
                "expression": expr,
                "error": sim.get("message") if sim.get("status") != "COMPLETE" else None,
            }
    except Exception as e:
        return {
            "neutralization": neutralization,
            "status": "ERROR",
            "error": str(e),
            "expression": expr,
        }
    
    return {
        "neutralization": neutralization,
        "status": "ERROR",
        "error": "No result returned",
        "expression": expr,
    }


def save_results_json(all_results: List[Dict[str, Any]]):
    """Save all results to JSON file."""
    output_file = NEUTRALIZATION_OUTPUT_DIR / "neutralization_comparison.json"
    
    output_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_settings_tested": len(all_results),
        "results": all_results,
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved JSON results to: {output_file}\n")


def save_results_csv(all_results: List[Dict[str, Any]]):
    """Save results in CSV format for easy comparison."""
    import csv
    
    output_file = NEUTRALIZATION_OUTPUT_DIR / "neutralization_comparison.csv"
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        # Headers
        headers = ["Neutralization", "Status", "Alpha_ID", "Overall_Sharpe", "Overall_Returns", 
                   "Overall_Turnover", "Overall_Fitness", "APAC_Sharpe", "APAC_Returns", "APAC_Turnover",
                   "EMEA_Sharpe", "EMEA_Returns", "EMEA_Turnover", "AMER_Sharpe", "AMER_Returns", "AMER_Turnover"]
        writer.writerow(headers)
        
        # Data rows
        for result in all_results:
            neut = result.get("neutralization", "")
            status = result.get("status", "")
            alpha_id = result.get("alpha_id", "")
            
            metrics = result.get("metrics", {})
            
            row = [
                neut,
                status,
                alpha_id,
                metrics.get("OVERALL", {}).get("sharpe", ""),
                metrics.get("OVERALL", {}).get("returns", ""),
                metrics.get("OVERALL", {}).get("turnover", ""),
                metrics.get("OVERALL", {}).get("fitness", ""),
                metrics.get("APAC", {}).get("sharpe", ""),
                metrics.get("APAC", {}).get("returns", ""),
                metrics.get("APAC", {}).get("turnover", ""),
                metrics.get("EMEA", {}).get("sharpe", ""),
                metrics.get("EMEA", {}).get("returns", ""),
                metrics.get("EMEA", {}).get("turnover", ""),
                metrics.get("AMER", {}).get("sharpe", ""),
                metrics.get("AMER", {}).get("returns", ""),
                metrics.get("AMER", {}).get("turnover", ""),
            ]
            writer.writerow(row)
    
    print(f"✓ Saved CSV results to: {output_file}\n")


def print_comprehensive_report(all_results: List[Dict[str, Any]]):
    """Print comprehensive comparison report."""
    
    print("\n" + "=" * 120)
    print("  NEUTRALIZATION SETTINGS COMPARISON REPORT")
    print("=" * 120)
    
    print("\n📊 OVERALL METRICS COMPARISON")
    print("-" * 120)
    print(f"{'Neutralization':<20} {'Status':<12} {'Sharpe':<10} {'Returns':<12} {'Turnover':<12} {'Fitness':<10}")
    print("-" * 120)
    
    for result in all_results:
        neut = result.get("neutralization", "")
        status = result.get("status", "")
        metrics = result.get("metrics", {})
        overall = metrics.get("OVERALL", {})
        
        sharpe = overall.get("sharpe", 0)
        returns = overall.get("returns", 0)
        turnover = overall.get("turnover", 0)
        fitness = overall.get("fitness", 0)
        
        status_icon = "✓" if status == "COMPLETE" else "✗"
        print(f"{neut:<20} {status_icon} {status:<10} {sharpe:>9.3f}  {returns:>10.4f}  {turnover:>10.4f}  {fitness:>9.3f}")
    
    print("\n" + "=" * 120)
    print("📍 REGIONAL METRICS BREAKDOWN")
    print("=" * 120)
    
    for region in ["APAC", "EMEA", "AMER"]:
        print(f"\n🌍 {region} REGION")
        print("-" * 100)
        print(f"{'Neutralization':<20} {'Sharpe':<12} {'Returns':<12} {'Turnover':<12} {'Fitness':<10}")
        print("-" * 100)
        
        for result in all_results:
            if result.get("status") != "COMPLETE":
                continue
            
            neut = result.get("neutralization", "")
            metrics = result.get("metrics", {})
            regional = metrics.get(region, {})
            
            sharpe = regional.get("sharpe", 0)
            returns = regional.get("returns", 0)
            turnover = regional.get("turnover", 0)
            fitness = regional.get("fitness", 0)
            
            print(f"{neut:<20} {sharpe:>10.3f}  {returns:>10.4f}  {turnover:>10.4f}  {fitness:>9.3f}")
    
    print("\n" + "=" * 120)
    print("📈 KEY INSIGHTS")
    print("=" * 120)
    
    # Find best by metric
    complete_results = [r for r in all_results if r.get("status") == "COMPLETE"]
    
    if complete_results:
        best_sharpe = max(complete_results, 
                         key=lambda r: r.get("metrics", {}).get("OVERALL", {}).get("sharpe", 0))
        best_returns = max(complete_results,
                          key=lambda r: r.get("metrics", {}).get("OVERALL", {}).get("returns", 0))
        best_fitness = max(complete_results,
                          key=lambda r: r.get("metrics", {}).get("OVERALL", {}).get("fitness", 0))
        
        print(f"\n✓ Best Sharpe Ratio: {best_sharpe.get('neutralization')} "
              f"({best_sharpe.get('metrics', {}).get('OVERALL', {}).get('sharpe', 0):.3f})")
        print(f"✓ Best Returns: {best_returns.get('neutralization')} "
              f"({best_returns.get('metrics', {}).get('OVERALL', {}).get('returns', 0):.4f})")
        print(f"✓ Best Fitness: {best_fitness.get('neutralization')} "
              f"({best_fitness.get('metrics', {}).get('OVERALL', {}).get('fitness', 0):.3f})")
    
    print("\n" + "=" * 120 + "\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Test Multiple Neutralization Settings with Regional Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_neutralization_settings.py                   # Use default formula
  python3 test_neutralization_settings.py --alpha "rank(...)"  # Custom alpha
  python3 test_neutralization_settings.py --settings SLOW FAST SUBINDUSTRY  # Specific settings
        """
    )
    
    parser.add_argument("--alpha", default=None,
                       help="Alpha expression (default: uses formula from requirement)")
    parser.add_argument("--expr-file", default=None,
                       help="Read alpha from file")
    parser.add_argument("--settings", nargs="+", 
                       default=NEUTRALIZATION_SETTINGS,
                       help=f"Neutralization settings to test (default: all)")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 120)
    print("  TEST NEUTRALIZATION SETTINGS - REGIONAL ANALYSIS")
    print("=" * 120)
    print()
    
    # Determine alpha expression
    if args.expr_file and Path(args.expr_file).exists():
        with open(args.expr_file, "r") as f:
            alpha_expr = f.read().strip()
        print(f"📄 Loaded alpha from: {args.expr_file}")
    elif args.alpha:
        alpha_expr = args.alpha
        print(f"📝 Using custom alpha")
    else:
        alpha_expr = DEFAULT_ALPHA
        print(f"📝 Using default alpha formula")
    
    print(f"\n📊 Testing {len(args.settings)} neutralization settings: {', '.join(args.settings)}")
    print(f"   (Note: replacing <neut> placeholder in expression)\n")
    
    # Show alpha expression
    if len(alpha_expr) > 100:
        print(f"Expression:\n   {alpha_expr[:100]}...\n")
    else:
        print(f"Expression:\n   {alpha_expr}\n")
    
    # Connect to BRAIN API
    print("🔗 Connecting to BRAIN API...")
    client = BrainClient(max_concurrent=1)
    client.connect()
    print("✓ Connected!\n")
    
    # Run simulations
    print("⏳ Running simulations...\n")
    all_results = []
    
    for i, neutralization in enumerate(args.settings, 1):
        print(f"[{i}/{len(args.settings)}] Testing {neutralization}...")
        
        result = simulate_with_setting(alpha_expr, neutralization, client)
        
        if result.get("status") == "COMPLETE":
            metrics = extract_regional_metrics(result.get("sim_data", {}))
            result["metrics"] = metrics
            
            overall = metrics.get("OVERALL", {})
            print(f"     ✓ Sharpe: {overall.get('sharpe', 0):.3f}, "
                  f"Returns: {overall.get('returns', 0):.4f}, "
                  f"Turnover: {overall.get('turnover', 0):.4f}")
        else:
            error_msg = result.get("error", "unknown error")
            print(f"     ✗ {error_msg}")
        
        all_results.append(result)
    
    # Save results
    print("\n💾 Saving results...")
    save_results_json(all_results)
    save_results_csv(all_results)
    
    # Print report
    print_comprehensive_report(all_results)
    
    print("✓ Test completed!\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
