#!/usr/bin/env python3
"""run_per_paper_workflow.py — Automated per-paper mining workflow orchestrator.

This script chains together the complete per-paper mining workflow:
  1. Generate extraction prompt for a paper
  2. [MANUAL: User extracts templates using LLM]
  3. Ingest extracted templates from JSON
  4. Run mining loop to explore templates
  5. Repeat for next paper

Usage (Interactive Mode):
  python3 scripts/run_per_paper_workflow.py interactive

Usage (Automated Mode - requires pre-extracted JSON):
  python3 scripts/run_per_paper_workflow.py src_001 extraction_output.json --mining-rounds 5

Usage (Generate Prompts for Multiple Papers):
  python3 scripts/run_per_paper_workflow.py batch --papers src_001,src_002,src_003

Usage (Full Single-Paper Workflow - waiting for manual extraction):
  python3 scripts/run_per_paper_workflow.py single src_002 --mining-rounds 3
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
# Paths
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
TEMPLATES_DIR = SKILL_DIR / "templates"
PAPERS_REGISTRY_PATH = SKILL_DIR / "papers_registry.json"
LESSONS_PATH = SKILL_DIR / "lessons.json"


def run_command(cmd: list[str], description: str = None) -> tuple[int, str]:
    """Run a shell command and return exit code + output.
    
    Args:
        cmd: Command and args as list
        description: Human-readable description of what's running
    
    Returns:
        (exit_code, output)
    """
    if description:
        logger.info("Running: %s", description)
        print(f"\n[*] {description}...")
    
    try:
        # Run with streaming output (show logs in real-time)
        result = subprocess.run(
            cmd,
            timeout=3600,  # 1 hour timeout
        )
        return result.returncode, ""
    except subprocess.TimeoutExpired:
        logger.error("Command timed out: %s", description)
        return 1, "Command timed out"
    except Exception as e:
        logger.error("Command failed: %s error=%s", description, e)
        return 1, str(e)


def generate_extraction_prompt(paper_id: str) -> Optional[Path]:
    """Generate extraction prompt for a paper.
    
    Args:
        paper_id: Source ID (e.g., src_001)
    
    Returns:
        Path to generated prompt, or None if failed
    """
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "generate_extraction_prompt.py"),
        paper_id,
    ]
    
    exit_code, output = run_command(cmd, f"Generate extraction prompt for {paper_id}")
    
    if exit_code != 0:
        logger.error("Failed to generate extraction prompt: %s", output)
        return None
    
    # Extract output path from log
    prompt_path = SKILL_DIR / f"_extraction_prompt_{paper_id}.md"
    if prompt_path.exists():
        logger.info("Generated extraction prompt path=%s", prompt_path)
        print(f"✓ Extraction prompt ready: {prompt_path.name}")
        return prompt_path
    else:
        logger.error("Generated prompt file not found: %s", prompt_path)
        return None


def ingest_extracted_templates(json_path: Path, paper_id: Optional[str] = None) -> tuple[bool, int]:
    """Ingest extracted templates from JSON.
    
    Args:
        json_path: Path to JSON file from LLM
        paper_id: Source paper ID for registry tracking
    
    Returns:
        (success: bool, template_count: int)
    """
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "ingest_extracted_templates.py"),
        str(json_path),
    ]
    
    if paper_id:
        cmd.extend(["--paper", paper_id])
    
    exit_code, output = run_command(cmd, f"Ingest extracted templates from {json_path.name}")
    
    if exit_code != 0:
        print("✗ Template ingestion failed!")
        return False, 0
    
    # Count templates by checking templates directory
    try:
        template_files = list((SKILL_DIR / "templates").glob("*.json"))
        success_count = len(template_files)
        
        if success_count > 0:
            logger.info("Templates available: count=%s", success_count)
            print(f"✓ Templates ready for mining")
            return True, success_count
        else:
            logger.warning("No templates found after ingestion")
            return False, 0
    except Exception as e:
        logger.warning("Could not count templates: %s", e)
        return True, 0


def run_mining_loop(max_rounds: int = 5, keep_initial_breadth: bool = False) -> bool:
    """Run the mining loop for one round of exploration.
    
    Args:
        max_rounds: Maximum number of mining rounds
        keep_initial_breadth: Whether to keep initial breadth phase
    
    Returns:
        True if mining completed successfully
    """
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "mining_loop.py"),
        "--max-rounds",
        str(max_rounds),
    ]
    
    if keep_initial_breadth:
        cmd.append("--keep-initial-breadth")
    
    exit_code, _ = run_command(cmd, f"Run mining loop ({max_rounds} rounds)")
    
    if exit_code != 0:
        print("✗ Mining loop failed!")
        return False
    
    # Check for mining report
    try:
        if (SKILL_DIR / "mining_report.json").exists():
            report = json.loads((SKILL_DIR / "mining_report.json").read_text())
            logger.info("Mining completed: rounds=%s submitted=%s active=%s", 
                       report.get('total_rounds', 0),
                       report.get('total_submitted', 0),
                       len(report.get('active_alphas', {})))
            print("✓ Mining loop completed successfully")
            return True
        else:
            print("✓ Mining loop completed")
            return True
    except Exception as e:
        logger.warning("Could not read mining report: %s", e)
        return True


def print_workflow_summary(paper_id: str, template_count: int = 0):
    """Print a summary of the workflow status."""
    print(f"\n{'=' * 70}")
    print(f"  WORKFLOW SUMMARY - {paper_id}")
    print(f"{'=' * 70}")
    
    # Load registry to show status
    try:
        registry = json.loads(PAPERS_REGISTRY_PATH.read_text(encoding="utf-8"))
        paper_entry = registry.get("sources", {}).get(paper_id, {})
        status = paper_entry.get("status", "unknown")
        templates_created = len(paper_entry.get("templates_created", []))
        
        print(f"\nPaper: {paper_id}")
        print(f"  Title: {paper_entry.get('title', 'N/A')}")
        print(f"  Status: {status}")
        print(f"  Templates created: {templates_created}")
        
        # Show lessons summary
        lessons = json.loads(LESSONS_PATH.read_text(encoding="utf-8"))
        pattern_count = len(lessons.get("patterns", {}))
        print(f"\nLessons Learned:")
        print(f"  Total patterns: {pattern_count}")
        
    except Exception as e:
        logger.warning("Failed to load status: %s", e)
    
    print(f"\n{'=' * 70}\n")


def interactive_workflow():
    """Run interactive workflow mode."""
    print("\n" + "=" * 70)
    print("  PER-PAPER MINING WORKFLOW - INTERACTIVE MODE")
    print("=" * 70)
    
    while True:
        print("\nOptions:")
        print("  1. Generate extraction prompt for a paper")
        print("  2. Ingest extracted templates from JSON")
        print("  3. Run mining loop")
        print("  4. Full workflow (1+2+3)")
        print("  5. Check status")
        print("  q. Quit")
        
        choice = input("\nSelect option (1-5, q): ").strip().lower()
        
        if choice == "q":
            print("✓ Exiting workflow")
            break
        elif choice == "1":
            paper_id = input("Enter paper ID (e.g., src_001): ").strip()
            if paper_id:
                generate_extraction_prompt(paper_id)
        elif choice == "2":
            json_path = input("Enter path to extracted JSON (e.g., output.json): ").strip()
            paper_id = input("Enter paper ID (optional): ").strip() or None
            if json_path:
                ingest_extracted_templates(Path(json_path), paper_id)
        elif choice == "3":
            max_rounds = int(input("Enter max rounds (default 5): ") or "5")
            run_mining_loop(max_rounds)
        elif choice == "4":
            paper_id = input("Enter paper ID (e.g., src_002): ").strip()
            json_path = input("Enter path to extracted JSON: ").strip()
            max_rounds = int(input("Enter max mining rounds (default 3): ") or "3")
            
            if paper_id and json_path:
                success, count = ingest_extracted_templates(Path(json_path), paper_id)
                if success:
                    run_mining_loop(max_rounds)
                    print_workflow_summary(paper_id, count)
        elif choice == "5":
            paper_id = input("Enter paper ID (optional): ").strip() or None
            if paper_id:
                print_workflow_summary(paper_id)
            else:
                # Show all papers status
                try:
                    registry = json.loads(PAPERS_REGISTRY_PATH.read_text(encoding="utf-8"))
                    print("\nAll Papers Status:")
                    for sid, entry in registry.get("sources", {}).items():
                        status = entry.get("status", "pending")
                        print(f"  {sid}: {status}")
                except Exception as e:
                    logger.warning("Failed to load registry: %s", e)


def single_paper_workflow(paper_id: str, json_path: Optional[Path], max_rounds: int = 3):
    """Run complete workflow for a single paper.
    
    Args:
        paper_id: Source ID (e.g., src_002)
        json_path: Path to extracted JSON (if None, only generates prompt)
        max_rounds: Maximum mining rounds
    """
    print(f"\n{'=' * 70}")
    print(f"  SINGLE PAPER WORKFLOW - {paper_id}")
    print(f"{'=' * 70}")
    
    # Step 1: Generate extraction prompt
    print(f"\n[Step 1/3] Generate extraction prompt...")
    prompt_path = generate_extraction_prompt(paper_id)
    
    if not prompt_path:
        print("✗ Failed to generate extraction prompt")
        return False
    
    # If no JSON provided, wait for manual extraction
    if json_path is None:
        print(f"\n{'─' * 70}")
        print("MANUAL STEP REQUIRED:")
        print(f"  1. Copy the extraction prompt:")
        print(f"     {prompt_path}")
        print(f"  2. Open ChatGPT or Claude")
        print(f"  3. Paste the prompt + paper PDF")
        print(f"  4. Get the JSON array response")
        print(f"  5. Save JSON to a file (e.g., extraction_{paper_id}.json)")
        print(f"  6. Run: python3 scripts/run_per_paper_workflow.py ingest {paper_id} <json_file>")
        print(f"{'─' * 70}\n")
        return False
    
    # Step 2: Ingest templates
    print(f"\n[Step 2/3] Ingest extracted templates...")
    success, count = ingest_extracted_templates(json_path, paper_id)
    
    if not success:
        print("✗ Failed to ingest templates")
        return False
    
    # Step 3: Run mining loop
    print(f"\n[Step 3/3] Run mining loop...")
    if not run_mining_loop(max_rounds, keep_initial_breadth=True):
        print("✗ Mining loop failed")
        return False
    
    print_workflow_summary(paper_id, count)
    return True


def batch_workflow(paper_ids: list[str]):
    """Generate prompts for multiple papers.
    
    Args:
        paper_ids: List of source IDs (e.g., ['src_001', 'src_002'])
    """
    print(f"\n{'=' * 70}")
    print(f"  BATCH GENERATION - {len(paper_ids)} papers")
    print(f"{'=' * 70}")
    
    generated = []
    failed = []
    
    for paper_id in paper_ids:
        print(f"\nGenerating prompt for {paper_id}...")
        prompt_path = generate_extraction_prompt(paper_id)
        
        if prompt_path:
            generated.append((paper_id, prompt_path))
        else:
            failed.append(paper_id)
    
    # Summary
    print(f"\n{'=' * 70}")
    print(f"  BATCH SUMMARY")
    print(f"{'=' * 70}")
    print(f"\n✓ Generated: {len(generated)}")
    for paper_id, prompt_path in generated:
        print(f"  • {paper_id}: {prompt_path.name}")
    
    if failed:
        print(f"\n✗ Failed: {len(failed)}")
        for paper_id in failed:
            print(f"  • {paper_id}")
    
    print(f"\nNext steps:")
    print(f"  1. Extract templates from each prompt using LLM")
    print(f"  2. Run: python3 scripts/run_per_paper_workflow.py single <paper_id> <json_file>")
    print(f"  3. Repeat for all papers\n")


def ingest_workflow(paper_id: str, json_path: Path, max_rounds: int = 3):
    """Run ingest + mining for a paper with pre-extracted JSON.
    
    Args:
        paper_id: Source ID
        json_path: Path to extracted JSON
        max_rounds: Maximum mining rounds
    """
    success, count = ingest_extracted_templates(json_path, paper_id)
    
    if success:
        run_mining_loop(max_rounds, keep_initial_breadth=True)
        print_workflow_summary(paper_id, count)


def main():
    parser = argparse.ArgumentParser(
        description="Automated per-paper mining workflow orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python3 scripts/run_per_paper_workflow.py interactive
  
  # Generate prompts for multiple papers
  python3 scripts/run_per_paper_workflow.py batch --papers src_001,src_002,src_003
  
  # Full workflow for a single paper (with pre-extracted JSON)
  python3 scripts/run_per_paper_workflow.py single src_002 extraction_output.json --mining-rounds 5
  
  # Just ingest and mine (for pre-extracted templates)
  python3 scripts/run_per_paper_workflow.py ingest src_003 extraction_output.json --mining-rounds 3
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Workflow mode")
    
    # Interactive mode
    subparsers.add_parser("interactive", help="Interactive workflow mode")
    
    # Batch generation
    batch_parser = subparsers.add_parser("batch", help="Batch generate extraction prompts")
    batch_parser.add_argument(
        "--papers",
        required=True,
        help="Comma-separated paper IDs (e.g., src_001,src_002,src_003)",
    )
    
    # Single paper workflow
    single_parser = subparsers.add_parser("single", help="Full workflow for single paper")
    single_parser.add_argument("paper_id", help="Paper ID (e.g., src_002)")
    single_parser.add_argument(
        "json_file",
        nargs="?",
        help="Path to extracted JSON (optional - if not provided, only generates prompt)",
    )
    single_parser.add_argument(
        "--mining-rounds",
        type=int,
        default=3,
        help="Maximum mining rounds (default: 3)",
    )
    
    # Ingest workflow
    ingest_parser = subparsers.add_parser("ingest", help="Ingest templates and run mining")
    ingest_parser.add_argument("paper_id", help="Paper ID (e.g., src_003)")
    ingest_parser.add_argument("json_file", help="Path to extracted JSON file")
    ingest_parser.add_argument(
        "--mining-rounds",
        type=int,
        default=3,
        help="Maximum mining rounds (default: 3)",
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    try:
        if args.command == "interactive":
            interactive_workflow()
        
        elif args.command == "batch":
            paper_ids = [p.strip() for p in args.papers.split(",")]
            batch_workflow(paper_ids)
        
        elif args.command == "single":
            json_path = Path(args.json_file) if args.json_file else None
            single_paper_workflow(args.paper_id, json_path, args.mining_rounds)
        
        elif args.command == "ingest":
            json_path = Path(args.json_file)
            if not json_path.exists():
                logger.error("JSON file not found: %s", json_path)
                sys.exit(1)
            ingest_workflow(args.paper_id, json_path, args.mining_rounds)
    
    except Exception as e:
        logger.error("Workflow failed: %s", e)
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
