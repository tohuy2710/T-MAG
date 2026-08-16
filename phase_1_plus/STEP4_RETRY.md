# Step 4 Retry - Với Cookie Mới

## Status

✅ **Đang chạy**: Mô phỏng lại 64 alphas Bước 4

🔄 **Lý do retry**: Cookie hết hạn trong lần chạy trước

⏱️ **Thời gian ước tính**: ~20-30 phút

📊 **Config**:
- 64 alphas (Bước 4 - Logic Refactor)
- Batch size: 3 (3 alphas cùng lúc)
- Max concurrent: 3
- Log: `step4_new.log`

## Bước 4 Categories

### 4.1: Money Flow Divergence (24 alphas)
- Price-CMF Divergence
- Weighted Divergence
- Windows: 10, 20, 60
- Groups: industry, subindustry

### 4.2: CMF Momentum + Reversal (8 alphas)
- Kết hợp động lượng CMF và đảo chiều giá

### 4.3: CMF Spike Detection (8 alphas)
- Z-score CMF × Volume anomaly

### 4.4: CMF + Fundamentals (8 alphas)
- CMF × Low Accruals
- CMF × Asset Turnover Delta

### 4.5: CMF + Analyst (4 alphas)
- CMF × Analyst revisions
- CMF × EPS estimates

### 4.6: Cross-sectional Momentum (6 alphas)
- Momentum chéo của CMF

### 4.7: Mean Reversion (4 alphas)
- CMF oversold strategy

### 4.8: Multi-timeframe Consensus (2 alphas)
- Consensus qua nhiều khung thời gian

## Theo dõi

```bash
cd /home/tohuy2710/T-MAG/phase_1_plus

# Monitor script
./monitor_step4.sh

# Xem log realtime
tail -f step4_new.log

# Check tiến độ
grep -c "Batch simulate stream complete" step4_new.log
```

## Tại sao Bước 4 quan trọng?

**Logic hoàn toàn mới** - Khác hẳn với Bước 2 & 3:
- Bước 2: Chỉ thay đổi parameters
- Bước 3: Thêm operators (rank, neutralize)
- **Bước 4**: Logic mới → Tiềm năng alpha cao nhất!

**So sánh với kết quả hiện có:**
- Bước 2 & 3 best: Sharpe 1.93, Fitness 0.86
- Bước 4 target: Sharpe > 2.0, Fitness > 1.0?

## Kết quả mong đợi

### Scenario tốt:
- 20-30 alphas thành công (30-50%)
- Một vài alphas có fitness > 1.0
- Logic divergence hoặc spike detection hoạt động

### Scenario xấu:
- Tất cả lỗi như lần trước
- → Expressions quá phức tạp cho BRAIN
- → Cần đơn giản hóa

## Nếu vẫn lỗi toàn bộ

**Plan B**: Đơn giản hóa Bước 4
1. Bỏ weighted variants (giữ basic only)
2. Bỏ các toán tử phức tạp (ts_stddev, z-score)
3. Chỉ giữ logic đơn giản nhất

**Plan C**: Dùng kết quả Bước 2 & 3
- Đã có 105 alphas thành công
- TOP 10 có Sharpe ~1.9, Fitness ~0.85
- Đủ tốt để submit

## Sau khi xong

### Check kết quả:
```bash
cd /home/tohuy2710/T-MAG/phase_1_plus

# Tổng quan
cat output/simulation_results.json | jq '.results | group_by(.step) | map({step: .[0].step, complete: map(select(.status=="COMPLETE")) | length, total: length})'

# TOP Step 4
cat output/simulation_results.json | jq '.results[] | select(.step==4 and .status=="COMPLETE")' | jq -s 'sort_by(-.sim_data.is.fitness) | .[0:10]'
```

### So sánh Step 2, 3, 4:
```bash
# Best từ mỗi bước
for step in 2 3 4; do
  echo "=== STEP $step ==="
  cat output/simulation_results.json | jq ".results[] | select(.step==$step and .status==\"COMPLETE\")" | jq -s 'sort_by(-.sim_data.is.fitness) | .[0] | {alpha_id, sharpe: .sim_data.is.sharpe, fitness: .sim_data.is.fitness, description}'
done
```

---

**Đang chạy... Đợi kết quả sau ~20-30 phút! 🤞**

Created: 2026-08-16 15:24
