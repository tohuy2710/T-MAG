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

### Những Template Thành Công (từ các bài báo trước)


**1. ashare_value_reversal_combo**
- Mô tả: Template: ashare_value_reversal_combo
- Đã test: 32 candidates
- Pass rate: 0.0% (0/32)
- Avg Sharpe: 1.407
- Avg Fitness: 0.609
- Best Sharpe: 1.460 (alpha_id: qMNE9l21)
- Hành động: EXPAND

**2. analyst_estimate_trend**
- Mô tả: Template: analyst_estimate_trend
- Đã test: 36 candidates
- Pass rate: 0.0% (0/36)
- Avg Sharpe: 1.092
- Avg Fitness: 0.342
- Best Sharpe: 1.270 (alpha_id: E5GGbKO0)
- Hành động: EXPAND

**3. ashare_short_reversal**
- Mô tả: Template: ashare_short_reversal
- Đã test: 27 candidates
- Pass rate: 0.0% (0/27)
- Avg Sharpe: 0.995
- Avg Fitness: 0.297
- Best Sharpe: 1.260 (alpha_id: d5Z1NeNJ)
- Hành động: DEPRIORITIZE

**4. ashare_volscaled_reversal**
- Mô tả: Template: ashare_volscaled_reversal
- Đã test: 24 candidates
- Pass rate: 0.0% (0/24)
- Avg Sharpe: 0.924
- Avg Fitness: 0.266
- Best Sharpe: 1.200 (alpha_id: QPGGg3br)
- Hành động: DEPRIORITIZE

**5. portable_alpha_graft**
- Mô tả: Template: portable_alpha_graft
- Đã test: 6 candidates
- Pass rate: 0.0% (0/6)
- Avg Sharpe: 0.790
- Avg Fitness: 0.237
- Best Sharpe: 0.920 (alpha_id: xANNLdOw)
- Hành động: EXPAND



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

1 
 101 Formulaic Alphas 
Zura Kakushadze §†1 
§ Quantigic® Solutions LLC,2 1127 High Ridge Road, #135, Stamford, CT 06905 
 
†  Free University of Tbilisi, Business School & Schoo l of Physics 
240, David Agmashenebeli Alley, Tbilisi, 0159, Geor gia 
 
December 9, 2015 
“There are two kinds of people in this world:  
Those seeking happiness, and bullfighters.” 
(Zura Kakushadze, ca. early ’90s)3  
 
Abstract 
We present explicit formulas – that are also comput er code – for 
101 real-life quantitative trading alphas.  Their a verage holding 
period approximately ranges 0.6-6.4 days.  The aver age pair-wise 
correlation of these alphas is low, 15.9%.  The ret urns are strongly 
correlated with volatility, but have no significant  dependence on 
turnover, directly confirming an earlier result bas ed on a more 
indirect empirical analysis.  We further find empir ically that 
turnover has poor explanatory power for alpha corre lations.      
 
  
                                                           
1 Zura Kakushadze, Ph.D., is the President and a Co- Founder of Quantigic® Solutions LLC and a Full Prof essor in the 
Business School and the School of Physics at Free U niversity of Tbilisi. Email: zura@quantigic.com  
 
2 DISCLAIMER: This address is used by the correspond ing author for no purpose other than to indicate hi s 
professional affiliation as is customary in publica tions. In particular, the contents of this paper ar e not intended as 
an investment, legal, tax or any other such advice,  and in no way represent views of Quantigic® Soluti ons LLC, the 
website www.quantigic.com  or any of their other affiliates. 
 
3 Paraphrasing Blondie’s  (Clint Eastwood) one-liners from a great 1966 moti on picture The Good, the Bad and the 
Ugly  (directed by Sergio Leone). 
2 
 1.  Introduction 
There are two complementary – and in some sense eve n competing – trends in modern 
quantitative trading.  On the one hand, more and mo re market participants (e.g., quantitative 
traders, inter alia) employ sophisticated quantitat ive techniques to mine alphas. 4  This results in 
ever fainter and more ephemeral alphas.  On the oth er hand, technological advances allow to 
essentially automate (much of) the alpha harvesting  process.  This yields an ever increasing 
number of alphas, whose count can be in hundreds of  thousands and even millions, and with 
the exponentially increasing progress in this field  will likely be in billions before we know it… 
This proliferation of alphas – albeit mostly faint and ephemeral – allows combining them in 
a sophisticated fashion to arrive at a unified “meg a-alpha”.  It is then this “mega-alpha” that is 
actually traded – as opposed to trading individual alphas – with a bonus of automatic internal 
crossing of trades (and thereby crucial-for-profita bility savings on trading costs, etc.), alpha 
portfolio diversification (which hedges against any  subset of alphas going bust in any given time 
period), and so on.  One of the challenges in combi ning alphas is the usual “too many variables, 
too few observations” dilemma.  Thus, the alpha sam ple covariance matrix is badly singular. 
Also, naturally, quantitative trading is a secretiv e field and data and other information from 
practitioners is not readily available.  This inadv ertently creates an enigma around modern 
quant trading.  E.g., with such a large number of a lphas, are they not highly correlated with 
each other?  What do these alphas look like?  Are t hey mostly based on price and volume data, 
mean-reversion, momentum, etc.?  How do alpha retur ns depend on volatility, turnover, etc.? 
In a previous paper [Kakushadze and Tulchinsky, 201 5] took a step in demystifying the 
realm of modern quantitative trading by studying so me empirical properties of 4,000 real-life 
alphas.  In this paper we take another step and pre sent explicit formulas – that are also 
computer code – for 101 real-life quant trading alp has.  Our formulaic alphas – albeit most are 
not necessarily all that “simple” – serve a purpose  of giving the reader a glimpse into what 
some of the simpler real-life alphas look like. 5  It also enables the reader to replicate and test 
these alphas on historical data and do new research  and other empirical analyses.  Hopefully, it 
further inspires (young) researchers to come up wit h new ideas and create their own alphas.   
                                                           
4 “An alpha is a combination of mathematical express ions, computer source code, and configuration param eters 
that can be used, in combination with historical da ta, to make predictions about future movements of v arious 
financial instruments.” [Tulchinsky et al , 2015]  Here “alpha” – following the common trader  lingo – generally 
means any reasonable “expected return” that one may  wish to trade on and is not necessarily the same a s the 
“academic” alpha.  In practice, often the detailed information about how alphas are constructed may ev en not be 
available, e.g., the only data available could be t he position data, so “alpha” then is a set of instr uctions to achieve 
certain stock (or other instrument) holdings by som e times  2g34722g2459, 2g34722g247′,… (e.g., a tickers by holdings matrix for each 2g34722g3′45). 
 
5 We picked these alphas largely based on simplicity  considerations, so they can be presented within th e inherent 
limitations of a paper.  There also exist myriad ot her, “non-formulaic” (coded and too-complex-to-pres ent) alphas.   
3 
 We discuss some general features of our formulaic a lphas in Section 2.  These alphas are 
mostly “price-volume” (daily close-to-close returns , open, close, high, low, volume and vwap) 
based, albeit “fundamental” input is used in some o f the alphas, including one alpha utilizing 
market cap, and a number of alphas employing some k ind of a binary industry classification 
such as GICS, BICS, NAICS, SIC, etc., which are use d to industry-neutralize various quantities. 6 
We discuss empirical properties of our alphas in Se ction 3 based on data for individual alpha 
Sharpe ratio, turnover and cents-per-share, and als o on a sample covariance matrix.  The 
average holding period approximately ranges from 0. 6 to 6.4 days.  The average (median) pair-
wise correlation of these alphas is low, 15.9% (14. 3%).  The returns 2g3444 are strongly correlated 
with the volatility 2g3444, and as in [Kakushadze and Tulchinsky, 2015] we fi nd an empirical scaling 
																																																			 																												2g3444	~	2g34442g3′2√																																																			 																							(1)  
with 2g34√′ ≈ 0.76  for our 101 alphas.  Furthermore, we find that the  returns have no significant 
dependence on the turnover 2g3445.  This is a direct confirmation of an earlier resu lt by [Kakushadze 
and Tulchinsky, 2015], which is based on a more ind irect empirical analysis. 7 
We further find empirically that the turnover per s e has poor explanatory power for alpha 
correlations.  This is not to say that the turnover  does not add value in, e.g., modeling the 
covariance matrix via a factor model. 8  A more precise statement is that pair-wise correl ations 
2g2′′52g3′352g3′37  of the alphas ( 2g3453,2g3452 = 1,…,2g344′  label the 2g344′ alphas, 2g3453 ≠ 2g3452 ) are not highly correlated with the 
product ln (2g2′242g3′35)	ln(2g2′242g3′37), where 2g2′242g3′35= 2g34452g3′35	/	2g2′2′, and 2g2′2′ is an a priori arbitrary normalization constant. 9 
We briefly conclude in Section 4.  Appendix A conta ins our formulaic alphas with definitions 
of the functions, operators and input data used the rein.  Appendix B contains some legalese.  
2.  Formulaic Alphas 
In this section we describe some general features o f our 101 formulaic alphas.  The alphas 
are proprietary to WorldQuant LLC and are used here  with its express permission.  We provide 
as many details as we possibly can within the const raints imposed by the proprietary nature of 
the alphas.  The formulaic expressions – that are a lso computer code – are given in Appendix A. 
                                                           
6 More precisely, depending on the alpha and industr y classification used, neutralization can be w.r.t.  sectors, 
industries, subindustries, etc. – different classif ications use different nomenclature for levels of s imilar granularity. 
 
7 In [Kakushadze and Tulchinsky, 2015] the alpha ret urn volatility was not directly available and was e stimated 
indirectly based on the Sharpe ratio, cents-per-sha re and turnover data.  Here we use direct realized volatility data.  
 
8 Depending on a construction, a priori the turnover  might add value via the specific (idiosyncratic) r isk for alphas.  
 
9 Here we use log of the turnover as opposed to the turnover itself as the latter has a skewed, roughly  log-normal 
distribution, while pair-wise correlations take val ues in (−1,1)  (in fact, their distribution is tighter – see belo w).    
4 
 Very coarsely, one can think of alpha signals as ba sed on mean-reversion or momentum.10   
A mean-reversion alpha has a sign opposite to the r eturn on which it is based.  E.g., a simple 
mean-reversion alpha is given by 
																																															−ln( today2g4√93s	open	/	yesterday2g4√93s	close)																																											 			(2)  
Here yesterday’s close is adjusted for any splits a nd dividends if the ex-date is today.  The idea 
(or hope) here is that the stock will mean-revert a nd give back part of the gains (if today’s open 
is higher than yesterday’s close) or recoup part of  the losses (if today’s open is lower than 
yesterday’s close).  This is a so-called “delay-0” alpha.  Generally, “delay-0” means that the time 
of some data (e.g., a price) used in the alpha coin cides with the time during which the alpha is 
intended to be traded.  E.g., the alpha (2) would i de

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
