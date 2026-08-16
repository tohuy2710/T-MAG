# 🚀 SIMULATION ĐANG CHẠY (3X NHANH HƠN!)

## Status

✅ **Đang chạy**: 3 alphas SONG SONG cùng lúc

⏱️ **Thời gian ước tính**: ~1-2 giờ (nhanh gấp 3 lần!)

📊 **Breakdown**:
- Tổng: 206 alphas (69 batches x 3 alphas)
- Bước 2 (Parameter Sweeping): 16 alphas
- Bước 3 (Operator Nesting): 126 alphas  
- Bước 4 (Logic Refactor): 64 alphas

## Theo dõi tiến độ

### Cách 1: Script check nhanh
```bash
cd /home/tohuy2710/T-MAG/phase_1_plus
./check_progress.sh
```

### Cách 2: Xem log realtime
```bash
tail -f full_simulation_3x.log
```

### Cách 3: Xem summary
```bash
# Đếm số alphas đã xong
grep -c "Batch simulate stream complete" full_simulation_3x.log

# Xem thành công/lỗi
grep "✓\|✗" full_simulation_3x.log | tail -20
```

## Dừng simulation (nếu cần)

```bash
pkill -f phase_1_plus_sim.py
```

## Sau khi hoàn thành

### 1. Xem kết quả tổng hợp
```bash
cat output/simulation_results.json | jq '.results[] | select(.status=="COMPLETE") | {alpha_id, step, sharpe: .sim_data.is.sharpe, fitness: .sim_data.is.fitness}'
```

### 2. Xem TOP 20 performers
```bash
cat output/simulation_results.json | jq '.results[] | select(.status=="COMPLETE")' | jq -s 'sort_by(-.sim_data.is.fitness) | .[0:20] | .[] | {alpha_id, step, fitness: .sim_data.is.fitness, sharpe: .sim_data.is.sharpe, turnover: .sim_data.is.turnover}'
```

### 3. Xem chi tiết 1 alpha
```bash
cat output/individual/{alpha_id}.json | jq .
```

### 4. Export top performers
```bash
cat output/simulation_results.json | jq -r '.results[] | select(.status=="COMPLETE") | select(.sim_data.is.fitness > 1.0) | .expression' > top_performers.txt
```

## Metrics đánh giá

| Metric | Tốt | Xuất sắc |
|--------|-----|----------|
| **Fitness** | > 1.0 | > 2.0 |
| **Sharpe** | > 1.5 | > 2.0 |
| **Turnover** | 0.05-0.20 | 0.08-0.15 |
| **Returns** | > 0.01 | > 0.02 |

## Phân tích sau khi xong

### Câu hỏi cần trả lời:

1. **Bước nào cho kết quả tốt nhất?**
   - Bước 2: Parameter tuning?
   - Bước 3: Operator nesting?
   - Bước 4: Logic refactor?

2. **Logic nào hiệu quả?**
   - Divergence?
   - Spike detection?
   - CMF + Fundamentals?
   - CMF + Analyst?

3. **Group neutralization nào tốt hơn?**
   - Industry?
   - Subindustry?

### Filter top alphas theo step:

```bash
# Top 5 từ Bước 2
cat output/simulation_results.json | jq '.results[] | select(.step==2 and .status=="COMPLETE")' | jq -s 'sort_by(-.sim_data.is.fitness) | .[0:5]'

# Top 5 từ Bước 3
cat output/simulation_results.json | jq '.results[] | select(.step==3 and .status=="COMPLETE")' | jq -s 'sort_by(-.sim_data.is.fitness) | .[0:5]'

# Top 5 từ Bước 4
cat output/simulation_results.json | jq '.results[] | select(.step==4 and .status=="COMPLETE")' | jq -s 'sort_by(-.sim_data.is.fitness) | .[0:5]'
```

## Submit lên BRAIN

**Chọn 3-5 alpha tốt nhất để submit manual:**

1. Mở https://platform.worldquantbrain.com
2. Tạo alpha mới
3. Copy expression từ top performer
4. Settings:
   - Region: GLB
   - Universe: TOPDIV3000
   - Delay: 1
   - Neutralization: SUBINDUSTRY
   - Decay: 10
   - Truncation: 0.08
5. Run simulation để verify
6. Submit nếu kết quả tốt

## Troubleshooting

### Simulation dừng đột ngột?
```bash
# Check log
tail -50 full_simulation.log

# Restart từ đầu
source ../phase_1/venv/bin/activate
nohup python3 phase_1_plus_sim.py --batch-size 1 --max-concurrent 1 --top 20 > full_simulation_retry.log 2>&1 &
```

### Muốn chạy nhanh hơn?
Hiện tại chạy từng alpha một để tránh lỗi. Nếu muốn nhanh:
```bash
# Rủi ro: có thể bị rate limit
python3 phase_1_plus_sim.py --batch-size 3 --max-concurrent 1 --top 20
```

---

**Để yên cho nó chạy, check lại sau 3-6 giờ! 🎯**
