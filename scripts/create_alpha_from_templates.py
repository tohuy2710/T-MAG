#!/usr/bin/env python3
"""create_alpha_from_templates.py — Direct alpha creation from templates with GLB TOPDIV3000 settings.

This script generates and submits alphas directly from templates, configured for:
- Region: GLB
- Universe: TOPDIV3000
- Delay: 1
- High Turnover ratio test: PASS
- Excluded datasets: model110

Usage:
    python3 scripts/create_alpha_from_templates.py --template profitability_trend --max-candidates 10
    python3 scripts/create_alpha_from_templates.py --all-templates --max-per-template 5
    python3 scripts/create_alpha_from_templates.py --template-list analyst_estimate_trend overnight_reversal --max-candidates 8
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from brain_api import (
    BrainClient,
    load_alpha_db,
    load_lessons,
    save_alpha_db,
    save_lessons,
    quality_filter,
    compute_correlation,
    update_lessons_from_result,
)
from generate_candidates import (
    FieldValidator,
    deduplicate,
    expand_template,
    load_templates,
)
from research_target import load_target


def filter_high_turnover_templates(templates: list[dict]) -> list[dict]:
    """Filter templates that pass high turnover ratio test.
    
    High turnover templates are those with:
    - Tags including 'HIGH_TURNOVER' or 'high_turnover'
    - default_settings.decay >= 10 (technical factors)
    - Or explicitly marked for high turnover testing
    """
    filtered = []
    for tmpl in templates:
        # Check tags
        tags = tmpl.get("tags", [])
        if any(tag.upper() == "HIGH_TURNOVER" for tag in tags):
            filtered.append(tmpl)
            continue
        
        # Check decay settings - higher decay means lower turnover
        default_settings = tmpl.get("default_settings", {})
        decay = default_settings.get("decay", 0)
        
        # For high turnover test, we want templates that can pass with high turnover
        # This includes fundamental factors (decay=0) which typically have low turnover
        # and some technical factors with moderate decay
        if decay <= 4:  # Low decay can result in high turnover, but often still passes
            filtered.append(tmpl)
            continue
            
        # Check if template has turnover-related settings or comments
        desc = tmpl.get("description", "").lower()
        hypothesis = tmpl.get("hypothesis", "").lower()
        if any(keyword in desc or keyword in hypothesis for keyword in ["reversal", "momentum", "volume", "price"]):
            filtered.append(tmpl)
    
    return filtered


def create_alphas_from_template(
    template: dict,
    max_candidates: int,
    client: BrainClient,
    lessons: dict,
    db: dict,
    submit_threshold: float = 1.5,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Generate and submit alphas from a single template.
    
    Returns a summary with counts and results.
    """
    target = load_target()
    template_id = template.get("template_id", "unknown")
    
    print(f"\n{'='*70}")
    print(f"Processing template: {template_id}")
    print(f"Description: {template.get('description', 'N/A')}")
    print(f"{'='*70}")
    
    # Validate fields
    validator = FieldValidator(
        target.require_fields_reference(),
        target.excluded_dataset_ids
    )
    
    # Expand template into candidates
    print(f"\n[expand] Generating candidates from template...")
    candidates = expand_template(
        template,
        max_candidates=max_candidates,
        validator=validator,
        param_insights=lessons.get("param_insights", {}),
        target=target,
    )
    
    # Deduplicate
    before_dedup = len(candidates)
    candidates = deduplicate(candidates)
    print(f"[expand] Generated {before_dedup} candidates ({len(candidates)} after dedup)")
    
    if not candidates:
        print(f"[skip] No valid candidates generated from {template_id}")
        return {
            "template_id": template_id,
            "candidates": 0,
            "simulated": 0,
            "submitted": 0,
            "observed": 0,
            "errors": 0,
        }
    
    if dry_run:
        print(f"\n[dry-run] Would simulate {len(candidates)} candidates:")
        for i, cand in enumerate(candidates[:5], 1):
            expr = cand.get("expression", "")[:80]
            settings = cand.get("settings", {})
            print(f"  {i}. {expr}... (decay={settings.get('decay')}, neut={settings.get('neutralization')})")
        if len(candidates) > 5:
            print(f"  ... and {len(candidates) - 5} more")
        return {
            "template_id": template_id,
            "candidates": len(candidates),
            "simulated": 0,
            "submitted": 0,
            "observed": 0,
            "errors": 0,
            "dry_run": True,
        }
    
    # Fetch existing ACTIVE alphas for correlation check
    print(f"\n[correlate] Fetching existing ACTIVE alphas...")
    try:
        remote_active = client.refresh_alpha_db_from_remote(db)
        save_alpha_db(db)
        active_alphas = {
            a["id"]: db.get("alphas", {}).get(a["id"], a)
            for a in remote_active
            if a.get("id")
        }
    except Exception as e:
        print(f"[warning] Could not fetch remote alphas: {e}")
        active_alphas = {
            aid: a for aid, a in db.get("alphas", {}).items()
            if a.get("status") == "ACTIVE"
        }
    
    print(f"[correlate] Found {len(active_alphas)} ACTIVE alphas")
    
    # Fetch PnLs for correlation
    active_pnls: dict[str, list[float]] = {}
    for aid in active_alphas:
        pnl = client.fetch_pnl(aid)
        if len(pnl) >= 50:
            active_pnls[aid] = pnl
    print(f"[correlate] Retrieved {len(active_pnls)} usable PnL series")
    
    # Simulate and submit
    results = {
        "template_id": template_id,
        "candidates": len(candidates),
        "simulated": 0,
        "submitted": 0,
        "submit_failed": 0,
        "observed": 0,
        "discarded": 0,
        "errors": 0,
        "error_details": [],
        "submitted_alphas": [],
        "observed_alphas": [],
    }
    
    print(f"\n[simulate] Starting batch simulation...")
    
    # Use streaming simulation for immediate results
    for i, result in enumerate(client.batch_simulate_stream(candidates), 1):
        sim = result.get("sim_result", {})
        status = sim.get("status", "ERROR")
        expression = result.get("expression", "")
        
        print(f"\n[{i}/{len(candidates)}] Candidate completed: {status}")
        print(f"  Expression: {expression[:80]}...")
        
        if status != "COMPLETE":
            results["errors"] += 1
            error_detail = {
                "expression": expression[:100],
                "status": status,
                "error": str(sim.get("error", ""))[:200],
            }
            results["error_details"].append(error_detail)
            update_lessons_from_result(lessons, result, sim)
            continue
        
        results["simulated"] += 1
        
        # Get metrics
        sim_data = sim.get("sim_data", {})
        is_data = sim_data.get("is", {})
        sharpe = is_data.get("sharpe")
        fitness = is_data.get("fitness")
        turnover = is_data.get("turnover")
        alpha_id = sim.get("alpha_id")
        
        print(f"  Alpha ID: {alpha_id}")
        print(f"  Sharpe: {f'{sharpe:.3f}' if sharpe is not None else 'N/A'}")
        print(f"  Fitness: {f'{fitness:.3f}' if fitness is not None else 'N/A'}")
        print(f"  Turnover: {f'{turnover:.3f}' if turnover is not None else 'N/A'}")
        
        # Store in DB
        if alpha_id:
            db["alphas"][alpha_id] = {
                "expression": expression,
                "status": "UNSUBMITTED",
                "sharpe": sharpe,
                "fitness": fitness,
                "turnover": turnover,
                "template_id": template_id,
                "simulated_at": datetime.now(timezone.utc).isoformat(),
            }
        
        # Compute correlation
        max_corr = None
        if alpha_id:
            # Try platform self-correlation first
            platform_corr = client.fetch_self_correlation(alpha_id)
            if platform_corr is not None:
                max_corr = platform_corr
                print(f"  Self-correlation (platform): {max_corr:.3f}")
            elif active_pnls:
                # Fallback to local PnL correlation
                new_pnl = client.fetch_pnl(alpha_id)
                if len(new_pnl) >= 50:
                    corr_list = compute_correlation(
                        new_pnl,
                        {"alphas": {aid: {"status": "ACTIVE", "pnl": p} for aid, p in active_pnls.items()}},
                    )
                    if corr_list:
                        max_corr = max(abs(c.get("correlation", 0)) for c in corr_list)
                        print(f"  Self-correlation (local): {max_corr:.3f}")
        
        # Store correlation
        if alpha_id and alpha_id in db["alphas"]:
            db["alphas"][alpha_id]["max_corr"] = max_corr
        
        # Quality filter
        checks = is_data.get("checks")
        action = quality_filter(
            sharpe, fitness, turnover, max_corr,
            checks=checks,
            sharpe_threshold=submit_threshold,
            trials=len(lessons.get("experiments", [])),
        )
        
        print(f"  Quality verdict: {action}")
        
        # Update lessons
        update_lessons_from_result(lessons, result, sim, max_corr)
        
        # Handle submission
        if action == "SUBMIT":
            print(f"  [SUBMIT] Attempting submission...")
            submit_result = client.submit_alpha(alpha_id)
            submit_status = submit_result.get("status", "unknown")
            
            if submit_status == "ACTIVE":
                results["submitted"] += 1
                results["submitted_alphas"].append({
                    "alpha_id": alpha_id,
                    "sharpe": sharpe,
                    "fitness": fitness,
                    "turnover": turnover,
                    "max_corr": max_corr,
                })
                db["alphas"][alpha_id].update({
                    "status": "ACTIVE",
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                })
                # Add to active PnL pool for subsequent correlations
                new_pnl = client.fetch_pnl(alpha_id)
                if len(new_pnl) >= 50:
                    active_pnls[alpha_id] = new_pnl
                print(f"  ✓ ACTIVE: {alpha_id}")
            elif submit_status == "PENDING":
                results["submitted"] += 1
                results["submitted_alphas"].append({
                    "alpha_id": alpha_id,
                    "sharpe": sharpe,
                    "status": "PENDING",
                })
                db["alphas"][alpha_id].update({
                    "status": "PENDING",
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                })
                print(f"  ⏳ PENDING: {alpha_id}")
            else:
                results["submit_failed"] += 1
                db["alphas"][alpha_id]["submit_failed_at"] = datetime.now(timezone.utc).isoformat()
                db["alphas"][alpha_id]["submit_fail_reason"] = submit_status
                print(f"  ✗ SUBMIT FAILED: {submit_status}")
        
        elif action == "OBSERVE":
            results["observed"] += 1
            results["observed_alphas"].append({
                "alpha_id": alpha_id,
                "sharpe": sharpe,
                "fitness": fitness,
            })
            if alpha_id:
                db["alphas"][alpha_id]["status"] = "OBSERVE"
            print(f"  👁️  OBSERVED: {alpha_id}")
        
        else:
            results["discarded"] += 1
            if alpha_id:
                db["alphas"][alpha_id]["status"] = "DISCARD"
            print(f"  🗑️  DISCARDED")
        
        # Save progress after each candidate
        save_lessons(lessons)
        save_alpha_db(db)
        
        # Brief pause between candidates
        time.sleep(2)
    
    # Summary
    print(f"\n{'='*70}")
    print(f"Template {template_id} Summary:")
    print(f"  Candidates: {results['candidates']}")
    print(f"  Simulated: {results['simulated']}")
    print(f"  Submitted (ACTIVE): {results['submitted']}")
    print(f"  Submit Failed: {results['submit_failed']}")
    print(f"  Observed: {results['observed']}")
    print(f"  Discarded: {results['discarded']}")
    print(f"  Errors: {results['errors']}")
    print(f"{'='*70}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Create and submit alphas directly from templates (GLB TOPDIV3000 delay=1)"
    )
    parser.add_argument(
        "--template",
        type=str,
        help="Template ID to process (e.g., 'profitability_trend')",
    )
    parser.add_argument(
        "--template-list",
        nargs="+",
        help="List of template IDs to process",
    )
    parser.add_argument(
        "--all-templates",
        action="store_true",
        help="Process all available templates",
    )
    parser.add_argument(
        "--high-turnover-only",
        action="store_true",
        help="Only process templates suitable for high turnover test",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=10,
        help="Max candidates per template (default: 10)",
    )
    parser.add_argument(
        "--max-per-template",
        type=int,
        help="Alias for --max-candidates",
    )
    parser.add_argument(
        "--submit-threshold",
        type=float,
        default=1.5,
        help="Minimum Sharpe threshold for auto-submit (default: 1.5)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview candidates without simulating or submitting",
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List all available templates and exit",
    )
    
    args = parser.parse_args()
    
    # Handle max-per-template alias
    if args.max_per_template:
        args.max_candidates = args.max_per_template
    
    # Load target and templates
    target = load_target()
    print(f"Target: {target.describe()}")
    print(f"  Region: {target.region}")
    print(f"  Universe: {target.universe}")
    print(f"  Delay: {target.delay}")
    print(f"  Neutralizations: {list(target.neutralizations)}")
    print(f"  Excluded datasets: {sorted(target.excluded_dataset_ids)}")
    
    templates = load_templates()
    print(f"\nLoaded {len(templates)} templates")
    
    # List templates mode
    if args.list_templates:
        print("\nAvailable templates:")
        for i, tmpl in enumerate(templates, 1):
            tid = tmpl.get("template_id", "unknown")
            desc = tmpl.get("description", "N/A")
            tags = tmpl.get("tags", [])
            print(f"  {i:2d}. {tid:<35} {desc[:50]}")
            if tags:
                print(f"      Tags: {', '.join(tags)}")
        return
    
    # Filter templates
    selected_templates = []
    if args.template:
        selected = [t for t in templates if t.get("template_id") == args.template]
        if not selected:
            print(f"Error: Template '{args.template}' not found")
            sys.exit(1)
        selected_templates = selected
    elif args.template_list:
        for tid in args.template_list:
            matching = [t for t in templates if t.get("template_id") == tid]
            if not matching:
                print(f"Warning: Template '{tid}' not found")
            else:
                selected_templates.extend(matching)
        if not selected_templates:
            print("Error: No valid templates found in list")
            sys.exit(1)
    elif args.all_templates:
        selected_templates = templates
    else:
        print("Error: Must specify --template, --template-list, --all-templates, or --list-templates")
        parser.print_help()
        sys.exit(1)
    
    # Filter for high turnover if requested
    if args.high_turnover_only:
        before = len(selected_templates)
        selected_templates = filter_high_turnover_templates(selected_templates)
        print(f"\n[filter] High turnover filter: {before} → {len(selected_templates)} templates")
    
    if not selected_templates:
        print("No templates to process")
        return
    
    print(f"\nProcessing {len(selected_templates)} template(s):")
    for tmpl in selected_templates:
        print(f"  - {tmpl.get('template_id')}")
    
    # Load state
    lessons = load_lessons()
    db = load_alpha_db()
    
    # Connect to BRAIN
    if not args.dry_run:
        print("\n[init] Connecting to BRAIN API...")
        client = BrainClient(target=target)
        client.connect()
        print("[init] Connected successfully")
    else:
        client = BrainClient(target=target)  # type: ignore
        print("\n[init] Dry-run mode - no API calls will be made")
    
    # Process each template
    all_results = []
    overall_submitted = 0
    overall_observed = 0
    overall_errors = 0
    
    for tmpl in selected_templates:
        result = create_alphas_from_template(
            template=tmpl,
            max_candidates=args.max_candidates,
            client=client,
            lessons=lessons,
            db=db,
            submit_threshold=args.submit_threshold,
            dry_run=args.dry_run,
        )
        all_results.append(result)
        overall_submitted += result.get("submitted", 0)
        overall_observed += result.get("observed", 0)
        overall_errors += result.get("errors", 0)
        
        # Pause between templates
        if not args.dry_run and len(selected_templates) > 1:
            print("\n[pause] Waiting 10s before next template...")
            time.sleep(10)
    
    # Final summary
    print(f"\n{'='*70}")
    print("OVERALL SUMMARY")
    print(f"{'='*70}")
    print(f"Templates processed: {len(selected_templates)}")
    print(f"Total submitted (ACTIVE/PENDING): {overall_submitted}")
    print(f"Total observed: {overall_observed}")
    print(f"Total errors: {overall_errors}")
    print(f"{'='*70}")
    
    # Save final report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target": target.describe(),
        "templates_processed": len(selected_templates),
        "total_submitted": overall_submitted,
        "total_observed": overall_observed,
        "total_errors": overall_errors,
        "results_by_template": all_results,
    }
    
    report_path = SKILL_DIR / "alpha_creation_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
