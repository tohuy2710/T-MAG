# Absolute-gap parameter mining

Generated: 2026-08-17T07:47:15.689207+00:00

Anchor: `group_neutralize(ts_rank(abs(short_term_price_change_2 - short_term_price_change), 9) * (1 - ts_rank(returns, 15)), industry)`, with the reference windows field=9 and returns=15.

- Variants: **7**
- Field windows: **[2, 3, 4, 5, 6, 7, 8, 9, 10]**
- Return windows: **[10, 15, 20, 25, 30]**
- Total expressions: **315** (45 direct parameter replacements + 270 focused operator variants when the full set is kept)

## Priority order

1. `base_ts_rank`: direct sensitivity map around the supplied expression.
2. `ranked_gap_dual_rank`: preserves the anchor while testing rank normalization.
3. `zscore_gap` and `rolling_zscore_gap`: test normalization without changing the factor family.
4. `mean_gap`, `delayed_gap`, `delta_gap`: operator-neighbourhood extensions.

All candidates keep the campaign settings: GLB / TOPDIV3000 / Delay 1 / Market / Decay 20 / Truncation 0.08 / Pasteurization ON / Unit Verify / NaN ON / Max Trade OFF / Max Position OFF.

No performance metrics are fabricated here; submit this focused set to BRAIN when simulation quota/rate-limit permits.
