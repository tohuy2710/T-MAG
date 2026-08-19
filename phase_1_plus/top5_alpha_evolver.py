#!/usr/bin/env python3
"""
Top 5 Alpha Evolution Framework
================================

Step 1: Parameter Mining
- Test multiple window sizes
- Test different thresholds

Step 2: Operator Nesting
- Add ts_rank, group_rank, decay operators
- Test combinations

Settings: Fixed (same as baseline)
- Region: GLB
- Universe: TOPDIV3000
- Delay: 1
- Neutralization: SUBINDUSTRY
- Truncation: 0.08
- Decay: 10
"""

import sys
import itertools
from typing import List, Dict, Any

# ============================================================================
# TOP 5 ALPHA BASE TEMPLATES
# ============================================================================

TOP5_TEMPLATES = {
    "alpha1_spring": {
        "name": "Spring Detection (negative price + positive CMF)",
        "base": "rank(-ts_delta(close, {w1})) * sign(short_term_price_change_2)",
        "params": {
            "w1": [2, 3, 5, 10, 14, 21, 25, 30, 63, 126, 252],  # Price momentum window
        },
        "description": "L15 — Wyckoff spring pattern",
    },
    
    "alpha2_country_cmf": {
        "name": "Country-Relative CMF Level",
        "base": "group_rank(short_term_price_change_2, country)",
        "params": {},  # No parameters to vary
        "description": "L7 — Best performer (Sharpe 1.21)",
    },
    
    "alpha3_raw_cmf": {
        "name": "Raw CMF Level",
        "base": "rank(short_term_price_change_2)",
        "params": {},  # No parameters to vary
        "description": "L1 — Simple baseline",
    },
    
    "alpha4_cmf_additive": {
        "name": "CMF Level + CMF Momentum (Additive)",
        "base": "rank(short_term_price_change_2) + rank(ts_delta(short_term_price_change_2, {w1}))",
        "params": {
            "w1": [2, 3, 5, 10, 14, 21, 25, 30, 63, 126, 252],  # CMF momentum window
        },
        "description": "L11 — Combo signal",
    },
    
    "alpha5_cmf_multiplicative": {
        "name": "CMF Level * CMF Momentum",
        "base": "rank(short_term_price_change_2) * rank(ts_delta(short_term_price_change_2, {w1}))",
        "params": {
            "w1": [2, 3, 5, 10, 14, 21, 25, 30, 63, 126, 252],  # CMF momentum window
        },
        "description": "L11 — Multiplicative combo",
    },
}


# ============================================================================
# OPERATOR NESTING PATTERNS
# ============================================================================

NESTING_OPERATORS = [
    # Time-series operators
    ("ts_rank", "ts_rank({expr}, {w2})"),
    ("ts_decay_linear", "ts_decay_linear({expr}, {w2})"),
    ("ts_mean", "ts_mean({expr}, {w2})"),
    
    # Group operators
    ("group_rank_sector", "group_rank({expr}, subindustry)"),
    ("group_rank_country", "group_rank({expr}, country)"),
    
    # Sign/threshold operators
    ("sign_filter", "sign({expr}) * rank({expr})"),
    ("abs_normalize", "rank(abs({expr}))"),
]


# ============================================================================
# STEP 1: PARAMETER MINING
# ============================================================================

def generate_parameter_variants(template_key: str) -> List[Dict[str, Any]]:
    """
    Generate all parameter combinations for a template.
    
    Returns list of candidates with filled parameters.
    """
    template = TOP5_TEMPLATES[template_key]
    base_expr = template["base"]
    params = template["params"]
    
    candidates = []
    
    if not params:
        # No parameters to vary
        candidates.append({
            "id": f"{template_key}_base",
            "name": template["name"],
            "description": template["description"],
            "expression": base_expr,
            "step": "baseline",
            "params": {},
        })
    else:
        # Generate all combinations
        param_names = list(params.keys())
        param_values = [params[k] for k in param_names]
        
        for combo in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combo))
            
            # Fill expression
            expr = base_expr.format(**param_dict)
            
            # Create candidate ID
            param_str = "_".join([f"{k}{v}" for k, v in param_dict.items()])
            candidate_id = f"{template_key}_{param_str}"
            
            candidates.append({
                "id": candidate_id,
                "name": template["name"],
                "description": f"{template['description']} | Params: {param_dict}",
                "expression": expr,
                "step": "param_mining",
                "params": param_dict,
            })
    
    return candidates


# ============================================================================
# STEP 2: OPERATOR NESTING
# ============================================================================

def generate_nested_variants(base_expr: str, template_key: str, max_nesting: int = 2) -> List[Dict[str, Any]]:
    """
    Generate nested variants by wrapping base expression with operators.
    
    Args:
        base_expr: Base expression to nest
        template_key: Template identifier
        max_nesting: Maximum nesting depth (1 or 2)
    
    Returns list of nested candidates.
    """
    candidates = []
    
    # Single-level nesting
    for op_name, op_pattern in NESTING_OPERATORS:
        # Window parameter for time-series operators
        if "{w2}" in op_pattern:
            for w2 in [5, 10, 20]:
                expr = op_pattern.format(expr=base_expr, w2=w2)
                candidates.append({
                    "id": f"{template_key}_nest_{op_name}_w{w2}",
                    "name": f"Nested: {op_name}",
                    "description": f"Base wrapped with {op_name}(window={w2})",
                    "expression": expr,
                    "step": "operator_nesting_1",
                    "nesting": {"op": op_name, "w2": w2},
                })
        else:
            expr = op_pattern.format(expr=base_expr)
            candidates.append({
                "id": f"{template_key}_nest_{op_name}",
                "name": f"Nested: {op_name}",
                "description": f"Base wrapped with {op_name}",
                "expression": expr,
                "step": "operator_nesting_1",
                "nesting": {"op": op_name},
            })
    
    # Double-level nesting (selective)
    if max_nesting >= 2:
        # Only nest time-series ops on top of time-series ops
        ts_ops = [("ts_rank", "ts_rank({expr}, {w2})"), 
                  ("ts_decay_linear", "ts_decay_linear({expr}, {w2})")]
        
        for op1_name, op1_pattern in ts_ops:
            for w1 in [10, 20]:
                inner_expr = op1_pattern.format(expr=base_expr, w2=w1)
                
                for op2_name, op2_pattern in ts_ops:
                    if op1_name == op2_name:
                        continue  # Don't nest same operator
                    
                    for w2 in [5, 10]:
                        outer_expr = op2_pattern.format(expr=inner_expr, w2=w2)
                        candidates.append({
                            "id": f"{template_key}_nest2_{op1_name}_w{w1}_{op2_name}_w{w2}",
                            "name": f"Double Nested: {op2_name} → {op1_name}",
                            "description": f"{op2_name}({op1_name}(base, w={w1}), w={w2})",
                            "expression": outer_expr,
                            "step": "operator_nesting_2",
                            "nesting": {"op1": op1_name, "w1": w1, "op2": op2_name, "w2": w2},
                        })
    
    return candidates


# ============================================================================
# MAIN GENERATION
# ============================================================================

def generate_all_candidates() -> List[Dict[str, Any]]:
    """
    Generate all alpha candidates:
    1. Parameter mining variants
    2. Operator nesting variants (on best params)
    
    Returns full candidate list.
    """
    all_candidates = []
    
    print("=" * 80)
    print("  TOP 5 ALPHA EVOLUTION — CANDIDATE GENERATION")
    print("=" * 80)
    
    for template_key, template in TOP5_TEMPLATES.items():
        print(f"\n[{template_key}] {template['name']}")
        
        # Step 1: Parameter mining
        param_variants = generate_parameter_variants(template_key)
        print(f"  Step 1 (Parameter Mining): {len(param_variants)} variants")
        all_candidates.extend(param_variants)
        
        # Step 2: Operator nesting (on base expression only)
        if param_variants:
            base_candidate = param_variants[0]  # Use first (baseline or first param combo)
            base_expr = base_candidate["expression"]
            
            nested_variants = generate_nested_variants(base_expr, template_key, max_nesting=2)
            print(f"  Step 2 (Operator Nesting): {len(nested_variants)} variants")
            all_candidates.extend(nested_variants)
    
    print(f"\n{'=' * 80}")
    print(f"  Total Candidates Generated: {len(all_candidates)}")
    print(f"{'=' * 80}\n")
    
    return all_candidates


def export_to_template_file(candidates: List[Dict[str, Any]], output_file: str):
    """Export candidates to alpha template file."""
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# ============================================================================\n")
        f.write("# TOP 5 ALPHA EVOLUTION — Generated Candidates\n")
        f.write("# ============================================================================\n")
        f.write("#\n")
        f.write("# Step 1: Parameter Mining (window sizes, thresholds)\n")
        f.write("# Step 2: Operator Nesting (ts_rank, group_rank, decay, etc.)\n")
        f.write("#\n")
        f.write("# Settings (Fixed):\n")
        f.write("#   Region: GLB\n")
        f.write("#   Universe: TOPDIV3000\n")
        f.write("#   Delay: 1\n")
        f.write("#   Neutralization: SUBINDUSTRY\n")
        f.write("#   Truncation: 0.08\n")
        f.write("#   Decay: 10\n")
        f.write("#\n")
        f.write("# ============================================================================\n\n")
        
        # Group by template
        by_template = {}
        for cand in candidates:
            template_key = cand["id"].split("_")[0] + "_" + cand["id"].split("_")[1]
            if template_key not in by_template:
                by_template[template_key] = []
            by_template[template_key].append(cand)
        
        for template_key, cands in by_template.items():
            template = TOP5_TEMPLATES.get(template_key.replace("_", "_", 1))
            if template:
                f.write(f"# ==== {template['name'].upper()} ====\n")
                f.write(f"# Base: {template['description']}\n\n")
            
            for cand in cands:
                f.write(f"# {cand['id']} — {cand['description']}\n")
                f.write(f"{cand['expression']}\n\n")
    
    print(f"✓ Exported {len(candidates)} candidates to {output_file}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    # Generate all candidates
    candidates = generate_all_candidates()
    
    # Export to template file
    output_file = "top5_evolved_alphas.txt"
    export_to_template_file(candidates, output_file)
    
    # Summary
    print("\nCandidate Summary:")
    print(f"  Parameter Mining: {sum(1 for c in candidates if c['step'] == 'param_mining')}")
    print(f"  Baseline (no params): {sum(1 for c in candidates if c['step'] == 'baseline')}")
    print(f"  Operator Nesting L1: {sum(1 for c in candidates if c['step'] == 'operator_nesting_1')}")
    print(f"  Operator Nesting L2: {sum(1 for c in candidates if c['step'] == 'operator_nesting_2')}")
    print(f"\nTotal: {len(candidates)} alphas ready to simulate")
    print(f"\nNext step:")
    print(f"  python3 cmf_wyckoff_simulator.py --file {output_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
