# CMF Wyckoff Alpha Family — Simulation Report
**Generated:** 2026-08-19 06:59:15
**Region:** GLB | **Universe:** TOPDIV3000

## Executive Summary
- **Total Alphas Tested:** 54
- **Successful:** 37 (68.5%)
- **Failed:** 17

### Key Metrics (Complete Alphas)

| Metric | Mean | Max | Min | StdDev |
|--------|------|-----|-----|--------|
| Sharpe | 0.444 | 1.210 | -1.120 | 0.509 |
| Fitness | 0.186 | 0.620 | -0.590 | 0.251 |
| Turnover | 0.11726 | 0.20200 | 0.03210 | 0.04380 |
| Returns (%) | 0.0144 | 0.0387 | -0.0343 | 0.0164 |

## Performance by Alpha Level

| Level | Alpha Count | Complete | Avg Sharpe | Best Fitness | Avg Turnover |
|-------|-------------|----------|-----------|--------------|---------------|
| L 1 |   3 |        3 |     0.980 |        0.590 |       0.05197 |
| L 2 |   3 |        3 |     0.493 |        0.180 |       0.14423 |
| L 3 |   2 |        2 |     0.020 |        0.130 |       0.06700 |
| L 4 |   3 |        3 |     0.463 |        0.280 |       0.13890 |
| L 5 |   3 |        3 |     0.293 |        0.250 |       0.11947 |
| L 6 |   3 |        1 |     0.190 |        0.050 |       0.10960 |
| L 7 |   3 |        3 |     0.777 |        0.610 |       0.11927 |
| L 8 |   2 |        0 |     0.000 |        0.000 |       0.00000 |
| L 9 |   6 |        0 |     0.000 |        0.000 |       0.00000 |
| L10 |   2 |        2 |    -0.255 |        0.010 |       0.15210 |
| L11 |   3 |        3 |     0.917 |        0.510 |       0.10830 |
| L12 |   2 |        2 |     0.875 |        0.450 |       0.03560 |
| L13 |   2 |        1 |    -0.490 |       -0.210 |       0.15240 |
| L14 |   2 |        2 |     0.295 |        0.170 |       0.16955 |
| L15 |   2 |        2 |     0.585 |        0.620 |       0.12555 |
| L16 |   2 |        2 |     0.740 |        0.450 |       0.13110 |
| L17 |   2 |        0 |     0.000 |        0.000 |       0.00000 |
| L18 |   4 |        0 |     0.000 |        0.000 |       0.00000 |
| L19 |   3 |        3 |     0.357 |        0.190 |       0.14620 |
| L20 |   2 |        2 |    -0.325 |        0.130 |       0.11490 |

## Metric Correlations

- **sharpe_vs_fitness:** 0.978
- **sharpe_vs_turnover:** -0.258
- **fitness_vs_turnover:** -0.345
- **fitness_vs_returns:** 0.950

## Top 10 Alphas by Fitness

| Rank | Alpha ID | Description | Sharpe | Fitness | Turnover | Returns |
|------|----------|-------------|--------|---------|----------|----------|
|  1 | Xg7GnRjx | Spring detection: negative price momentum + positive CMF |  1.120 |   0.620 |  0.10270 |   0.0387 |
|  2 | np79gEYl | Country-relative CMF level |  1.210 |   0.610 |  0.07860 |   0.0319 |
|  3 | 6Xl7wnRY | CMF Level (Raw)      |  1.120 |   0.590 |  0.07380 |   0.0343 |
|  4 | d5jp0L3E | CMF level + CMF momentum (additive) |  1.060 |   0.510 |  0.11650 |   0.0287 |
|  5 | np792bew | CMF level * CMF momentum |  1.020 |   0.480 |  0.11730 |   0.0279 |
|  6 | Jj7qpVNx | CMF Level (20-day MA) |  0.930 |   0.450 |  0.04590 |   0.0294 |
|  7 | ak76noOW | CMF 20-day + 40-day combination (mean) |  0.920 |   0.450 |  0.03910 |   0.0300 |
|  8 | RR7M8vNe | Accumulation only when positive CMF |  0.930 |   0.450 |  0.10030 |   0.0297 |
|  9 | j2jvZ5WQ | CMF Level (40-day MA) |  0.890 |   0.430 |  0.03620 |   0.0292 |
| 10 | mLjpbXO5 | CMF persistence over 60 days |  0.830 |   0.390 |  0.03210 |   0.0282 |

## Top 10 Alphas by Sharpe Ratio

| Rank | Alpha ID | Description | Sharpe | Fitness | Turnover | Returns |
|------|----------|-------------|--------|---------|----------|----------|
|  1 | np79gEYl | Country-relative CMF level |  1.210 |   0.610 |  0.07860 |   0.0319 |
|  2 | 6Xl7wnRY | CMF Level (Raw)      |  1.120 |   0.590 |  0.07380 |   0.0343 |
|  3 | Xg7GnRjx | Spring detection: negative price momentum + positive CMF |  1.120 |   0.620 |  0.10270 |   0.0387 |
|  4 | d5jp0L3E | CMF level + CMF momentum (additive) |  1.060 |   0.510 |  0.11650 |   0.0287 |
|  5 | np792bew | CMF level * CMF momentum |  1.020 |   0.480 |  0.11730 |   0.0279 |
|  6 | Jj7qpVNx | CMF Level (20-day MA) |  0.930 |   0.450 |  0.04590 |   0.0294 |
|  7 | RR7M8vNe | Accumulation only when positive CMF |  0.930 |   0.450 |  0.10030 |   0.0297 |
|  8 | ak76noOW | CMF 20-day + 40-day combination (mean) |  0.920 |   0.450 |  0.03910 |   0.0300 |
|  9 | j2jvZ5WQ | CMF Level (40-day MA) |  0.890 |   0.430 |  0.03620 |   0.0292 |
| 10 | mLjpbXO5 | CMF persistence over 60 days |  0.830 |   0.390 |  0.03210 |   0.0282 |

## Top Alpha Expressions (for reference)

### 1. Xg7GnRjx - Spring detection: negative price momentum + positive CMF

```
rank(-ts_delta(close, 20)) * sign(short_term_price_change_2)
```

### 2. np79gEYl - Country-relative CMF level

```
group_rank(short_term_price_change_2, country)
```

### 3. 6Xl7wnRY - CMF Level (Raw)

```
rank(short_term_price_change_2)
```

### 4. d5jp0L3E - CMF level + CMF momentum (additive)

```
rank(short_term_price_change_2) + rank(ts_delta(short_term_price_change_2, 20))
```

### 5. np792bew - CMF level * CMF momentum

```
rank(short_term_price_change_2) * rank(ts_delta(short_term_price_change_2, 20))
```

## Key Findings

1. **Sharpe Distribution:** Mean Sharpe of 0.444 suggests **low risk-adjusted returns** — may need refinement or combination.

2. **Fitness-Sharpe Correlation:** 0.978 (strong positive) — fitness is a reliable metric.

3. **Turnover Profile:** Mean turnover 0.11726 (high) may require decay or other smoothing.

## Recommendations

- **Start with:** Xg7GnRjx (Fitness: 0.620)
- **Test country/region neutralization:** Level 7-9 alphas show promise for GLB
- **Monitor turnover-Sharpe tradeoff:** Some alphas may benefit from decay tuning
- **Combine top performers:** Pool 3-5 uncorrelated alphas for robustness
- **Regional breadth analysis:** Check Sharpe by country/region before deployment

---

*Report generated by cmf_wyckoff_analyzer.py*
