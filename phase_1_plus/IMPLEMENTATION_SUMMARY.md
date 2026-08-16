# Phase 1 Plus: Implementation Summary

## ✅ Hoàn thành

Đã triển khai thành công framework tối ưu Alpha theo 4 bước cho template CMF (Chaikin Money Flow).

### Files đã tạo

1. **alpha_optimizer_4steps.py** - Script sinh expressions
   - Tạo 206 biến thể từ template gốc
   - Phân chia rõ ràng theo 4 bước

2. **phase_1_plus_sim.py** - Script mô phỏng
   - Batch simulation với BRAIN API
   - Hỗ trợ filter theo bước
   - Tự động lưu kết quả

3. **README.md** - Documentation đầy đủ
   - Giải thích chi tiết 4 bước
   - Ví dụ expressions cho mỗi bước
   - Hướng dẫn sử dụng

4. **QUICK_START.md** - Hướng dẫn nhanh
   - 3 scenarios sử dụng phổ biến
   - Troubleshooting tips
   - Best practices

5. **alphas_4steps_cmf.txt** - Output expressions
   - 206 expressions đã được sinh
   - Có comments mô tả cho mỗi expression

## 📊 Thống kê Expressions

### Tổng quan
- **Tổng số**: 206 expressions
- **Bước 2 (Parameter Sweeping)**: 16 expressions
- **Bước 3 (Operator Nesting)**: 126 expressions  
- **Bước 4 (Logic Refactor)**: 64 expressions

### Phân loại Bước 4

| Category | Số lượng | Mô tả |
|----------|----------|-------|
| Money Flow Divergence | 24 | Phân kỳ giữa giá và CMF |
| Momentum + Reversal | 8 | Kết hợp động lượng CMF và đảo chiều giá |
| CMF Spike Detection | 8 | Đột biến dòng tiền + volume anomaly |
| CMF + Fundamentals | 8 | Kết hợp CMF với chất lượng cơ bản |
| CMF + Analyst | 4 | Kết hợp CMF với kỳ vọng analyst |
| Cross-sectional Momentum | 6 | Momentum chéo của CMF |
| Mean Reversion | 4 | CMF oversold mean reversion |
| Multi-timeframe Consensus | 2 | Consensus qua nhiều khung thời gian |

## 🎯 Template Gốc

```
ts_rank(short_term_price_change_2, 3) * (1 - ts_rank(returns, 20))
```

**Logic**: Bắt đáy cổ phiếu quá bán dựa trên xác nhận dòng tiền ngắn hạn (CMF - Chaikin Money Flow).

**Target**: `short_term_price_change_2` (GLB / TOPDIV3000 / Delay 1)

## 🔧 4 Bước Tối Ưu

### Bước 1: Settings Tuning (80 biến thể)
Tối ưu cấu hình hệ thống trên BRAIN UI:
- Neutralization: SLOW, FAST, SLOW_AND_FAST, SUBINDUSTRY, CROWDING
- Decay: 5, 7, 10, 15, 20
- Truncation: 0.05, 0.08, 0.10, 0.12

**Lưu ý**: Bước này chỉnh trên giao diện, không sinh expressions mới.

### Bước 2: Parameter Sweeping (16 expressions)
Thay đổi lookback windows:
- CMF window: 3, 5, 10, 22
- Reversal window: 5, 10, 20, 60

**Ví dụ**:
```python
ts_rank(short_term_price_change_2, 5) * (1 - ts_rank(returns, 10))
ts_rank(short_term_price_change_2, 10) * (1 - ts_rank(returns, 60))
```

### Bước 3: Operator Nesting (126 expressions)
Lồng các toán tử chuẩn hóa và điều chỉnh rủi ro:
- `rank()` - Chuẩn hóa phân phối
- `group_rank()` - Rank theo nhóm ngành
- `group_neutralize()` - Triệt tiêu yếu tố ngành
- Risk adjustment - Chia cho volatility
- Dual rank - Rank từng vế riêng
- Signal smoothing - Làm mượt bằng ts_decay_linear

**Ví dụ**:
```python
# Dual rank + neutralize
group_neutralize(
    rank(ts_rank(short_term_price_change_2, 5)) * rank(1 - ts_rank(returns, 20)),
    subindustry
)

# Risk-adjusted
group_neutralize(
    (ts_rank(short_term_price_change_2, 5) * (1 - ts_rank(returns, 20))) / 
    (ts_stddev(returns, 20) + 1e-6),
    industry
)
```

### Bước 4: Logic Refactor (64 expressions)
Thay đổi hoàn toàn logic để tìm Alpha mới:

#### 4.1: Money Flow Divergence (24 expressions)
```python
# Giá tăng nhưng CMF giảm
group_neutralize(ts_rank(close, 20) - ts_rank(short_term_price_change_2, 20), industry)
```

#### 4.2: CMF Momentum + Reversal (8 expressions)
```python
group_neutralize(
    ts_mean(short_term_price_change_2, 5) * (1 - ts_rank(returns, 20)),
    industry
)
```

#### 4.3: CMF Spike Detection (8 expressions)
```python
# Z-score CMF × Volume anomaly
group_neutralize(
    ((short_term_price_change_2 - ts_mean(short_term_price_change_2, 20)) / 
     (ts_stddev(short_term_price_change_2, 20) + 1e-6)) * 
    (volume / (adv20 + 1e-6)),
    subindustry
)
```

#### 4.4: CMF + Fundamentals (8 expressions)
```python
# CMF × Low Accruals (high quality)
group_neutralize(
    short_term_price_change_2 * (1 - ts_rank(accruals_percentage_earnings, 126)),
    industry
)
```

#### 4.5: CMF + Analyst (4 expressions)
```python
group_neutralize(
    short_term_price_change_2 * analyst_revisions_score_2,
    industry
)
```

#### 4.6: Cross-sectional Momentum (6 expressions)
```python
group_neutralize(
    rank(ts_delta(short_term_price_change_2, 10)) * 
    rank(ts_rank(short_term_price_change_2, 10)),
    industry
)
```

#### 4.7: Mean Reversion (4 expressions)
```python
# CMF oversold
group_neutralize(-ts_rank(short_term_price_change_2, 60), subindustry)
```

#### 4.8: Multi-timeframe Consensus (2 expressions)
```python
group_neutralize(
    rank(ts_rank(short_term_price_change_2, 5)) + 
    rank(ts_rank(short_term_price_change_2, 10)) + 
    rank(ts_rank(short_term_price_change_2, 20)),
    industry
)
```

## 🚀 Cách sử dụng

### Quick Start (3 lệnh)

```bash
cd /home/tohuy2710/T-MAG/phase_1_plus

# 1. Sinh expressions (đã hoàn thành ✓)
python3 alpha_optimizer_4steps.py

# 2. Mô phỏng (chọn 1 trong các options)
# Option A: Toàn bộ
python3 phase_1_plus_sim.py --batch-size 15 --max-concurrent 3

# Option B: Chỉ 1 bước (nhanh hơn)
python3 phase_1_plus_sim.py --step 2 --batch-size 10
python3 phase_1_plus_sim.py --step 3 --batch-size 20 --max-concurrent 5  
python3 phase_1_plus_sim.py --step 4 --batch-size 15 --max-concurrent 3

# 3. Xem kết quả
cat output/simulation_results.json | jq '.results[] | select(.status=="COMPLETE") | {alpha_id, sharpe: .sim_data.is.sharpe, fitness: .sim_data.is.fitness, step}' | head -20
```

### Recommended Approach

1. **Test nhanh với Bước 2** (16 expressions - ~5-10 phút)
   ```bash
   python3 phase_1_plus_sim.py --step 2 --batch-size 10
   ```

2. **Nếu kết quả tốt, chạy Bước 4** (64 expressions - ~20-30 phút)
   ```bash
   python3 phase_1_plus_sim.py --step 4 --batch-size 15 --max-concurrent 3
   ```

3. **Sau đó mới chạy Bước 3** (126 expressions - ~30-45 phút)
   ```bash
   python3 phase_1_plus_sim.py --step 3 --batch-size 20 --max-concurrent 5
   ```

**Lý do**: Bước 4 (Logic Refactor) thường cho alpha tốt nhất vì thay đổi logic hoàn toàn.

## 📈 Đánh giá kết quả

### Metrics quan trọng

| Metric | Tốt | Xuất sắc |
|--------|-----|----------|
| Fitness | > 1.0 | > 2.0 |
| Sharpe | > 1.5 | > 2.0 |
| Turnover | 0.05-0.20 | 0.08-0.15 |
| Returns | > 0.01 | > 0.02 |

### Top performers sẽ được hiển thị tự động

Script sẽ in ra:
- Tổng kết (total, success, errors)
- Statistics (avg/max/min cho các metrics)
- Top 10 performers (sorted by fitness)

## 📁 Output Structure

```
phase_1_plus/
├── output/
│   ├── simulation_results.json      # Tổng hợp tất cả
│   └── individual/
│       ├── {alpha_id_1}.json        # Chi tiết từng alpha
│       ├── {alpha_id_2}.json
│       └── ...
```

## 🔍 Troubleshooting

### Nếu gặp lỗi simulation

1. **Kiểm tra BRAIN API connection**
   ```bash
   cd ../scripts
   python3 check_quota.py
   ```

2. **Thử với 1 expression đơn giản**
   ```bash
   echo "rank(close)" > test.txt
   python3 phase_1_plus_sim.py --file test.txt --batch-size 1
   ```

3. **Giảm batch size hoặc concurrency**
   ```bash
   python3 phase_1_plus_sim.py --step 2 --batch-size 5 --max-concurrent 2
   ```

### Nếu simulation quá chậm

- Tăng `--max-concurrent` lên 5-7 (nếu server cho phép)
- Chạy background: `nohup python3 phase_1_plus_sim.py ... > sim.log 2>&1 &`
- Theo dõi: `tail -f sim.log`

## 📝 Next Steps

1. **Chạy simulation** theo recommended approach ở trên
2. **Phân tích top performers** - Bước nào cho kết quả tốt nhất?
3. **Submit lên BRAIN** - Chọn 3-5 alpha tốt nhất để submit manual
4. **Iterate** - Dựa trên insights, điều chỉnh và sinh thêm expressions

## 🎓 Insights & Best Practices

### Từ kinh nghiệm Alpha mining

1. **Bước 4 thường cho alpha tốt nhất** vì thay đổi logic hoàn toàn
2. **Operator nesting quan trọng** - group_neutralize thường cải thiện performance
3. **Risk adjustment cần thiết** - Chia cho volatility giúp tránh cổ phiếu rác
4. **Multi-factor fusion hiệu quả** - Kết hợp CMF với fundamentals/analyst signals

### Common Patterns của Alpha tốt

- **Divergence strategies** hiệu quả trong thị trường GLB
- **Group neutralization** theo subindustry thường tốt hơn industry
- **Moderate turnover** (0.08-0.15) optimal cho chi phí giao dịch
- **Combining signals** từ nhiều time frames cải thiện stability

## ✅ Checklist

- [x] Tạo framework 4 bước
- [x] Sinh 206 expressions
- [x] Tạo simulation script
- [x] Viết documentation đầy đủ
- [x] Tạo quick start guide
- [ ] Chạy simulation (user task)
- [ ] Phân tích kết quả (user task)
- [ ] Submit top performers (user task)

## 📚 References

- Template gốc: `/phase_1_plus/alphas_cmf_short_term_price_change_2.txt`
- BRAIN API: `/scripts/brain_api.py`
- Research target config: `/config/research_target.json`
- Data fields: `/references/wq_glb_topdiv3000_delay1_data_fields.json`

---

**Status**: ✅ Implementation Complete - Ready for Simulation

**Created**: 2026-08-16

**Framework**: T-MAG Phase 1 Plus
