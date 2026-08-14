# Per-Paper Mining Guide (Per-Chunk Architecture)

## ✅ System Status: Ready!

- **Configuration:** GLB/TOPDIV3000/delay=1 ✓
- **Papers:** 14 papers ready for extraction ✓
- **Templates:** Extraction template ready ✓
- **State:** Fresh start ✓

---

## Quy Trình Làm Việc (Workflow Overview)

```
Mỗi bài báo = 1 Mining Chunk

┌─ ROUND 1 ──────────────────────────────────────────┐
│ Paper 1: alpha_101.pdf                             │
│                                                    │
│ 1. Generate extraction prompt                      │
│ 2. You: Copy → ChatGPT + Paper → Get JSON          │
│ 3. Feed JSON → Tạo templates                       │
│ 4. BREADTH: Mở rộng templates mới → Simulate       │
│ 5. Learn + Save (lessons.json tích luỹ)           │
└─────────────────────────────────────────────────────┘
         ↓
┌─ ROUND 2 ──────────────────────────────────────────┐
│ Paper 2: A股市场的动量反转效应研究                  │
│                                                    │
│ 1. Generate extraction prompt (lessons từ Paper 1) │
│ 2. You: Copy → ChatGPT + Paper → Get JSON          │
│ 3. Feed JSON → Tạo templates mới                   │
│ 4. BREADTH: Mở rộng tất cả templates               │
│           (từ Paper 1 + Paper 2)                  │
│ 5. Learn thêm + Save                              │
└─────────────────────────────────────────────────────┘
         ↓
    ... Repeat cho 12 papers còn lại
```

---

## Bước 1: Tạo Prompt Cho Paper Đầu Tiên

```bash
cd /Volumes/SSD-WDBlue/tohuy/y3s2/wq-modified

# Generate prompt cho Paper 1 (alpha_101.pdf)
python3 scripts/generate_extraction_prompt.py src_001

# Output: _extraction_prompt_src_001.md (đã fill placeholders)
```

**Output sẽ hiển thị:**
```
✓ Extraction prompt generated: _extraction_prompt_src_001.md
  Paper: 101 Formulaic Alphas
  Content: 10000 characters
  File size: 45000 characters
  
  Next step: Copy & paste this .md into ChatGPT/Claude with the paper PDF
  Then save the JSON output and use: ingest_extracted_templates.py
```

---

## Bước 2: Extract Templates với LLM Bên Ngoài

### 2.1 Chuẩn Bị

1. **Mở file prompt:**
   ```bash
   cat _extraction_prompt_src_001.md
   # Hoặc mở trong editor
   ```

2. **Chuẩn Bị Paper PDF:**
   - File: `papers/alpha_101.pdf`
   - Hoặc copy nội dung vào ChatGPT

### 2.2 Dùng ChatGPT/Claude

1. **Vào https://chat.openai.com hoặc https://claude.ai**

2. **Upload hoặc paste:**
   - Paste toàn bộ nội dung `_extraction_prompt_src_001.md`
   - Upload hoặc paste nội dung paper PDF

3. **Claude/ChatGPT sẽ trả JSON** giống như:
   ```json
   [
     {
       "template_id": "alpha1_cross_sectional_rank",
       "description": "Nhân tố cross-sectional dựa trên mối tương quan...",
       "skeleton": "group_rank(-ts_corr(rank(...), ...), {group})",
       "field_pairs": [...],
       "param_ranges": {...},
       "default_settings": {...},
       "tags": ["technical", "volume"],
       "hypothesis": "Giả thuyết: ..."
     },
     {
       "template_id": "alpha4_mean_reversion_volume",
       "description": "...",
       ...
     }
   ]
   ```

4. **Copy toàn bộ JSON** (chỉ phần mảng, không có text khác)

---

## Bước 3: Feed JSON Vào Repo

### 3.1 Lưu JSON File

```bash
# Paste JSON vào file (hoặc dùng editor)
cat > extraction_output.json << 'EOF'
[
  {
    "template_id": "alpha1_cross_sectional_rank",
    ...
  }
]
EOF

# Validate JSON (optional nhưng khuyên dùng)
python3 -m json.tool extraction_output.json > /dev/null && echo "✓ Valid JSON"
```

### 3.2 Ingest Templates

```bash
python3 scripts/ingest_extracted_templates.py extraction_output.json --paper src_001

# Output sẽ hiển thị:
# ======================================================================
# INGEST REPORT
# ======================================================================
#
# ✓ Successful: 2
#   • alpha1_cross_sectional_rank
#   • alpha4_mean_reversion_volume
#
# ======================================================================
# ✓ All templates ingested successfully!
#   2 template(s) ready for mining
# ======================================================================
```

**Các templates sẽ được lưu vào:**
- `templates/alpha1_cross_sectional_rank.json`
- `templates/alpha4_mean_reversion_volume.json`
- Và được tracked trong `papers_registry.json`

---

## Bước 4: Chạy Mining Loop

```bash
# Run mining loop (breadth phase sẽ sử dụng templates mới)
python3 scripts/mining_loop.py

# Hoặc với options:
python3 scripts/mining_loop.py --max-rounds 10 --depth-backend manual
```

**Lần chạy đầu tiên:**
- ❌ SKIP breadth ở đầu (tiết kiệm 4 giờ)
- ✅ Nhảy vào extraction paper 1
- ✅ Breadth với templates mới từ paper 1
- ✅ Learn + Save lessons

**Output:**
```
======================================================================
  WorldQuant BRAIN — Automatic Alpha Discovery System
======================================================================
  Started: 2026-08-13T10:00:00+00:00
  Max rounds: 50
  Keep initial breadth: False
  Target: GLB/TOPDIV3000/delay=1
======================================================================

[breadth] SKIPPED initial breadth phase
         (use --keep-initial-breadth to enable)

[depth] Candidate pool empty. Reading next paper: src_001

[breadth] Building candidates (producer=template)...
[breadth] Generated 18 candidates
[breadth] Simulating batch (18 candidates)...
[breadth] Candidate 1/18: alpha1_cross_sectional_rank → Sharpe=1.523
[breadth] Round 1 complete: 2 ACTIVE, 3 OBSERVE, 13 DISCARD
...
```

---

## Bước 5: Lặp Lại Cho Paper Tiếp Theo

Khi mining loop dừng sau round 1-2 (lessons đã ổn định từ paper 1):

```bash
# Generate prompt cho paper 2
python3 scripts/generate_extraction_prompt.py src_002

# Output: _extraction_prompt_src_002.md
# (Chứa lessons_summary từ paper 1 → LLM sẽ học từ nó)
```

**Lợi ích:**
- LLM thấy templates nào từ paper 1 đã thành công
- LLM sẽ tạo templates tương tự hoặc bổ sung cho paper 2
- Lessons.json tiếp tục tích luỹ

---

## Commands Tóm Tắt

### Toàn Bộ Workflow Cho Một Paper

```bash
# 1. Generate prompt
python3 scripts/generate_extraction_prompt.py src_001

# 2. [Manual] Copy → ChatGPT → Get JSON → Save extraction_output.json

# 3. Ingest templates
python3 scripts/ingest_extracted_templates.py extraction_output.json --paper src_001

# 4. Run mining (tự động chạy breadth với templates mới)
python3 scripts/mining_loop.py --max-rounds 10

# 5. Monitor (optional)
python3 -c "
import json
from pathlib import Path
reg = json.load(open('papers_registry.json'))
for src_id, src in reg['sources'].items():
    print(f'{src_id}: {src.get(\"status\")} - {src.get(\"title\")[:40]}')
"
```

### Chỉ Generate Prompt (Không Chạy Mining)

```bash
python3 scripts/generate_extraction_prompt.py src_002
# Có thể bạn muốn generate prompts cho cả 14 papers trước
```

### Validate JSON Trước Khi Ingest

```bash
python3 -m json.tool extraction_output.json
# Hoặc
python3 scripts/ingest_extracted_templates.py extraction_output.json --paper src_001 --validate
```

---

## Tùy Chọn: Giữ Initial Breadth

Nếu bạn muốn chạy initial breadth (với 31 templates hiện có) trước khi đi vào papers:

```bash
python3 scripts/mining_loop.py --keep-initial-breadth --max-rounds 30
```

**Workflow:**
```
Round 1-3: Initial BREADTH (31 templates cũ) → 4 giờ
Round 4+:  Depth → Paper 1 extract
Round 5+:  BREADTH (31 cũ + 3 mới từ paper 1)
```

**Khi nào dùng:**
- Muốn test initial templates trước
- Có thời gian dư
- Muốn accumulate lessons từ 31 templates

---

## Troubleshooting

### Issue: JSON không hợp lệ từ LLM

**Solution:**
```bash
# Kiểm tra JSON
python3 -m json.tool extraction_output.json

# Sửa lỗi + retry
python3 scripts/ingest_extracted_templates.py extraction_output.json --paper src_001
```

### Issue: Ingest báo lỗi "expand_template produced zero candidates"

**Nguyên nhân:** Trường trong field_pairs không tồn tại hoặc param_ranges không hợp lệ

**Solution:**
```bash
# Check available fields
python3 -c "
import json
fields = json.load(open('references/wq_glb_topdiv3000_delay1_data_fields.json'))
print(f'Total fields: {len(fields)}')
for f in fields[:10]:
    print(f['id'])
"

# Edit template, verify fields exist
# Retry ingest
```

### Issue: Mining loop không detect templates mới

**Solution:**
```bash
# Confirm templates saved
ls -la templates/alpha*.json

# Run mining loop again
python3 scripts/mining_loop.py --max-rounds 5
```

### Issue: Paper PDF không extract được text

**Cause:** Có thể PDF bị scan (image-based)

**Solution:**
- LLM (ChatGPT/Claude) có thể xử lý được PDF images
- Hoặc hãy copy text từ paper thủ công vào prompt
- Edit `_extraction_prompt_src_NNN.md` và paste text vào section {PAPER_CONTENT}

---

## Monitoring Progress

### Xem Papers Status

```bash
python3 -c "
import json
from pathlib import Path

reg = json.load(open('papers_registry.json'))
print(f'Total: {reg[\"stats\"][\"total\"]}, Consumed: {reg[\"stats\"][\"consumed\"]}, Remaining: {reg[\"stats\"][\"remaining\"]}')
print()
for src_id in sorted(reg['sources'].keys()):
    src = reg['sources'][src_id]
    status = src.get('status', 'unknown')
    title = src.get('title', 'N/A')[:40]
    templates = len(src.get('templates_created', []))
    print(f'{src_id}: [{status:15s}] {title:40s} (templates: {templates})')
"
```

### Xem Lessons Tích Luỹ

```bash
python3 -c "
import json
lessons = json.load(open('lessons.json'))
patterns = lessons.get('patterns', {})
viable = [(k, v) for k, v in patterns.items() if v.get('action') != 'skip']
viable.sort(key=lambda x: -x[1].get('avg_fitness', 0))
print(f'Total patterns: {len(patterns)}, Viable: {len(viable)}')
for tid, data in viable[:5]:
    print(f'  {tid}: fitness={data.get(\"avg_fitness\", 0):.2f}, pass_rate={data.get(\"pass_rate\", 0):.1%}')
"
```

### Xem Active Alphas

```bash
python3 -c "
import json
db = json.load(open('alpha_db.json'))
active = [a for a in db.get('alphas', {}).values() if a.get('status') == 'ACTIVE']
print(f'Active alphas: {len(active)}')
for a in active[:5]:
    print(f'  {a.get(\"alpha_id\")}: Sharpe={a.get(\"sharpe\", 0):.2f}')
"
```

---

## Next Steps (Mục Tiêu Tiếp Theo)

1. **Per-Paper Extraction**: Process tất cả 14 papers, mỗi cái một prompt
2. **Accumulate Lessons**: Lessons.json sẽ chứa hàng chục patterns
3. **High-Fitness Alphas**: Từ lessons, các alphas mới sẽ có fitness > 1.0
4. **Portfolio**: Combine ACTIVE alphas → Low correlation portfolio

---

## File References

| File | Mục Đích |
|------|----------|
| `PAPER_EXTRACTION_PROMPT.md` | Template chung cho tất cả papers |
| `_extraction_prompt_src_NNN.md` | Filled prompt cho paper cụ thể (LLM sẽ dùng) |
| `templates/` | Lưu trữ templates sau khi ingest |
| `papers_registry.json` | Tracking papers status + templates created |
| `lessons.json` | Accumulate knowledge từ tất cả papers |
| `alpha_db.json` | Lưu tất cả alphas + status |
| `mining_state.json` | State của mining loop |
| `mining_report.json` | Final report sau mining |

---

## Tips & Tricks

1. **Batch Process**: Generate prompts cho 3-4 papers trước, rồi extract từng cái

   ```bash
   for i in 1 2 3 4; do
     python3 scripts/generate_extraction_prompt.py src_00$i
   done
   # Rồi ChatGPT từng cái, lưu JSON
   ```

2. **Re-use Good Templates**: Nếu paper N tạo ra templates tốt, có thể copy+modify cho papers khác

3. **Monitor Lessons**: Kiểm tra `lessons.json` thường xuyên để thấy patterns nào thành công

4. **Early Stop**: Nếu mining không có ACTIVE mới sau 3 rounds, có thể chuyển paper tiếp theo

5. **Parallel Extraction**: Bạn có thể generate prompts cho nhiều papers rồi extract song song (3-4 LLM tabs)

---

## FAQ

**Q: Tại sao lần đầu breadth bị skip?**
A: Để tiết kiệm thời gian. 31 templates cũ đã test từ trước, ít ra được ý tưởng mới. Papers mới là source của ý tưởng mới nhất.

**Q: Lessons từ paper 1 giúp paper 2 như thế nào?**
A: Khi generate prompt cho paper 2, `lessons_summary` sẽ hiển thị templates thành công từ paper 1. LLM sẽ tạo templates tương tự hoặc bổ sung, thay vì lặp lại.

**Q: Có thể chạy nhiều mining loops song song không?**
A: Không khuyến khích (cạnh tranh API quota). Chạy tuần tự từng paper.

**Q: Bao lâu thì một paper xong?**
A: ~1-2 giờ (extract templates + 5-10 breadth rounds)

**Q: Nếu ingest fail, phải làm gì?**
A: Kiểm tra JSON, sửa lỗi, retry. Templates failed sẽ không được lưu.

---

**Ready to start! 🚀**

```bash
python3 scripts/generate_extraction_prompt.py src_001
# Rồi copy & paste prompt vào ChatGPT với paper PDF
```
