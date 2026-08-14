# T-MAG v2.0 Data Discovery & Mutation Engine Guide

**Version**: 2.0  
**Date**: August 14, 2026  
**Status**: ✅ IMPLEMENTED

---

## Table of Contents

1. [Overview](#overview)
2. [The 70-20-10 Rule](#the-70-20-10-rule)
3. [Architecture](#architecture)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [Field Performance Tracking](#field-performance-tracking)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The **T-MAG v2.0 Data Discovery & Mutation Engine** transforms the alpha mining system from a "theory copy machine" into a "true Quant researcher" capable of discovering **Hidden Alphas** through intelligent field selection and controlled mutation.

### Key Innovation: The Exploration vs. Exploitation Balance

Instead of manually specifying `field_pairs` in templates, the system now **automatically discovers** diverse field combinations using three strategies:

- **Pool A (70%)**: Exploitation - High-relevance semantic matching
- **Pool B (20%)**: Cross-domain exploration - Logically related but different categories
- **Pool C (10%)**: Wildcard mutation - Type-safe random field selection

This approach enables discovery of:
- **Decorrelated alphas**: Low correlation with existing factors
- **Hidden relationships**: Market anomalies human intuition misses
- **Orthogonal strategies**: Fields from unexpected categories that work

---

## The 70-20-10 Rule

### Pool A: Exploitation (70%)

**Purpose**: Find fields with highest semantic relevance to the placeholder

**Method**: Hybrid keyword matching + coverage/usage scoring

**Scoring Formula**:
```
score = 0.5 × keyword_match + 0.3 × coverage + 0.2 × usage
```

**Example**: For `{profitability}`:
- `operating_income` (exact match in field ID)
- `net_income_annual` (substring match in description)
- `earnings_yield_next_twelve_months` (keyword "earnings" match)

### Pool B: Cross-Domain Exploration (20%)

**Purpose**: Find logically related fields from **different** data categories

**Method**: Category mapping rules + weighted sampling

**Category Rules**:
```python
{
    "fundamental": ["analyst", "model"],      # Profits → Estimates
    "analyst": ["fundamental", "model"],      # Estimates → Actuals
    "technical": ["fundamental", "sentiment"], # Price → Value/Mood
    "volume": ["sentiment", "options"],       # Trading → Interest
}
```

**Example**: For `{profitability}` (fundamental):
- From analyst: `est_eps`, `earnings_revisions`
- From model: `quality_score`, `valuation_score`

### Pool C: Wildcard Mutation (10%)

**Purpose**: Discover unexpected relationships through type-safe random selection

**Method**: Random sampling with data type constraints

**Type Safety**:
- Operators like `ts_rank()` → only numerical fields (MATRIX type)
- Denominators in divisions → only numerical fields
- Boolean expressions → categorical OK

**Example**: For `{profitability}` / `{scale}`:
- Wildcard for numerator: `insider_buying_ratio` (completely random!)
- Wildcard for denominator: `options_implied_volatility` (random but numerical)

**Success Story**: When a wildcard field produces `sharpe > 1.2`, it's promoted to "prefer" status and becomes part of Pool A in future discoveries!

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Template Skeleton (from LLM or Manual)                   │
│    "group_rank(ts_rank({profitability} / {scale}, ...)"     │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Data Discovery Engine                                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Placeholder Analyzer                                  │  │
│  │  • Extract: {profitability}, {scale}                 │  │
│  │  • Infer keywords: ["profit", "income", "earnings"]  │  │
│  │  • Detect type: numerical (in denominator)           │  │
│  └──────────────────────────────────────────────────────┘  │
│             │                                                │
│             ▼                                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Field Discovery (70-20-10)                           │  │
│  │                                                        │  │
│  │  Pool A (70%): Semantic Match                         │  │
│  │   operating_income, net_income, ebitda...             │  │
│  │                                                        │  │
│  │  Pool B (20%): Cross-Domain                           │  │
│  │   est_eps, quality_score...                           │  │
│  │                                                        │  │
│  │  Pool C (10%): Wildcard                               │  │
│  │   insider_buying_ratio (random!)                      │  │
│  └──────────────────────────────────────────────────────┘  │
│             │                                                │
│             ▼                                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Lessons-Driven Adjustment                             │  │
│  │  • Boost "prefer" fields (+20%)                       │  │
│  │  • Skip "avoid" fields                                │  │
│  │  • Adjust by avg_sharpe history                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Output: field_pairs with diversity metadata                │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Candidate Generation (existing system)                   │
│    expand_template() → 100+ candidates → Simulation         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Performance Tracking (NEW)                                │
│    Successful wildcards → "prefer"                          │
│    Failed fields → "avoid"                                   │
│    Update lessons.json field_performance                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Usage

### Basic Usage: Auto-Discovery During Template Ingestion

```bash
# Traditional mode (manual field_pairs required)
python3 scripts/ingest_extracted_templates.py extraction.json --paper src_001

# T-MAG v2.0 mode (auto-discover field_pairs if missing)
python3 scripts/ingest_extracted_templates.py extraction.json \
    --paper src_002 \
    --enable-discovery \
    --max-discovered-fields 12
```

### Programmatic Usage

```python
from data_discovery import DataDiscoveryEngine, FieldCatalog

# Load catalog
catalog = FieldCatalog.load()

# Initialize engine
engine = DataDiscoveryEngine(
    catalog=catalog,
    lessons_path="lessons.json",  # Optional: use historical performance
    config_path="config/discovery_config.json"  # Optional: custom config
)

# Discover fields for a skeleton
field_pairs = engine.discover_fields(
    skeleton="group_rank(ts_rank({profitability} / {scale}, {window}), {group})",
    max_fields=12  # Total fields across all placeholders
)

# Result: 12 field_pairs with ~70% Pool A, ~20% Pool B, ~10% Pool C
# Example output:
# [
#   {"profitability": "operating_income", "_metadata": {"source_pool": "A"}},
#   {"profitability": "net_income_annual", "_metadata": {"source_pool": "A"}},
#   {"profitability": "est_eps", "_metadata": {"source_pool": "B"}},
#   {"profitability": "insider_buying_ratio", "_metadata": {"source_pool": "C"}},
#   ...
# ]
```

### Advanced: Per-Placeholder Discovery

```python
# Discover 12 fields PER placeholder (total: 24 field_pairs)
field_pairs = engine.discover_fields(
    skeleton="group_rank({signal1} + {signal2}, {group})",
    max_fields=12,
    per_placeholder=True  # 12 for signal1, 12 for signal2
)
```

---

## Configuration

### config/discovery_config.json

```json
{
  "pool_ratios": {
    "exploitation": 0.7,
    "cross_domain": 0.2,
    "wildcard": 0.1
  },
  "coverage_thresholds": {
    "pool_a": 0.8,  
    "pool_b": 0.7,  
    "pool_c": 0.5   
  },
  "scoring_weights": {
    "keyword_match": 0.5,
    "coverage": 0.3,
    "usage": 0.2
  },
  "cross_category_rules": {
    "fundamental": ["analyst", "model"],
    "technical": ["fundamental", "sentiment"]
  }
}
```

### Environment Variable Overrides

```bash
# Adjust pool ratios
export WQ_DISCOVERY_POOL_A_RATIO=0.8  # More exploitation
export WQ_DISCOVERY_POOL_C_RATIO=0.05 # Less randomness

# Adjust coverage thresholds
export WQ_DISCOVERY_POOL_A_COVERAGE=0.9  # Stricter coverage for Pool A

python3 scripts/ingest_extracted_templates.py ... --enable-discovery
```

### Tuning Guidelines

**More Exploitation (safer)**:
```json
{
  "pool_ratios": {
    "exploitation": 0.8,
    "cross_domain": 0.15,
    "wildcard": 0.05
  }
}
```
- Use when: Starting with new paper, conservative approach
- Result: More predictable alphas, less discovery

**More Exploration (riskier)**:
```json
{
  "pool_ratios": {
    "exploitation": 0.6,
    "cross_domain": 0.25,
    "wildcard": 0.15
  }
}
```
- Use when: Seeking decorrelated alphas, aggressive research
- Result: More Hidden Alphas, higher variance

---

## Field Performance Tracking

### lessons.json Structure

After mining with discovered fields, `lessons.json` contains:

```json
{
  "field_performance": {
    "operating_income": {
      "tested": 45,
      "submit_count": 12,
      "observe_count": 8,
      "discard_count": 25,
      "avg_sharpe": 1.15,
      "avg_fitness": 0.82,
      "source_pool": "A",
      "discovery_count": 5,
      "status": "prefer"
    },
    "insider_buying_ratio": {
      "tested": 8,
      "submit_count": 3,
      "discard_count": 5,
      "avg_sharpe": 1.42,
      "source_pool": "C",
      "discovery_count": 2,
      "status": "prefer"  // ← Promoted from wildcard!
    },
    "some_failed_field": {
      "tested": 15,
      "submit_count": 0,
      "avg_sharpe": 0.25,
      "status": "avoid"
    }
  }
}
```

### Status Meanings

| Status | Criteria | Effect |
|--------|----------|--------|
| **prefer** | success_rate ≥ 30% AND avg_sharpe ≥ 1.2 | +20% boost in Pool A scoring |
| **neutral** | Default status | No adjustment |
| **avoid** | 0% success after 10+ tests | Excluded from future discovery |

### Wildcard Promotion Logic

```python
if field["tested"] >= 5:
    success_rate = field["submit_count"] / field["tested"]
    
    if success_rate >= 0.3 and field["avg_sharpe"] >= 1.2:
        field["status"] = "prefer"
        # This wildcard field is now prioritized in Pool A!
```

**Example Success Story**:
1. Paper 1: `insider_buying_ratio` discovered as Pool C wildcard (10% chance)
2. Simulation: 3 SUBMIT out of 8 tests, avg_sharpe=1.42
3. Promotion: Status → "prefer"
4. Paper 2: `insider_buying_ratio` now appears in Pool A (70% chance) for similar placeholders!

---

## Examples

### Example 1: Template Without field_pairs

**Input** (`extraction_src_003.json`):
```json
[
  {
    "template_id": "quality_value_combo",
    "description": "Kết hợp chất lượng cơ bản và định giá",
    "skeleton": "group_rank({quality_metric} / {valuation}, {group})",
    "field_pairs": [],  // Empty - let discovery engine fill this
    "param_ranges": {
      "group": ["industry", "subindustry"]
    }
  }
]
```

**Command**:
```bash
python3 scripts/ingest_extracted_templates.py extraction_src_003.json \
    --paper src_003 \
    --enable-discovery \
    --max-discovered-fields 10
```

**Output** (logs):
```
[INFO] Auto-discovering field_pairs for template_id=quality_value_combo (T-MAG v2.0)
[INFO] Discovering fields for placeholder=quality_metric keywords=['quality', 'metric'] numerical=True
[INFO] Matched 7 fields for keywords=['quality', 'metric'] (Pool A)
[INFO] Explored 2 cross-domain fields from categories=['analyst', 'model'] (Pool B)
[INFO] Sampled 1 wildcard fields (Pool C)
[INFO] Discovered 10 field_pairs: Pool A=7, B=2, C=1
```

**Generated template/quality_value_combo.json**:
```json
{
  "template_id": "quality_value_combo",
  "skeleton": "group_rank({quality_metric} / {valuation}, {group})",
  "field_pairs": [
    {"quality_metric": "return_on_equity_ttm"},
    {"quality_metric": "operating_margin_ttm"},
    {"quality_metric": "asset_turnover_ttm"},
    {"quality_metric": "free_cash_flow_margin"},
    {"quality_metric": "earnings_quality_score"},
    {"quality_metric": "est_roe_next_year"},
    {"quality_metric": "analyst_accuracy_score"},
    {"quality_metric": "quality_score"},
    {"quality_metric": "revenue_per_employee"},
    {"quality_metric": "insider_buying_ratio"}
  ],
  "_discovery_enabled": true
}
```

### Example 2: Check Pool Distribution

```python
from data_discovery import DataDiscoveryEngine, FieldCatalog

catalog = FieldCatalog.load()
engine = DataDiscoveryEngine(catalog)

field_pairs = engine.discover_fields(
    skeleton="rank({momentum})",
    max_fields=10
)

# Check distribution
distribution = engine.get_pool_distribution(field_pairs)
print(distribution)
# Output: {'A': 7, 'B': 2, 'C': 1}
```

### Example 3: Validate Discovered Fields

```python
field_pairs = engine.discover_fields(...)

is_valid, errors = engine.validate_field_pairs(field_pairs)

if not is_valid:
    for error in errors:
        print(f"Validation error: {error}")
else:
    print("✓ All discovered fields are valid!")
```

---

## Troubleshooting

### Issue: "No fields found matching keywords"

**Cause**: Keywords from placeholder too specific or misspelled

**Solution**: Check placeholder naming
```python
# Bad: {very_specific_uncommon_metric}
# Good: {profitability}, {momentum}, {quality}
```

### Issue: Discovery produces too few fields

**Cause**: Coverage thresholds too strict

**Solution**: Lower coverage threshold in config
```json
{
  "coverage_thresholds": {
    "pool_a": 0.7,  // Lower from 0.8
    "pool_b": 0.6,
    "pool_c": 0.4
  }
}
```

### Issue: Wildcard fields causing simulation errors

**Cause**: Type safety failure (non-numerical in math operation)

**Solution**: This should not happen! File bug report with:
```bash
# Check logs for type inference
grep "requires_numerical" logs/*.log
```

### Issue: Field performance not updating

**Cause**: Metadata missing from field_pairs

**Solution**: Ensure discovery engine is used during ingestion:
```bash
# Wrong: Manual field_pairs without metadata
python3 scripts/ingest_extracted_templates.py extraction.json

# Correct: Discovery adds metadata
python3 scripts/ingest_extracted_templates.py extraction.json --enable-discovery
```

### Issue: Too many wildcards, not enough semantic matches

**Cause**: Pool ratios misconfigured

**Solution**:
```bash
# Check current config
cat config/discovery_config.json

# Adjust ratios
export WQ_DISCOVERY_POOL_A_RATIO=0.8
export WQ_DISCOVERY_POOL_C_RATIO=0.05
```

---

## Performance Metrics

### Expected Results (after 3-5 papers with discovery enabled)

| Metric | Expected Range |
|--------|----------------|
| **Wildcard promotion rate** | 5-15% of Pool C fields → "prefer" |
| **Hidden Alpha discovery** | 1-3 new successful fields per paper |
| **Decorrelation improvement** | 10-20% lower avg correlation |
| **Coverage** | Pool A: 95%+, Pool B: 85%+, Pool C: 70%+ |

### Monitoring Commands

```bash
# Check field performance summary
python3 -c "
import json
from pathlib import Path

lessons = json.loads(Path('lessons.json').read_text())
field_perf = lessons.get('field_performance', {})

preferred = [f for f, d in field_perf.items() if d.get('status') == 'prefer']
avoided = [f for f, d in field_perf.items() if d.get('status') == 'avoid']

print(f'Preferred fields: {len(preferred)}')
print(f'Avoided fields: {len(avoided)}')
print(f'Total tracked: {len(field_perf)}')

# Show top performers
top = sorted(field_perf.items(), key=lambda x: x[1].get('avg_sharpe', 0), reverse=True)[:5]
print('\nTop 5 fields by sharpe:')
for field, data in top:
    print(f'  {field}: {data.get(\"avg_sharpe\", 0):.2f} (pool={data.get(\"source_pool\", \"?\")}, tested={data.get(\"tested\", 0)})')
"
```

---

## Next Steps

1. **Run first discovery-enabled ingestion**:
   ```bash
   python3 scripts/ingest_extracted_templates.py extraction_src_001.json --enable-discovery
   ```

2. **Mine the templates**:
   ```bash
   python3 scripts/mining_loop.py --max-rounds 5
   ```

3. **Check field performance**:
   ```bash
   cat lessons.json | jq '.field_performance'
   ```

4. **Iterate with next paper** - discovery engine now uses lessons from paper 1!

5. **Monitor wildcard promotions** - watch for Pool C → "prefer" transitions

---

**Status**: ✅ T-MAG v2.0 fully implemented and ready for production use

**Support**: Check logs in `*.log` files for detailed discovery engine operation

**Version History**:
- v2.0 (2026-08-14): Initial T-MAG Data Discovery Engine
- v1.0: Original template-based system with manual field_pairs
