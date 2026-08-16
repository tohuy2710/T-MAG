# Debugging HTTP 400 Error

## Vấn đề

Tất cả expressions đều bị reject với `status_code=400` và cùng một `body_hash=3287bede0488`.

## Nguyên nhân có thể

### 1. Expressions quá giống nhau (Most Likely)

BRAIN có cơ chế detect duplicate hoặc similar alphas. Các expressions từ Bước 2 rất giống nhau:
```python
ts_rank(short_term_price_change_2, 3) * (1 - ts_rank(returns, 5))
ts_rank(short_term_price_change_2, 3) * (1 - ts_rank(returns, 10))
ts_rank(short_term_price_change_2, 3) * (1 - ts_rank(returns, 20))
```

→ Chỉ khác nhau parameter, logic giống hệt nhau.

### 2. Settings format không đúng

Có thể một số settings field không được BRAIN chấp nhận trong format hiện tại.

### 3. Rate limiting

Submit quá nhiều requests cùng lúc có thể trigger rate limit.

## Giải pháp đề xuất

### Giải pháp 1: Test với expression hoàn toàn khác biệt

```bash
cd /home/tohuy2710/T-MAG/phase_1_plus

# Test với expression đơn giản
echo "rank(close)" > test_simple.txt
python3 phase_1_plus_sim.py --file test_simple.txt --batch-size 1
```

Nếu cái này work → vấn đề là expressions của bước 2 quá similar.

### Giải pháp 2: Chạy Bước 4 thay vì Bước 2

Bước 4 có logic hoàn toàn khác biệt, ít khả năng bị reject:

```bash
python3 phase_1_plus_sim.py --step 4 --batch-size 10 --max-concurrent 2
```

### Giải pháp 3: Giảm concurrency và batch size

```bash
python3 phase_1_plus_sim.py --step 2 --batch-size 3 --max-concurrent 1
```

Chạy từng expression một để tránh rate limit.

### Giải pháp 4: Kiểm tra error message chi tiết

Thêm logging để capture error response body:

1. Mở file `../scripts/brain_api.py`
2. Tìm dòng: `logger.debug("POST error body url=%s body=%s", url, resp.text[:1000])`
3. Thêm ngay sau đó: `print(f"BRAIN ERROR BODY: {resp.text[:500]}")`
4. Chạy lại simulation

Hoặc set logging level:
```bash
export BRAIN_LOG_LEVEL=DEBUG
python3 phase_1_plus_sim.py --step 2 --batch-size 1
```

## Khuyến nghị ngay

**Chạy Bước 4 trước** vì:
- Logic hoàn toàn khác biệt (divergence, spike, fundamental, analyst)
- Ít khả năng duplicate detection
- Tiềm năng alpha cao nhất

```bash
python3 phase_1_plus_sim.py --step 4 --batch-size 10 --max-concurrent 2 --top 15
```

Nếu Bước 4 work → vấn đề confirm là Bước 2 expressions quá similar.

## Alternative: Modify expressions Bước 2

Thay vì submit tất cả 16 expressions của Bước 2, chỉ submit một vài representative:

```bash
# Tạo file filtered
cat alphas_4steps_cmf.txt | grep -A 1 "CMF_window=3, Reversal_window=5" > step2_filtered.txt
cat alphas_4steps_cmf.txt | grep -A 1 "CMF_window=10, Reversal_window=20" >> step2_filtered.txt
cat alphas_4steps_cmf.txt | grep -A 1 "CMF_window=22, Reversal_window=60" >> step2_filtered.txt

# Simulate filtered
python3 phase_1_plus_sim.py --file step2_filtered.txt --batch-size 3
```

## Temporary Workaround

Nếu vẫn gặp lỗi, có thể submit manual trên BRAIN UI:
1. Mở BRAIN platform
2. Tạo alpha mới
3. Copy 1-2 expressions tốt nhất từ file `alphas_4steps_cmf.txt`
4. Verify settings: GLB / TOPDIV3000 / Delay 1 / SUBINDUSTRY neutralization
5. Run simulation manually

## Next Action

**Hãy thử:**
```bash
cd /home/tohuy2710/T-MAG/phase_1_plus
python3 phase_1_plus_sim.py --step 4 --batch-size 10 --max-concurrent 2 --top 15
```

Nếu step 4 vẫn bị lỗi → Vấn đề là ở settings hoặc rate limit, cần debug sâu hơn.

Nếu step 4 work → Confirm vấn đề là step 2 expressions quá similar, ta có thể:
- Skip step 2
- Hoặc chỉ chọn 3-4 expressions đại diện từ step 2
- Focus vào step 3 và step 4 (có logic phong phú hơn)
