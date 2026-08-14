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

 
 
 
  
请务必阅读正文之后的信息披露和法律声明  
 
  
 
 选股因子系列研究 （十） 
 
基于机构持股信息的 Portable Alpha 策略增强   
 
 
 
 基于机构持股信息将上市公司分类。 上市公司的股东结构与股价存在一定关联。
本文通过上市公司、 基金公司以及理财产品的定期报告所披露的信息可以将上市
公司分为有 /无机构持股两类。通过两类组合收益的对比，设计了一种基于机构
持股信息的 Portable Alpha 策略增强方法。  
 A股市场机构持股范围不断上升，持股比例显著下降。 A股市场的主要机构投资
者包括基金 、券商、保险、社保、私募以及 QFII等。回顾 2008H2至2014H1
机构持股的情况，我们发现，机构持股范围不断扩大，但持股比例 显著下降。机
构持股比例的显著下降主要由于基金规模的停滞不前。 这与 A股市场近年来的市
场环境息息相关。  
 由于市值效应，无机构持股组合优于有机构持股组合。 根据机构持股信息构建有
/无机构持股组合，并考察组合收益。我们发现，无论等权还是流通市值加权，
无机构持股组合具有约 8%左右的超额收益。然而，无机构持股组合主要由小市
值股票构成，其超额 收益中掺杂着市值因素。  
 控制市值因素后，有机构持股组合具有超额收益。 通过市值控制 的Monte Carlo
模拟方法，构建与无机构持股组合市值效应接近 的有机构持股组合。控制市值效
应后，有机构持股组合优于无机构持股组合，年化超额收益约为 3%。考察组合
的微观结构，策略超额收益稳定，但在特定报告期具有较大回撤，并不适合作为
单策略运行。  
 通过 Portable Alp ha的方法可以增强策略收益。 在实际研究中，我们常常会发
现一些因子具有一定的超额收益，但受限于收益幅度或策略回撤，不适合作为单
策略运行。 借鉴 Portable Alpha 的思想，可以将上述策略的超额收益嫁接到已有
的策略之中，在不额外增加策略换手率与稳定性的情况下增强策略收益。  
  
相关研究  
选股因子系列研究（一） ——弱者终有逆
袭日，强势几无持续时  
2012-07-23 
选股因子系列研究（二） ——因子模型的
尾部相关性研究  
2013-03-25 
选股因子系列研究 （三）——从Spearman
相关系数出发研究因子有效性 ——Kalman  
Filtter模型在因子选择中的应用  
                          2013-10-11 
选股因子系列研究（四） ——多因子选股
模型的失效与有效  
                          2013-10-28 
选股因子系列研究（五） ——寻找股价驱
动新因子之净换手率  
                          2013 -10-31 
选股因子系列研究（六） ——极值视角下
的多因子选股策略  
                          2014 -05-20 
选股因子系列研究（七） ——融资推动股
价明显，融券作用有限 ——融资融券对个
股收益的影响研究  
                          2014 -05-26 
选股因子系列研究（八） ——从串联到并
联——单因子多策略组合  
                          2014 -10-08 
选股因子系列研究（ 九）——上市公司薪
酬那些事 
                          2014 -12-10 
金融工程 首席分析师  
高道德  
SAC执业证书编号： S08505110 10035  
电话： 021-23219 569 
Email：gaodd@htsec.com  
 
金融工程 高级分析师  
冯佳睿  
SAC执业证书编号： S0850512080006  
电话： 021-2321 9732  
Email：fengjr @htsec.com  
 
联系人  
沈泽承  
电话： 021-23212067  
Email：szc9633@htsec.com  
 
定量研究  
 
2015年02月27日 
 证券研究报告  
专题报告  
 

  
 
 
  
请务必阅读正文之后的信息披露和法律声明  
       量化选股研究  2 
司
研
究
〃
中
泰
化
学 
  
目录  
1. 投资机构持股概况  ................................ ................................ ................................ ..........  5 
1.1机构持股范围不断扩大  ................................ ................................ .............................  5 
1.2机构持股比例显著下降  ................................ ................................ .............................  6 
1.3机构持股结构向新兴产业转移  ................................ ................................ ..................  7 
2. 机构持股组合的收益分析  ................................ ................................ ...............................  7 
2.1有无机构持股组合收益比较  ................................ ................................ ......................  7 
2.2 市值控制下的 MONTE CARLO模拟收益比较  ................................ .............................  8 
2.3 市值配对下的有无机构持股组合收益比较  ................................ ................................  9 
3. 基于机构持股信息的策略增强  ................................ ................................ ......................  11 
3.1策略增强示例  ................................ ................................ ................................ ..........  11 
3.2 PORTABLE ALPHA与策略嫁接  ................................ ................................ ..................  12 
 
 
 
 
  

hXpYxPsP6McMbRnPnNnPrReRqQqNiNoOrO9PnMvNwMqMsQNZnMuM  
 
 
  
请务必阅读正文之后的信息披露和法律声明  
       量化选股研究  3 
司
研
究
〃
中
泰
化
学 
  
图目录  
  
图1  2008H2至2014H1 机构持股范围变化趋势  ................................ ..........................  5 
图2  2008H2至2014H1 机构持股比例变化趋势  ................................ ..........................  6 
图3  2009M4至2014M12 有/无机构持股等权组合净值走势  ................................ ........  8 
图4  无机构持股组合的市值分位点分布  ................................ ................................ ........  8 
图5  构建具有相同市值效应的有机构持股组合配对方法  ................................ ............  10 
图6  2009M4至2014M12 市值配对后有 /无机构持股等权组合净值走势  ....................  10 
图7  2009H2至2014H1 市值配对后有 /无机构持股收益对比  ................................ ..... 11 
图8  2009M4 至2014M12 原始策略与增强策略的净值走势  ................................ ....... 12 
图9  PORTABLE ALPHA策略收益嫁接图解  ................................ ................................ .... 13 
 
  

  
 
 
  
请务必阅读正文之后的信息披露和法律声明  
       量化选股研究  4 
司
研
究
〃
中
泰
化
学 
  
表目录  
  
表1  2008H2至2014H1 机构持股规模与比例变化趋势  ................................ ...............  7 
表2  2008H2与2014H1 机构最青睐的行业  ................................ ................................ . 7 
表3  市值控制 下的 MONTE CARLO模拟收益再比较  ................................ .......................  9 
表4  市值控制下的 MONTE CARLO模拟收益再比较（续）  ................................ ............  9 
表5  原始策略与增强策略收益相关统计数据  ................................ ..............................  12 
  

  
 
 
  
请务必阅读正文之后的信息披露和法律声明  
       量化选股研究  5 
司
研
究
〃
中
泰
化
学 上市公司的股东结构与股价变化存在一定的关联。尤其是 具有专业知识与信息优势
的机构投资者，通过分析他们的投资行为与持股信息，可以帮助我们挖掘潜在的投资机
会。在此前的专题报告《事件驱动策略之十二 ——重要股东持股结构变动蕴含的信息分
析》一文中，我们发现，机构投资者大幅增持的个股具有显著的超额收益。  
本文通过上市公司 、基金公司以及理财产品 等定期报告 所披露的信息 ，将 A股上市
公司分成 有/无机构持股两类。研究发现，控制市值效应后，有机构持股组合优于无机构
持股组合。 此外，借鉴 Portable Alpha 的思想， 设计了一种策略增强的方法， 将机构持
股信息的超额收益嫁接到原始策略之中 。 
1. 投资机构持股概况  
根据上市公 司、基金公司以及理财产品定期报告所披露的信息，我们可以大致了解
2008H2 以来上市公司的机构持股情况 ，并作简要概述 。 
 投资机构 ：A股市场主要的机构投资者包括基金、券商（及其集合计划）、保险、
社保、阳光私募、 QFII、信托、财务公司等。在本文中， 为便于统计， 将阳光私募、
信托以及财务公司 统一归入“私募”大类。 
 数据来源 ：根据上市公司，基金公司以及理财产品等年报 /半年报所披露的信息。 A
股最主要的机构投资者 ——基金公司 （占机构投资者总规模 70%以上）一般于半年
报/年报披露持仓明细 。以半年为一个样本周期可以尽可能 保证数据的准确性。  
 时间范围 ：2008H2至2014H1，共计 12个报告期。由于 2008年前后， A股市场
先后经历了急涨急跌以及箱体震荡两类行情。为了避免市场环境对分析结果的影响，
我们选择 2008年底作为时间 节点？，进行具体分析。  
根据上述规则，将上市公司分为有 /无机构持股两类，并通过机构持股范围以及机构
持股比例两类指标对 2008H2以来机构持股情况进行简要总结。  
1.1机构持股范围不断扩大  
定义机构持股范围为报告期当日（如 20081231 ）有机构持股的上市公司数 占上市
公司总数 的比例。图 1为2008H2至2014H1 机构持股范围的变化趋势。  
图1  2008H2至2014H1机构持股范围变化趋势  
 
资料来源： WIND，海通证券研究所  
20%40%60%80%100%120%
050010001500200025003000无机构持股数 机构持股数 机构覆盖比例

  
 
 
  
请务必阅读正文之后的信息披露和法律声明  
       量化选股研究  6 
司
研
究
〃
中
泰
化
学 如图 1所示， 2008H2以来，机构持股范围不断上升 。2008H2，有机构持股的上市
公司为1042家，占全市场 1600家上市公司的 65%。2014H1，有机构持股的上市公司
上升至 2332家，占全市场 2519家上市公司的 92%。 
机构持股范围不断增加，反映了机构投资 类型与策略多元化的发展趋势 。近年来，
随着资本市场的发展与监管口径的放松， 适合不同投资者需求的各类机构应运而生。除
了基金、保险等 传统的大型综合性投资机构 外，阳光私募，信托公司 ，券商集合理财计
划等新颖的投资形式如雨后春笋般崛起。这些投资机构受到的监管较为宽松，投资范围
也更加灵活。 同时，随着投资机构研究实力 的增强与投资策略的丰富，价值、成长、量
化等多样化 的投资方式，也拓展了 机构的投资范围。  
1.2机构持股比例显著下降  
定义机构持股比例为报告期当日（如 20081231 ）机构持有 股份的流通市值占上市
公司总流通市值 的比例。图 2为2008H2至2014H1 机构持股比例的变化趋势。  
图2  2008H2至2014H1机构持股比例变化趋势  
 
资料来源： WIND，海通证券研究所  
如图 2所示，与机构持股 的范围不断上升不同， 2008H2 以来，机构持股 比例显著
下降。2008H2，A股流通市值约为 3.6万亿，其中机构持有的流通市值约为 8700万，
占总流通市值的 23.95%。2014H1，A股流通市值约为 9.3万亿，机构持有的流通市值
约为 1.1万亿，占总流通市值的 11.75%。由于信息披露等原因，机构 实际持股比例应高
于上述数值，但与 2008H1近24%的份额相比 仍有明显的回落。  
分析各类投资机构的规模变化发现， 投资机构持股比例的萎缩主要源于基金规模的
停滞不前 。如表 1所示， 2008H2至今，券商、保险、社保、私募以及 QFII等机构的持
股比例基本保持不变，而基金持股比例下降约 13%。公募基金的主要投资者为个人。近
年来， A股市场持续低迷， 股票对投资者的吸引力逐渐下降。加之融资成本高企导致的
利率上行，使得市场上出现了大批高收益的理财产品 ，进一步蚕食了股票市场的份额。
因此，个人投资者对公募产品的需求逐步下降，从而导致了基金规模的停滞不前。  
 
 
0%5%10%15%20%25%30%
0 2 4 6 8 10 12 非机构持股规模 机构持股规模 机构持股占比

  
 
 
  
请务必阅读正文之后的信息披露和法律声明  
       量化选股研究  7 
司
研
究
〃
中
泰
化
学 表1  2008H2至2014H1机构持股规模与比例变化趋势  
投资机构  持股规模（亿）  流通市值占比  
20081231  20140630  变化趋势  20081231  20140630  变化趋势  
基金 7720.43  7857.63  +137.20  21.25%  8.44%  -12.81%  
券商 147.09  439.36  +292.26  0.40%  0.47%  +0.07%  
保险 417.05  1125.39  +708.33  1.15%  1.21%  +0.06%  
社保 88.12  596.88  +508.76  0.24%  0.64%  +0.40%  
私募 162.81  528.81  +366.01  0.45%  0.57%  +0.12%  
QFII 165.55  395.53  +229.97  0.46%  0.42%  -0.04% 
合计 8701  10944  +2243  23.95%  11.75%  -12.20%  
全市场  36330  93131  +56831  - - - 
 
资料来源： WIND，海通证券研究所  
1.3机构持股结构向新兴产业转移  
对比 2008H2与2014H1投资机构的持股结构，发现机构所青睐的行业也发生了巨
大的变化。表 2按持股比例排序，统计了 2008H2 与2014H1 投资机构最青睐的行业，
发现投资机构的持股偏好从传统行业向新兴产业转移 。 
表2  2008H2与2014H1机构最青睐的行业  
排序 20081231  持股比例  20140630  持股比例  
1 银行 15.62%  医药 14.03%  
2 房地产 7.81%  银行 12.24%  
3 医药 7.05%  电子元器件  6.58%  
4 食品饮料  6.69%  计算机 6.46%  
5 非银行金融  6.43%  非银行金融  6.32%  
 
资料来源： WIND，海通证券研究所  
除去处于配臵型需求的金融行业（银行与非银行金融）， 2008年底投资机构偏爱房
地产、医药以及食品饮料行业；而截至 2014H2，机构的投资重心转向了电子、计算机
等新兴产业 。 
2008年底，市场刚刚经历了 6000至1800点的大跌，机构投资者的资产配臵以防
御型行业为主，如医药、食品饮料。 2014年中，市场经历着 2年多创业板强势， 主板萎
靡的结构性行情，以 TMT行业、医药为代表的成长股越来越多地受到投资者的追捧 。
表2中的信息也是 A股这几年来市场行情的真实写照。  
2. 机构持股组合的收益分析  
根据上市公司的持股信息可以将全市场个股分为有 /无机构持股两类组合：以报告期
当日（如 2008 1231）全市场上市公司为样本空间，剔除上市不足 3个月或停牌超过 3
个月的个股。按照机构持股信息将剩余样本分为有 /无机构持股 两类，按等权 /流通市值
两种方式 加权。组合 于半年报 /年报披露截止日后一交易日，即 5月、9月首个交易日进
行调整，并计算组合净值。  
2.1有无机构持股组合收益比较  
图3为2009M4 至2014M12 有/无机构持股等权组合的净值走势与相对强弱。 如图
所示，无机构持股组合显著优于有机构持股组合 ，等权组合年化超额收益 约为7.6%。同

  
 
 
  
请务必阅读正文之后的信息披露和法律声明  
       量化选股研究  8 
司
研
究
〃
中
泰
化
学 样地，流通市值加权的无机构持股组合表现也优于有机构持股组合，年化超额收益 约为
8.4%。 
图3  2009M4 至2014M12 有/无机构持股等权组合净值走势  
 
资料来源： WIND，海通证券研究所  
然而，考察无机构持股组合的微观结构发现， 无机构持股组合呈现显著的小市值 特
征。A股市场具有显著的市值效应，许多投资组合的超额收益往往与市值因素掺杂。 图
4为无机构持股组合的市值分位点分布，从中可以看出相对于基准分布，无机构持股的
市值分布显著左偏。  
图4  无机构持股组合的市值分位点分布  
 
资料来源： WIND，海通证券研究所  
2.2 市值控制下的 Monte Carlo 模拟收益比较 
为了控制市值因素对分析结果的影响 ，我们采用 Monte Carlo 模拟的方法，比较有
无机构持股组合的收益：  
步骤 1：在各报告期，按市值大小将无机构持股组合分为 N组。 
步骤 2：将市值大于无机构持股股票最大值的有机构持股股票剔除。  
0.00 0.20 0.40 0.60 0.80 1.00 1.20 1.40 1.60 1.80 
0.00 0.50 1.00 1.50 2.00 2.50 3.00 3.50 4.00 
20090501
20090714
20090922
20091209
20100225
20100510
20100722
20101012
20101221
20110309
20110523
20110802
20111019
20111228
20120316
20120601
20120813
20121029
20130110
20130328
20130618
20130827
20131114
20140124
20140414
20140626
20140904
20141121有机构持股 无机构持股 相对强弱
0.00%1.00%2.00%3.00%4.00%5.00%6.00%7.00%8.00%9.00%
7.75
7.25
6.75
6.25
5.75
5.25
4.75
4.25
3.75
3.25
2.75
2.25
1.75
1.25
0.75
0.25
0.25
0.75
1.25
1.75
2.25
2.75
3.25
3.75
4.25
4.75
5.25
5.75
6.25
6.75
7.25
7.75无机构覆盖
基准分布

  
 
 
  
请务必阅读正文之后的信息披露和法律声明  
       量化选股研究  9 
司
研
究
〃
中
泰
化
学 步骤 3：按照无机构持股组合各组的 市值范围将 剩余的有机构持股股票 分为 N组。 
步骤 4：在各组中随机抽取与无机构持股股票 数量相同 有机构持股 股票，并计算该
组合的净值。  
步骤 5：重复步骤 4的操作 M次，构建有机构持股 组合的分布。  
令（N，M）=（10,1000）、（ 10，5000）、（ 20,1000）以及（ 20,5000），分别
统计 Monte Carlo 模拟后的有机构持股净值分布，如表 3所示。  
表3  市值控制下的 Monte Carlo 模拟收益再比较  
（N，M） 无机构持股组
合净值分位点  Q0.05 Q0.25 Q0.5 Q0.75 Q0.95 
（10,1000） 0.0240  3.4044  3.5716  3.6873  3.8129  3.9983  
（10,5000） 0.0224  3.3904  3.5594  3.6881  3.8270  4.0061  
（20,1000） 0.0100  3.4354  3.5792  3.6936  3.8313  4.0340  
（20,5000） 0.0122  3.4238  3.5848  3.7056  3.8314  4.0262  
 
资料来源： WIND

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
