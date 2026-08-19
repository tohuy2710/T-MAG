#!/usr/bin/env python3
"""
CMF Wyckoff Alpha Family Simulator
Chạy 53 alpha từ template trên GLB/TOPDIV3000 với settings cố định.

Settings:
  - Neut: MARKET
  - Trunc: 0.08
  - Decay: 10

Usage:
  python3 cmf_wyckoff_simulator.py                          # Chạy tất cả
  python3 cmf_wyckoff_simulator.py --level 4                # Chỉ Level 4
  python3 cmf_wyckoff_simulator.py --start 0 --end 10       # Alpha 0-10
  python3 cmf_wyckoff_simulator.py --batch-size 15          # Batch size lớn
  python3 cmf_wyckoff_simulator.py --dry-run                # Preview only
"""

import sys
import json
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
import csv

# Add parent scripts directory to path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# Try multiple import paths
BrainClient = None
try:
    from brain_api import BrainClient
except ImportError:
    try:
        # Try absolute import
        import importlib.util
        spec = importlib.util.spec_from_file_location("brain_api", SCRIPTS_DIR / "brain_api.py")
        if spec and spec.loader:
            brain_api_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(brain_api_module)
            BrainClient = getattr(brain_api_module, 'BrainClient', None)
    except Exception as e:
        pass

if not BrainClient:
    print("⚠ BrainClient not available - will run in preview mode only")


# ============================================================================
# CONFIGURATION
# ============================================================================

PHASE_1_PLUS_ROOT = Path(__file__).parent
OUTPUT_DIR = PHASE_1_PLUS_ROOT / "output" / "cmf_wyckoff"
INDIVIDUAL_OUTPUT_DIR = OUTPUT_DIR / "individual"
RESULTS_FILE = OUTPUT_DIR / "results.json"
CSV_RESULTS_FILE = OUTPUT_DIR / "results.csv"

# Settings cố định
# Note: For GLB/TOPDIV3000, available neutralizations are:
# SLOW, FAST, SLOW_AND_FAST, SUBINDUSTRY, CROWDING
# Using SUBINDUSTRY as proxy for market-level neutralization (similar to MARKET concept)
FIXED_SETTINGS = {
    "region": "GLB",
    "universe": "TOPDIV3000",
    "delay": 1,
    "neutralization": "SUBINDUSTRY",
    "decay": 10,
    "truncation": 0.08,
    "pasteurization": "ON",
    "unit_handling": "VERIFY",
    "nan_handling": "OFF",
}

# Create output directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INDIVIDUAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# PARSER
# ============================================================================

def parse_alpha_file(filepath: str) -> List[Dict[str, Any]]:
    """
    Parse alpha template file.
    
    Supports two formats:
    1. Original CMF Wyckoff format (# L#.## - Description)
    2. Top5 evolved format (# alpha_id — Description)
    
    Returns: List of {level, index, description, expression, full_desc}
    """
    alphas = []
    
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        
        # Skip empty lines and section headers
        if not line or line.startswith("# ====") or line.startswith("# ==="):
            continue
        
        # Look back for description
        desc_line = None
        for j in range(i-2, max(0, i-5), -1):
            candidate_line = lines[j].strip()
            if candidate_line.startswith("# L") or candidate_line.startswith("# alpha"):
                desc_line = candidate_line
                break
        
        # Skip non-expression lines (headers, comments without expression following)
        if line.startswith("#"):
            continue
        
        # This is an expression
        expr = line
        
        # Parse level and index (try both formats)
        level_match = None
        alpha_id = None
        
        if desc_line:
            # Format 1: # L#.## - Description
            m1 = re.search(r"# L(\d+)\.(\d+)\s*-\s*(.*)", desc_line)
            if m1:
                level = int(m1.group(1))
                idx = int(m1.group(2))
                desc = m1.group(3).strip()
                level_match = (level, idx, desc)
                alpha_id = f"L{level}.{idx:02d}"
            else:
                # Format 2: # alpha_id — Description
                m2 = re.search(r"# (alpha\d+_\S+)\s+—\s+(.*)", desc_line)
                if m2:
                    alpha_id = m2.group(1)
                    desc = m2.group(2).strip()
                    # Assign pseudo-level based on alpha number
                    level = int(alpha_id.split("_")[0].replace("alpha", ""))
                    idx = hash(alpha_id) % 100
                    level_match = (level, idx, desc)
        
        if not alpha_id:
            # Fallback: create ID from expression hash
            alpha_id = f"unknown_{hash(expr) % 10000:04d}"
            level = 99
            idx = hash(expr) % 100
            desc = "Auto-parsed alpha"
            level_match = (level, idx, desc)
        
        if level_match:
            level, idx, desc = level_match
            
            alpha = {
                "level": level,
                "index": idx,
                "id": alpha_id,
                "description": desc,
                "expression": expr,
                "settings": FIXED_SETTINGS.copy(),
            }
            
            alphas.append(alpha)
    
    return alphas


def filter_alphas(
    alphas: List[Dict[str, Any]],
    level_filter: int = None,
    start: int = None,
    end: int = None,
) -> List[Dict[str, Any]]:
    """Filter alphas by level or index range."""
    result = alphas
    
    if level_filter:
        result = [a for a in result if a["level"] == level_filter]
    
    if start is not None or end is not None:
        start = start or 0
        end = end or len(result)
        result = result[start:end]
    
    return result


# ============================================================================
# SIMULATION
# ============================================================================

def simulate_batch(
    alphas: List[Dict[str, Any]],
    batch_size: int = 10,
    max_concurrent: int = 3,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:
    """
    Simulate alphas in batches.
    
    Returns: List of result dicts with metadata and metrics
    """
    
    if dry_run:
        print("\n[DRY RUN MODE] Sẽ không gọi BRAIN API\n")
        results = []
        for alpha in alphas:
            result = {
                "alpha_id": alpha["id"],
                "expression": alpha["expression"],
                "description": alpha["description"],
                "level": alpha["level"],
                "settings": alpha["settings"],
                "status": "DRY_RUN",
                "sim_data": {},
                "simulated_at": datetime.now(timezone.utc).isoformat(),
            }
            results.append(result)
        return results
    
    if not BrainClient:
        print("\n⚠ BrainClient not available - cannot run simulation")
        return []
    
    print(f"\n[sim] Bắt đầu mô phỏng: {len(alphas)} alphas")
    print(f"      Batch size: {batch_size}")
    print(f"      Max concurrent: {max_concurrent}")
    print(f"      Settings: Neut={FIXED_SETTINGS['neutralization']}, "
          f"Trunc={FIXED_SETTINGS['truncation']}, Decay={FIXED_SETTINGS['decay']}\n")
    
    client = BrainClient(max_concurrent=max_concurrent)
    try:
        client.connect()
        print("✓ Đã kết nối BRAIN API\n")
    except Exception as e:
        print(f"✗ Không thể kết nối: {e}")
        return []
    
    all_results = []
    total_batches = (len(alphas) + batch_size - 1) // batch_size
    
    for batch_idx, i in enumerate(range(0, len(alphas), batch_size)):
        batch = alphas[i:i+batch_size]
        batch_num = batch_idx + 1
        
        print(f"[batch {batch_num}/{total_batches}] Mô phỏng {len(batch)} alphas...")
        
        try:
            for result in client.batch_simulate_stream(batch, max_concurrent=max_concurrent):
                sim = result.get("sim_result", {})
                status = sim.get("status", "ERROR")
                alpha_id = sim.get("alpha_id", "?")
                
                # Extract metrics
                sim_data = sim.get("sim_data", {})
                is_data = sim_data.get("is", {})
                sharpe = is_data.get("sharpe", 0)
                fitness = is_data.get("fitness", 0)
                turnover = is_data.get("turnover", 0)
                returns = is_data.get("returns", 0)
                
                output = {
                    "alpha_id": alpha_id,
                    "expression": result.get("expression"),
                    "description": result.get("description"),
                    "level": result.get("level"),
                    "status": status,
                    "sim_data": sim_data,
                    "settings": result.get("settings"),
                    "simulated_at": datetime.now(timezone.utc).isoformat(),
                }
                
                all_results.append(output)
                
                # Log result
                if status == "COMPLETE":
                    print(f"  ✓ {alpha_id:8s} | sharpe={sharpe:7.3f} fitness={fitness:7.3f} "
                          f"turnover={turnover:8.5f} returns={returns:7.4f}")
                else:
                    error = sim.get("message", "unknown error")
                    print(f"  ✗ {alpha_id:8s} | {status}: {error[:50]}")
                
                # Save individual result
                _save_individual_result(output)
        
        except Exception as e:
            print(f"  ✗ Batch {batch_num} failed: {e}")
            import traceback
            traceback.print_exc()
    
    return all_results


def _save_individual_result(result: Dict[str, Any]):
    """Lưu individual result."""
    alpha_id = result.get("alpha_id", "unknown")
    output_file = INDIVIDUAL_OUTPUT_DIR / f"{alpha_id}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


# ============================================================================
# ANALYSIS & REPORTING
# ============================================================================

def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze simulation results.
    
    Returns: Stats dict
    """
    
    complete = [r for r in results if r.get("status") == "COMPLETE"]
    
    stats = {
        "total": len(results),
        "complete": len(complete),
        "errors": len(results) - len(complete),
        "completion_rate": len(complete) / len(results) if results else 0,
    }
    
    if complete:
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
        
        stats["sharpe"] = {
            "mean": sum(sharpes) / len(sharpes),
            "max": max(sharpes),
            "min": min(sharpes),
        }
        stats["fitness"] = {
            "mean": sum(fitnesses) / len(fitnesses),
            "max": max(fitnesses),
            "min": min(fitnesses),
        }
        stats["turnover"] = {
            "mean": sum(turnovers) / len(turnovers),
            "max": max(turnovers),
            "min": min(turnovers),
        }
        stats["returns"] = {
            "mean": sum(returns_list) / len(returns_list),
            "max": max(returns_list),
            "min": min(returns_list),
        }
    
    return stats


def get_top_alphas(
    results: List[Dict[str, Any]],
    top_n: int = 10,
    metric: str = "fitness",
) -> List[Dict[str, Any]]:
    """Get top N alphas by metric."""
    
    complete = [r for r in results if r.get("status") == "COMPLETE"]
    
    def get_metric_value(r):
        sim_data = r.get("sim_data", {})
        is_data = sim_data.get("is", {})
        return is_data.get(metric, 0)
    
    sorted_alphas = sorted(complete, key=get_metric_value, reverse=True)
    return sorted_alphas[:top_n]


def export_csv(results: List[Dict[str, Any]], filepath: str):
    """Export results to CSV."""
    
    rows = []
    for r in results:
        sim_data = r.get("sim_data", {})
        is_data = sim_data.get("is", {})
        
        row = {
            "alpha_id": r.get("alpha_id"),
            "level": r.get("level"),
            "description": r.get("description"),
            "expression": r.get("expression"),
            "status": r.get("status"),
            "sharpe": is_data.get("sharpe", ""),
            "fitness": is_data.get("fitness", ""),
            "turnover": is_data.get("turnover", ""),
            "returns": is_data.get("returns", ""),
            "simulated_at": r.get("simulated_at"),
        }
        rows.append(row)
    
    # Sort by fitness desc
    rows = sorted(rows, key=lambda x: float(x["fitness"]) if x["fitness"] else 0, reverse=True)
    
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        fieldnames = list(rows[0].keys()) if rows else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n[export] Đã lưu CSV: {filepath}")


def save_json_results(results: List[Dict[str, Any]], filepath: str):
    """Save all results to JSON."""
    
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "settings": FIXED_SETTINGS,
        "total_alphas": len(results),
        "results": results,
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"[export] Đã lưu JSON: {filepath}")


def print_summary(stats: Dict[str, Any]):
    """In tóm tắt."""
    
    print("\n" + "=" * 80)
    print("  SUMMARY - CMF WYCKOFF ALPHA SIMULATION")
    print("=" * 80)
    
    print(f"\nTotal alphas: {stats['total']}")
    print(f"  ✓ Thành công: {stats['complete']}")
    print(f"  ✗ Lỗi: {stats['errors']}")
    print(f"  Completion rate: {stats['completion_rate']*100:.1f}%")
    
    if "sharpe" in stats:
        print(f"\nSharpe Ratio:")
        print(f"  Mean: {stats['sharpe']['mean']:.3f}")
        print(f"  Max:  {stats['sharpe']['max']:.3f}")
        print(f"  Min:  {stats['sharpe']['min']:.3f}")
    
    if "fitness" in stats:
        print(f"\nFitness:")
        print(f"  Mean: {stats['fitness']['mean']:.3f}")
        print(f"  Max:  {stats['fitness']['max']:.3f}")
        print(f"  Min:  {stats['fitness']['min']:.3f}")
    
    if "turnover" in stats:
        print(f"\nTurnover:")
        print(f"  Mean: {stats['turnover']['mean']:.5f}")
        print(f"  Max:  {stats['turnover']['max']:.5f}")
        print(f"  Min:  {stats['turnover']['min']:.5f}")
    
    if "returns" in stats:
        print(f"\nReturns (annual %):")
        print(f"  Mean: {stats['returns']['mean']:.4f}")
        print(f"  Max:  {stats['returns']['max']:.4f}")
        print(f"  Min:  {stats['returns']['min']:.4f}")


def print_top_performers(top_alphas: List[Dict[str, Any]]):
    """In top performers."""
    
    print("\n" + "=" * 80)
    print(f"  TOP {len(top_alphas)} PERFORMERS (by Fitness)")
    print("=" * 80)
    
    for i, alpha in enumerate(top_alphas, 1):
        sim_data = alpha.get("sim_data", {})
        is_data = sim_data.get("is", {})
        
        alpha_id = alpha.get("alpha_id")
        desc = alpha.get("description", "")
        expr = alpha.get("expression", "")
        sharpe = is_data.get("sharpe", 0)
        fitness = is_data.get("fitness", 0)
        turnover = is_data.get("turnover", 0)
        returns = is_data.get("returns", 0)
        
        print(f"\n{i}. {alpha_id} | {desc}")
        print(f"   Sharpe: {sharpe:7.3f} | Fitness: {fitness:7.3f} | Turnover: {turnover:8.5f} | Returns: {returns:7.4f}")
        
        if len(expr) > 100:
            expr = expr[:97] + "..."
        print(f"   Expr: {expr}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CMF Wyckoff Alpha Family Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 cmf_wyckoff_simulator.py                  # Chạy tất cả 53 alphas
  python3 cmf_wyckoff_simulator.py --level 4        # Chỉ Level 4
  python3 cmf_wyckoff_simulator.py --start 0 --end 10  # Alpha 0-10
  python3 cmf_wyckoff_simulator.py --dry-run        # Preview mode
  python3 cmf_wyckoff_simulator.py --batch-size 15  # Batch size lớn
        """
    )
    
    parser.add_argument("--file", default="alphas_cmf_wyckoff_template.txt",
                       help="File chứa alpha template")
    parser.add_argument("--level", type=int,
                       help="Chỉ mô phỏng Level cụ thể (1-20)")
    parser.add_argument("--start", type=int,
                       help="Chỉ số alpha bắt đầu")
    parser.add_argument("--end", type=int,
                       help="Chỉ số alpha kết thúc")
    parser.add_argument("--batch-size", type=int, default=10,
                       help="Batch size (default: 10)")
    parser.add_argument("--max-concurrent", type=int, default=3,
                       help="Max concurrent (default: 3)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview mode (không gọi API)")
    parser.add_argument("--top", type=int, default=10,
                       help="Số lượng top performers hiển thị")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("  CMF WYCKOFF ALPHA FAMILY SIMULATOR")
    print("=" * 80)
    print(f"\n  Region: {FIXED_SETTINGS['region']}")
    print(f"  Universe: {FIXED_SETTINGS['universe']}")
    print(f"  Delay: {FIXED_SETTINGS['delay']}")
    print(f"  Neutralization: {FIXED_SETTINGS['neutralization']}")
    print(f"  Truncation: {FIXED_SETTINGS['truncation']}")
    print(f"  Decay: {FIXED_SETTINGS['decay']}")
    print()
    
    # Load alphas
    alpha_file = PHASE_1_PLUS_ROOT / args.file
    
    if not alpha_file.exists():
        print(f"✗ File không tồn tại: {alpha_file}")
        return 1
    
    print(f"[load] Đọc file: {alpha_file}")
    alphas = parse_alpha_file(str(alpha_file))
    print(f"[load] Đã parse {len(alphas)} alphas\n")
    
    # Filter
    filtered = filter_alphas(alphas, level_filter=args.level, start=args.start, end=args.end)
    print(f"[filter] Sau lọc: {len(filtered)} alphas\n")
    
    if not filtered:
        print("✗ Không có alphas nào được lọc")
        return 1
    
    # Show samples
    print("Sample alphas:")
    for i, alpha in enumerate(filtered[:3], 1):
        expr = alpha["expression"]
        if len(expr) > 80:
            expr = expr[:77] + "..."
        print(f"  {i}. {alpha['id']} | {alpha['description']}")
        print(f"     {expr}")
    if len(filtered) > 3:
        print(f"  ... và {len(filtered) - 3} alphas khác\n")
    else:
        print()
    
    if args.dry_run:
        print("⚠ DRY RUN MODE - sẽ không gọi BRAIN API\n")
    
    # Simulate
    results = simulate_batch(
        filtered,
        batch_size=args.batch_size,
        max_concurrent=args.max_concurrent,
        dry_run=args.dry_run,
    )
    
    # Analyze
    stats = analyze_results(results)
    top_alphas = get_top_alphas(results, top_n=args.top, metric="fitness")
    
    # Export
    save_json_results(results, str(RESULTS_FILE))
    export_csv(results, str(CSV_RESULTS_FILE))
    
    # Print
    print_summary(stats)
    print_top_performers(top_alphas)
    
    print(f"\n[export] Kết quả đã lưu:")
    print(f"  JSON: {RESULTS_FILE}")
    print(f"  CSV:  {CSV_RESULTS_FILE}")
    print(f"  Individual: {INDIVIDUAL_OUTPUT_DIR}/")
    
    print("\n" + "=" * 80)
    print("  ✓ Hoàn thành!")
    print("=" * 80 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
