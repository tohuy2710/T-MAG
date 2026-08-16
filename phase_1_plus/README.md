# Phase 1 Plus: 4-Step Alpha Optimization Framework

## Tổng quan

Phase 1 Plus triển khai quy trình tối ưu Alpha theo 4 bước tuần tự, từ template gốc đến các biến thể phức tạp.

### Template Gốc

```
ts_rank(short_term_price_change_2, 3) * (1 - ts_rank(returns, 20))
```

**Logic kinh tế**: Bắt đáy cổ phiếu quá bán dựa trên xác nhận dòng tiền ngắn hạn (Chaikin Money Flow - CMF).

**Target Data Field**: `short_term_price_change_2` (CMF indicator)

**Default Settings**:
- Region: GLB
- Universe: TOPDIV3000
- Delay: 1
- Neutralization: Subindustry (valid options: SLOW, FAST, SLOW_AND_FAST, SUBINDUSTRY, CROWDING)
- Decay: 10
- Truncation: 0.08
- Pasteurization: On
- Unit Handling: Verify
- NaN Handling: On

---

## 4 Bước Tối Ưu

### BƯỚC 1: CHỈNH SETTINGS (System Configuration Tuning)

**Mục đích**: Tối ưu performance bằng cách thay đổi cấu hình hệ thống trên giao diện BRAIN.

**Thay đổi**:
- **Neutralization**: subindustry → slow → fast → slow_and_fast → crowding
- **Decay**: 5, 7, 10, 15, 20
- **Truncation**: 0.05, 0.08, 0.10, 0.12

**Lưu ý**: Bước này không thay đổi expression code, chỉ điều chỉnh settings trên UI.

---

### BƯỚC 2: CHỈNH PARAM TRONG EXPR (Parameter Sweeping)

**Mục đích**: Giữ nguyên cấu trúc logic, tìm tham số lookback window tối ưu.

**Thay đổi**:
- **CMF Window**: 3, 5, 10, 22 ngày
- **Reversal Window**: 5, 10, 20, 60 ngày

**Ví dụ expressions**:
```python
# CMF=3, Reversal=20 (gốc)
ts_rank(short_term_price_change_2, 3) * (1 - ts_rank(returns, 20))

# CMF=5, Reversal=10
ts_rank(short_term_price_change_2, 5) * (1 - ts_rank(returns, 10))

# CMF=10, Reversal=60
ts_rank(short_term_price_change_2, 10) * (1 - ts_rank(returns, 60))
```

**Tổng số biến thể**: 4 × 4 = 16 expressions

---

### BƯỚC 3: LỒNG THÊM TOÁN TỬ HỢP LỆ (Operator Nesting & Normalization)

**Mục đích**: Chuẩn hóa phân phối tín hiệu và điều chỉnh rủi ro bằng các toán tử.

**Các kỹ thuật lồng**:

#### 3.1: Rank Normalization
```python
# Chuẩn hóa phân phối uniform
rank(ts_rank(short_term_price_change_2, 5) * (1 - ts_rank(returns, 20)))
```

#### 3.2: Group Rank
```python
# Rank trong nhóm ngành
group_rank(ts_rank(short_term_price_change_2, 5) * (1 - ts_rank(returns, 20)), subindustry)
```

#### 3.3: Group Neutralize
```python
# Triệt tiêu yếu tố ngành
group_neutralize(ts_rank(short_term_price_change_2, 5) * (1 - ts_rank(returns, 20)), industry)
```

#### 3.4: Risk Adjustment
```python
# Điều chỉnh rủi ro - chia cho volatility
group_neutralize(
    (ts_rank(short_term_price_change_2, 5) * (1 - ts_rank(returns, 20))) / (ts_stddev(returns, 20) + 1e-6),
    industry
)
```

#### 3.5: Dual Rank
```python
# Rank từng vế riêng biệt
group_neutralize(
    rank(ts_rank(short_term_price_change_2, 5)) * rank(1 - ts_rank(returns, 20)),
    subindustry
)
```

#### 3.6: Signal Smoothing
```python
# Làm mượt tín hiệu
group_neutralize(
    ts_decay_linear(ts_rank(short_term_price_change_2, 5) * (1 - ts_rank(returns, 20)), 5),
    industry
)
```

**Tổng số biến thể**: ~150+ expressions (3 CMF windows × 3 Reversal windows × 2 groups × 6 techniques)

---

### BƯỚC 4: PHÁ LOGIC (Logic Refactor & Multi-Factor Fusion)

**Mục đích**: Thay đổi hoàn toàn logic gốc để khám phá nguồn Alpha mới.

#### 4.1: Money Flow Divergence (Phân kỳ dòng tiền - giá)
```python
# Giá tăng nhưng CMF giảm → Tín hiệu phân kỳ âm
group_neutralize(ts_rank(close, 20) - ts_rank(short_term_price_change_2, 20), industry)

# Weighted divergence
group_neutralize(
    (ts_rank(vwap, 20) - ts_rank(short_term_price_change_2, 20)) * ts_mean(short_term_price_change_2, 10),
    subindustry
)
```

#### 4.2: CMF Momentum + Reversal Combo
```python
# Động lượng dòng tiền kết hợp đảo chiều giá
group_neutralize(
    ts_mean(short_term_price_change_2, 5) * (1 - ts_rank(returns, 20)),
    industry
)
```

#### 4.3: CMF Spike Detection (Đột biến dòng tiền)
```python
# Z-score của CMF × Volume anomaly
group_neutralize(
    ((short_term_price_change_2 - ts_mean(short_term_price_change_2, 20)) / (ts_stddev(short_term_price_change_2, 20) + 1e-6)) * (volume / (adv20 + 1e-6)),
    subindustry
)
```

#### 4.4: CMF + Fundamentals (Dòng tiền + Chất lượng cơ bản)
```python
# CMF × Low Accruals (chất lượng cao)
group_neutralize(
    short_term_price_change_2 * (1 - ts_rank(accruals_percentage_earnings, 126)),
    industry
)

# CMF × Asset Turnover Delta
group_neutralize(
    short_term_price_change_2 * ts_delta(asset_turnover_ratio_2, 4),
    subindustry
)
```

#### 4.5: CMF + Analyst Expectations
```python
# CMF × Analyst revisions
group_neutralize(
    short_term_price_change_2 * analyst_revisions_score_2,
    industry
)

# CMF × EPS estimate changes
group_neutralize(
    short_term_price_change_2 * avg_estimate_change_pct_current_year_eps_14d_long,
    subindustry
)
```

#### 4.6: CMF Cross-sectional Momentum
```python
# Momentum chéo của CMF
group_neutralize(
    rank(ts_delta(short_term_price_change_2, 10)) * rank(ts_rank(short_term_price_change_2, 10)),
    industry
)
```

#### 4.7: CMF Mean Reversion (Extreme)
```python
# Bắt cổ phiếu oversold theo CMF
group_neutralize(-ts_rank(short_term_price_change_2, 60), subindustry)
```

#### 4.8: Multi-timeframe CMF Consensus
```python
# Consensus qua nhiều khung thời gian
group_neutralize(
    rank(ts_rank(short_term_price_change_2, 5)) + 
    rank(ts_rank(short_term_price_change_2, 10)) + 
    rank(ts_rank(short_term_price_change_2, 20)),
    industry
)
```

**Tổng số biến thể**: ~200+ expressions (8 categories × multiple parameter combinations)

---

## Sử dụng

### 1. Sinh expressions

```bash
cd /home/tohuy2710/T-MAG/phase_1_plus
python3 alpha_optimizer_4steps.py
```

**Output**: File `alphas_4steps_cmf.txt` chứa tất cả expressions từ 4 bước.

### 2. Mô phỏng trên BRAIN

#### Mô phỏng tất cả
```bash
python3 phase_1_plus_sim.py
```

#### Mô phỏng chỉ 1 bước cụ thể
```bash
# Chỉ bước 2 (Parameter Sweeping)
python3 phase_1_plus_sim.py --step 2

# Chỉ bước 3 (Operator Nesting)
python3 phase_1_plus_sim.py --step 3

# Chỉ bước 4 (Logic Refactor)
python3 phase_1_plus_sim.py --step 4
```

#### Tùy chỉnh batch và concurrency
```bash
python3 phase_1_plus_sim.py --batch-size 20 --max-concurrent 5
```

#### Hiển thị nhiều top performers hơn
```bash
python3 phase_1_plus_sim.py --top 20
```

### 3. Xem kết quả

**File tổng hợp**: `output/simulation_results.json`

**Chi tiết từng alpha**: `output/individual/{alpha_id}.json`

**Top performers** sẽ hiển thị trực tiếp trên terminal sau khi mô phỏng hoàn thành.

---

## Cấu trúc thư mục

```
phase_1_plus/
├── README.md                        # Tài liệu này
├── alpha_optimizer_4steps.py        # Script sinh expressions theo 4 bước
├── phase_1_plus_sim.py              # Script mô phỏng
├── alphas_4steps_cmf.txt            # Output: danh sách expressions
├── output/
│   ├── simulation_results.json      # Tổng hợp kết quả
│   └── individual/                  # Kết quả chi tiết từng alpha
│       ├── {alpha_id_1}.json
│       ├── {alpha_id_2}.json
│       └── ...
└── (legacy files...)
```

---

## Metrics đánh giá

Khi xem xét kết quả mô phỏng, ưu tiên theo thứ tự:

1. **Fitness** (tổng hợp): Fitness càng cao càng tốt (thường > 1.0 là khả quan)
2. **Sharpe Ratio**: Sharpe > 1.5 là tốt, > 2.0 là xuất sắc
3. **Turnover**: Turnover thấp hơn tốt hơn (chi phí giao dịch thấp)
4. **Returns**: Return dương và ổn định

**Lưu ý**: Các alpha có fitness cao nhất thường có balance tốt giữa return và risk-adjusted metrics.

---

## Best Practices

### Khi sinh expressions

1. **Bắt đầu từ bước 2**: Nếu chưa chắc chắn, hãy tập trung vào parameter sweeping trước.
2. **Tăng dần độ phức tạp**: Chỉ chuyển sang bước 3-4 khi bước trước đã có kết quả khả quan.
3. **Giới hạn số lượng**: Nếu sinh quá nhiều, hãy filter theo bước (`--step`) khi mô phỏng.

### Khi mô phỏng

1. **Batch size hợp lý**: 10-20 là tốt, tránh batch quá lớn gây timeout.
2. **Max concurrent**: Tăng lên 5-7 nếu server BRAIN cho phép.
3. **Monitor quota**: Kiểm tra quota BRAIN trước khi chạy batch lớn.

### Sau khi có kết quả

1. **Xem xét top 10-20**: Đừng chỉ nhìn #1, xem xét top performers để tìm pattern.
2. **So sánh giữa các bước**: Bước nào cho kết quả tốt nhất?
3. **Kết hợp insights**: Có thể kết hợp logic từ nhiều alpha tốt thành 1 alpha mới.

---

## Troubleshooting

### File không tồn tại
```
✗ File không tồn tại: alphas_4steps_cmf.txt
```
**Giải pháp**: Chạy `python3 alpha_optimizer_4steps.py` để sinh file.

### Không có candidates nào
```
✗ Không có candidates nào được load
```
**Giải pháp**: Kiểm tra filter `--step`, có thể file không có alphas từ bước đó.

### BRAIN API connection failed
**Giải pháp**: 
1. Kiểm tra file `.env` có đủ credentials
2. Kiểm tra quota bằng `python3 ../scripts/check_quota.py`
3. Kiểm tra network connection

### Simulation timeout
**Giải pháp**: Giảm `--batch-size` hoặc tăng timeout trong `brain_api.py`.

---

## Tham khảo

- **Template gốc**: `/phase_1_plus/alphas_cmf_short_term_price_change_2.txt`
- **BRAIN API**: `/scripts/brain_api.py`
- **Phase 1 reference**: `/phase_1/README_PHASE_1.md`
- **Data fields**: `/references/wq_glb_topdiv3000_delay1_data_fields.json`

---

## Contact & Support

Nếu có câu hỏi hoặc gặp vấn đề, vui lòng tham khảo:
- Phase 1 framework documentation
- BRAIN API documentation
- WorldQuant BRAIN platform help

---

**Chúc bạn tìm được nhiều Alpha tốt! 🚀**
