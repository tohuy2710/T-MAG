# Phase 1: Quarterly Return Reversal

## Tổng quan

Phase 1 tập trung vào việc mô phỏng hàng loạt alpha sử dụng template **Quarterly Return Reversal** - một chiến lược đảo chiều có điều kiện dựa trên quý.

**Môi trường:** GLB / TOPDIV3000 / Delay 1

## Lý thuyết Template

### Financial Rationale

Hiệu ứng mùa vụ (seasonal effects) có thể khiến cùng một loại price action có sức dự báo khác nhau ở từng quý. Ví dụ:

- Sau một đợt giảm mạnh trong Q4 hoặc Q1, dòng tiền/positioning có thể tạo ra reversal
- Thay vì giả định Q1 luôn bullish hay Q4 luôn bearish, ta sử dụng `quarter_indicator_code` như một bộ lọc regime

### Template Structure

```
trade_when(
    quarter_indicator_code == <quarter>,
    group_neutralize(
        rank(-ts_delta(<field>, <lookback>)),
        <group>
    ),
    -1
)
```

### Parameters

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `quarter` | int | 1, 2, 3, 4 | Quý để filter |
| `field` | field | close, returns, vwap, open | Trường dữ liệu giá |
| `lookback` | int | 3, 5, 10, 20 | Lookback period |
| `group` | group | subindustry, industry, sector | Nhóm neutralization |

### Ví dụ Expressions

```python
# Q4 reversal với 10-day lookback, industry neutral
trade_when(
    quarter_indicator_code == 4,
    group_neutralize(rank(-ts_delta(close, 10)), industry),
    -1
)

# Q1 reversal với returns, subindustry neutral
trade_when(
    quarter_indicator_code == 1,
    group_neutralize(rank(-ts_delta(returns, 5)), subindustry),
    -1
)
```

## Cách sử dụng

### 1. Mô phỏng cơ bản

```bash
cd phase_1
python3 phase_1_sim.py
```

Mặc định:
- Template: `quarterly_return_reversal`
- Batch size: 10
- Max candidates: 20
- Max concurrent: 3
- **Auto-submit: DISABLED** (chỉ simulate, không tự động submit)

### 2. Tùy chỉnh parameters

```bash
# Batch size lớn hơn
python3 phase_1_sim.py --batch-size 15

# Generate nhiều candidates hơn
python3 phase_1_sim.py --max-per-template 50

# Tăng concurrency
python3 phase_1_sim.py --max-concurrent 5

# Hiển thị top 20 performers
python3 phase_1_sim.py --show-top 20
```

### 3. Kết hợp parameters

```bash
python3 phase_1_sim.py \
  --batch-size 20 \
  --max-per-template 40 \
  --max-concurrent 5 \
  --show-top 15
```

## Output Structure

```
phase_1/
├── output/
│   ├── simulation_results.json       # Tổng hợp kết quả
│   └── individual/
│       ├── <alpha_id_1>.json        # Kết quả từng alpha
│       ├── <alpha_id_2>.json
│       └── ...
├── phase_1_config.py                 # Configuration
├── phase_1_sim.py                    # Main simulation script
└── phase_1_utils.py                  # Utility functions
```

### simulation_results.json Format

```json
{
  "phase": "phase_1",
  "timestamp": "2026-08-15T10:30:00Z",
  "total_simulated": 80,
  "passed": 65,
  "failed": 15,
  "results": [
    {
      "expression": "trade_when(...)",
      "template_id": "quarterly_return_reversal",
      "status": "COMPLETE",
      "alpha_id": "ABC123XY",
      "sim_data": {
        "is": {
          "sharpe": 1.85,
          "fitness": 0.92,
          "turnover": 0.0234
        }
      },
      "simulated_at": "2026-08-15T10:31:23Z"
    }
  ]
}
```

## Environment Variables

Có thể override các config thông qua environment variables:

```bash
# Batch size
export PHASE_1_BATCH_SIZE=15

# Max candidates per template
export PHASE_1_MAX_PER_TEMPLATE=30

# Max concurrent simulations
export PHASE_1_MAX_CONCURRENT=5

# Log level
export PHASE_1_LOG_LEVEL=DEBUG

# Run simulation
python3 phase_1_sim.py
```

## Analysis & Review

### 1. Xem tổng quan kết quả

```bash
cat output/simulation_results.json | jq '.total_simulated, .passed, .failed'
```

### 2. Top performers by Sharpe

```bash
cat output/simulation_results.json | jq -r '
  .results[] 
  | select(.status=="COMPLETE") 
  | [.alpha_id, .sim_data.is.sharpe, .sim_data.is.fitness] 
  | @tsv' | sort -k2 -rn | head -10
```

### 3. Filter theo quarter

```bash
# Alphas cho Q4
cat output/simulation_results.json | jq -r '
  .results[] 
  | select(.expression | contains("== 4"))
  | [.alpha_id, .sim_data.is.sharpe] 
  | @tsv'
```

## Next Steps

Sau khi review kết quả phase_1:

1. **Identify top performers**: Alphas có Sharpe > threshold
2. **Manual submission**: Submit thủ công các alphas tốt nhất
3. **Parameter tuning**: Điều chỉnh template parameters dựa trên insights
4. **Extend to Phase 2**: Mở rộng với templates khác

## Troubleshooting

### No candidates generated

```bash
# Check template file exists
ls -la ../templates/quarterly_return_reversal.json

# Check field validator
python3 -c "from scripts.research_target import load_target; print(load_target().require_fields_reference())"
```

### Simulation failures

```bash
# Check BRAIN API connection
cd ../scripts
python3 check_quota.py

# Verify .env credentials
cat ../.env | grep BRAIN
```

### Low success rate

- Kiểm tra field validator có đúng không
- Xem error messages trong individual results
- Reduce complexity của expressions (simplify template)

## Related Files

- Template definition: `templates/quarterly_return_reversal.json`
- Research target: `config/research_target.json`
- Field reference: `references/wq_glb_topdiv3000_delay1_data_fields.json`

## Notes

- **Auto-submit bị DISABLE**: Phase 1 chỉ simulate, không tự động submit
- Template này tương tự các alpha price-reversal với `-ts_delta(close, N)` nhưng có thêm quarter regime filter
- Các template reversal dạng này đã được sử dụng rộng rãi trong các ví dụ BRAIN công khai
