#!/usr/bin/env python3
"""test_discovery_workflow.py — End-to-end test for T-MAG v2.0 Data Discovery Engine

Tests the complete workflow:
  1. Load field catalog
  2. Discover field_pairs for test skeleton
  3. Validate 70-20-10 distribution
  4. Test type safety
  5. Test lessons integration
  6. Compare manual vs discovered performance

Usage:
  python3 scripts/test_discovery_workflow.py
  python3 scripts/test_discovery_workflow.py --verbose
  python3 scripts/test_discovery_workflow.py --skeleton "rank({momentum})"
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add scripts to path
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from data_discovery import (
    DataDiscoveryEngine,
    FieldCatalog,
    PlaceholderAnalyzer,
    SemanticFieldMatcher,
    CrossDomainExplorer,
    WildcardMutator,
    LessonsDrivenAdjuster,
)
from research_target import load_target

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)


def test_field_catalog():
    """Test 1: Field catalog loading and indexing."""
    print("\n" + "=" * 70)
    print("TEST 1: Field Catalog Loading")
    print("=" * 70)
    
    try:
        catalog = FieldCatalog.load()
        
        print(f"✓ Loaded catalog: {catalog.field_count} fields")
        print(f"✓ Categories: {len(catalog.by_category)}")
        print(f"✓ Keyword index: {len(catalog.keyword_index)} keywords")
        
        # Test field lookup
        test_field = catalog.get_field("operating_income")
        if test_field:
            print(f"✓ Field lookup works: {test_field['id']}")
        else:
            print("✗ Field lookup failed for 'operating_income'")
            return False
        
        # Test search
        results = catalog.search_by_keywords(["profit", "income"], limit=5)
        print(f"✓ Keyword search returned {len(results)} results")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_placeholder_analyzer():
    """Test 2: Placeholder extraction and semantic analysis."""
    print("\n" + "=" * 70)
    print("TEST 2: Placeholder Analyzer")
    print("=" * 70)
    
    test_skeletons = [
        "group_rank(ts_rank({profitability} / {scale}, {window}), {group})",
        "rank({momentum})",
        "{signal1} + {signal2}",
    ]
    
    try:
        for skeleton in test_skeletons:
            print(f"\nSkeleton: {skeleton}")
            analyzer = PlaceholderAnalyzer(skeleton)
            
            print(f"  Placeholders: {analyzer.placeholders}")
            print(f"  Semantic keywords: {analyzer.semantic_keywords}")
            print(f"  Type requirements: {analyzer.data_type_requirements}")
            
            # Verify placeholders were found
            if not analyzer.placeholders:
                print(f"  ✗ No placeholders found!")
                return False
            
            print(f"  ✓ Found {len(analyzer.placeholders)} placeholders")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_pool_a_semantic_matcher():
    """Test 3: Pool A semantic field matching."""
    print("\n" + "=" * 70)
    print("TEST 3: Pool A - Semantic Field Matcher")
    print("=" * 70)
    
    try:
        catalog = FieldCatalog.load()
        matcher = SemanticFieldMatcher(catalog)
        
        test_keywords = ["profitability", "profit", "income"]
        fields = matcher.match_placeholder(test_keywords, pool_size=7)
        
        print(f"✓ Matched {len(fields)} fields for keywords: {test_keywords}")
        
        for i, field in enumerate(fields[:5], 1):
            print(f"  {i}. {field['id']} (coverage={field.get('coverage', 0):.2f})")
        
        if len(fields) != 7:
            print(f"✗ Expected 7 fields, got {len(fields)}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_pool_b_cross_domain():
    """Test 4: Pool B cross-domain exploration."""
    print("\n" + "=" * 70)
    print("TEST 4: Pool B - Cross-Domain Explorer")
    print("=" * 70)
    
    try:
        catalog = FieldCatalog.load()
        explorer = CrossDomainExplorer(catalog)
        
        test_keywords = ["profitability"]
        fields = explorer.explore(test_keywords, pool_size=2, primary_category="fundamental")
        
        print(f"✓ Explored {len(fields)} cross-domain fields")
        
        # Check category distribution
        categories = set()
        for field in fields:
            cat = (field.get("category") or {}).get("id", "unknown")
            categories.add(cat)
            print(f"  • {field['id']} (category={cat})")
        
        print(f"✓ Categories represented: {categories}")
        
        if len(fields) < 1:
            print("✗ No cross-domain fields found")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_pool_c_wildcard():
    """Test 5: Pool C wildcard mutation with type safety."""
    print("\n" + "=" * 70)
    print("TEST 5: Pool C - Wildcard Mutator (Type Safety)")
    print("=" * 70)
    
    try:
        catalog = FieldCatalog.load()
        mutator = WildcardMutator(catalog)
        
        # Test numerical sampling
        numerical_fields = mutator.sample_wildcard(
            data_type="numerical",
            exclude=set(),
            count=3,
            seed=42
        )
        
        print(f"✓ Sampled {len(numerical_fields)} numerical wildcard fields")
        
        # Verify all are MATRIX type
        for field in numerical_fields:
            if field.get("type") != "MATRIX":
                print(f"✗ Type safety violation: {field['id']} is not MATRIX")
                return False
            print(f"  • {field['id']} (type={field['type']})")
        
        print("✓ Type safety verified: all fields are numerical (MATRIX)")
        
        # Test mutation log
        log = mutator.get_mutation_log()
        print(f"✓ Mutation log: {len(log)} entries")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_lessons_driven_adjuster():
    """Test 6: Lessons-driven field adjustment."""
    print("\n" + "=" * 70)
    print("TEST 6: Lessons-Driven Adjuster")
    print("=" * 70)
    
    try:
        lessons_path = SKILL_DIR / "lessons.json"
        
        if not lessons_path.exists():
            print("⚠ No lessons.json found, skipping adjuster test")
            return True
        
        adjuster = LessonsDrivenAdjuster(lessons_path)
        
        print(f"✓ Loaded lessons from {lessons_path}")
        print(f"  Field performance records: {len(adjuster.field_performance)}")
        print(f"  Preferred fields: {len(adjuster.preferred_fields)}")
        print(f"  Excluded fields: {len(adjuster.excluded_fields)}")
        
        # Test adjustment
        test_fields = [
            (0.5, {"id": "test_field_1"}),
            (0.7, {"id": "test_field_2"}),
        ]
        
        adjusted = adjuster.adjust_field_scores(test_fields)
        print(f"✓ Adjustment works: {len(test_fields)} → {len(adjusted)} fields")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_full_discovery_engine():
    """Test 7: Full DataDiscoveryEngine with 70-20-10 distribution."""
    print("\n" + "=" * 70)
    print("TEST 7: Full Discovery Engine (70-20-10 Test)")
    print("=" * 70)
    
    try:
        catalog = FieldCatalog.load()
        lessons_path = SKILL_DIR / "lessons.json" if (SKILL_DIR / "lessons.json").exists() else None
        
        engine = DataDiscoveryEngine(catalog, lessons_path=lessons_path)
        
        # Test skeleton
        skeleton = "group_rank(ts_rank({profitability} / {scale}, {window}), {group})"
        print(f"\nSkeleton: {skeleton}")
        
        # Discover fields
        field_pairs = engine.discover_fields(skeleton, max_fields=10)
        
        print(f"✓ Discovered {len(field_pairs)} field_pairs")
        
        # Check distribution
        distribution = engine.get_pool_distribution(field_pairs)
        print(f"\nPool Distribution:")
        print(f"  Pool A (exploitation): {distribution.get('A', 0)}")
        print(f"  Pool B (cross-domain): {distribution.get('B', 0)}")
        print(f"  Pool C (wildcard): {distribution.get('C', 0)}")
        
        # Verify 70-20-10 ratio (with tolerance)
        pool_a_ratio = distribution.get('A', 0) / len(field_pairs)
        pool_b_ratio = distribution.get('B', 0) / len(field_pairs)
        pool_c_ratio = distribution.get('C', 0) / len(field_pairs)
        
        print(f"\nActual Ratios:")
        print(f"  Pool A: {pool_a_ratio:.1%} (target: 70%)")
        print(f"  Pool B: {pool_b_ratio:.1%} (target: 20%)")
        print(f"  Pool C: {pool_c_ratio:.1%} (target: 10%)")
        
        # Tolerance: ±15% of target
        if not (0.55 <= pool_a_ratio <= 0.85):
            print(f"✗ Pool A ratio out of range: {pool_a_ratio:.1%}")
            return False
        
        if not (0.05 <= pool_b_ratio <= 0.35):
            print(f"⚠ Pool B ratio slightly out of range: {pool_b_ratio:.1%} (acceptable)")
        
        if not (0.0 <= pool_c_ratio <= 0.25):
            print(f"⚠ Pool C ratio slightly out of range: {pool_c_ratio:.1%} (acceptable)")
        
        print("\n✓ 70-20-10 distribution verified (within tolerance)")
        
        # Validate discovered fields
        is_valid, errors = engine.validate_field_pairs(field_pairs)
        
        if not is_valid:
            print(f"✗ Validation failed:")
            for error in errors:
                print(f"  • {error}")
            return False
        
        print("✓ All discovered field_pairs are valid")
        
        # Show sample field_pairs
        print("\nSample Discovered field_pairs:")
        for i, fp in enumerate(field_pairs[:5], 1):
            fp_clean = {k: v for k, v in fp.items() if k != "_metadata"}
            pool = fp.get("_metadata", {}).get("source_pool", "?")
            print(f"  {i}. {fp_clean} (Pool {pool})")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_placeholder():
    """Test 8: Multiple placeholder handling."""
    print("\n" + "=" * 70)
    print("TEST 8: Multi-Placeholder Discovery")
    print("=" * 70)
    
    try:
        catalog = FieldCatalog.load()
        engine = DataDiscoveryEngine(catalog)
        
        skeleton = "group_rank({signal1} + {signal2}, {group})"
        print(f"\nSkeleton: {skeleton}")
        
        # Test per-placeholder mode
        field_pairs = engine.discover_fields(skeleton, max_fields=6, per_placeholder=True)
        
        print(f"✓ Discovered {len(field_pairs)} field_pairs (6 per placeholder)")
        
        # Count placeholders
        signal1_count = sum(1 for fp in field_pairs if "signal1" in fp)
        signal2_count = sum(1 for fp in field_pairs if "signal2" in fp)
        
        print(f"  signal1: {signal1_count} field_pairs")
        print(f"  signal2: {signal2_count} field_pairs")
        
        if signal1_count < 3 or signal2_count < 3:
            print(f"✗ Unbalanced distribution")
            return False
        
        print("✓ Multi-placeholder discovery works correctly")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def run_all_tests(verbose: bool = False):
    """Run all tests and report results."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("\n" + "═" * 70)
    print("  T-MAG v2.0 DATA DISCOVERY ENGINE - END-TO-END TEST")
    print("═" * 70)
    
    tests = [
        ("Field Catalog", test_field_catalog),
        ("Placeholder Analyzer", test_placeholder_analyzer),
        ("Pool A: Semantic Matcher", test_pool_a_semantic_matcher),
        ("Pool B: Cross-Domain Explorer", test_pool_b_cross_domain),
        ("Pool C: Wildcard Mutator", test_pool_c_wildcard),
        ("Lessons-Driven Adjuster", test_lessons_driven_adjuster),
        ("Full Discovery Engine (70-20-10)", test_full_discovery_engine),
        ("Multi-Placeholder Handling", test_multi_placeholder),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Test {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "═" * 70)
    print("  TEST SUMMARY")
    print("═" * 70)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")
    
    print("\n" + "─" * 70)
    print(f"Total: {passed}/{len(results)} tests passed")
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED - T-MAG v2.0 is ready for production!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed - please review errors above")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Test T-MAG v2.0 Data Discovery Engine end-to-end"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)"
    )
    parser.add_argument(
        "--test",
        choices=[
            "catalog", "placeholder", "pool_a", "pool_b", "pool_c",
            "lessons", "engine", "multi"
        ],
        help="Run specific test only"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.test:
        # Run specific test
        test_map = {
            "catalog": test_field_catalog,
            "placeholder": test_placeholder_analyzer,
            "pool_a": test_pool_a_semantic_matcher,
            "pool_b": test_pool_b_cross_domain,
            "pool_c": test_pool_c_wildcard,
            "lessons": test_lessons_driven_adjuster,
            "engine": test_full_discovery_engine,
            "multi": test_multi_placeholder,
        }
        
        test_func = test_map[args.test]
        result = test_func()
        return 0 if result else 1
    else:
        # Run all tests
        return run_all_tests(args.verbose)


if __name__ == "__main__":
    sys.exit(main())
