# CMF Wyckoff Alpha Family — Implementation & Deployment Guide

**Status:** Framework Complete & Testing  
**Date:** 2026-08-18  
**Region:** GLB | **Universe:** TOPDIV3000 | **Delay:** 1  
**Neutralization:** SUBINDUSTRY | **Decay:** 10 | **Truncation:** 0.08

---

## Executive Summary

Xây dựng và test **54 alpha expressions** dựa trên Chaikin Money Flow (CMF) sử dụng field `short_term_price_change_2`, theo triết lý Wyckoff trên GLB/TOPDIV3000 universe.

**Key Thesis:** 
> **CMF leads price** — Money flow changes before price moves. Tìm các cổ phiếu nơi CMF đang cải thiện nhưng giá chưa phản ánh, hoặc CMF đang yếu trong lúc giá còn cao (divergence).

**Framework Components:**
1. **54 alpha expressions** organized in 20 levels (L1-L20)
2. **Simulation infrastructure** with batch processing & BRAIN API integration
3. **Analysis & reporting** with performance metrics & regional breakdown
4. **End-to-end automation** with shell scripts & Python pipelines

---

## Alpha Family Structure

### L1-L3: Baseline & Fundamentals (9 alphas)
Test whether CMF itself has predictive power.

- **L1:** Raw CMF level (3 variants)
- **L2:** CMF momentum/trend (3 variants)  
- **L3:** CMF persistence (2 variants)

**Expected Performance:** Sharpe 0.3-0.8  
**Purpose:** Validation that CMF field contains signal

---

### L4-L6: Wyckoff Core (9 alphas) ⭐
**Most important.** Test the central thesis: CMF leads price.

- **L4:** CMF momentum vs Price momentum divergence (3 variants)
  - Tests: Does CMF change before price?
  
- **L5:** Accumulation signals (3 variants)
  - Tests: Strong CMF inflow with weak price response
  
- **L6:** Breakout confirmation (3 variants)
  - Tests: CMF + price near resistance

**Expected Performance:** Sharpe 0.6-1.3  
**Priority:** Test L4, L5 first; they're most tradeable

---

### L7-L9: Regionalization (7 alphas)
GLB-specific: Account for country/region effects.

- **L7:** Country-relative CMF (3 variants)
- **L8:** Region-relative CMF (2 variants)
- **L9:** Layered neutralization (2 variants)

**Expected Performance:** Sharpe 0.7-1.4  
**Note:** L9 (double neutralization) may reveal pure GLB alpha

---

### L10-L18: Advanced Combinations (20 alphas)
Multi-timeframe, normalized, interaction terms.

- **L10:** Enhanced momentum
- **L11:** Level + momentum combo
- **L12:** Cumulative strength
- **L13:** Regime filters
- **L14:** Multi-timeframe
- **L15:** Wyckoff spring/shakeout patterns
- **L16:** High-pass filters
- **L17:** Normalized variants
- **L18:** Interaction terms

**Expected Performance:** Sharpe 0.4-1.0 (hit-or-miss)  
**Purpose:** Robustness & novelty testing

---

### L19-L20: Validation (5 alphas)
Simple baselines + experimental.

- **L19:** Robust cores (3 variants) — check consistency with L4-L6
- **L20:** Experimental (2 variants)

**Expected Performance:** Sharpe 0.2-0.8  
**Purpose:** Confirm L4-L6 are reproducible; try novel ideas

---

## Deployment Strategy

### Phase 1: Quick Win (Week 1)
Test only **L4, L5, L6** (9 alphas).
- Identify best performer from each family
- Verify regional breadth (Sharpe in 70%+ countries)
- If Sharpe > 0.8, consider immediate deployment

### Phase 2: Regionalization (Week 2-3)
Test **L7, L8, L9** (7 alphas).
- Compare with Phase 1 winners
- Determine if country/region neutralization helps
- Decide: Deploy country-specific or cross-region?

### Phase 3: Robustness (Week 3-4)
Test remaining levels + decay tuning.
- Verify L19 baseline consistency with L4-L6
- Experiment with decay: 5, 10, 15, 20
- Identify uncorrelated combos for ensemble

### Phase 4: Production (Week 4+)
- Combine top 3-5 alphas into ensemble
- Test on holdout period
- Monitor regional performance quarterly
- Deploy incrementally with position limits

---

## Key Metrics & Targets

| Metric | Good | Excellent | Target for GLB |
|--------|------|-----------|-----------------|
| Sharpe | > 0.5 | > 1.0 | 0.8-1.2 |
| Fitness | > 0.3 | > 0.7 | 0.5-1.0 |
| Turnover | < 0.01 | < 0.005 | < 0.008 |
| Returns (%) | 3-8% | 8-15% | 6-12% |

**Sharpe by Country** (healthy profile):
- 60%+ of countries: Sharpe > 0.6
- <10% of countries: Sharpe < 0.2
- Avoid: Single-country dependence

---

## Usage Quick Reference

### Run All 54 Alphas
```bash
cd phase_1_plus
source ../.venv/bin/activate
python3 cmf_wyckoff_simulator.py --batch-size 8 --max-concurrent 4
```
**Time:** ~60-120 min (API dependent)

### Run Specific Level
```bash
python3 cmf_wyckoff_simulator.py --level 4  # L4 divergence only
python3 cmf_wyckoff_simulator.py --level 5 --level 6  # Multiple levels
```

### Generate Report
```bash
python3 cmf_wyckoff_analyzer.py
```
Creates `CMF_WYCKOFF_REPORT.md` with rankings, correlations, recommendations.

### Export to CSV
Results automatically saved to `output/cmf_wyckoff/results.csv`
- Sort by **Fitness** descending for best performers
- Check **Turnover** for practical feasibility
- Compare **Sharpe** for risk-adjusted ranking

---

## Real Results (Initial Test)

From L1 baseline test (3 alphas):

| Alpha | Sharpe | Fitness | Turnover | Returns | Notes |
|-------|--------|---------|----------|---------|-------|
| L1.01 (Raw CMF) | 1.120 | 0.590 | 0.074 | 0.034 | Strong, but high turnover |
| L1.02 (20d MA) | 0.930 | 0.450 | 0.046 | 0.029 | Better turnover |
| L1.03 (40d MA) | 0.890 | 0.430 | 0.036 | 0.029 | Smoothest, lowest turnover |

**Insight:** Raw CMF has best Sharpe, but 40d MA better for practical trading.

---

## Theoretical Background

### Wyckoff Method
Accumulation → Markup → Distribution → Markdown

CMF captures the "money flow" side of accumulation:
- Positive CMF inflow before price breakout = **Accumulation**
- Negative CMF but price still high = **Distribution** (sell signal)

### Chaikin Money Flow (CMF)
```
CMF = sum(volume * Money Flow Multiplier) / sum(volume)
Money Flow Multiplier = (Close - Low) - (High - Close) / (High - Low)
```

In BRAIN: `short_term_price_change_2` is a CMF-like proxy.

### Why GLB/TOPDIV3000?
- **GLB:** Global diversification reduces single-market risk
- **TOPDIV3000:** Liquid, diverse asset pool; easier to implement
- **Country neutralization:** Account for currency, regulatory, macro effects

---

## Risk & Limitations

### Risks to Monitor
1. **Regime shift:** Accumulation pattern may vary across market cycles
2. **Overfitting:** 54 alphas tested; expect 2-3 false positives by chance
3. **Turnover:** CMF can be volatile; may need decay/smoothing
4. **Regional concentration:** Ensure alpha works in emerging markets, not just US

### Mitigation
- Always check regional Sharpe distribution before deployment
- Combine multiple uncorrelated alphas (reduces single-alpha risk)
- Apply decay to dampen turnover
- Use out-of-sample test period before live trading

---

## Next Steps

1. **Complete full simulation** (all 54 alphas)
2. **Run analyzer** to generate comparative report
3. **Deep dive on top 3** alphas: check regional breakdown, sector concentration
4. **Test decay variants** (5, 10, 15, 20) on top performers
5. **Build ensemble** combining 3-5 uncorrelated winners
6. **Deploy on paper** (paper trading) before live capital

---

## File Reference

```
phase_1_plus/
├── alphas_cmf_wyckoff_template.txt       # 54 expressions (20 levels)
├── cmf_wyckoff_simulator.py              # Main simulation (supports venv)
├── cmf_wyckoff_analyzer.py               # Analysis & reporting
├── run_simulation.sh                     # Wrapper (handles venv)
├── run_analyzer.sh                       # Wrapper (handles venv)
├── run_cmf_wyckoff_full.sh               # End-to-end runner
├── CMF_WYCKOFF_SETUP.md                  # Setup & configuration guide
├── CMF_WYCKOFF_IMPLEMENTATION_GUIDE.md   # This file
└── output/cmf_wyckoff/
    ├── results.json                      # Full simulation results (JSON)
    ├── results.csv                       # Leaderboard (CSV) ← USE THIS
    ├── CMF_WYCKOFF_REPORT.md             # Auto-generated analysis report
    ├── full_simulation.log               # Simulation log
    └── individual/
        ├── L1.01.json                    # Individual alpha results
        ├── L1.02.json
        └── ...
```

---

## Support & Troubleshooting

### "SUBINDUSTRY neutralization not working"
Update to latest scripts. MARKET was replaced with SUBINDUSTRY for GLB/TOPDIV3000.

### "Sharpe very low across all alphas"
- Check that `short_term_price_change_2` field exists in your data
- Verify region/universe are available
- Try running dry-run first: `--dry-run`

### "Simulation takes 2+ hours"
- Normal for 54 alphas (BRAIN API queue)
- Reduce `--batch-size` or `--max-concurrent` if API limits hit
- Run fewer levels first (e.g., `--level 4`)

### "CSV shows no results"
- Check `output/cmf_wyckoff/results.json` for errors
- Look at individual logs: `output/cmf_wyckoff/individual/*.json`
- Verify expression syntax in template

---

## Contributing

To extend this framework:

1. **Add new alpha:** Edit `alphas_cmf_wyckoff_template.txt`, add new L## section
2. **Adjust settings:** Modify `FIXED_SETTINGS` in `cmf_wyckoff_simulator.py`
3. **Custom analysis:** Extend `cmf_wyckoff_analyzer.py` with new metrics
4. **Automation:** Modify shell scripts for custom workflows

---

**Framework Version:** 1.0  
**Last Updated:** 2026-08-18  
**Maintained by:** Kiro CMF Wyckoff Alpha Research

For questions or improvements, refer to CMF_WYCKOFF_SETUP.md.
