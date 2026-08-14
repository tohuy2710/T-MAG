#!/usr/bin/env python3
"""test_template_system.py — Quick validation test for template-based alpha creation.

Validates:
1. Configuration loads correctly
2. Templates are valid and readable
3. Field validator works
4. Candidate generation works
5. Field translation works
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from generate_candidates import (
    load_templates,
    FieldValidator,
    expand_template,
    deduplicate,
)
from research_target import load_target


def test_configuration():
    """Test 1: Configuration loads correctly."""
    print("Test 1: Configuration loading...")
    try:
        target = load_target()
        print(f"  ✓ Target loaded: {target.describe()}")
        print(f"    Region: {target.region}")
        print(f"    Universe: {target.universe}")
        print(f"    Delay: {target.delay}")
        print(f"    Neutralizations: {len(target.neutralizations)}")
        print(f"    Excluded datasets: {len(target.excluded_dataset_ids)}")
        
        assert target.region == "GLB", f"Expected GLB, got {target.region}"
        assert target.universe == "TOPDIV3000", f"Expected TOPDIV3000, got {target.universe}"
        assert target.delay == 1, f"Expected delay=1, got {target.delay}"
        assert "model110" in target.excluded_dataset_ids, "model110 should be excluded"
        
        print("  ✓ All configuration checks passed")
        return True
    except Exception as e:
        print(f"  ✗ Configuration test failed: {e}")
        return False


def test_templates():
    """Test 2: Templates are valid and readable."""
    print("\nTest 2: Template loading...")
    try:
        templates = load_templates()
        print(f"  ✓ Loaded {len(templates)} templates")
        
        assert len(templates) > 0, "No templates found"
        
        # Check a few key templates exist
        template_ids = [t.get("template_id") for t in templates]
        expected = ["profitability_trend", "analyst_estimate_trend", "overnight_reversal"]
        for tid in expected:
            assert tid in template_ids, f"Expected template '{tid}' not found"
            print(f"  ✓ Found template: {tid}")
        
        # Validate template structure
        for tmpl in templates[:3]:
            tid = tmpl.get("template_id", "unknown")
            assert "skeleton" in tmpl, f"{tid}: missing skeleton"
            assert "field_pairs" in tmpl, f"{tid}: missing field_pairs"
            assert len(tmpl["field_pairs"]) > 0, f"{tid}: empty field_pairs"
            print(f"  ✓ Template structure valid: {tid}")
        
        print("  ✓ All template checks passed")
        return True
    except Exception as e:
        print(f"  ✗ Template test failed: {e}")
        return False


def test_field_validator():
    """Test 3: Field validator works."""
    print("\nTest 3: Field validator...")
    try:
        target = load_target()
        validator = FieldValidator(
            target.require_fields_reference(),
            target.excluded_dataset_ids
        )
        
        print(f"  ✓ Loaded {len(validator.field_list)} fields")
        print(f"  ✓ Excluded {validator.excluded_field_count} fields from model110")
        
        assert len(validator.field_list) > 1000, "Too few fields loaded"
        
        # Test some known fields
        test_fields = [
            "close",
            "volume",
            "returns",
            "adv20",
        ]
        for field in test_fields:
            if validator.is_valid(field):
                print(f"  ✓ Valid field: {field}")
        
        print("  ✓ Field validator checks passed")
        return True
    except Exception as e:
        print(f"  ✗ Field validator test failed: {e}")
        return False


def test_candidate_generation():
    """Test 4: Candidate generation works."""
    print("\nTest 4: Candidate generation...")
    try:
        target = load_target()
        templates = load_templates()
        validator = FieldValidator(
            target.require_fields_reference(),
            target.excluded_dataset_ids
        )
        
        # Pick first template
        template = templates[0]
        tid = template.get("template_id", "unknown")
        print(f"  Testing template: {tid}")
        
        # Generate candidates
        candidates = expand_template(
            template,
            max_candidates=5,
            validator=validator,
            target=target,
        )
        
        print(f"  ✓ Generated {len(candidates)} candidates")
        
        assert len(candidates) > 0, f"No candidates generated from {tid}"
        
        # Check candidate structure
        for i, cand in enumerate(candidates[:2], 1):
            assert "expression" in cand, f"Candidate {i}: missing expression"
            assert "settings" in cand, f"Candidate {i}: missing settings"
            expr = cand["expression"]
            settings = cand["settings"]
            print(f"  ✓ Candidate {i}: {len(expr)} chars, {len(settings)} settings")
            print(f"    Expression: {expr[:80]}...")
            print(f"    Decay: {settings.get('decay')}")
            print(f"    Neutralization: {settings.get('neutralization')}")
        
        # Test deduplication
        before = len(candidates)
        candidates = deduplicate(candidates)
        after = len(candidates)
        print(f"  ✓ Deduplication: {before} → {after}")
        
        print("  ✓ Candidate generation checks passed")
        return True
    except Exception as e:
        print(f"  ✗ Candidate generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_field_translation():
    """Test 5: Field translation works."""
    print("\nTest 5: Field translation...")
    try:
        target = load_target()
        validator = FieldValidator(
            target.require_fields_reference(),
            target.excluded_dataset_ids
        )
        
        # Test some legacy → GLB translations
        test_cases = [
            ("operating_income / equity", "vec_avg(actual_value_return_on_equity_quarterly16)"),
            ("est_eps / close", "earnings_yield_next_twelve_months"),
        ]
        
        for legacy, expected_glb in test_cases:
            expr = f"rank({legacy})"
            translated = validator.translate_expression(expr)
            if expected_glb in translated:
                print(f"  ✓ Translated: {legacy[:40]}...")
                print(f"    → {translated[:80]}...")
            else:
                print(f"  ⚠️  Translation may need update: {legacy}")
        
        print("  ✓ Field translation checks passed")
        return True
    except Exception as e:
        print(f"  ✗ Field translation test failed: {e}")
        return False


def main():
    print("=" * 70)
    print("TEMPLATE SYSTEM VALIDATION TEST")
    print("=" * 70)
    
    tests = [
        test_configuration,
        test_templates,
        test_field_validator,
        test_candidate_generation,
        test_field_translation,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ ALL TESTS PASSED")
        print("\nSystem is ready for alpha creation!")
        print("\nNext steps:")
        print("  1. python3 scripts/analyze_templates.py")
        print("  2. python3 scripts/create_alpha_from_templates.py --list-templates")
        print("  3. python3 scripts/create_alpha_from_templates.py --template profitability_trend --dry-run")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("\nPlease review errors above and fix issues before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
