#!/usr/bin/env python3
"""
Regional Metrics Analyzer
Phân tích chi tiết metrics theo region từ simulation results.

Usage:
  python3 analyze_regional_metrics.py                          # Phân tích output/simulation_results.json
  python3 analyze_regional_metrics.py --file output/simulation_results.json
  python3 analyze_regional_metrics.py --neutralization SLOW    # Lọc theo neutralization
  python3 analyze_regional_metrics.py --top 20                 # Top 20 alphas by overall fitness
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import statistics


# ============================================================================
# CONFIGURATION
# ============================================================================

PHASE_1_PLUS_ROOT = Path(__file__).parent
DEFAULT_RESULTS_FILE = PHASE_1_PLUS_ROOT / "output" / "simulation_results.json"

REGIONS = {
    "APAC": "glbApac",
    "EMEA": "glbEmea", 
    "AMER": "glbAmer",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_results(filepath: str) -> List[Dict[str, Any]]:
    """Load simulation results from JSON file."""
    with open(filepath, "r") as f:
        data = json.load(f)
    
    return data.get("results", [])


def extract_metrics(result: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extract metrics for overall + all regions from result."""
    metrics = {}
    
    if result.get("status") != "COMPLETE":
        return metrics
    
    sim_data = result.get("sim_data", {})
    is_data = sim_data.get("is", {})
    
    # Overall
    metrics["OVERALL"] = {
        "sharpe": is_data.get("sharpe", 0),
        "returns": is_data.get("returns", 0),
        "turnover": is_data.get("turnover", 0),
        "fitness": is_data.get("fitness", 0),
        "drawdown": is_data.get("drawdown", 0),
    }
    
    # Regions
    for region_name, region_key in REGIONS.items():
        region_data = is_data.get(region_key, {})
        metrics[region_name] = {
            "sharpe": region_data.get("sharpe", 0),
            "returns": region_data.get("returns", 0),
            "turnover": region_data.get("turnover", 0),
            "fitness": region_data.get("fitness", 0),
            "drawdown": region_data.get("drawdown", 0),
        }
    
    return metrics


def calculate_aggregates(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aggregate statistics across all regions."""
    metrics_by_region = defaultdict(list)
    
    for result in results:
        if result.get("status") != "COMPLETE":
            continue
        
        metrics = extract_metrics(result)
        
        for region, metric_dict in metrics.items():
            metrics_by_region[region].append(metric_dict)
    
    aggregates = {}
    
    for region, metric_list in metrics_by_region.items():
        if not metric_list:
            continue
        
        sharpes = [m.get("sharpe", 0) for m in metric_list]
        returns_list = [m.get("returns", 0) for m in metric_list]
        turnovers = [m.get("turnover", 0) for m in metric_list]
        fitnesses = [m.get("fitness", 0) for m in metric_list]
        drawdowns = [m.get("drawdown", 0) for m in metric_list]
        
        aggregates[region] = {
            "count": len(metric_list),
            "sharpe": {
                "mean": statistics.mean(sharpes),
                "median": statistics.median(sharpes),
                "min": min(sharpes),
                "max": max(sharpes),
                "stdev": statistics.stdev(sharpes) if len(sharpes) > 1 else 0,
            },
            "returns": {
                "mean": statistics.mean(returns_list),
                "median": statistics.median(returns_list),
                "min": min(returns_list),
                "max": max(returns_list),
                "stdev": statistics.stdev(returns_list) if len(returns_list) > 1 else 0,
            },
            "turnover": {
                "mean": statistics.mean(turnovers),
                "median": statistics.median(turnovers),
                "min": min(turnovers),
                "max": max(turnovers),
                "stdev": statistics.stdev(turnovers) if len(turnovers) > 1 else 0,
            },
            "fitness": {
                "mean": statistics.mean(fitnesses),
                "median": statistics.median(fitnesses),
                "min": min(fitnesses),
                "max": max(fitnesses),
                "stdev": statistics.stdev(fitnesses) if len(fitnesses) > 1 else 0,
            },
            "drawdown": {
                "mean": statistics.mean(drawdowns),
                "median": statistics.median(drawdowns),
                "min": min(drawdowns),
                "max": max(drawdowns),
                "stdev": statistics.stdev(drawdowns) if len(drawdowns) > 1 else 0,
            }
        }
    
    return aggregates


def print_regional_comparison(results: List[Dict[str, Any]]):
    """Print regional metrics comparison."""
    print("\n" + "=" * 140)
    print("  REGIONAL METRICS COMPARISON - ALL ALPHAS")
    print("=" * 140)
    
    for region in ["OVERALL", "APAC", "EMEA", "AMER"]:
        print(f"\n🌍 {region} REGION")
        print("-" * 140)
        print(f"{'Alpha ID':<12} {'Desc':<30} {'Sharpe':<10} {'Returns':<12} {'Turnover':<12} {'Fitness':<10} {'Drawdown':<10}")
        print("-" * 140)
        
        rows = []
        for result in results:
            if result.get("status") != "COMPLETE":
                continue
            
            alpha_id = result.get("alpha_id", "")[:11]
            desc = result.get("description", "")[:29]
            
            metrics = extract_metrics(result)
            metric_dict = metrics.get(region, {})
            
            sharpe = metric_dict.get("sharpe", 0)
            returns = metric_dict.get("returns", 0)
            turnover = metric_dict.get("turnover", 0)
            fitness = metric_dict.get("fitness", 0)
            drawdown = metric_dict.get("drawdown", 0)
            
            rows.append((region, alpha_id, desc, sharpe, returns, turnover, fitness, drawdown))
        
        # Sort by sharpe (descending)
        rows.sort(key=lambda x: x[3], reverse=True)
        
        for row in rows[:10]:  # Top 10 per region
            _, alpha_id, desc, sharpe, returns, turnover, fitness, drawdown = row
            print(f"{alpha_id:<12} {desc:<30} {sharpe:>9.3f}  {returns:>10.4f}  {turnover:>10.4f}  {fitness:>9.3f}  {drawdown:>9.3f}")
        
        if len(rows) > 10:
            print(f"... and {len(rows) - 10} more")
    
    print("\n" + "=" * 140)


def print_aggregate_stats(aggregates: Dict[str, Dict[str, Any]]):
    """Print aggregate statistics."""
    print("\n" + "=" * 140)
    print("  AGGREGATE STATISTICS BY REGION")
    print("=" * 140)
    
    for region in ["OVERALL", "APAC", "EMEA", "AMER"]:
        if region not in aggregates:
            continue
        
        stats = aggregates[region]
        count = stats.get("count", 0)
        
        print(f"\n🌍 {region} (n={count} alphas)")
        print("-" * 140)
        
        for metric_name in ["sharpe", "returns", "turnover", "fitness", "drawdown"]:
            metric_stats = stats.get(metric_name, {})
            mean = metric_stats.get("mean", 0)
            median = metric_stats.get("median", 0)
            min_val = metric_stats.get("min", 0)
            max_val = metric_stats.get("max", 0)
            stdev = metric_stats.get("stdev", 0)
            
            print(f"  {metric_name.upper():<10}: "
                  f"mean={mean:>8.4f}  median={median:>8.4f}  "
                  f"[{min_val:>8.4f} ~ {max_val:>8.4f}]  stdev={stdev:>8.4f}")
    
    print("\n" + "=" * 140)


def print_regional_consistency(results: List[Dict[str, Any]]):
    """Analyze consistency of alphas across regions."""
    print("\n" + "=" * 140)
    print("  REGIONAL CONSISTENCY ANALYSIS")
    print("=" * 140)
    print("\nAnalyzing how well alphas perform across different regions...\n")
    
    # Calculate region-to-region correlation
    regional_sharpes = {region: [] for region in ["APAC", "EMEA", "AMER"]}
    
    for result in results:
        if result.get("status") != "COMPLETE":
            continue
        
        metrics = extract_metrics(result)
        
        for region in ["APAC", "EMEA", "AMER"]:
            sharpe = metrics.get(region, {}).get("sharpe", 0)
            regional_sharpes[region].append(sharpe)
    
    # Find best and worst performing alphas per region
    print("🏆 TOP 5 PERFORMERS BY REGION (by Sharpe Ratio)")
    print("-" * 140)
    
    for region in ["APAC", "EMEA", "AMER"]:
        print(f"\n{region}:")
        
        region_key = REGIONS[region]
        top_results = []
        
        for result in results:
            if result.get("status") != "COMPLETE":
                continue
            
            sim_data = result.get("sim_data", {})
            is_data = sim_data.get("is", {})
            region_data = is_data.get(region_key, {})
            
            sharpe = region_data.get("sharpe", 0)
            alpha_id = result.get("alpha_id", "")
            
            top_results.append((alpha_id, sharpe))
        
        top_results.sort(key=lambda x: x[1], reverse=True)
        
        for i, (alpha_id, sharpe) in enumerate(top_results[:5], 1):
            print(f"  {i}. {alpha_id:<12} Sharpe: {sharpe:>8.3f}")
    
    print("\n" + "=" * 140)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Analyze Regional Metrics from Simulation Results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 analyze_regional_metrics.py
  python3 analyze_regional_metrics.py --file output/simulation_results.json
  python3 analyze_regional_metrics.py --top 50
        """
    )
    
    parser.add_argument("--file", default=str(DEFAULT_RESULTS_FILE),
                       help="Path to simulation_results.json")
    parser.add_argument("--top", type=int, default=None,
                       help="Show top N alphas per region")
    
    args = parser.parse_args()
    
    # Load results
    results_file = Path(args.file)
    
    if not results_file.exists():
        print(f"✗ File not found: {results_file}")
        return 1
    
    print(f"\n📊 Loading results from: {results_file}")
    results = load_results(str(results_file))
    
    complete_count = sum(1 for r in results if r.get("status") == "COMPLETE")
    print(f"✓ Loaded {len(results)} alphas ({complete_count} complete)\n")
    
    if complete_count == 0:
        print("✗ No complete results to analyze")
        return 1
    
    # Calculate aggregates
    aggregates = calculate_aggregates(results)
    
    # Print analyses
    print_aggregate_stats(aggregates)
    print_regional_comparison(results)
    print_regional_consistency(results)
    
    print("✓ Analysis complete!\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
