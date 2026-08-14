# Phase 0: Simple Batch Simulation

## Overview

**Phase 0** is a lightweight, no-frills simulation workflow designed to quickly explore alpha signals extracted from research papers.

```
Paper Templates → Generate Candidates → Batch Simulate → Save Results
                                      (No submission, no quota waste)
```

### Key Features

✅ **Simple:** Only simulate, no complex filtering or submission  
✅ **Fast:** Batch process candidates in parallel  
✅ **Safe:** No quota waste (simulations are free exploratory)  
✅ **Transparent:** Save all results for analysis  
✅ **Modular:** Easy to integrate with other workflows  

---

## Quick Start

### 1. Prerequisites

Ensure you have:
- ✅ WorldQuant BRAIN credentials (`.env` with cookie or password)
- ✅ Paper templates in `templates/` directory
- ✅ Python environment activated

### 2. Run Phase 0

**Simulate all templates:**
```bash
cd /Volumes/SSD-WDBlue/tohuy/y3s2/wq-modified
python3 phase_0/phase_0_sim.py
```

**Simulate specific template:**
```bash
python3 phase_0/phase_0_sim.py --template analyst_estimate_trend
```

**Custom batch size:**
```bash
python3 phase_0/phase_0_sim.py --batch-size 20 --max-per-template 10
```

### 3. View Results

Results saved to `phase_0/output/`:

```
phase_0/output/
├── simulation_results.json      # Aggregated results
├── phase_0.log                  # Detailed logs
└── individual/                  # Individual alpha results
    ├── alpha_1Ypp13jm.json
    ├── alpha_omNNvOqE.json
    └── ...
```

---

## Configuration

Edit environment variables or use CLI flags:

### Environment Variables

```bash
# Batch size
export PHASE_0_BATCH_SIZE=10

# Max candidates per template
export PHASE_0_MAX_PER_TEMPLATE=8

# Max concurrent simulations
export PHASE_0_MAX_CONCURRENT=2

# Simulation timeout (seconds)
export PHASE_0_SIM_TIMEOUT=600

# Logging level
export PHASE_0_LOG_LEVEL=INFO

# Save individual results
export PHASE_0_SAVE_INDIVIDUAL=true

# Include/exclude templates
export PHASE_0_INCLUDED="alpha1,alpha2"
export PHASE_0_EXCLUDED="beta1,beta2"
```

### CLI Arguments

```bash
python3 phase_0/phase_0_sim.py --help

Options:
  --template TEMPLATE_ID           Specific template to simulate
  --batch-size N                   Candidates per batch (default: 10)
  --max-per-template N             Max candidates per template (default: 8)
  --max-concurrent N               Parallel simulations (default: 2)
  --output FILE                    Output JSON file path
```

---

## Output Format

### simulation_results.json

```json
{
  "timestamp": "2026-08-13T21:00:00+00:00",
  "total_simulated": 60,
  "passed": 45,
  "failed": 15,
  "results": [
    {
      "expression": "group_rank(ts_rank(earnings_yield_next_twelve_months, 252), subindustry)",
      "template_id": "analyst_estimate_trend",
      "status": "COMPLETE",
      "alpha_id": "1Ypp13jm",
      "sim_data": {
        "is": {
          "sharpe": 1.06,
          "fitness": 0.24,
          "turnover": 0.3522,
          ...
        }
      },
      "simulated_at": "2026-08-13T21:00:15+00:00"
    },
    ...
  ]
}
```

### Individual Result (alpha_XXX.json)

```json
{
  "expression": "...",
  "template_id": "analyst_estimate_trend",
  "status": "COMPLETE",
  "alpha_id": "1Ypp13jm",
  "sim_data": {...},
  "simulated_at": "2026-08-13T21:00:15+00:00"
}
```

---

## Workflow Example

### Step 1: Generate Templates from Paper

```bash
# Extract templates from paper (manual or automated)
python3 scripts/generate_extraction_prompt.py src_001
# → _extraction_prompt_src_001.md

# Run through LLM (ChatGPT/Claude)
# → extraction_src_001.json

# Ingest templates
python3 scripts/ingest_extracted_templates.py extraction_src_001.json --paper src_001
# → templates/alpha1_*.json
```

### Step 2: Simulate with Phase 0

```bash
python3 phase_0/phase_0_sim.py
# Generates candidates from all templates
# Simulates in batches
# Saves results
```

### Step 3: Analyze Results

```bash
# Check summary
cat phase_0/output/simulation_results.json | jq '.passed, .failed, .results | length'

# Find best alphas
cat phase_0/output/simulation_results.json | \
  jq '.results[] | select(.status=="COMPLETE") | {alpha_id, sharpe: .sim_data.is.sharpe, fitness: .sim_data.is.fitness}' | \
  sort by .sharpe | tail -10
```

---

## Architecture

### Files

```
phase_0/
├── __init__.py              # Package init
├── phase_0_config.py        # Configuration & paths
├── phase_0_utils.py         # Utility functions
├── phase_0_sim.py           # Main simulation script
├── README_PHASE_0.md        # This file
└── output/                  # Results directory
    ├── simulation_results.json
    ├── phase_0.log
    └── individual/
```

### Classes & Functions

**phase_0_config.py:**
- `TEMPLATES_DIR` - Path to templates
- `PHASE_0_OUTPUT_DIR` - Output directory
- Configuration constants (batch size, timeout, etc.)

**phase_0_utils.py:**
- `load_templates()` - Load all templates
- `load_template_by_id()` - Load specific template
- `generate_candidates_from_templates()` - Create candidates
- `save_simulation_results()` - Save aggregated results
- `save_individual_result()` - Save per-alpha result
- `get_summary_stats()` - Compute statistics
- `print_summary()` - Display summary

**phase_0_sim.py:**
- `main()` - Orchestrate simulation
- `batch_simulate()` - Stream simulate candidates

---

## Performance

### Expected Speed

```
Batch size: 10 candidates
Concurrency: 2
Simulation time: 30-60s per candidate

10 candidates / 2 concurrent = ~5 minutes per batch
60 candidates total = ~30 minutes
```

### Monitoring

Check progress via logs:

```bash
tail -f phase_0/output/phase_0.log

# Or check heartbeat
grep heartbeat phase_0/output/phase_0.log | tail -5
```

---

## Differences from mining_loop.py

| Feature | Phase 0 | mining_loop |
|---------|---------|-------------|
| Submission | ❌ No | ✅ Yes |
| Quota usage | ❌ None | ✅ High |
| Correlation check | ❌ No | ✅ Yes (expensive) |
| Complexity | ✅ Simple | ⚠️ Complex |
| Speed | ✅ Fast | ⚠️ Slow (due to checks) |
| Purpose | 🔬 Exploration | 🎯 Production |

---

## Troubleshooting

### No templates found

```
✗ No templates found
```

**Solution:**
1. Check `templates/` directory exists
2. Ensure template JSON files are present
3. Use `python3 scripts/ingest_extracted_templates.py` to ingest

### Connection failed

```
✗ Connection failed: Authentication failed
```

**Solution:**
1. Check `.env` has valid cookie or credentials
2. Verify cookie is not expired: `python3 scripts/check_quota.py`
3. Update cookie if needed (see BRAIN docs)

### Simulation timeout

```
Polling simulation timeout sim_id=... elapsed=600.2s
```

**Solution:**
1. Increase timeout: `export PHASE_0_SIM_TIMEOUT=900`
2. Reduce concurrency: `export PHASE_0_MAX_CONCURRENT=1`
3. Check BRAIN platform status

### Out of memory

```
MemoryError: Unable to allocate ... MiB
```

**Solution:**
1. Reduce batch size: `--batch-size 5`
2. Reduce concurrent: `--max-concurrent 1`
3. Run multiple times with `--template` flag

---

## Next Steps

After Phase 0:

1. **Analyze Results:** Use `analysis_script.py` to extract best alphas
2. **Phase 1:** Run correlation checks on top performers
3. **Phase 2:** Submit high-quality alphas to platform
4. **Integration:** Combine Phase 0 with `mining_loop.py` for full pipeline

---

## Advanced Usage

### Integrate with mining_loop.py

```python
# In mining_loop.py
from phase_0.phase_0_sim import batch_simulate

results = batch_simulate(candidates, batch_size=20)
```

### Custom candidate generation

```python
from phase_0.phase_0_utils import load_templates

templates = load_templates()
# Your custom filtering/generation logic
```

### Parse results programmatically

```python
import json

with open("phase_0/output/simulation_results.json") as f:
    data = json.load(f)
    
for result in data["results"]:
    if result["status"] == "COMPLETE":
        alpha_id = result["alpha_id"]
        sharpe = result["sim_data"]["is"]["sharpe"]
        print(f"{alpha_id}: Sharpe={sharpe}")
```

---

## Support

For issues or questions:
- Check logs: `phase_0/output/phase_0.log`
- Review config: `phase_0/phase_0_config.py`
- Compare with mining_loop: `scripts/mining_loop.py`
- BRAIN docs: https://docs.worldquantbrain.com/

---

**Created:** August 13, 2026  
**Version:** 0.1.0  
**Status:** Experimental
