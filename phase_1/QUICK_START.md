# Phase 1 - Quick Start Guide

## Mô phỏng Quarterly Return Reversal

### 1. Setup nhanh

```bash
cd /home/tohuy2710/T-MAG/phase_1
```

### 2. Run mô phỏng mặc định

```bash
python3 phase_1_sim.py
```

Output mong đợi:
- Generate ~20 candidates từ template
- Simulate tất cả candidates
- Hiển thị top 10 performers
- Lưu kết quả vào `output/`

### 3. Run với nhiều candidates hơn

```bash
python3 phase_1_sim.py --max-per-template 50 --batch-size 20
```

### 4. Xem kết quả

```bash
# Summary
cat output/simulation_results.json | jq '{
  total: .total_simulated,
  passed: .passed,
  failed: .failed
}'

# Top 5 by Sharpe
cat output/simulation_results.json | jq -r '
  .results[] 
  | select(.status=="COMPLETE") 
  | [.alpha_id, .sim_data.is.sharpe, .sim_data.is.fitness, .sim_data.is.turnover] 
  | @tsv' | sort -k2 -rn | head -5
```

### 5. Examine individual results

```bash
ls -lh output/individual/
cat output/individual/<alpha_id>.json | jq .
```

## Parameters chính

| Flag | Default | Description |
|------|---------|-------------|
| `--batch-size` | 10 | Số candidates per batch |
| `--max-per-template` | 20 | Max candidates generate |
| `--max-concurrent` | 3 | Parallel simulations |
| `--show-top` | 10 | Top N performers hiển thị |

## Template info

```bash
cat ../templates/quarterly_return_reversal.json | jq '{
  id: .template_id,
  template: .template,
  placeholders: .placeholders | keys
}'
```

## Lưu ý

- **Không tự động submit**: Phase 1 chỉ simulate
- Review kết quả trước khi submit manually
- Environment: GLB / TOPDIV3000 / Delay 1
