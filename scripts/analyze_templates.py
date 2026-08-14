#!/usr/bin/env python3
"""analyze_templates.py — Analyze and recommend templates for GLB TOPDIV3000 alpha creation.

Helps users understand which templates are suitable for their needs.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from generate_candidates import load_templates, FieldValidator
from research_target import load_target


def categorize_template(template: dict) -> list[str]:
    """Categorize template by type."""
    categories = []
    
    desc = template.get("description", "").lower()
    hypo = template.get("hypothesis", "").lower()
    tid = template.get("template_id", "").lower()
    
    # Fundamental
    if any(term in desc or term in hypo or term in tid for term in [
        "profitability", "quality", "fundamental", "roe", "roa", "leverage"
    ]):
        categories.append("fundamental")
    
    # Analyst
    if any(term in desc or term in hypo or term in tid for term in [
        "analyst", "estimate", "consensus", "revision", "forecast"
    ]):
        categories.append("analyst")
    
    # Technical
    if any(term in desc or term in hypo or term in tid for term in [
        "momentum", "reversal", "price", "volume", "vwap", "gap", "technical"
    ]):
        categories.append("technical")
    
    # Sentiment
    if any(term in desc or term in hypo or term in tid for term in [
        "sentiment", "news", "buzz", "social"
    ]):
        categories.append("sentiment")
    
    if not categories:
        categories.append("other")
    
    return categories


def estimate_turnover_level(template: dict) -> str:
    """Estimate turnover level from template settings."""
    default_settings = template.get("default_settings", {})
    decay = default_settings.get("decay", 0)
    
    param_ranges = template.get("param_ranges", {})
    decay_range = param_ranges.get("decay", [])
    
    avg_decay = decay
    if decay_range:
        avg_decay = sum(decay_range) / len(decay_range)
    
    if avg_decay == 0:
        return "low"  # Fundamental factors
    elif avg_decay <= 4:
        return "low-moderate"
    elif avg_decay <= 10:
        return "moderate"
    elif avg_decay <= 20:
        return "moderate-high"
    else:
        return "high"


def count_field_pairs(template: dict) -> int:
    """Count number of field pair combinations."""
    field_pairs = template.get("field_pairs", [])
    return len(field_pairs)


def estimate_candidate_count(template: dict) -> int:
    """Estimate total candidate count from template."""
    field_pairs = len(template.get("field_pairs", []))
    param_ranges = template.get("param_ranges", {})
    
    total = field_pairs
    for param, values in param_ranges.items():
        if isinstance(values, list) and param != "neutralization":
            total *= len(values)
    
    # Multiply by number of neutralizations (from target)
    target = load_target()
    total *= len(target.neutralizations)
    
    return total


def validate_template_fields(template: dict, validator: FieldValidator) -> dict[str, Any]:
    """Check if template fields are available.
    
    For templates with placeholders, validation is deferred until expansion.
    """
    field_pairs = template.get("field_pairs", [])
    skeleton = template.get("skeleton", "")
    
    # If skeleton has placeholders, we can only validate the actual field_pair values
    has_placeholders = '{' in skeleton and '}' in skeleton
    
    all_fields = set()
    for fp in field_pairs:
        for key, value in fp.items():
            if key not in ("name", "description", "label"):
                field_val = str(value)
                # Only add if it looks like a simple field name (not a complex expression)
                # Complex expressions with placeholders will be validated after expansion
                if not ('{' in field_val or '}' in field_val or 
                        '(' in field_val or ')' in field_val or
                        '>' in field_val or '<' in field_val or
                        '/' in field_val or '*' in field_val):
                    all_fields.add(field_val)
    
    invalid_fields = []
    for field in all_fields:
        # Skip built-in operators and primitives
        if field.lower() in {'close', 'open', 'high', 'low', 'volume', 'returns', 
                             'vwap', 'adv20', 'cap', 'sharesout'}:
            continue
        if not validator.is_valid(field):
            invalid_fields.append(field)
    
    status = "valid" if not invalid_fields else ("partial" if has_placeholders else "invalid")
    
    return {
        "total_fields": len(all_fields),
        "valid_fields": len(all_fields) - len(invalid_fields),
        "invalid_fields": invalid_fields,
        "status": status,
        "has_placeholders": has_placeholders,
    }


def analyze_templates(show_details: bool = False, show_recommendations: bool = False):
    """Analyze all templates and show statistics."""
    
    target = load_target()
    templates = load_templates()
    
    print(f"Target Configuration: {target.describe()}")
    print(f"Loaded {len(templates)} templates\n")
    
    # Load field validator
    validator = FieldValidator(
        target.require_fields_reference(),
        target.excluded_dataset_ids
    )
    print(f"Field validator: {len(validator.field_list)} fields available")
    print(f"Excluded datasets: {sorted(target.excluded_dataset_ids)}")
    print(f"Excluded fields: {validator.excluded_field_count}\n")
    
    # Categorize templates
    by_category = defaultdict(list)
    by_turnover = defaultdict(list)
    
    for tmpl in templates:
        tid = tmpl.get("template_id", "unknown")
        categories = categorize_template(tmpl)
        turnover = estimate_turnover_level(tmpl)
        
        for cat in categories:
            by_category[cat].append(tid)
        by_turnover[turnover].append(tid)
    
    print("=" * 70)
    print("TEMPLATE CATEGORIES")
    print("=" * 70)
    for cat in sorted(by_category.keys()):
        print(f"\n{cat.upper()} ({len(by_category[cat])} templates):")
        for tid in sorted(by_category[cat])[:10]:
            print(f"  - {tid}")
        if len(by_category[cat]) > 10:
            print(f"  ... and {len(by_category[cat]) - 10} more")
    
    print("\n" + "=" * 70)
    print("ESTIMATED TURNOVER LEVELS")
    print("=" * 70)
    for level in ["low", "low-moderate", "moderate", "moderate-high", "high"]:
        if level in by_turnover:
            print(f"\n{level.upper()} ({len(by_turnover[level])} templates):")
            for tid in sorted(by_turnover[level])[:5]:
                print(f"  - {tid}")
            if len(by_turnover[level]) > 5:
                print(f"  ... and {len(by_turnover[level]) - 5} more")
    
    # Field validation summary
    print("\n" + "=" * 70)
    print("FIELD VALIDATION STATUS")
    print("=" * 70)
    
    all_valid = []
    partial_valid = []
    needs_update = []
    
    for tmpl in templates:
        tid = tmpl.get("template_id", "unknown")
        validation = validate_template_fields(tmpl, validator)
        
        status = validation.get("status", "unknown")
        if status == "valid":
            all_valid.append(tid)
        elif status == "partial":
            partial_valid.append(tid)
        else:
            needs_update.append((tid, validation))
    
    print(f"\nTemplates ready (all fields valid): {len(all_valid)}")
    print(f"Templates with placeholders (validated on expansion): {len(partial_valid)}")
    print(f"Templates needing field updates: {len(needs_update)}")
    
    if show_details and needs_update:
        print("\nTemplates needing field updates:")
        for tid, validation in needs_update[:10]:
            print(f"\n  {tid}:")
            print(f"    Valid: {validation['valid_fields']}/{validation['total_fields']}")
            if validation['invalid_fields']:
                print(f"    Invalid: {', '.join(validation['invalid_fields'][:3])}")
                if len(validation['invalid_fields']) > 3:
                    print(f"    ... and {len(validation['invalid_fields']) - 3} more")
    
    # Detailed template info
    if show_details:
        print("\n" + "=" * 70)
        print("DETAILED TEMPLATE ANALYSIS")
        print("=" * 70)
        
        for tmpl in templates:
            tid = tmpl.get("template_id", "unknown")
            desc = tmpl.get("description", "N/A")
            categories = ", ".join(categorize_template(tmpl))
            turnover = estimate_turnover_level(tmpl)
            field_count = count_field_pairs(tmpl)
            est_candidates = estimate_candidate_count(tmpl)
            tags = tmpl.get("tags", [])
            
            print(f"\n{tid}")
            print(f"  Description: {desc[:60]}...")
            print(f"  Categories: {categories}")
            print(f"  Turnover level: {turnover}")
            print(f"  Field pairs: {field_count}")
            print(f"  Estimated candidates: {est_candidates}")
            if tags:
                print(f"  Tags: {', '.join(tags)}")
            
            validation = validate_template_fields(tmpl, validator)
            if validation["invalid_fields"]:
                print(f"  ⚠️  Invalid fields: {len(validation['invalid_fields'])}")
    
    # Recommendations
    if show_recommendations:
        print("\n" + "=" * 70)
        print("RECOMMENDATIONS")
        print("=" * 70)
        
        print("\n🏆 HIGH WIN RATE (Start Here)")
        for tid in ["profitability_trend", "analyst_estimate_trend"]:
            if tid in [t.get("template_id") for t in templates]:
                print(f"  python3 scripts/create_alpha_from_templates.py --template {tid} --max-candidates 10")
        
        print("\n📊 DIVERSIFIED PORTFOLIO")
        portfolio_templates = [
            "profitability_trend",
            "analyst_estimate_trend", 
            "sector_relative_momentum",
            "overnight_reversal"
        ]
        available = [t for t in portfolio_templates if t in [tmpl.get("template_id") for tmpl in templates]]
        if available:
            print(f"  python3 scripts/create_alpha_from_templates.py \\")
            print(f"      --template-list {' '.join(available[:4])} \\")
            print(f"      --max-per-template 5")
        
        print("\n⚡ HIGH TURNOVER TEST")
        high_turnover = [tid for tid in by_turnover.get("low", []) + by_turnover.get("low-moderate", [])]
        if high_turnover:
            print(f"  # Process {len(high_turnover)} templates suitable for high turnover")
            print(f"  python3 scripts/create_alpha_from_templates.py \\")
            print(f"      --all-templates \\")
            print(f"      --high-turnover-only \\")
            print(f"      --max-per-template 5")
        
        print("\n🔍 DRY RUN (Preview First)")
        print(f"  python3 scripts/create_alpha_from_templates.py \\")
        print(f"      --template profitability_trend \\")
        print(f"      --max-candidates 5 \\")
        print(f"      --dry-run")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze templates for GLB TOPDIV3000 alpha creation"
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Show detailed template information",
    )
    parser.add_argument(
        "--recommendations",
        action="store_true",
        help="Show recommended commands",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all information (details + recommendations)",
    )
    
    args = parser.parse_args()
    
    if args.all:
        args.details = True
        args.recommendations = True
    
    analyze_templates(
        show_details=args.details,
        show_recommendations=args.recommendations,
    )


if __name__ == "__main__":
    main()
