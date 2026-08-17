# WjAv9LeG focused alpha development

Generated: 2026-08-17T09:34:04.686654+00:00

## Source alpha

`WjAv9LeG`: `group_neutralize(ts_rank(sign(short_term_price_change_2 - short_term_price_change), 7) * (1 - ts_rank(returns, 10)), industry)`

Interpretation: signed price-gap direction between the two supplied short-term price fields, ranked over time and interacted with short-term reversal in returns.

## Scope

- Generated: **315** candidates = 45 parameter replacements + 270 operator nests.
- Matched completed local BRAIN results: **25**.
- Base parameter results matched: **6**.
- Allowed inputs: `short_term_price_change_2`, `short_term_price_change`, `returns`; `industry` is used only as the reference grouping key.
- No volume, fundamentals, analyst, capitalization or other external data were added.

## Settings

All candidates retain the source settings: GLB / TOPDIV3000 / Delay 1 / Market / Decay 20 / Truncation 0.08 / Pasteurization ON / Unit Verify / NaN ON / Max Trade OFF / Max Position OFF.

## Best direct parameter replacements

| Alpha | Field window | Returns window | Sharpe | Fitness | Turnover | Returns | Expression |
|---|---:|---:|---:|---:|---:|---:|---|
| `WjAv9LeG` | 7 | 10 | 1.79 | 0.82 | 0.4646 | 0.0979 | `group_neutralize(ts_rank(sign(short_term_price_change_2 - short_term_price_change), 7) * (1 - ts_rank(returns, 10)), industry)` |
| `d5ZNg87v` | 10 | 10 | 1.72 | 0.79 | 0.4133 | 0.0864 | `group_neutralize(ts_rank(sign(short_term_price_change_2 - short_term_price_change), 10) * (1 - ts_rank(returns, 10)), industry)` |
| `leWo7lnO` | 4 | 15 | 1.7 | 0.8 | 0.4913 | 0.11 | `group_neutralize(ts_rank(sign(short_term_price_change_2 - short_term_price_change), 4) * (1 - ts_rank(returns, 15)), industry)` |
| `1YprnQVk` | 7 | 15 | 1.65 | 0.77 | 0.4368 | 0.0948 | `group_neutralize(ts_rank(sign(short_term_price_change_2 - short_term_price_change), 7) * (1 - ts_rank(returns, 15)), industry)` |
| `A1GoaP7d` | 4 | 20 | 1.63 | 0.78 | 0.4673 | 0.1077 | `group_neutralize(ts_rank(sign(short_term_price_change_2 - short_term_price_change), 4) * (1 - ts_rank(returns, 20)), industry)` |
| `kqPz3xdg` | 9 | 30 | 1.49 | 0.71 | 0.3774 | 0.0862 | `group_neutralize(ts_rank(sign(short_term_price_change_2 - short_term_price_change), 9) * (1 - ts_rank(returns, 30)), industry)` |

## Best operator nests

| Variant | Alpha | Field window | Returns window | Sharpe | Fitness | Turnover |
|---|---|---:|---:|---:|---:|---:|
| `dual_rank` | `GrGZePeo` | 7 | 10 | 1.59 | 0.68 | 0.3817 |
| `dual_rank` | `mL5EgXXK` | 4 | 20 | 1.52 | 0.69 | 0.4444 |
| `dual_rank` | `gJ8nQ2JQ` | 7 | 15 | 1.5 | 0.65 | 0.3705 |
| `one_day_delayed_signal` | `d5ZNjbEg` | 7 | 10 | 1.69 | 0.76 | 0.4609 |
| `one_day_delayed_signal` | `JjG6NjRe` | 10 | 10 | 1.62 | 0.72 | 0.4102 |
| `one_day_delayed_signal` | `MPGJL7ln` | 9 | 30 | 1.43 | 0.68 | 0.3819 |
| `rank_signal` | `MPGJ1dd6` | 7 | 10 | 1.63 | 0.7 | 0.3839 |
| `rank_signal` | `rK2ZPrzJ` | 7 | 15 | 1.53 | 0.67 | 0.3683 |
| `rank_signal` | `ZYEOEEdZ` | 9 | 30 | 1.43 | 0.65 | 0.314 |
| `rolling_zscore_signal` | `KPGW7gGk` | 9 | 30 | 0.12 | 0.02 | 0.2405 |
| `rolling_zscore_signal` | `WjAvGb2d` | 4 | 20 | 0.06 | 0.0 | 0.3187 |
| `rolling_zscore_signal` | `omNxNbov` | 7 | 15 | 0.03 | 0.0 | 0.265 |
| `zscore_signal` | `E5G9vMeK` | 9 | 30 | 0.23 | 0.03 | 0.5057 |
| `zscore_signal` | `JjG67kMn` | 7 | 15 | 0.16 | 0.02 | 0.5951 |
| `zscore_signal` | `A1Go7LzW` | 10 | 10 | 0.11 | 0.01 | 0.4727 |

## Development conclusion

The strongest direct replacement in the matched sample is `WjAv9LeG` with field window=7 and returns window=10.
Prioritize short returns windows 10–15 for turnover, then compare field windows 4, 7, 9 and 10; validate each operator nest separately because z-score/rolling normalization can materially change the signal distribution.
IC is not included in the local BRAIN response schema; Sharpe, fitness, turnover and returns are reported without fabricating IC.
