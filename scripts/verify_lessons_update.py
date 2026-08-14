#!/usr/bin/env python3
"""verify_lessons_update.py — Verify that lessons.json is updated during mining rounds.

This script:
  1. Snapshots current lessons.json state
  2. Runs mining loop for N rounds (with actual API calls, not dry-run)
  3. Checks if lessons.json was updated
  4. Reports changes: new patterns, updated stats, improved Sharpe ratios

Usage:
  python3 scripts/verify_lessons_update.py --rounds 2
  python3 scripts/verify_lessons_update.py --rounds 5 --timeout 300
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))

import os

LOG_LEVEL = os.getenv("WQ_LOG_LEVEL", "INFO").upper()
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
logger = logging.getLogger(__name__)

# Paths
LESSONS_PATH = SKILL_DIR / "lessons.json"
MINING_REPORT_PATH = SKILL_DIR / "mining_report.json"


def snapshot_lessons() -> dict:
    """Create a snapshot of current lessons.json state.
    
    Returns:
        Dictionary with version, pattern_count, experiment_count, patterns snapshot
    """
    if not LESSONS_PATH.exists():
        logger.warning("lessons.json not found")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": None,
            "pattern_count": 0,
            "experiment_count": 0,
            "patterns": {},
        }
    
    lessons = json.loads(LESSONS_PATH.read_text(encoding="utf-8"))
    
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": lessons.get("version"),
        "pattern_count": len(lessons.get("patterns", {})),
        "experiment_count": sum(p.get("tested", 0) for p in lessons.get("patterns", {}).values()),
        "patterns": {},
    }
    
    # Snapshot each pattern's key metrics
    for tid, data in lessons.get("patterns", {}).items():
        snapshot["patterns"][tid] = {
            "tested": data.get("tested", 0),
            "passed": data.get("passed", 0),
            "observed": data.get("observed", 0),
            "avg_sharpe": data.get("avg_sharpe", 0),
            "avg_fitness": data.get("avg_fitness", 0),
            "pass_rate": data.get("pass_rate", 0),
            "best_sharpe": data.get("best", {}).get("sharpe", 0) if data.get("best") else 0,
        }
    
    return snapshot


def run_mining_loop(max_rounds: int, timeout: int = 3600) -> bool:
    """Run mining loop.
    
    Args:
        max_rounds: Maximum rounds to run
        timeout: Timeout in seconds
    
    Returns:
        True if mining completed
    """
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "mining_loop.py"),
        "--max-rounds",
        str(max_rounds),
        "--keep-initial-breadth",
    ]
    
    logger.info("Running mining loop: %s", " ".join(cmd))
    print(f"\n[*] Running mining loop for {max_rounds} rounds (timeout: {timeout}s)...")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,
            timeout=timeout,
        )
        
        if result.returncode == 0:
            logger.info("Mining loop completed successfully")
            return True
        else:
            logger.error("Mining loop exited with code %d", result.returncode)
            return False
    
    except subprocess.TimeoutExpired:
        logger.error("Mining loop timed out after %d seconds", timeout)
        print(f"✗ Mining loop timed out after {timeout}s")
        return False
    except Exception as e:
        logger.error("Mining loop failed: %s", e)
        print(f"✗ Mining loop failed: {e}")
        return False


def compare_snapshots(before: dict, after: dict) -> dict:
    """Compare two lesson snapshots and generate a report.
    
    Args:
        before: Snapshot before mining
        after: Snapshot after mining
    
    Returns:
        Comparison report
    """
    report = {
        "before_timestamp": before.get("timestamp"),
        "after_timestamp": after.get("timestamp"),
        "changes": {
            "pattern_count_delta": after.get("pattern_count", 0) - before.get("pattern_count", 0),
            "experiment_count_delta": after.get("experiment_count", 0) - before.get("experiment_count", 0),
        },
        "patterns_updated": [],
        "patterns_improved": [],
        "new_patterns": [],
    }
    
    before_patterns = before.get("patterns", {})
    after_patterns = after.get("patterns", {})
    
    # Find new patterns
    for tid in after_patterns:
        if tid not in before_patterns:
            report["new_patterns"].append(tid)
    
    # Compare existing patterns
    for tid in before_patterns:
        if tid not in after_patterns:
            continue
        
        before_data = before_patterns[tid]
        after_data = after_patterns[tid]
        
        # Check if tested count increased
        if after_data.get("tested", 0) > before_data.get("tested", 0):
            delta = after_data.get("tested", 0) - before_data.get("tested", 0)
            report["patterns_updated"].append({
                "template_id": tid,
                "tested_delta": delta,
                "before_tested": before_data.get("tested", 0),
                "after_tested": after_data.get("tested", 0),
            })
        
        # Check if Sharpe improved
        before_sharpe = before_data.get("avg_sharpe", 0)
        after_sharpe = after_data.get("avg_sharpe", 0)
        
        if after_sharpe > before_sharpe and abs(after_sharpe - before_sharpe) > 0.001:
            report["patterns_improved"].append({
                "template_id": tid,
                "sharpe_delta": after_sharpe - before_sharpe,
                "before_sharpe": before_sharpe,
                "after_sharpe": after_sharpe,
                "best_sharpe": after_data.get("best_sharpe", 0),
            })
    
    return report


def print_report(report: dict):
    """Print verification report."""
    print(f"\n{'=' * 70}")
    print("LESSONS UPDATE VERIFICATION REPORT")
    print(f"{'=' * 70}")
    
    print(f"\nTimestamps:")
    print(f"  Before: {report.get('before_timestamp', 'N/A')}")
    print(f"  After:  {report.get('after_timestamp', 'N/A')}")
    
    changes = report.get("changes", {})
    print(f"\nChanges Summary:")
    print(f"  New patterns: {changes.get('pattern_count_delta', 0)}")
    print(f"  New experiments: {changes.get('experiment_count_delta', 0)}")
    
    # Patterns updated
    updated = report.get("patterns_updated", [])
    if updated:
        print(f"\nPatterns Updated ({len(updated)}):")
        for item in sorted(updated, key=lambda x: x.get("tested_delta", 0), reverse=True)[:10]:
            tid = item.get("template_id")
            delta = item.get("tested_delta")
            before = item.get("before_tested")
            after = item.get("after_tested")
            print(f"  • {tid}: {before} → {after} (+{delta})")
    
    # Patterns improved
    improved = report.get("patterns_improved", [])
    if improved:
        print(f"\nPatterns Improved Sharpe ({len(improved)}):")
        for item in sorted(improved, key=lambda x: x.get("sharpe_delta", 0), reverse=True)[:10]:
            tid = item.get("template_id")
            before_sharpe = item.get("before_sharpe")
            after_sharpe = item.get("after_sharpe")
            best_sharpe = item.get("best_sharpe")
            delta = item.get("sharpe_delta")
            print(f"  • {tid}: {before_sharpe:.3f} → {after_sharpe:.3f} (Δ{delta:.3f})")
            if best_sharpe > 0:
                print(f"    Best alpha Sharpe: {best_sharpe:.3f}")
    
    # New patterns
    new = report.get("new_patterns", [])
    if new:
        print(f"\nNew Patterns ({len(new)}):")
        for tid in new:
            print(f"  • {tid}")
    
    print(f"\n{'=' * 70}")
    
    # Success indicator
    total_changes = (
        changes.get("pattern_count_delta", 0) +
        changes.get("experiment_count_delta", 0) +
        len(updated) +
        len(improved) +
        len(new)
    )
    
    if total_changes > 0:
        print("✓ LESSONS.JSON WAS UPDATED SUCCESSFULLY")
    else:
        print("⚠ No changes detected in lessons.json")
        print("  (This may be normal if mining produced no active alphas)")
    
    print(f"{'=' * 70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Verify that lessons.json is updated during mining"
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=2,
        help="Number of mining rounds to run (default: 2)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Mining timeout in seconds (default: 3600)",
    )
    parser.add_argument(
        "--compare-only",
        action="store_true",
        help="Only compare snapshots without running mining",
    )
    
    args = parser.parse_args()
    
    print(f"\n{'=' * 70}")
    print("LESSONS.JSON UPDATE VERIFICATION")
    print(f"{'=' * 70}")
    
    # Take before snapshot
    print("\n[1/3] Capturing lessons.json state before mining...")
    before_snapshot = snapshot_lessons()
    print(f"✓ Captured: {before_snapshot.get('pattern_count')} patterns, {before_snapshot.get('experiment_count')} experiments")
    
    # Run mining (unless --compare-only)
    if not args.compare_only:
        print(f"\n[2/3] Running {args.rounds} mining rounds...")
        success = run_mining_loop(args.rounds, args.timeout)
        
        if not success:
            print("✗ Mining failed or timed out")
            sys.exit(1)
    else:
        print(f"\n[2/3] Skipping mining (--compare-only mode)")
    
    # Take after snapshot
    print(f"\n[3/3] Capturing lessons.json state after mining...")
    time.sleep(1)  # Give time for file I/O
    after_snapshot = snapshot_lessons()
    print(f"✓ Captured: {after_snapshot.get('pattern_count')} patterns, {after_snapshot.get('experiment_count')} experiments")
    
    # Compare
    print(f"\n[4/4] Comparing snapshots...")
    comparison = compare_snapshots(before_snapshot, after_snapshot)
    print_report(comparison)


if __name__ == "__main__":
    main()
