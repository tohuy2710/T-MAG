#!/usr/bin/env python3
"""
Phase 1 Plus: Alpha Simulation for 4-Step Optimization
Mô phỏng các Alpha được sinh từ framework 4 bước trên BRAIN API.

Usage:
  python3 phase_1_plus_sim.py                     # Mô phỏng tất cả alphas
  python3 phase_1_plus_sim.py --batch-size 20     # Tùy chỉnh batch size
  python3 phase_1_plus_sim.py --max-concurrent 5  # Tăng concurrency
  python3 phase_1_plus_sim.py --step 2            # Chỉ mô phỏng alphas từ bước 2
  python3 phase_1_plus_sim.py --top 20            # Hiển thị top 20 performers
"""

import sys
import json
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone

# Add parent scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from brain_api import BrainClient


# ============================================================================
# CONFIGURATION
# ============================================================================

PHASE_1_PLUS_ROOT = Path(__file__).parent
OUTPUT_DIR = PHASE_1_PLUS_ROOT / "output"
INDIVIDUAL_OUTPUT_DIR = OUTPUT_DIR / "individual"
RESULTS_FILE = OUTPUT_DIR / "simulation_results.json"

# Default settings for BRAIN simulation
DEFAULT_SETTINGS = {
    "region": "GLB",
    "universe": "TOPDIV3000",
    "delay": 1,
    "neutralization": "subindustry",  # Changed from "country" - valid options: SLOW, FAST, SLOW_AND_FAST, SUBINDUSTRY, CROWDING
    "decay": 10,
    "truncation": 0.08,
    "pasteurization": "ON",  # Must be string "ON" or "OFF", not boolean
    "unit_handling": "VERIFY",  # Must be uppercase
    "nan_handling": "OFF",  # Must be string "ON" or "OFF", not boolean
}

# Create output directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INDIVIDUAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_alphas_from_file(filepath: str, step_filter: int = None) -> List[Dict[str, Any]]:
    """
    Đọc file alphas và parse thành list candidates.
    
    Args:
        filepath: Đường dẫn file chứa expressions
        step_filter: Chỉ lấy alphas từ bước cụ thể (2, 3, 4) hoặc None để lấy tất cả
        
    Returns:
        List các candidate dictionaries
    """
    candidates = []
    
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    current_desc = None
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
        
        # Comment line = description
        if line.startswith("#"):
            current_desc = line[1:].strip()
            continue
        
        # Expression line
        expr = line
        
        # Extract step number from description
        step_num = None
        if current_desc:
            if "Step3" in current_desc or "BƯỚC 3" in current_desc:
                step_num = 3
            elif "Step4" in current_desc or "BƯỚC 4" in current_desc:
                step_num = 4
            elif "Step2" in current_desc or "Param:" in current_desc or "BƯỚC 2" in current_desc:
                step_num = 2
        
        # Filter by step if requested
        if step_filter is not None and step_num != step_filter:
            current_desc = None
            continue
        
        candidate = {
            "expression": expr,
            "description": current_desc or f"Alpha expression",
            "step": step_num,
            "settings": DEFAULT_SETTINGS.copy(),
        }
        
        candidates.append(candidate)
        current_desc = None
    
    return candidates


def save_individual_result(result: Dict[str, Any]):
    """Lưu kết quả mô phỏng riêng lẻ."""
    alpha_id = result.get("alpha_id")
    if not alpha_id:
        alpha_id = "None"
    
    output_file = INDIVIDUAL_OUTPUT_DIR / f"{alpha_id}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


def save_all_results(results: List[Dict[str, Any]]):
    """Lưu tất cả kết quả vào file tổng hợp."""
    output_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "results": results,
    }
    
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[save] Đã lưu {len(results)} kết quả vào {RESULTS_FILE}")


def print_summary(results: List[Dict[str, Any]]):
    """In tóm tắt kết quả mô phỏng."""
    total = len(results)
    complete = sum(1 for r in results if r.get("status") == "COMPLETE")
    errors = total - complete
    
    print("\n" + "=" * 80)
    print("  KẾT QUẢ MÔ PHỎNG")
    print("=" * 80)
    print(f"\nTổng số: {total}")
    print(f"  ✓ Thành công: {complete}")
    print(f"  ✗ Lỗi: {errors}")
    
    if complete > 0:
        # Extract metrics
        sharpes = []
        fitnesses = []
        turnovers = []
        
        for r in results:
            if r.get("status") == "COMPLETE":
                sim_data = r.get("sim_data", {})
                is_data = sim_data.get("is", {})
                
                sharpe = is_data.get("sharpe", 0)
                fitness = is_data.get("fitness", 0)
                turnover = is_data.get("turnover", 0)
                
                sharpes.append(sharpe)
                fitnesses.append(fitness)
                turnovers.append(turnover)
        
        if sharpes:
            print(f"\nSharpe Ratio:")
            print(f"  Trung bình: {sum(sharpes)/len(sharpes):.3f}")
            print(f"  Max: {max(sharpes):.3f}")
            print(f"  Min: {min(sharpes):.3f}")
        
        if fitnesses:
            print(f"\nFitness:")
            print(f"  Trung bình: {sum(fitnesses)/len(fitnesses):.3f}")
            print(f"  Max: {max(fitnesses):.3f}")
            print(f"  Min: {min(fitnesses):.3f}")
        
        if turnovers:
            print(f"\nTurnover:")
            print(f"  Trung bình: {sum(turnovers)/len(turnovers):.4f}")
            print(f"  Max: {max(turnovers):.4f}")
            print(f"  Min: {min(turnovers):.4f}")


def print_top_performers(results: List[Dict[str, Any]], top_n: int = 10):
    """In danh sách top performers."""
    # Filter complete results
    complete_results = [r for r in results if r.get("status") == "COMPLETE"]
    
    if not complete_results:
        print("\nKhông có kết quả thành công để hiển thị.")
        return
    
    # Sort by fitness (descending)
    sorted_results = sorted(
        complete_results,
        key=lambda r: r.get("sim_data", {}).get("is", {}).get("fitness", 0),
        reverse=True
    )
    
    print("\n" + "=" * 80)
    print(f"  TOP {min(top_n, len(sorted_results))} PERFORMERS (Sorted by Fitness)")
    print("=" * 80)
    
    for i, result in enumerate(sorted_results[:top_n], 1):
        alpha_id = result.get("alpha_id")
        sim_data = result.get("sim_data", {})
        is_data = sim_data.get("is", {})
        
        sharpe = is_data.get("sharpe", 0)
        fitness = is_data.get("fitness", 0)
        turnover = is_data.get("turnover", 0)
        returns = is_data.get("returns", 0)
        
        desc = result.get("description", "")
        step = result.get("step", "?")
        
        print(f"\n{i}. {alpha_id}")
        print(f"   Step: {step} | {desc}")
        print(f"   Sharpe: {sharpe:.3f} | Fitness: {fitness:.3f} | Turnover: {turnover:.4f} | Returns: {returns:.4f}")
        
        expr = result.get("expression", "")
        if len(expr) > 100:
            expr = expr[:97] + "..."
        print(f"   Expression: {expr}")


def batch_simulate(
    candidates: List[Dict[str, Any]],
    batch_size: int = 10,
    max_concurrent: int = 3,
) -> List[Dict[str, Any]]:
    """
    Batch simulate candidates using BRAIN API.
    
    Args:
        candidates: List of candidate dictionaries
        batch_size: Number of candidates per batch
        max_concurrent: Maximum concurrent simulations
        
    Returns:
        List of simulation results
    """
    
    print(f"\n[sim] Bắt đầu mô phỏng: {len(candidates)} candidates")
    print(f"      Batch size: {batch_size}")
    print(f"      Max concurrent: {max_concurrent}\n")
    
    client = BrainClient(max_concurrent=max_concurrent)
    client.connect()
    print("✓ Đã kết nối BRAIN API\n")
    
    all_results = []
    
    # Process in batches
    for batch_idx, i in enumerate(range(0, len(candidates), batch_size)):
        batch = candidates[i:i+batch_size]
        batch_num = batch_idx + 1
        total_batches = (len(candidates) + batch_size - 1) // batch_size
        
        print(f"[batch {batch_num}/{total_batches}] Mô phỏng {len(batch)} candidates...")
        
        try:
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
                    "description": result.get("description"),
                    "step": result.get("step"),
                    "status": status,
                    "alpha_id": alpha_id,
                    "sim_data": sim.get("sim_data"),
                    "settings": result.get("settings"),
                    "simulated_at": datetime.now(timezone.utc).isoformat(),
                }
                
                batch_results.append(output)
                save_individual_result(output)
                
                if status == "COMPLETE":
                    print(f"  ✓ {alpha_id} | sharpe={sharpe:.2f} fitness={fitness:.2f} turnover={turnover:.4f}")
                else:
                    error_msg = sim.get("message", "unknown error")
                    print(f"  ✗ {status}: {error_msg}")
            
            all_results.extend(batch_results)
            
        except Exception as e:
            print(f"  ✗ Batch {batch_num} failed: {e}")
            import traceback
            traceback.print_exc()
    
    return all_results


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Phase 1 Plus: 4-Step Alpha Optimization Simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 phase_1_plus_sim.py                         # Mô phỏng tất cả alphas
  python3 phase_1_plus_sim.py --step 2                # Chỉ mô phỏng bước 2
  python3 phase_1_plus_sim.py --batch-size 20         # Batch size lớn hơn
  python3 phase_1_plus_sim.py --max-concurrent 5      # Tăng concurrency
  python3 phase_1_plus_sim.py --top 20                # Hiển thị top 20
        """
    )
    
    parser.add_argument("--file", default="alphas_4steps_cmf.txt",
                       help="File chứa expressions (default: alphas_4steps_cmf.txt)")
    parser.add_argument("--step", type=int, choices=[2, 3, 4],
                       help="Chỉ mô phỏng alphas từ bước cụ thể (2, 3, 4)")
    parser.add_argument("--batch-size", type=int, default=10,
                       help="Batch size (default: 10)")
    parser.add_argument("--max-concurrent", type=int, default=3,
                       help="Max concurrent simulations (default: 3)")
    parser.add_argument("--top", type=int, default=10,
                       help="Số lượng top performers hiển thị (default: 10)")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("  Phase 1 Plus — 4-Step Alpha Optimization Simulation")
    print("=" * 80)
    print(f"\n  Environment: GLB / TOPDIV3000 / Delay 1")
    print(f"  File: {args.file}")
    if args.step:
        print(f"  Filter: Chỉ mô phỏng Bước {args.step}")
    print()
    
    # Load alphas
    alpha_file = PHASE_1_PLUS_ROOT / args.file
    
    if not alpha_file.exists():
        print(f"✗ File không tồn tại: {alpha_file}")
        print(f"  Hãy chạy: python3 alpha_optimizer_4steps.py để sinh expressions")
        return 1
    
    print(f"[load] Đọc file: {alpha_file}")
    candidates = load_alphas_from_file(str(alpha_file), step_filter=args.step)
    print(f"[load] Đã load {len(candidates)} candidates\n")
    
    if not candidates:
        print("✗ Không có candidates nào được load")
        return 1
    
    # Show sample candidates
    print("Sample candidates:")
    for i, cand in enumerate(candidates[:3], 1):
        desc = cand.get("description", "")
        expr = cand.get("expression", "")
        step = cand.get("step", "?")
        if len(expr) > 80:
            expr = expr[:77] + "..."
        print(f"  {i}. [Step {step}] {desc}")
        print(f"     {expr}")
    if len(candidates) > 3:
        print(f"  ... và {len(candidates) - 3} candidates khác")
    print()
    
    # Simulate
    results = batch_simulate(
        candidates,
        batch_size=args.batch_size,
        max_concurrent=args.max_concurrent
    )
    
    # Save results
    save_all_results(results)
    
    # Print summaries
    print_summary(results)
    print_top_performers(results, top_n=args.top)
    
    print(f"\n[save] Kết quả đã lưu tại:")
    print(f"       Tổng hợp: {RESULTS_FILE}")
    print(f"       Chi tiết: {INDIVIDUAL_OUTPUT_DIR}/")
    
    print("\n" + "=" * 80)
    print("  ✓ Hoàn thành mô phỏng!")
    print("=" * 80 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
