# CMF + Williams %R alpha campaign

Generated: 2026-08-17T09:21:20.091986+00:00

## Scope and settings

The campaign uses the user-specified fields and exact runtime settings below:

```text
{
  "instrumentType": "EQUITY",
  "region": "GLB",
  "universe": "TOPDIV3000",
  "delay": 1,
  "neutralization": "MARKET",
  "decay": 20,
  "truncation": 0.08,
  "pasteurization": "ON",
  "unitHandling": "VERIFY",
  "nanHandling": "ON",
  "maxTrade": "OFF",
  "maxPosition": "OFF",
  "language": "FASTEXPR",
  "visualization": false
}
TEST PERIOD = 0 YEARS 0 MONTHS (startDate/endDate omitted; platform history)
```

The expression-level `group_neutralize(..., industry)` is retained from the reference alpha; the platform-level setting remains `neutralization=MARKET`.
The official operator spelling `ts_std_dev` is used for the requested rolling standard deviation transformation.

## Experiment coverage

- Generated candidate definitions: **144**
- Results recorded: **145**
- Completed by BRAIN: **144**
- Non-completed: **1**
- Stage 1: 14 raw A/B templates (including A-only and B-only controls), field windows 2–10, return windows 10/15/20/25/30.
- Stage 2: generator implemented for dual-rank, z-score, rolling-z-score, delay, delta and return-interaction nests; it was not submitted in this snapshot because BRAIN rate-limited new POSTs after the Stage 1 campaign.

## Metric availability

BRAIN returned strategy-level Sharpe, fitness, turnover, returns and drawdown. The API response did not expose cross-sectional daily IC in the observed schema, so `IC mean`, `IC std` and `IC IR` are reported as `N/A`; they must not be reconstructed from cumulative PnL.

## Top 10 diversified candidates

| # | Alpha | Sharpe | Fitness | Turnover | Returns | Max corr vs selected | Template / variant |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | `WjAv9LeG` | 1.79 | 0.82 | 0.4646 | 0.0979 | 0.8376 | `signed_gap` / `base_ts_rank` |
| 2 | `QPGwGP6G` | 1.7 | 0.83 | 0.3751 | 0.0886 | 0.8222 | `A_plus_B` / `dual_rank` |
| 3 | `kqPz3xdg` | 1.49 | 0.71 | 0.3774 | 0.0862 | 0.8376 | `signed_gap` / `base_ts_rank` |
| 4 | `rK2ZPrzJ` | 1.53 | 0.67 | 0.3683 | 0.0704 | 0.0000 | `signed_gap` / `rank_signal` |
| 5 | `2rp37LYJ` | 1.55 | 0.67 | 0.3497 | 0.0646 | 0.0000 | `A_plus_B` / `base_ts_rank` |
| 6 | `gJ8nQ2JQ` | 1.5 | 0.65 | 0.3705 | 0.0702 | 0.0000 | `signed_gap` / `dual_rank` |
| 7 | `88pMOApa` | 1.57 | 0.7 | 0.3142 | 0.0617 | 0.8222 | `max_A_B` / `base_ts_rank` |
| 8 | `GrGZEJmQ` | 1.52 | 0.66 | 0.3426 | 0.0653 | 0.0000 | `A_plus_B` / `base_ts_rank` |
| 9 | `rK2ZbE1J` | 1.44 | 0.54 | 0.386 | 0.0548 | 0.0000 | `absolute_gap` / `base_ts_rank` |
| 10 | `blQeQebq` | 1.49 | 0.64 | 0.3214 | 0.0589 | 0.0000 | `signed_gap` / `dual_rank` |

## Evaluated expressions

See `evaluated_expressions.txt` and `candidates.json` for every expression and parameter combination.

## Recommended 3–5 expressions

### 1. `WjAv9LeG`

`group_neutralize(ts_rank(sign(short_term_price_change_2 - short_term_price_change), 7) * (1 - ts_rank(returns, 10)), industry)`

Sharpe=1.79, Fitness=0.82, Turnover=0.4646, Returns=0.0979. Selected because the composite ranking gives 45% weight to Sharpe, 25% to fitness and 30% to turnover, with a correlation-diversification pass.

### 2. `QPGwGP6G`

`group_neutralize(rank(ts_rank((short_term_price_change_2 + short_term_price_change), 2)) * rank(1 - ts_rank(returns, 15)), industry)`

Sharpe=1.7, Fitness=0.83, Turnover=0.3751, Returns=0.0886. Selected because the composite ranking gives 45% weight to Sharpe, 25% to fitness and 30% to turnover, with a correlation-diversification pass.

### 3. `kqPz3xdg`

`group_neutralize(ts_rank(sign(short_term_price_change_2 - short_term_price_change), 9) * (1 - ts_rank(returns, 30)), industry)`

Sharpe=1.49, Fitness=0.71, Turnover=0.3774, Returns=0.0862. Selected because the composite ranking gives 45% weight to Sharpe, 25% to fitness and 30% to turnover, with a correlation-diversification pass.

### 4. `rK2ZPrzJ`

`group_neutralize(rank(ts_rank(sign(short_term_price_change_2 - short_term_price_change), 7)) * (1 - ts_rank(returns, 15)), industry)`

Sharpe=1.53, Fitness=0.67, Turnover=0.3683, Returns=0.0704. Selected because the composite ranking gives 45% weight to Sharpe, 25% to fitness and 30% to turnover, with a correlation-diversification pass.

### 5. `2rp37LYJ`

`group_neutralize(ts_rank((short_term_price_change_2 + short_term_price_change), 2) * (1 - ts_rank(returns, 15)), industry)`

Sharpe=1.55, Fitness=0.67, Turnover=0.3497, Returns=0.0646. Selected because the composite ranking gives 45% weight to Sharpe, 25% to fitness and 30% to turnover, with a correlation-diversification pass.
