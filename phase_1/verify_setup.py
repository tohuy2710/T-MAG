#!/usr/bin/env python3
"""Verify Phase 1 setup without requiring full dependencies."""

import sys
import json
from pathlib import Path

def verify_setup():
    """Verify phase 1 is properly set up."""
    
    print("\n" + "="*70)
    print("  Phase 1 Setup Verification")
    print("="*70 + "\n")
    
    errors = []
    warnings = []
    
    # Check directory structure
    phase1_dir = Path(__file__).parent
    required_files = [
        "phase_1_config.py",
        "phase_1_sim.py",
        "phase_1_utils.py",
        "__init__.py",
        "README_PHASE_1.md",
        "QUICK_START.md",
    ]
    
    print("[1] Checking file structure...")
    for fname in required_files:
        fpath = phase1_dir / fname
        if fpath.exists():
            print(f"    ✓ {fname}")
        else:
            print(f"    ✗ {fname} MISSING")
            errors.append(f"Missing file: {fname}")
    
    # Check output directory
    output_dir = phase1_dir / "output"
    individual_dir = output_dir / "individual"
    
    print("\n[2] Checking output directories...")
    if output_dir.exists():
        print(f"    ✓ output/")
    else:
        print(f"    ⚠ output/ directory missing (will be created)")
        warnings.append("Output directory not created yet")
    
    if individual_dir.exists():
        print(f"    ✓ output/individual/")
    else:
        print(f"    ⚠ output/individual/ missing (will be created)")
    
    # Check template
    template_file = phase1_dir.parent / "templates" / "quarterly_return_reversal.json"
    
    print("\n[3] Checking template...")
    if template_file.exists():
        try:
            data = json.loads(template_file.read_text())
            template_id = data.get("template_id")
            skeleton = data.get("skeleton")
            field_pairs = data.get("field_pairs", [])
            param_ranges = data.get("param_ranges", {})
            
            print(f"    ✓ Template file exists")
            print(f"    ✓ Template ID: {template_id}")
            print(f"    ✓ Skeleton: {skeleton}")
            print(f"    ✓ Field pairs: {len(field_pairs)}")
            print(f"    ✓ Parameters: {list(param_ranges.keys())}")
            
            if not skeleton:
                errors.append("Template missing skeleton")
            if not field_pairs:
                errors.append("Template missing field_pairs")
            if not param_ranges:
                warnings.append("Template has no param_ranges")
                
        except json.JSONDecodeError as e:
            print(f"    ✗ Template JSON invalid: {e}")
            errors.append("Invalid template JSON")
        except Exception as e:
            print(f"    ✗ Template error: {e}")
            errors.append(f"Template error: {e}")
    else:
        print(f"    ✗ Template file not found")
        errors.append("Template file missing")
    
    # Check research target
    target_file = phase1_dir.parent / "config" / "research_target.json"
    
    print("\n[4] Checking research target...")
    if target_file.exists():
        try:
            data = json.loads(target_file.read_text())
            region = data.get("region")
            universe = data.get("universe")
            delay = data.get("delay")
            
            print(f"    ✓ Research target: {region}/{universe}/Delay{delay}")
            
            if region != "GLB" or universe != "TOPDIV3000" or delay != 1:
                warnings.append(f"Expected GLB/TOPDIV3000/Delay1, got {region}/{universe}/Delay{delay}")
        except Exception as e:
            print(f"    ⚠ Research target error: {e}")
            warnings.append(f"Research target error: {e}")
    else:
        print(f"    ✗ Research target not found")
        errors.append("Research target missing")
    
    # Check config can be imported
    print("\n[5] Checking configuration import...")
    try:
        sys.path.insert(0, str(phase1_dir))
        from phase_1_config import (
            DEFAULT_TEMPLATE, BATCH_SIZE, MAX_CANDIDATES_PER_TEMPLATE,
            MAX_CONCURRENT, AUTO_SUBMIT
        )
        print(f"    ✓ Config imports successfully")
        print(f"    ✓ Default template: {DEFAULT_TEMPLATE}")
        print(f"    ✓ Batch size: {BATCH_SIZE}")
        print(f"    ✓ Max per template: {MAX_CANDIDATES_PER_TEMPLATE}")
        print(f"    ✓ Max concurrent: {MAX_CONCURRENT}")
        print(f"    ✓ Auto-submit: {AUTO_SUBMIT}")
        
        if AUTO_SUBMIT:
            warnings.append("Auto-submit is ENABLED - may submit alphas automatically!")
            
    except Exception as e:
        print(f"    ✗ Config import failed: {e}")
        errors.append(f"Config import error: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("  Verification Summary")
    print("="*70)
    
    if errors:
        print(f"\n✗ {len(errors)} ERROR(S) FOUND:")
        for err in errors:
            print(f"  - {err}")
    
    if warnings:
        print(f"\n⚠ {len(warnings)} WARNING(S):")
        for warn in warnings:
            print(f"  - {warn}")
    
    if not errors and not warnings:
        print("\n✓ ALL CHECKS PASSED!")
        print("\nPhase 1 is ready to run:")
        print("  cd /home/tohuy2710/T-MAG/phase_1")
        print("  python3 phase_1_sim.py")
    elif not errors:
        print("\n✓ SETUP COMPLETE (with warnings)")
        print("\nPhase 1 is ready to run:")
        print("  cd /home/tohuy2710/T-MAG/phase_1")
        print("  python3 phase_1_sim.py")
    else:
        print("\n✗ SETUP INCOMPLETE - fix errors before running")
        return 1
    
    print("\n" + "="*70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(verify_setup())
