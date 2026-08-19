# CMF Wyckoff Alpha Testing Framework

## Overview

Framework hoàn chỉnh để test **53 alpha expressions** dựa trên Chaikin Money Flow (CMF) sử dụng field `short_term_price_change_2`, theo triết lý Wyckoff với settings cố định trên GLB/TOPDIV3000.

**Fixed Settings:**
- Region: GLB
- Universe: TOPDIV3000
- Delay: 1
- Neutralization: SUBINDUSTRY (proxy for market-level; MARKET not available in GLB/TOPDIV3000)
- Truncation: 0.08
- Decay: 10
- Pasteurization: ON

## File Structure

```
phase_1_plus/
├── alphas_cmf_wyckoff_template.txt        # 53 alpha expressions (20 levels)
├── cmf_wyckoff_simulator.py               # Main simulation script
├── cmf_wyckoff_analyzer.py                # Analysis & reporting
├── run_cmf_wyckoff_full.sh               # End-to-end runner
├── CMF_WYCKOFF_SETUP.md                  # This file
└── output/cmf_wyckoff/
    ├── results.json                       # All results (JSON)
    ├── results.csv                        # All results (CSV) ← USE THIS FOR TRACKING
    ├── CMF_WYCKOFF_REPORT.md             # Comprehensive markdown report
    └── individual/                        # Individual alpha results (JSON)
        ├── L1.01.json
        ├── L1.02.json
        └── ...
```

## Alpha Levels

| Level | Category | Count | Focus |
|-------|----------|-------|-------|
| L1 | Baseline CMF Levels | 3 | Raw CMF, 20d MA, 40d MA |
| L2 | CMF Trends/Momentum | 3 | Delta 20, Delta 10, Acceleration |
| L3 | CMF Persistence | 2 | Sustained flow, mean reversion |
| L4 | CMF vs Price Divergence | 3 | Core Wyckoff — CMF leading |
| L5 | Accumulation Signals | 3 | CMF in, price out (weak) |
| L6 | Breakout Confirmation | 3 | CMF level + price action |
| L7 | Country-Relative CMF | 3 | GLB-specific: country grouping |
| L8 | Region-Relative CMF | 2 | GLB-specific: region grouping |
| L9 | Layered Neutralization | 2 | Country → Region double layer |
| L10 | Enhanced Momentum | 2 | Multi-timeframe momentum |
| L11 | Level + Momentum | 3 | Combo strategies |
| L12 | Cumulative Strength | 2 | 60-day aggregation |
| L13 | Regime Filters | 2 | Price action filters |
| L14 | Multi-Timeframe | 2 | 5/30 lead/lag |
| L15 | Wyckoff Spring/Shakeout | 2 | Specific Wyckoff setups |
| L16 | High-Pass Filters | 2 | Threshold-based |
| L17 | Normalized Variants | 2 | Volatility-adjusted |
| L18 | Interaction Terms | 2 | Combined signals |
| L19 | Robust Cores | 3 | Simple baselines for validation |
| L20 | Experimental | 2 | Novel approaches |

**Total: 53 alphas**

## Quick Start

### 1. Run All Alphas (Full Test)

```bash
cd phase_1_plus/
python3 cmf_wyckoff_simulator.py
```

This will:
- Load all 53 expressions from template
- Simulate each via BRAIN API
- Save JSON results to `output/cmf_wyckoff/results.json`
- Export CSV to `output/cmf_wyckoff/results.csv`
- Show summary stats and top 10 performers

**Time estimate:** ~30-60 minutes (depends on API queue)

### 2. Run Specific Level (e.g., Level 4 — Divergence)

```bash
python3 cmf_wyckoff_simulator.py --level 4
```

Will run only the 3 alphas in L4 (CMF vs Price divergence).

### 3. Preview Mode (Dry Run)

```bash
python3 cmf_wyckoff_simulator.py --dry-run
```

Shows what would be run without calling BRAIN API. Useful for debugging.

### 4. Adjust Batch Settings

```bash
python3 cmf_wyckoff_simulator.py --batch-size 15 --max-concurrent 4
```

- Larger batch size → more alphas per batch
- Higher concurrency → faster but more API load

### 5. Generate Report

After simulation completes:

```bash
python3 cmf_wyckoff_analyzer.py
```

Generates:
- `CMF_WYCKOFF_REPORT.md` — comprehensive markdown report with:
  - Executive summary
  - Performance by level
  - Top 10 by fitness
  - Top 10 by Sharpe
  - Metric correlations
  - Key findings & recommendations
- Updates `results.csv` with sorted results by fitness

### 6. One-Command Full Test (End-to-End)

```bash
bash run_cmf_wyckoff_full.sh
```

Runs simulator + analyzer in sequence.

**With level filter:**

```bash
bash run_cmf_wyckoff_full.sh --level 7 --batch-size 20
```

## Results Analysis

### CSV Format

The `results.csv` file contains:

| Column | Meaning |
|--------|---------|
| alpha_id | L#.## format (e.g., L4.01) |
| level | Numeric level (1-20) |
| description | Brief description |
| expression | BRAIN expression string |
| status | COMPLETE or ERROR |
| sharpe | Sharpe ratio |
| fitness | Fitness metric (compound) |
| turnover | Turnover (lower is better) |
| returns | Annualized returns (%) |
| simulated_at | Timestamp |

**Sort by fitness (descending)** to find best performers.

### Key Metrics

1. **Sharpe Ratio**
   - Measures risk-adjusted returns
   - Target for GLB: > 1.0
   - Our mean should indicate breadth

2. **Fitness**
   - Compound metric (Sharpe × returns × stability)
   - Primary ranking metric
   - Higher is better

3. **Turnover**
   - Portfolio turnover rate
   - Lower = lower transaction costs
   - Typical good: < 0.01

4. **Returns**
   - Annualized return %
   - Should be positive
   - Check correlation with Sharpe (ideal: high Sharpe + solid returns)

### Interpretation

**Healthy profile:**
- Sharpe: 0.8 - 1.5
- Fitness: 0.5 - 2.0
- Turnover: < 0.005
- Returns: 5% - 20%

**Strong profile:**
- Sharpe: 1.5+
- Fitness: 2.0+
- Turnover: < 0.003
- Returns: 15%+

## Understanding Alpha Levels

### Levels 1-3: Baseline CMF Analysis

These answer: **"Does CMF itself have alpha?"**

- L1: Raw CMF level
- L2: CMF momentum (change over time)
- L3: CMF persistence (sustained vs spike)

*Expected:* Sharpe 0.3-0.8 (directional signal but noisy)

### Levels 4-5: Wyckoff Core

These are the **most important** — they test the thesis: **"Does CMF lead price?"**

- L4: CMF momentum - Price momentum (divergence)
- L5: CMF up + Price down (accumulation)

*Expected:* Sharpe 0.5-1.2 (cleaner signal than raw CMF)

**Key Alpha:** L4.01 and L5.01 should be tested first.

### Levels 6-9: Context & Regionalization

Add context (price level, region) to CMF.

- L6: CMF + breakout pressure
- L7-9: Country/region variants

*Expected:* Sharpe 0.6-1.3 (depends on region efficiency)

### Levels 10-18: Advanced Combinations

Multi-timeframe, normalized, interaction terms.

*Expected:* Sharpe 0.4-1.0 (hit-or-miss, but some may excel)

### Levels 19-20: Validation

Simple baselines + experimental.

*Expected:* Sharpe 0.2-0.8 (confirmatory)

## Regional Analysis (GLB Specific)

After running simulator, check regional breakdown:

```bash
# Extract by country (from results.csv or JSON)
cat output/cmf_wyckoff/results.json | jq '.results[] | select(.sim_data.is) | .sim_data.is' | grep -i region
```

**Healthy GLB alpha:**
- Positive Sharpe in 60%+ of countries
- No single-country dependence
- Stable across US, Europe, Asia, EM

**Red flag:**
- High Sharpe only in US or China
- Negative in multiple regions
- Suggests **geographic bias**, not true GLB signal

## Next Steps After Testing

### If 1 alpha clearly wins (Fitness > 2.0, Sharpe > 1.2):

1. **Deep dive:** Check regional breakdown, country correlation
2. **Robustness test:** Run with different decay (5, 15, 20) to ensure stability
3. **Turnover optimization:** If turnover > 0.01, try decay 10 → 15
4. **Deploy:** Consider adding to production pool

### If several alphas perform well (multiple Sharpe > 0.8):

1. **Correlation analysis:** Check which are uncorrelated
2. **Pool creation:** Combine 3-5 uncorrelated alphas
3. **Ensemble:** Weight by Sharpe (higher weight = higher Sharpe)
4. **Deploy:** As an alpha pool

### If overall performance is weak (mean Sharpe < 0.5):

1. **Investigate:** Check which levels underperform
2. **Adjust field:** Maybe use `close` or `volume` instead of CMF proxy
3. **Experiment:** Try different decay/truncation settings
4. **Pivot:** Consider different alpha family (momentum, mean reversion, etc.)

## Troubleshooting

### Simulator hangs or times out

**Cause:** BRAIN API queue or network issue

**Solution:**
1. Reduce `--max-concurrent` (e.g., 2 instead of 3)
2. Reduce `--batch-size` (e.g., 5 instead of 10)
3. Check BRAIN API status

### All alphas get "ERROR" status

**Cause:** Expression syntax error or field name mismatch

**Solution:**
1. Verify `short_term_price_change_2` is available in your data
2. Check BRAIN documentation for supported functions
3. Test one expression manually first

### Results show all zero Sharpe/Fitness

**Cause:** Settings mismatch or data issue

**Solution:**
1. Verify settings in `FIXED_SETTINGS` dict match your requirements
2. Check that region/universe exist
3. Verify pasteurization/NaN handling settings

## Code Reference

### cmf_wyckoff_simulator.py

**Main function:** `batch_simulate(candidates, batch_size, max_concurrent)`

- Loads alphas from template
- Calls BRAIN API via BrainClient
- Saves individual + aggregated results
- Supports filtering by level or index range

**Key parameters:**
- `--level` — Filter by level
- `--batch-size` — Alphas per batch
- `--max-concurrent` — Concurrent API calls
- `--dry-run` — Preview without API

### cmf_wyckoff_analyzer.py

**Main functions:**
- `load_results()` — Read results JSON
- `analyze_by_level()` — Group by level and compute stats
- `generate_markdown_report()` — Create comprehensive report

**Output:**
- Markdown report with tables, rankings, correlations
- CSV with sorted results

## File Locations

```
Results (read-only after simulation):
  output/cmf_wyckoff/results.json          # Full results
  output/cmf_wyckoff/results.csv           # ← USE THIS FOR ANALYSIS
  output/cmf_wyckoff/CMF_WYCKOFF_REPORT.md # Human-readable report

Individual result files:
  output/cmf_wyckoff/individual/L1.01.json
  output/cmf_wyckoff/individual/L1.02.json
  ...
```

## Performance Expectations

### Typical run (all 53 alphas, batch 10, concurrency 3):

- **Time:** 30-90 minutes (API dependent)
- **CPU:** Low (mostly waiting for API)
- **Disk:** ~5-10 MB for results

### Estimated Sharpe distribution:

- 5-10% will be Sharpe > 1.2 (strong)
- 30-40% will be Sharpe 0.5-1.2 (moderate)
- 50-65% will be Sharpe < 0.5 (weak)

This is normal for exploratory alpha research.

## References

- Wyckoff Method: Accumulation → Markup → Distribution → Markdown
- Chaikin Money Flow: Volume × (Close - Low - High + Close) / 2
- BRAIN API: WorldQuant's alpha expression language
- GLB: Global universe with multiple countries/regions

---

**Author:** Kiro CMF Wyckoff Framework  
**Version:** 1.0  
**Last Updated:** 2026-08-18
