# Top 5 Alpha Evolution — Summary

**Status:** 🔄 Running Simulation  
**Started:** 2026-08-19 07:30 UTC  
**Expected Completion:** ~2-3 hours

---

## What Was Done

### Step 1: Parameter Mining
Varied window parameters for parameterized alphas:

| Alpha | Base Expression | Parameter | Values Tested |
|-------|-----------------|-----------|---------------|
| Spring Detection | `rank(-ts_delta(close, w1)) * sign(CMF)` | w1 | 10, 15, 20, 25, 30 |
| CMF Additive | `rank(CMF) + rank(ts_delta(CMF, w1))` | w1 | 10, 15, 20, 25, 30 |
| CMF Multiplicative | `rank(CMF) * rank(ts_delta(CMF, w1))` | w1 | 10, 15, 20, 25, 30 |

**Parameter variants:** 15 alphas (5+5+5)

### Step 2: Operator Nesting
Wrapped base expressions with time-series and grouping operators:

**Single-level nesting (L1):**
- `ts_rank(base, w)` — w ∈ {5, 10, 20}
- `ts_decay_linear(base, w)` — w ∈ {5, 10, 20}
- `ts_mean(base, w)` — w ∈ {5, 10, 20}
- `group_rank(base, subindustry)`
- `group_rank(base, country)`
- `sign(base) * rank(base)`
- `rank(abs(base))`

**Double-level nesting (L2):**
- `ts_rank(ts_decay_linear(base, w1), w2)` — various w1, w2
- `ts_decay_linear(ts_rank(base, w1), w2)` — various w1, w2

**Nesting variants:** 105 alphas (65 L1 + 40 L2)

---

## Total Candidates

| Category | Count | Description |
|----------|-------|-------------|
| Baseline (no params) | 2 | Country-relative CMF, Raw CMF |
| Parameter mining | 15 | Window variations |
| Operator nesting L1 | 65 | Single wrapper |
| Operator nesting L2 | 40 | Double wrapper |
| **Total** | **122** | **Ready to test** |

---

## Top 5 Base Alphas (From Previous Round)

| # | Alpha | Expression | Sharpe | Fitness |
|---|-------|-----------|--------|---------|
| 1 | Country-relative CMF | `group_rank(short_term_price_change_2, country)` | 1.21 | 0.61 |
| 2 | Raw CMF | `rank(short_term_price_change_2)` | 1.12 | 0.59 |
| 3 | Spring Detection | `rank(-ts_delta(close, 20)) * sign(CMF)` | 1.12 | 0.62 |
| 4 | CMF Additive | `rank(CMF) + rank(ts_delta(CMF, 20))` | 1.06 | 0.51 |
| 5 | CMF Multiplicative | `rank(CMF) * rank(ts_delta(CMF, 20))` | 1.02 | 0.48 |

---

## Expected Outcomes

### Goal: Improve top performers
- **Target Sharpe:** > 1.3 (current best: 1.21)
- **Target Fitness:** > 0.7 (current best: 0.62)
- **Turnover constraint:** < 10% (current: 7-11%)

### Hypotheses

**H1: Optimal window parameter ≠ 20**
- Test: Spring detection with w=10, 15, 25, 30
- Expected: May find better w (e.g., w=15 may balance signal/noise better)

**H2: ts_rank improves signal stability**
- Test: `ts_rank(base, 20)` wrapper
- Expected: Reduces turnover by ranking over time window

**H3: ts_decay_linear smooths turnover**
- Test: `ts_decay_linear(base, 10)` wrapper
- Expected: Reduces turnover while maintaining Sharpe

**H4: Double nesting over-smooths**
- Test: `ts_rank(ts_decay_linear(base, 10), 5)`
- Expected: May reduce signal too much (Sharpe drops)

**H5: Country grouping after nesting beats before**
- Test: `group_rank(ts_rank(base, 20), country)` vs `ts_rank(group_rank(base, country), 20)`
- Expected: Order matters for composite operators

---

## Simulation Configuration

**Settings (Fixed):**
```
Region: GLB
Universe: TOPDIV3000
Delay: 1
Neutralization: SUBINDUSTRY
Truncation: 0.08
Decay: 10
Pasteurization: ON
Unit Handling: VERIFY
NaN Handling: OFF
```

**Batch Configuration:**
- Batch size: 10
- Max concurrent: 4
- Total batches: ~13

**Expected runtime:** 2-3 hours

---

## Files

| File | Purpose |
|------|---------|
| `top5_alpha_evolver.py` | Generator script |
| `top5_evolved_alphas.txt` | 122 alpha expressions |
| `output/cmf_wyckoff/top5_evolved_simulation.log` | Simulation log |
| `output/cmf_wyckoff/results.json` | Results (will overwrite) |
| `output/cmf_wyckoff/results.csv` | Leaderboard |
| `TOP5_EVOLUTION_SUMMARY.md` | This file |

---

## Next Steps After Completion

### 1. Analyze Results
```bash
cd phase_1_plus
python3 cmf_wyckoff_analyzer.py
cat output/cmf_wyckoff/CMF_WYCKOFF_REPORT.md
```

### 2. Compare with Baseline
- Best evolved alpha vs original top 5
- Turnover reduction achieved?
- Sharpe improvement?

### 3. Identify Winners
- Top 3 by Sharpe
- Top 3 by Fitness
- Top 3 by Sharpe/Turnover ratio

### 4. Deploy Best Performer
- Copy expression to BRAIN
- Submit for live tracking
- Monitor for 1 week

---

## Success Criteria

✅ **Success if:**
- At least 1 alpha beats Sharpe 1.21
- At least 1 alpha has Fitness > 0.65
- At least 3 alphas reduce turnover below 7%

⚠️ **Partial success if:**
- No Sharpe improvement, but turnover reduced significantly
- Sharpe improved slightly (>1.25) but turnover same

❌ **Failure if:**
- All alphas worse than baseline
- All nesting reduces Sharpe significantly (overfitting)

---

## Monitoring Progress

```bash
# Check simulation log
tail -f phase_1_plus/output/cmf_wyckoff/top5_evolved_simulation.log

# Check how many complete
wc -l phase_1_plus/output/cmf_wyckoff/results.csv

# Quick peek at top performers so far
head -10 phase_1_plus/output/cmf_wyckoff/results.csv
```

---

## Theoretical Expectations

### Parameter Mining Results

**Spring Detection (w1 variation):**
- w=10: More responsive, higher turnover
- w=15: Balance point (expected best)
- w=20: Current baseline
- w=25, 30: Slower, lower turnover

**CMF Additive/Multiplicative (w1 variation):**
- w=10: Short-term CMF momentum
- w=20: Mid-term (current)
- w=30: Long-term trend

### Operator Nesting Results

**ts_rank wrapper:**
- Converts absolute values to time-series ranks
- Expected: Lower turnover, stable Sharpe

**ts_decay_linear wrapper:**
- Exponentially weights recent data
- Expected: Lower turnover, slight Sharpe drop

**ts_mean wrapper:**
- Simple moving average
- Expected: Smoothest, lowest turnover, moderate Sharpe drop

**group_rank wrappers:**
- Sector/country grouping after signal computation
- Expected: May not help (already have country-relative base)

**Double nesting:**
- Combines two smoothing operations
- Expected: Very low turnover, but likely over-smoothed

---

## Key Insights to Watch For

1. **Does nesting hurt or help?**
   - Compare base vs nested variants

2. **What's the optimal window?**
   - Check parameter mining results

3. **Is there a Sharpe/Turnover tradeoff?**
   - Plot Sharpe vs Turnover for all candidates

4. **Do double-nested alphas work?**
   - Or do they over-smooth signal?

5. **Best operator for CMF?**
   - ts_rank? ts_decay_linear? ts_mean?

---

**Status:** 🔄 Simulation Running  
**Check back in:** 2-3 hours  
**Expected completion:** ~10:00 UTC

Monitor with:
```bash
tail -f phase_1_plus/output/cmf_wyckoff/top5_evolved_simulation.log
```
