# Phase 0 Quick Start

## What is Phase 0?

A **simple batch simulation** workflow for paper-extracted templates:

```
Templates → Generate Candidates → Batch Simulate → Save Results
```

**No submission, no quota waste, just raw exploration.**

---

## Files

```
phase_0/
├── __init__.py              # Package marker
├── phase_0_config.py        # Configuration (paths, batch size, timeouts)
├── phase_0_utils.py         # Utilities (load templates, save results)
├── phase_0_sim.py           # Main script - RUN THIS
├── README_PHASE_0.md        # Full documentation
├── QUICK_START.md           # This file
└── output/                  # Results directory (auto-created)
    ├── simulation_results.json    # Summary
    ├── phase_0.log               # Logs
    └── individual/               # Individual alpha results
```

---

## Run Phase 0

### Setup (one-time)

```bash
cd /Volumes/SSD-WDBlue/tohuy/y3s2/wq-modified
source venv/bin/activate
```

### Run all templates

```bash
python3 phase_0/phase_0_sim.py
```

### Run specific template

```bash
python3 phase_0/phase_0_sim.py --template analyst_estimate_trend
```

### Custom parameters

```bash
python3 phase_0/phase_0_sim.py \
  --template analyst_estimate_trend \
  --batch-size 5 \
  --max-per-template 3 \
  --max-concurrent 2
```

---

## Monitor Progress

```bash
# Watch logs
tail -f phase_0/output/phase_0.log

# Check individual results as they appear
ls -ltr phase_0/output/individual/ | tail -5

# Once done, view summary
cat phase_0/output/simulation_results.json | jq '.passed, .failed'
```

---

## View Results

### Summary statistics

```bash
cat phase_0/output/simulation_results.json | jq '
  {
    total: .total_simulated,
    passed: .passed,
    failed: .failed,
    success_rate: (.passed / .total_simulated * 100 | round)
  }
'
```

### Best alphas (by Sharpe)

```bash
cat phase_0/output/simulation_results.json | jq '
  .results[]
  | select(.status == "COMPLETE")
  | {
      alpha_id,
      sharpe: .sim_data.is.sharpe,
      fitness: .sim_data.is.fitness,
      turnover: .sim_data.is.turnover,
      template: .template_id
    }
  | sort_by(.sharpe)
  | reverse
  | .[0:10]
'
```

### Export to CSV (for analysis)

```bash
cat phase_0/output/simulation_results.json | jq -r '
  .results[]
  | select(.status == "COMPLETE")
  | [.alpha_id, .sim_data.is.sharpe, .sim_data.is.fitness, .sim_data.is.turnover, .template_id]
  | @csv
' > phase_0/output/results.csv
```

---

## Configuration

### Environment Variables

```bash
# Batch processing
export PHASE_0_BATCH_SIZE=10
export PHASE_0_MAX_PER_TEMPLATE=8
export PHASE_0_MAX_CONCURRENT=2

# Timeouts
export PHASE_0_SIM_TIMEOUT=600

# Logging
export PHASE_0_LOG_LEVEL=INFO

# Output
export PHASE_0_SAVE_INDIVIDUAL=true
```

### CLI Arguments

```
--template TEMPLATE_ID           # Specific template (default: all)
--batch-size N                   # Candidates per batch (default: 10)
--max-per-template N             # Max per template (default: 8)
--max-concurrent N               # Parallel simulations (default: 2)
--output FILE                    # Output JSON path
```

---

## Example: Full Workflow

```bash
# 1. Extract templates from paper (if not done)
python3 scripts/ingest_extracted_templates.py extraction_src_001.json --paper src_001

# 2. Run Phase 0
python3 phase_0/phase_0_sim.py --batch-size 10 --max-per-template 5

# 3. View results
cat phase_0/output/simulation_results.json | jq '.passed, .failed'

# 4. Export top alphas
cat phase_0/output/simulation_results.json | jq '
  .results[]
  | select(.status == "COMPLETE")
  | select(.sim_data.is.sharpe > 1.0)
  | {alpha_id, sharpe: .sim_data.is.sharpe}
' > phase_0/output/top_alphas.json

# 5. Next step: correlate or submit these in Phase 1
```

---

## Expected Performance

| Metric | Value |
|--------|-------|
| Candidates per template | 8 |
| Batch size | 10 |
| Simulation time per alpha | 30-60s |
| Total time (60 alphas) | ~30 min |
| Quota used | 0 (exploratory) |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No templates | Ingest templates first: `python3 scripts/ingest_extracted_templates.py ...` |
| Auth error | Update cookie: `export WQ_BRAIN_COOKIE="..."` |
| Timeout | Increase: `export PHASE_0_SIM_TIMEOUT=900` |
| Memory error | Reduce: `--batch-size 5 --max-concurrent 1` |
| Slow | Increase: `--max-concurrent 4` |

---

## Next Steps

After Phase 0:

1. **Analyze:** Find top alphas by Sharpe/Fitness
2. **Phase 1:** Check correlation with existing alphas
3. **Phase 2:** Submit best alphas to platform
4. **Integrate:** Combine with `mining_loop.py` for production

---

## Help

```bash
python3 phase_0/phase_0_sim.py --help
```

More details: See `README_PHASE_0.md`

---

**Quick Links:**
- Config: `phase_0/phase_0_config.py`
- Utils: `phase_0/phase_0_utils.py`
- Main: `phase_0/phase_0_sim.py`
- Docs: `phase_0/README_PHASE_0.md`
