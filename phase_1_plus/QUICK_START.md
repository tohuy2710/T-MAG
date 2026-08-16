# Phase 1 Plus - Quick Start Guide

## Quy trình nhanh: 3 bước để tối ưu Alpha

### Bước 1: Sinh expressions (đã hoàn thành ✓)

```bash
python3 alpha_optimizer_4steps.py
```

**Kết quả**: File `alphas_4steps_cmf.txt` với 206 expressions đã được tạo.

---

### Bước 2: Chạy mô phỏng

#### Option A: Mô phỏng toàn bộ (khuyên dùng cho lần đầu)
```bash
python3 phase_1_plus_sim.py --batch-size 15 --max-concurrent 3
```

#### Option B: Mô phỏng từng bước riêng lẻ
```bash
# Chỉ Bước 2 (16 expressions - nhanh nhất)
python3 phase_1_plus_sim.py --step 2 --batch-size 10

# Chỉ Bước 3 (126 expressions)
python3 phase_1_plus_sim.py --step 3 --batch-size 20 --max-concurrent 5

# Chỉ Bước 4 (64 expressions)
python3 phase_1_plus_sim.py --step 4 --batch-size 15 --max-concurrent 3
```

**Thời gian ước tính**:
- Bước 2: ~5-10 phút
- Bước 3: ~30-45 phút
- Bước 4: ~20-30 phút
- Toàn bộ: ~1-1.5 giờ

---

### Bước 3: Xem kết quả

#### Xem tổng quan
```bash
cat output/simulation_results.json | jq '.results[] | select(.status=="COMPLETE") | {alpha_id, sharpe: .sim_data.is.sharpe, fitness: .sim_data.is.fitness, step}' | head -20
```

#### Xem top performers (tự động hiển thị sau khi mô phỏng)
Hoặc xem lại:
```bash
python3 -c "
import json
with open('output/simulation_results.json') as f:
    data = json.load(f)
    results = [r for r in data['results'] if r.get('status') == 'COMPLETE']
    sorted_results = sorted(results, key=lambda x: x.get('sim_data', {}).get('is', {}).get('fitness', 0), reverse=True)
    
    print('\\nTOP 10 PERFORMERS:\\n')
    for i, r in enumerate(sorted_results[:10], 1):
        alpha_id = r['alpha_id']
        fitness = r['sim_data']['is']['fitness']
        sharpe = r['sim_data']['is']['sharpe']
        step = r.get('step', '?')
        print(f'{i}. {alpha_id} | Step {step} | Fitness={fitness:.3f} | Sharpe={sharpe:.3f}')
"
```

#### Xem chi tiết alpha cụ thể
```bash
cat output/individual/{alpha_id}.json | jq .
```

---

## Ví dụ thực tế

### Scenario 1: Test nhanh Bước 2 trước

```bash
# Chạy mô phỏng bước 2 (parameter sweeping)
python3 phase_1_plus_sim.py --step 2 --batch-size 10

# Nếu kết quả tốt, tiếp tục bước 3
python3 phase_1_plus_sim.py --step 3 --batch-size 20 --max-concurrent 5
```

**Lý do**: Bước 2 ít expressions nhất (16), nhanh để test framework hoạt động.

---

### Scenario 2: Chạy toàn bộ một lượt

```bash
# Chuẩn bị: kiểm tra quota
cd ../scripts
python3 check_quota.py

# Quay lại phase_1_plus
cd ../phase_1_plus

# Chạy toàn bộ với settings tối ưu
nohup python3 phase_1_plus_sim.py --batch-size 20 --max-concurrent 5 --top 20 > simulation.log 2>&1 &

# Theo dõi progress
tail -f simulation.log
```

**Lý do**: Chạy background, tự động lưu log, không lo bị disconnect.

---

### Scenario 3: Focus vào Logic Refactor (Bước 4)

```bash
# Chỉ chạy bước 4 - các alpha hoàn toàn mới
python3 phase_1_plus_sim.py --step 4 --batch-size 15 --max-concurrent 4 --top 15
```

**Lý do**: Bước 4 có nhiều ý tưởng sáng tạo nhất, tiềm năng alpha cao.

---

## Hiểu kết quả

### Metrics quan trọng

| Metric | Ý nghĩa | Giá trị tốt |
|--------|---------|-------------|
| **Fitness** | Tổng hợp performance | > 1.0 (khả quan), > 1.5 (tốt), > 2.0 (xuất sắc) |
| **Sharpe** | Risk-adjusted return | > 1.5 (tốt), > 2.0 (xuất sắc) |
| **Turnover** | Tần suất giao dịch | 0.05-0.20 (optimal), < 0.05 (quá thấp), > 0.30 (chi phí cao) |
| **Returns** | Return tuyệt đối | > 0.01 (1% yearly return scaled) |

### Ví dụ output tốt
```
✓ pwNkj2ag | sharpe=2.15 fitness=1.85 turnover=0.0850
```
→ Alpha này có sharpe và fitness cao, turnover hợp lý.

### Ví dụ output cần cân nhắc
```
✓ xyz123 | sharpe=0.85 fitness=0.42 turnover=0.3500
```
→ Sharpe/fitness thấp, turnover cao → không tối ưu.

---

## Bước tiếp theo sau khi có kết quả

### 1. Phân tích top performers
```bash
# Export top 10 alpha IDs
python3 -c "
import json
with open('output/simulation_results.json') as f:
    data = json.load(f)
    results = [r for r in data['results'] if r.get('status') == 'COMPLETE']
    sorted_results = sorted(results, key=lambda x: x.get('sim_data', {}).get('is', {}).get('fitness', 0), reverse=True)
    
    for r in sorted_results[:10]:
        print(r['alpha_id'])
" > top_10_alpha_ids.txt

cat top_10_alpha_ids.txt
```

### 2. Submit alpha tốt nhất lên BRAIN (manual)
1. Mở BRAIN UI
2. Tạo alpha mới
3. Paste expression từ top performer
4. Verify settings: GLB / TOPDIV3000 / Delay 1 / Country neutralization
5. Run simulation để confirm
6. Submit nếu kết quả khớp

### 3. Phân tích pattern
- Bước nào cho kết quả tốt nhất? (2, 3, hay 4?)
- Logic nào hiệu quả? (Divergence, Momentum, Spike, Fundamental?)
- Group nào tốt hơn? (industry vs subindustry?)

### 4. Tạo iteration tiếp theo
Dựa trên insights từ top performers, điều chỉnh `alpha_optimizer_4steps.py`:
- Thêm parameter combinations mới
- Thử logic mới
- Kết hợp các alpha tốt

---

## Troubleshooting nhanh

### Lỗi: BRAIN API connection
```bash
# Kiểm tra .env
cat ../.env | grep BRAIN

# Test connection
cd ../scripts
python3 -c "from brain_api import BrainClient; c = BrainClient(); c.connect(); print('✓ Connected')"
```

### Lỗi: Quota hết
```bash
cd ../scripts
python3 check_quota.py
```
→ Nếu quota thấp, chờ hoặc giảm số lượng simulations.

### Mô phỏng chậm
- Tăng `--max-concurrent` (5-7)
- Giảm `--batch-size` nếu có timeout
- Chạy background với `nohup ... &`

### Kết quả không tải được
```bash
# Kiểm tra file tồn tại
ls -lh output/

# Kiểm tra JSON valid
python3 -c "import json; json.load(open('output/simulation_results.json')); print('✓ Valid JSON')"
```

---

## Tips & Tricks

### Tip 1: Chạy nhiều processes song song
```bash
# Terminal 1: Bước 2
python3 phase_1_plus_sim.py --step 2 --batch-size 10

# Terminal 2: Bước 4
python3 phase_1_plus_sim.py --step 4 --batch-size 15 --max-concurrent 3
```

### Tip 2: Lọc expressions trước khi simulate
```bash
# Chỉ lấy expressions có group_neutralize
grep "group_neutralize" alphas_4steps_cmf.txt > alphas_filtered.txt

# Simulate file filtered
python3 phase_1_plus_sim.py --file alphas_filtered.txt
```

### Tip 3: So sánh với baseline
```bash
# Simulate baseline (template gốc)
echo "ts_rank(short_term_price_change_2, 3) * (1 - ts_rank(returns, 20))" > baseline.txt
python3 phase_1_plus_sim.py --file baseline.txt --batch-size 1
```

---

## Câu hỏi thường gặp

**Q: Bao nhiêu expressions là đủ?**
A: 200+ expressions là phù hợp. Nhiều hơn cũng tốt nhưng mất thời gian simulate.

**Q: Bước nào quan trọng nhất?**
A: Bước 4 (Logic Refactor) thường cho alpha tốt nhất vì thay đổi logic hoàn toàn. Nhưng nên chạy cả 4 bước để so sánh.

**Q: Có cần submit tất cả alpha tốt không?**
A: Không. Chỉ submit 3-5 alpha tốt nhất. Quá nhiều alpha tương tự không tốt.

**Q: Làm sao biết settings nào tốt nhất (Bước 1)?**
A: Bước 1 cần test manual trên BRAIN UI. Chạy 1 alpha tốt với các settings khác nhau, ghi lại kết quả.

**Q: Kết quả simulation có khớp với BRAIN UI không?**
A: Nên khớp hoặc rất gần. Nếu chênh lệch lớn, kiểm tra lại settings.

---

## Tổng kết

1. **Đã sinh**: 206 expressions ✓
2. **Tiếp theo**: Chạy mô phỏng theo 1 trong 3 scenarios
3. **Mục tiêu**: Tìm top 10-20 performers
4. **Hành động**: Submit alpha tốt nhất lên BRAIN

**Good luck! 🚀**
