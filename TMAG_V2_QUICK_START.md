# T-MAG v2.0 Quick Start Guide

**5-Minute Guide to Data Discovery & Mutation Engine**

---

## What is T-MAG v2.0?

Auto-discovery of diverse data fields using the **70-20-10 rule**:
- **70%**: High-relevance semantic matching (safe)
- **20%**: Cross-category exploration (decorrelated)
- **10%**: Random wildcards (Hidden Alphas)

---

## Quick Commands

### 1. Test the System

```bash
# Run all tests (~30 seconds)
python3 scripts/test_discovery_workflow.py

# Expected output: "✓ ALL TESTS PASSED"
```

### 2. Enable Discovery for Templates

```bash
# Traditional mode (manual field_pairs)
python3 scripts/ingest_extracted_templates.py extraction.json --paper src_001

# T-MAG v2.0 mode (auto-discover)
python3 scripts/ingest_extracted_templates.py extraction.json \
    --paper src_001 \
    --enable-discovery \
    --max-discovered-fields 12
```

### 3. Mine & Track Performance

```bash
# Run mining
python3 scripts/mining_loop.py --max-rounds 5

# Check field performance
python3 -c "
import json
fp = json.load(open('lessons.json')).get('field_performance', {})
print(f'Fields tracked: {len(fp)}')
print(f'Preferred: {sum(1 for d in fp.values() if d.get(\"status\") == \"prefer\")}')
"
```

---

## Configuration

### Adjust Pool Ratios

**Via Environment Variables**:
```bash
export WQ_DISCOVERY_POOL_A_RATIO=0.8  # More exploitation (safer)
export WQ_DISCOVERY_POOL_C_RATIO=0.05 # Less randomness
```

**Via Config File** (`config/discovery_config.json`):
```json
{
  "pool_ratios": {
    "exploitation": 0.7,
    "cross_domain": 0.2,
    "wildcard": 0.1
  }
}
```

---

## Usage Patterns

### Pattern 1: Template Without field_pairs

**Input** (`extraction.json`):
```json
[
  {
    "template_id": "momentum_strategy",
    "skeleton": "rank({momentum})",
    "field_pairs": [],  // Empty - let discovery fill this
    "param_ranges": {}
  }
]
```

**Command**:
```bash
python3 scripts/ingest_extracted_templates.py extraction.json --enable-discovery
```

**Result**: 12 field_pairs auto-discovered (7 Pool A, 2 Pool B, 1 Pool C)

### Pattern 2: Programmatic Discovery

```python
from data_discovery import DataDiscoveryEngine, FieldCatalog

catalog = FieldCatalog.load()
engine = DataDiscoveryEngine(catalog, lessons_path="lessons.json")

field_pairs = engine.discover_fields(
    skeleton="group_rank(ts_rank({profitability} / {scale}, {window}), {group})",
    max_fields=12
)

# Check pool distribution
dist = engine.get_pool_distribution(field_pairs)
print(f"Pool A: {dist.get('A', 0)}, B: {dist.get('B', 0)}, C: {dist.get('C', 0)}")
```

---

## Monitoring

### Check Wildcard Promotions

```bash
python3 -c "
import json
fp = json.load(open('lessons.json')).get('field_performance', {})
promoted = [(f, d) for f, d in fp.items() 
            if d.get('source_pool') == 'C' and d.get('status') == 'prefer']
print(f'Wildcards promoted to prefer: {len(promoted)}')
for field, data in promoted[:5]:
    print(f'  • {field}: sharpe={data.get(\"avg_sharpe\", 0):.2f}')
"
```

### View Top Performing Fields

```bash
python3 -c "
import json
fp = json.load(open('lessons.json')).get('field_performance', {})
top = sorted(fp.items(), key=lambda x: x[1].get('avg_sharpe', 0), reverse=True)[:10]
print('Top 10 fields by sharpe:')
for field, data in top:
    print(f'  {field:40} {data.get(\"avg_sharpe\", 0):6.2f} (pool={data.get(\"source_pool\", \"?\")}, n={data.get(\"tested\", 0)})')
"
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No fields found" | Lower coverage threshold in config |
| Too few Pool C fields | Increase `pool_ratios.wildcard` to 0.15 |
| Type safety errors | File bug - should not happen |
| Discovery disabled | Add `--enable-discovery` flag |

---

## Key Files

| File | Purpose |
|------|---------|
| `scripts/data_discovery.py` | Core engine (850 lines) |
| `config/discovery_config.json` | Configuration |
| `docs/DATA_DISCOVERY_GUIDE.md` | Full documentation |
| `scripts/test_discovery_workflow.py` | Test suite |
| `lessons.json` → `field_performance` | Performance tracking |

---

## Next Steps

1. **Test**: `python3 scripts/test_discovery_workflow.py`
2. **Enable**: Add `--enable-discovery` to ingestion
3. **Mine**: Run `mining_loop.py` and observe
4. **Monitor**: Check `lessons.json` for field promotions
5. **Iterate**: Process more papers, system learns!

---

## Success Indicators

- ✓ Tests pass
- ✓ Field_pairs auto-generated
- ✓ 70-20-10 distribution maintained
- ✓ Wildcards promoted to "prefer" (after 3-5 papers)
- ✓ New successful fields discovered

---

**Ready to discover Hidden Alphas!** 🚀

For detailed documentation, see: `docs/DATA_DISCOVERY_GUIDE.md`
