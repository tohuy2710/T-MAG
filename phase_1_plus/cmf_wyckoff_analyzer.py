#!/usr/bin/env python3
"""
CMF Wyckoff Alpha Analyzer
Phân tích kết quả simulation và tạo report.

Usage:
  python3 cmf_wyckoff_analyzer.py                    # Phân tích và tạo report
  python3 cmf_wyckoff_analyzer.py --results-file results.json
"""

import sys
import json
import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from statistics import mean, stdev

PHASE_1_PLUS_ROOT = Path(__file__).parent
OUTPUT_DIR = PHASE_1_PLUS_ROOT / "output" / "cmf_wyckoff"
RESULTS_FILE = OUTPUT_DIR / "results.json"
CSV_FILE = OUTPUT_DIR / "results.csv"
REPORT_FILE = OUTPUT_DIR / "CMF_WYCKOFF_REPORT.md"


# ============================================================================
# ANALYSIS
# ============================================================================

def load_results(filepath: str) -> List[Dict[str, Any]]:
    """Load results from JSON."""
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("results", [])


def analyze_by_level(results: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Group and analyze results by level."""
    
    by_level = {}
    
    for r in results:
        level = r.get("level", 0)
        status = r.get("status", "")
        
        if level not in by_level:
            by_level[level] = {
                "total": 0,
                "complete": 0,
                "sharpes": [],
                "fitnesses": [],
                "turnovers": [],
                "returns": [],
                "alphas": [],
            }
        
        by_level[level]["total"] += 1
        by_level[level]["alphas"].append(r)
        
        if status == "COMPLETE":
            by_level[level]["complete"] += 1
            
            sim_data = r.get("sim_data", {})
            is_data = sim_data.get("is", {})
            
            by_level[level]["sharpes"].append(is_data.get("sharpe", 0))
            by_level[level]["fitnesses"].append(is_data.get("fitness", 0))
            by_level[level]["turnovers"].append(is_data.get("turnover", 0))
            by_level[level]["returns"].append(is_data.get("returns", 0))
    
    # Calculate stats
    for level, data in by_level.items():
        if data["complete"] > 0:
            data["sharpe_mean"] = mean(data["sharpes"])
            data["fitness_mean"] = mean(data["fitnesses"])
            data["turnover_mean"] = mean(data["turnovers"])
            data["returns_mean"] = mean(data["returns"])
            
            data["sharpe_best"] = max(data["sharpes"])
            data["fitness_best"] = max(data["fitnesses"])
            
            if len(data["sharpes"]) > 1:
                data["sharpe_std"] = stdev(data["sharpes"])
            
            if len(data["fitnesses"]) > 1:
                data["fitness_std"] = stdev(data["fitnesses"])
    
    return by_level


def get_top_by_metric(
    results: List[Dict[str, Any]],
    metric: str = "fitness",
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    """Get top N alphas by metric."""
    
    complete = [r for r in results if r.get("status") == "COMPLETE"]
    
    def get_value(r):
        sim_data = r.get("sim_data", {})
        is_data = sim_data.get("is", {})
        return is_data.get(metric, 0)
    
    sorted_alphas = sorted(complete, key=get_value, reverse=True)
    return sorted_alphas[:top_n]


def correlate_metrics(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate correlations between metrics."""
    
    complete = [r for r in results if r.get("status") == "COMPLETE"]
    
    if len(complete) < 2:
        return {}
    
    # Extract metrics
    sharpes = []
    fitnesses = []
    turnovers = []
    returns_list = []
    
    for r in complete:
        sim_data = r.get("sim_data", {})
        is_data = sim_data.get("is", {})
        
        sharpes.append(is_data.get("sharpe", 0))
        fitnesses.append(is_data.get("fitness", 0))
        turnovers.append(is_data.get("turnover", 0))
        returns_list.append(is_data.get("returns", 0))
    
    # Simple correlation (Pearson-like)
    def correlation(x, y):
        n = len(x)
        if n < 2:
            return 0
        mean_x = mean(x)
        mean_y = mean(y)
        cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / n
        std_x = (sum((xi - mean_x)**2 for xi in x) / n) ** 0.5
        std_y = (sum((yi - mean_y)**2 for yi in y) / n) ** 0.5
        if std_x * std_y == 0:
            return 0
        return cov / (std_x * std_y)
    
    return {
        "sharpe_vs_fitness": correlation(sharpes, fitnesses),
        "sharpe_vs_turnover": correlation(sharpes, turnovers),
        "fitness_vs_turnover": correlation(fitnesses, turnovers),
        "fitness_vs_returns": correlation(fitnesses, returns_list),
    }


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_markdown_report(
    results: List[Dict[str, Any]],
    by_level: Dict[int, Dict[str, Any]],
    report_file: str,
):
    """Generate comprehensive markdown report."""
    
    complete = [r for r in results if r.get("status") == "COMPLETE"]
    total = len(results)
    
    # Global stats
    all_sharpes = []
    all_fitnesses = []
    all_turnovers = []
    all_returns = []
    
    for r in complete:
        sim_data = r.get("sim_data", {})
        is_data = sim_data.get("is", {})
        
        all_sharpes.append(is_data.get("sharpe", 0))
        all_fitnesses.append(is_data.get("fitness", 0))
        all_turnovers.append(is_data.get("turnover", 0))
        all_returns.append(is_data.get("returns", 0))
    
    correlations = correlate_metrics(results)
    top_fitness = get_top_by_metric(results, "fitness", 10)
    top_sharpe = get_top_by_metric(results, "sharpe", 10)
    
    # Build report
    lines = []
    
    lines.append("# CMF Wyckoff Alpha Family — Simulation Report\n")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**Region:** GLB | **Universe:** TOPDIV3000\n\n")
    
    # Executive Summary
    lines.append("## Executive Summary\n")
    lines.append(f"- **Total Alphas Tested:** {total}\n")
    lines.append(f"- **Successful:** {len(complete)} ({len(complete)/total*100:.1f}%)\n")
    lines.append(f"- **Failed:** {total - len(complete)}\n\n")
    
    if all_sharpes:
        lines.append(f"### Key Metrics (Complete Alphas)\n\n")
        lines.append("| Metric | Mean | Max | Min | StdDev |\n")
        lines.append("|--------|------|-----|-----|--------|\n")
        
        sharpe_std = stdev(all_sharpes) if len(all_sharpes) > 1 else 0
        lines.append(f"| Sharpe | {mean(all_sharpes):.3f} | {max(all_sharpes):.3f} | "
                    f"{min(all_sharpes):.3f} | {sharpe_std:.3f} |\n")
        
        fitness_std = stdev(all_fitnesses) if len(all_fitnesses) > 1 else 0
        lines.append(f"| Fitness | {mean(all_fitnesses):.3f} | {max(all_fitnesses):.3f} | "
                    f"{min(all_fitnesses):.3f} | {fitness_std:.3f} |\n")
        
        turnover_std = stdev(all_turnovers) if len(all_turnovers) > 1 else 0
        lines.append(f"| Turnover | {mean(all_turnovers):.5f} | {max(all_turnovers):.5f} | "
                    f"{min(all_turnovers):.5f} | {turnover_std:.5f} |\n")
        
        returns_std = stdev(all_returns) if len(all_returns) > 1 else 0
        lines.append(f"| Returns (%) | {mean(all_returns):.4f} | {max(all_returns):.4f} | "
                    f"{min(all_returns):.4f} | {returns_std:.4f} |\n\n")
    
    # Performance by Level
    lines.append("## Performance by Alpha Level\n\n")
    lines.append("| Level | Alpha Count | Complete | Avg Sharpe | Best Fitness | Avg Turnover |\n")
    lines.append("|-------|-------------|----------|-----------|--------------|---------------|\n")
    
    for level in sorted(by_level.keys()):
        data = by_level[level]
        avg_sharpe = data.get("sharpe_mean", 0)
        best_fitness = data.get("fitness_best", 0)
        avg_turnover = data.get("turnover_mean", 0)
        
        lines.append(f"| L{level:2d} | {data['total']:3d} | {data['complete']:8d} | "
                    f"{avg_sharpe:9.3f} | {best_fitness:12.3f} | {avg_turnover:13.5f} |\n")
    
    lines.append("\n")
    
    # Metric Correlations
    if correlations:
        lines.append("## Metric Correlations\n\n")
        for corr_name, corr_value in correlations.items():
            lines.append(f"- **{corr_name}:** {corr_value:.3f}\n")
        lines.append("\n")
    
    # Top Performers by Fitness
    if top_fitness:
        lines.append("## Top 10 Alphas by Fitness\n\n")
        lines.append("| Rank | Alpha ID | Description | Sharpe | Fitness | Turnover | Returns |\n")
        lines.append("|------|----------|-------------|--------|---------|----------|----------|\n")
        
        for i, alpha in enumerate(top_fitness, 1):
            sim_data = alpha.get("sim_data", {})
            is_data = sim_data.get("is", {})
            
            alpha_id = alpha.get("alpha_id", "")
            desc = alpha.get("description", "")
            sharpe = is_data.get("sharpe", 0)
            fitness = is_data.get("fitness", 0)
            turnover = is_data.get("turnover", 0)
            returns = is_data.get("returns", 0)
            
            lines.append(f"| {i:2d} | {alpha_id:8s} | {desc:20s} | {sharpe:6.3f} | "
                        f"{fitness:7.3f} | {turnover:8.5f} | {returns:8.4f} |\n")
        
        lines.append("\n")
    
    # Top Performers by Sharpe
    if top_sharpe:
        lines.append("## Top 10 Alphas by Sharpe Ratio\n\n")
        lines.append("| Rank | Alpha ID | Description | Sharpe | Fitness | Turnover | Returns |\n")
        lines.append("|------|----------|-------------|--------|---------|----------|----------|\n")
        
        for i, alpha in enumerate(top_sharpe, 1):
            sim_data = alpha.get("sim_data", {})
            is_data = sim_data.get("is", {})
            
            alpha_id = alpha.get("alpha_id", "")
            desc = alpha.get("description", "")
            sharpe = is_data.get("sharpe", 0)
            fitness = is_data.get("fitness", 0)
            turnover = is_data.get("turnover", 0)
            returns = is_data.get("returns", 0)
            
            lines.append(f"| {i:2d} | {alpha_id:8s} | {desc:20s} | {sharpe:6.3f} | "
                        f"{fitness:7.3f} | {turnover:8.5f} | {returns:8.4f} |\n")
        
        lines.append("\n")
    
    # Detailed Alpha Expressions
    if top_fitness:
        lines.append("## Top Alpha Expressions (for reference)\n\n")
        
        for i, alpha in enumerate(top_fitness[:5], 1):
            alpha_id = alpha.get("alpha_id", "")
            desc = alpha.get("description", "")
            expr = alpha.get("expression", "")
            
            lines.append(f"### {i}. {alpha_id} - {desc}\n\n")
            lines.append(f"```\n{expr}\n```\n\n")
    
    # Findings
    lines.append("## Key Findings\n\n")
    
    if all_sharpes:
        lines.append(f"1. **Sharpe Distribution:** Mean Sharpe of {mean(all_sharpes):.3f} suggests ")
        if mean(all_sharpes) > 1.0:
            lines.append("**strong risk-adjusted returns** for a GLB alpha pool.\n")
        elif mean(all_sharpes) > 0.5:
            lines.append("**moderate risk-adjusted returns** with potential for improvement.\n")
        else:
            lines.append("**low risk-adjusted returns** — may need refinement or combination.\n")
        
        lines.append(f"\n2. **Fitness-Sharpe Correlation:** ")
        if "sharpe_vs_fitness" in correlations:
            corr = correlations["sharpe_vs_fitness"]
            if corr > 0.5:
                lines.append(f"{corr:.3f} (strong positive) — fitness is a reliable metric.\n")
            elif corr > 0:
                lines.append(f"{corr:.3f} (weak positive) — fitness and Sharpe partially aligned.\n")
            else:
                lines.append(f"{corr:.3f} (negative/low) — fitness and Sharpe diverge.\n")
        
        lines.append(f"\n3. **Turnover Profile:** Mean turnover {mean(all_turnovers):.5f} ")
        if mean(all_turnovers) < 0.001:
            lines.append("(very low) is ideal for low transaction costs.\n")
        elif mean(all_turnovers) < 0.01:
            lines.append("(moderate) suggests practical implementation.\n")
        else:
            lines.append("(high) may require decay or other smoothing.\n")
    
    lines.append("\n## Recommendations\n\n")
    
    if top_fitness:
        best_alpha = top_fitness[0]
        lines.append(f"- **Start with:** {best_alpha.get('alpha_id')} ")
        lines.append(f"(Fitness: {best_alpha.get('sim_data', {}).get('is', {}).get('fitness', 0):.3f})\n")
    
    lines.append("- **Test country/region neutralization:** Level 7-9 alphas show promise for GLB\n")
    lines.append("- **Monitor turnover-Sharpe tradeoff:** Some alphas may benefit from decay tuning\n")
    lines.append("- **Combine top performers:** Pool 3-5 uncorrelated alphas for robustness\n")
    lines.append("- **Regional breadth analysis:** Check Sharpe by country/region before deployment\n\n")
    
    lines.append("---\n\n")
    lines.append("*Report generated by cmf_wyckoff_analyzer.py*\n")
    
    # Write report
    with open(report_file, "w", encoding="utf-8") as f:
        f.writelines(lines)
    
    print(f"✓ Report generated: {report_file}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CMF Wyckoff Alpha Analyzer"
    )
    
    parser.add_argument("--results-file", default=str(RESULTS_FILE),
                       help="Path to results.json")
    parser.add_argument("--report-file", default=str(REPORT_FILE),
                       help="Path to output report")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("  CMF WYCKOFF ALPHA ANALYZER")
    print("=" * 80 + "\n")
    
    results_file = Path(args.results_file)
    if not results_file.exists():
        print(f"✗ Results file not found: {results_file}")
        return 1
    
    print(f"[load] Đang đọc: {results_file}")
    results = load_results(str(results_file))
    print(f"[load] Đã load {len(results)} results\n")
    
    print("[analyze] Phân tích theo level...")
    by_level = analyze_by_level(results)
    print(f"[analyze] Tìm thấy {len(by_level)} levels\n")
    
    print(f"[report] Tạo report...")
    generate_markdown_report(results, by_level, args.report_file)
    
    print("\n" + "=" * 80)
    print("  ✓ Hoàn thành phân tích!")
    print("=" * 80 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
