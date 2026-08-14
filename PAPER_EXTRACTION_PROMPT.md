# Trích Xuất Template Alpha Từ Bài Báo

> **Mục đích**: Từ nội dung bài báo nghiên cứu, hãy trích xuất các ý tưởng alpha (factor) dưới dạng JSON template.
> 
> **Ngôn ngữ**: Bài báo thường là Tiếng Trung; hãy trả lời bằng JSON với mô tả Tiếng Việt.

---

## I. CONTEXT: Hệ Thống Phát Hiện Alpha

### Mục Tiêu
Phát hiện các factor (nhân tố dự báo) để xây dựng alpha expressions cho hệ thống trading WorldQuant BRAIN.

### Cấu Hình Hiện Tại
- **Market**: GLB (Global)
- **Universe**: TOPDIV3000 (top 3000 cổ phiếu đa dạng)
- **Delay**: 1 ngày (dữ liệu từ hôm qua)
- **Target Region**: Các thị trường lớn (USA, EU, CHN, v.v.)

### Các Yếu Tố Alpha Thường Gặp
1. **Chất Lượng Cơ Bản (Fundamental Quality)**
   - ROE, ROA, Profit Margin
   - Xu hướng thu nhập, xu hướng lợi nhuận
   - Tính bền vững của lợi nhuận
   
2. **Dự Báo Của Nhà Phân Tích (Analyst Forecasts)**
   - Thay đổi EPS, thay đổi revenue estimates
   - Breadth (số lượng nhà phân tích điều chỉnh tăng/giảm)
   - Revisions (điều chỉnh gần đây)

3. **Động Lực Giá (Price Momentum)**
   - Sự thay đổi giá gần đây
   - Momentum từ các khung thời gian khác nhau
   - Mean reversion

4. **Khối Lượng Giao Dịch (Volume/Liquidity)**
   - Thay đổi khối lượng
   - Thay đổi giá bình quân theo khối lượng
   - Illiquidity measures

5. **Yếu Tố Tâm Lý (Sentiment)**
   - Tin tức bất thường
   - Cảm xúc xã hội
   - Cảnh báo cảnh báo

---

## II. CÁC TEMPLATE ĐÃ THÀNH CÔNG (Học Từ Các Bài Báo Trước)

{LESSONS_TOP_PATTERNS}

---

## III. BẢNG CHỮCÁI TRƯỜNG (Field Catalog)

### A. Các Loại Trường Khả Dụng (GLB/TOPDIV3000/delay=1)

| Loại | Số Lượng | Ví Dụ |
|------|----------|-------|
| **Fundamental** | 1652 | `operating_income`, `free_cash_flow`, `equity`, `assets`, `sales`, `gross_profit_margin` |
| **Analyst** | 1324 | `est_eps`, `est_revenue`, `est_ebit`, `est_bookvalue`, `earnings_revisions`, `revenue_surprises` |
| **Price/Volume** | 195 | `close`, `open`, `high`, `low`, `volume`, `adv_20d`, `vwap` |
| **News/Sentiment** | ~1000 | `news_count_1d`, `abnormal_news_sentiment`, `stock_rank_sentiment` |
| **Options** | 138 | `implied_volatility`, `put_call_ratio`, `skew` |
| **Model** | 40 | `valuation_score`, `quality_score`, `momentum_score` |

### B. Các Toán Tử Chính

```
Truncate theo rank:
  rank(x) — rank từ 0 đến 1 hôm nay trên toàn universe
  
Chuỗi thời gian:
  ts_rank(x, window) — rank trong window ngày (với 1 cổ phiếu)
  ts_mean(x, window) — trung bình động
  ts_delta(x, lag) — thay đổi từ lag ngày trước
  ts_corr(a, b, window) — tương quan
  
Nhóm:
  group_rank(x, group) — rank trong nhóm (ngành/nhóm ngành)
  group_neutralize(x, group) — loại bỏ hiệu ứng nhóm

Điều Kiện:
  if_else(condition, true_val, false_val)
  trade_when(signal, condition, delay) — chỉ giao dịch khi điều kiện đúng

Kết Hợp:
  a + b, a * b, -a, abs(a), log(a), etc.
```

### C. Ví Dụ Các Template Tốt

```
① Xu Hướng ROE (pass_rate: 40%)
   group_rank(ts_rank(operating_income / equity, 126), subindustry)

② EPS Forecast Revision (pass_rate: 35%)
   group_rank(ts_rank(est_eps / close, 126), industry)

③ FCF Yield (pass_rate: 38%)
   group_rank(ts_rank(free_cash_flow_reported_value / equity, 126), industry)

④ Kết Hợp Multi-Factor (pass_rate: 32%)
   0.5 * group_rank(ts_rank(operating_income / equity, 126), subindustry)
   + 0.5 * group_rank(ts_rank(est_eps / close, 126), industry)

⑤ Technical + Fundamental (pass_rate: 28%)
   0.5 * rank(-(close / open - 1)) 
   + 0.5 * rank(ts_rank(operating_income / equity, 126))
```

### D. Mô Tả Chi Tiết Trường

Xem file: `references/wq_glb_topdiv3000_delay1_data_fields.json`

Để tìm trường cụ thể, hãy tìm kiếm từ khóa hoặc xem danh sách theo loại:
- Fundamental: `operating_income`, `sales`, `equity`, `gross_profit`, `free_cash_flow`, `roa`, `roe`, `debt_to_equity`, v.v.
- Analyst: `est_eps`, `est_revenue`, `est_ebit`, `est_pe`, `earnings_revisions`, `revenue_revisions`, `estimate_accuracy`, v.v.
- Price: `close`, `open`, `high`, `low`, `volume`, `returns`, v.v.

---

## IV. NỘI DUNG BÀI BÁO

{PAPER_CONTENT}

---

## V. HƯỚNG DẪN TRÍCH XUẤT

### Bước 1: Đọc Bài Báo
Tìm hiểu ý chính, các factor được đề xuất, công thức hoặc ý tưởng cho phép dự báo chuyển động giá.

### Bước 2: Định Dạng Ý Tưởng
Chuyển đổi mỗi ý tưởng alpha thành **skeleton** (template) có tham số.

Ví dụ:
- Ý tưởng: "ROE tăng -> cổ phiếu tăng"
- Skeleton: `group_rank(ts_rank({roe_field} / {scale}, {window}), {group})`
- Tham số: 
  - `roe_field` = [operating_income, net_income_annual]
  - `scale` = [equity, assets]
  - `window` = [60, 126, 252]
  - `group` = [industry, subindustry]

### Bước 3: Xác Thực Trường
Kiểm tra xem các trường có tồn tại trong danh sách trên không.

### Bước 4: Trả Về JSON
Xem phần VI dưới đây.

---

## VI. ĐỊNH DỰC JSON OUTPUT

Trả lại **mảng JSON** chứa 1-3 templates, mỗi template có cấu trúc:

```json
[
  {
    "template_id": "unique_name_from_paper",
    "description": "Mô tả bằng Tiếng Việt giải thích ý tưởng alpha",
    "hypothesis": "Giả thuyết: tại sao factor này dự báo được lợi nhuận?",
    "skeleton": "group_rank(ts_rank({estimate_field} / {denominator}, {window}), {group})",
    "field_pairs": [
      {"estimate_field": "est_eps", "denominator": "close"},
      {"estimate_field": "est_revenue", "denominator": "close"}
    ],
    "param_ranges": {
      "window": [60, 126, 252],
      "group": ["industry", "subindustry"]
    },
    "default_settings": {
      "decay": 0,
      "neutralization": "SUBINDUSTRY"
    },
    "tags": ["fundamental", "analyst", "momentum", "technical"],
    "source": "paper_name",
    "notes": "Ghi chú bổ sung (optional)"
  }
]
```

### Giải Thích Các Trường

| Trường | Kiểu | Bắt Buộc | Mô Tả |
|--------|------|---------|-------|
| `template_id` | str | ✅ | ID duy nhất, ví dụ: `alpha1_cross_sectional`, `momentum_reversal_hybrid` |
| `description` | str | ✅ | Mô tả bằng Tiếng Việt (2-3 câu) về ý tưởng factor |
| `hypothesis` | str | ✅ | Giả thuyết: tại sao nó dự báo được lợi nhuận? |
| `skeleton` | str | ✅ | Template với placeholders `{field_name}`, sẽ được điền với trường thực tế |
| `field_pairs` | list[dict] | ✅ | Danh sách các cặp trường có thể sử dụng (map placeholder → trường thực tế) |
| `param_ranges` | dict | ✅ | Phạm vi tham số: `window` (ngày), `group` (cách nhóm), v.v. |
| `default_settings` | dict | ✅ | Cài đặt mặc định cho mô phỏng: `decay`, `neutralization` |
| `tags` | list[str] | ❌ | Tags để phân loại: "fundamental", "analyst", "momentum", "technical", "volume", "sentiment" |
| `source` | str | ❌ | Tên bài báo hoặc ghi chú về nguồn |
| `notes` | str | ❌ | Ghi chú bổ sung |

### Ví Dụ Cụ Thể

```json
[
  {
    "template_id": "alpha1_cross_sectional_rank",
    "description": "Nhân tố cross-sectional dựa trên mối tương quan âm giữa sự thay đổi khối lượng và lợi suất trong ngày. Nếu khối lượng tăng nhưng lợi suất không tăng (hoặc giảm), có thể là tín hiệu mạnh cho lợi nhuận tương lai.",
    "hypothesis": "Mối tương quan âm giữa rank thay đổi khối lượng và rank lợi suất nội ngày dự báo lợi nhuận tương lai tích cực",
    "skeleton": "group_rank(-ts_corr(rank(ts_delta(log({volume_proxy}), 1)), rank(({close} - {open}) / {open}), {window}), {group})",
    "field_pairs": [
      {"volume_proxy": "volume", "close": "close", "open": "open"}
    ],
    "param_ranges": {
      "window": [6, 10, 20],
      "group": ["subindustry", "industry"]
    },
    "default_settings": {
      "decay": 10,
      "neutralization": "SUBINDUSTRY"
    },
    "tags": ["technical", "volume", "momentum"],
    "source": "Alpha 101",
    "notes": "Dựa trên Alpha #1 từ Dao et al."
  },
  {
    "template_id": "alpha4_mean_reversion_volume",
    "description": "Nhân tố mean reversion kết hợp khối lượng. Khi giá thay đổi lớn nhưng không có khối lượng hỗ trợ, có thể là dấu hiệu reversal.",
    "hypothesis": "Sự không khớp giữa thay đổi giá (độ lớn) và khối lượng là tín hiệu reversal mạnh",
    "skeleton": "group_rank(ts_rank(-(({close} - {open}) / {open}) / log({volume} + 0.000001), {window}), {group})",
    "field_pairs": [
      {"close": "close", "open": "open", "volume": "volume"}
    ],
    "param_ranges": {
      "window": [10, 20, 30],
      "group": ["industry", "subindustry"]
    },
    "default_settings": {
      "decay": 15,
      "neutralization": "INDUSTRY"
    },
    "tags": ["technical", "volume", "mean_reversion"],
    "source": "Alpha 101",
    "notes": "Dựa trên Alpha #4, focus trên volume mismatch"
  }
]
```

---

## VII. QUY TẮC QUAN TRỌNG

1. **Chỉ sử dụng các trường có sẵn** từ danh sách trên. Không bịa trường mới.

2. **Sử dụng các toán tử được phép**: `rank`, `ts_rank`, `group_rank`, `ts_mean`, `ts_delta`, `ts_corr`, `if_else`, v.v.

3. **Hạn chế số lượng templates**: 1-3 templates tốt nhất, không quá nhiều.

4. **Tên template_id phải ý nghĩa**: Liên quan đến ý tưởng, ví dụ: `momentum_reversal`, `analyst_forecast_breadth`, `fcf_yield`, v.v.

5. **Skeleton phải chứa placeholders**: Mỗi `{}` sẽ được thay thế trong bước genrating candidates.

6. **param_ranges phải hợp lý**: Có ít nhất 2 giá trị cho mỗi tham số.

---

## VIII. LỖI THƯỜNG GẶP

| Lỗi | Giải Pháp |
|-----|----------|
| Skeleton không có `{}` | Thêm placeholders cho các trường/tham số có thể thay đổi |
| field_pairs rỗng | Liệt kê tất cả các cặp trường có thể sử dụng |
| Trường không tồn tại | Kiểm tra danh sách field_catalog, thay bằng trường giống nhất |
| JSON không hợp lệ | Kiểm tra dấu ngoặc, dấu phẩy, ký tự đặc biệt |
| Quá nhiều templates | Giữ chỉ 1-3 templates tốt nhất, loại bỏ ý tưởng trùng lặp |

---

## IX. CHECKLIST TRƯỚC KHI TRẢ LỜI

- [ ] Template ID có ý nghĩa và duy nhất?
- [ ] Description bằng Tiếng Việt, 2-3 câu, rõ ràng?
- [ ] Hypothesis giải thích tại sao factor này hoạt động?
- [ ] Skeleton có placeholders `{}`?
- [ ] Tất cả trường trong field_pairs có tồn tại?
- [ ] param_ranges có ít nhất 2 giá trị mỗi tham số?
- [ ] Các tags phù hợp với ý tưởng?
- [ ] JSON hợp lệ (kiểm tra validator)?
- [ ] Không quá 3 templates?

---

**Bây giờ, hãy trích xuất từ bài báo trên và trả lại JSON mảng theo định dạng trên.**
