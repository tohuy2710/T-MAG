# Neutralization robustness — signed price-gap alpha

Generated: 2026-08-17T15:16:32.353636+00:00

## Design

```text
rank(group_neutralize(rank(ts_rank(sign(short_term_price_change_2 - short_term_price_change), 2)) * (1 - ts_rank(returns, 10)), <group>))
```

- Factorial matrix: **4 × 4 = 16** combinations.
- BRAIN setting `NEUTRALIZATION`: `MARKET`, `SECTOR`, `INDUSTRY`, `SUBINDUSTRY`.
- Formula grouping: `market`, `sector`, `industry`, `subindustry`.
- Fixed controls: GLB / TOPDIV3000 / Delay 1 / Decay 20 / Truncation 0.08 / Pasteurization ON / Unit Verify / NaN ON.
- APAC, EMEA and AMER are the `glbApac`, `glbEmea` and `glbAmer` benchmark blocks from each GLB simulation, not separate universe simulations.

## Completion and ranking

- Completed: **16/16**.
- Rows are ordered by minimum regional Sharpe, then mean regional Sharpe, then GLB Sharpe. This prevents a strong aggregate result from concealing a weak region.

## Benchmark matrix

`S` = Sharpe; `F` = Fitness; `R` = Returns; `TO` = Turnover. The CSV also includes drawdown and margin.

| System NEUTRALIZATION | Formula group | Alpha | GLB S/F/R/TO | APAC S/F/R/TO | EMEA S/F/R/TO | AMER S/F/R/TO | Min regional S | S spread |
|---|---|---|---|---|---|---|---:|---:|
| `INDUSTRY` | `sector` | `78jkxGn5` | 1.8300 / 0.8400 / 0.1229 / 0.5810 | 1.6600 / 1.0000 / 0.0575 / 0.1576 | 0.4500 / 0.1400 / 0.0124 / 0.1294 | 0.9900 / 0.4200 / 0.0531 / 0.2939 | 0.4500 | 1.2100 |
| `MARKET` | `industry` | `QP71nXA5` | 1.8400 / 0.8400 / 0.1234 / 0.5872 | 1.6100 / 0.9500 / 0.0554 / 0.1582 | 0.4400 / 0.1300 / 0.0120 / 0.1307 | 1.0500 / 0.4500 / 0.0560 / 0.2983 | 0.4400 | 1.1700 |
| `INDUSTRY` | `industry` | `omq1nXq5` | 1.8400 / 0.8400 / 0.1234 / 0.5888 | 1.6400 / 0.9800 / 0.0567 / 0.1592 | 0.4300 / 0.1300 / 0.0118 / 0.1308 | 1.0300 / 0.4400 / 0.0549 / 0.2988 | 0.4300 | 1.2100 |
| `SECTOR` | `industry` | `LL7Pn1a6` | 1.8300 / 0.8400 / 0.1228 / 0.5874 | 1.6000 / 0.9500 / 0.0554 / 0.1585 | 0.4300 / 0.1300 / 0.0118 / 0.1307 | 1.0500 / 0.4500 / 0.0556 / 0.2982 | 0.4300 | 1.1700 |
| `INDUSTRY` | `market` | `QP71nYxp` | 1.8200 / 0.8400 / 0.1239 / 0.5788 | 1.6800 / 1.0300 / 0.0591 / 0.1580 | 0.4200 / 0.1300 / 0.0116 / 0.1290 | 0.9800 / 0.4200 / 0.0533 / 0.2919 | 0.4200 | 1.2600 |
| `SUBINDUSTRY` | `sector` | `RR7Jd3kj` | 1.8800 / 0.8200 / 0.1095 / 0.5712 | 1.6200 / 0.9300 / 0.0518 / 0.1583 | 0.3900 / 0.1100 / 0.0099 / 0.1307 | 1.0500 / 0.4300 / 0.0478 / 0.2822 | 0.3900 | 1.2300 |
| `MARKET` | `sector` | `e7zlnJJz` | 1.6200 / 0.7400 / 0.1209 / 0.5848 | 1.4900 / 0.8800 / 0.0538 / 0.1558 | 0.3800 / 0.1100 / 0.0109 / 0.1298 | 0.9500 / 0.4100 / 0.0562 / 0.2992 | 0.3800 | 1.1100 |
| `SUBINDUSTRY` | `industry` | `omq1V5jn` | 1.8900 / 0.8200 / 0.1099 / 0.5773 | 1.6000 / 0.9100 / 0.0511 / 0.1597 | 0.3700 / 0.1000 / 0.0094 / 0.1318 | 1.0900 / 0.4500 / 0.0494 / 0.2858 | 0.3700 | 1.2300 |
| `INDUSTRY` | `subindustry` | `9qXz93wq` | 1.9600 / 0.8500 / 0.1116 / 0.5891 | 1.7000 / 0.9800 / 0.0529 / 0.1604 | 0.3500 / 0.0900 / 0.0086 / 0.1337 | 1.1200 / 0.4600 / 0.0501 / 0.2949 | 0.3500 | 1.3500 |
| `SUBINDUSTRY` | `market` | `RR7JNxRn` | 1.8600 / 0.8200 / 0.1104 / 0.5701 | 1.6300 / 0.9400 / 0.0528 / 0.1588 | 0.3500 / 0.0900 / 0.0089 / 0.1305 | 1.0500 / 0.4400 / 0.0486 / 0.2808 | 0.3500 | 1.2800 |
| `SECTOR` | `sector` | `LL7PnlJv` | 1.5700 / 0.7100 / 0.1184 / 0.5862 | 1.4900 / 0.8800 / 0.0541 / 0.1563 | 0.3500 / 0.1000 / 0.0102 / 0.1300 | 0.9100 / 0.3900 / 0.0541 / 0.2999 | 0.3500 | 1.1400 |
| `MARKET` | `subindustry` | `QP71nrAK` | 1.9100 / 0.8300 / 0.1103 / 0.5885 | 1.6600 / 0.9400 / 0.0516 / 0.1596 | 0.3400 / 0.0900 / 0.0084 / 0.1339 | 1.1100 / 0.4600 / 0.0504 / 0.2949 | 0.3400 | 1.3200 |
| `SECTOR` | `subindustry` | `GrlqnO9o` | 1.9200 / 0.8300 / 0.1100 / 0.5884 | 1.6600 / 0.9400 / 0.0515 / 0.1599 | 0.3300 / 0.0800 / 0.0083 / 0.1339 | 1.1200 / 0.4600 / 0.0502 / 0.2947 | 0.3300 | 1.3300 |
| `SUBINDUSTRY` | `subindustry` | `2rl1Jdp5` | 1.9000 / 0.8200 / 0.1092 / 0.5909 | 1.7100 / 0.9900 / 0.0539 / 0.1619 | 0.3300 / 0.0800 / 0.0083 / 0.1341 | 1.0400 / 0.4200 / 0.0470 / 0.2948 | 0.3300 | 1.3800 |
| `SECTOR` | `market` | `2rl1v7N6` | 1.5600 / 0.7000 / 0.1188 / 0.5834 | 1.5200 / 0.9100 / 0.0557 / 0.1566 | 0.3200 / 0.0900 / 0.0095 / 0.1294 | 0.8900 / 0.3800 / 0.0537 / 0.2974 | 0.3200 | 1.2000 |
| `MARKET` | `market` | `ak7rN6N1` | 1.3300 / 0.5900 / 0.1158 / 0.5860 | 1.4300 / 0.8400 / 0.0530 / 0.1533 | 0.2500 / 0.0600 / 0.0077 / 0.1291 | 0.8000 / 0.3400 / 0.0551 / 0.3036 | 0.2500 | 1.1800 |

## Robustness rule

Use `min_regional_sharpe` as the primary robustness filter and `regional_sharpe_spread` to reject geographically uneven candidates. The report records observations only; no acceptance threshold is assumed.
