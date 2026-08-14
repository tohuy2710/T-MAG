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

                                     http://www.sinoss.net  
 
 - 1 - 个股反转策略与行业动量策略  
—基于A股市场的实证研究  
 
丁大鹏，刘千秋  
（湖南大学经济管理研究中心，湖南省 、长沙市， 410006） 
 
摘要：自上世纪八十年代开始，越来越多的实证研究表明过去的股票价格往往在一定程度上能够预测未来
的股价运行趋势， 这其中最具代表性的便是反转效应 （ Reversal  Effect） 和动量效应 （ Momentum  Effect）。
这与学者们一直所信奉的有效市场理论相悖故而被称为市场异象（ Market  Anomaly ）。关于国内股票市场
是否存在反转效应与动量效应目前学界并没有一致的结论。 本文选取了 从1997年至 2016年中国股票市场
的月度交易数据，重点研究了 A股市场的动量效应和反转效应的存在性问题。实证结果表明： A股市场在
样本期并没有表现出显著的动量效应；在短期（ 3个月）内存在显著的反转效应，中长期内反转效应也并不
明显；分市场来看，深圳 A股市场反转效应强度大于上海 A股市场，创业板反转效应强度明显强于其他类
型市场；分时间来看， A股市场短期反转效应的强度有所波动但整体在增强这可能暗示国内 A股市场正在
变得更加市场无效；同时小市值公司比大市值公司更容易表现出反转效应。采用个股的反转策略可以为我
们带来约 0.57%的月度超额收益。除此以外，本文还对跨行业的动量策略进行了考察，结果表明在牛市状
态下采取行业动量策略可以为我们带来显著的正收益，但在考虑了无风险利率、交易成本等因素后该策略
收益并不乐观。  
关键词： 有效市场假说；市场异象；反转策略；动量策略  
中图分类号：  F832.5        文献标识码： A 
 
 
一，引言  
现代金融学领域，如何给资产定价一直是研究的核心问题之一。历史上已经有许多学
者在此方面做出了杰出的贡献。比如 H. Markowitz 的均值 -方差模型  (Mean -variance 
model ); W. Sharpe和J. Lintner 的资本资产定价模型  (Capital Asset Pricing Model, 
CAPM ); S. A. Ross 的套利定价理论  (Arbitrage Pricing Theory, APT ) 等等。这些理论从
数学模型出发探讨了如何给资产做出合理定价，研究这些理论不难发现它们都有一个共同
的理论基础，这便是有效市场假说  (Efficient Market Hypothesis, EMH)  。 
我国股票市场初建于上世纪九十年代初。其建立时间远远滞后于西方成熟的金融市
场，而且加之九十年代初我国 A股市场上市公司数量很少，数据非常匮乏且质量不佳，这
些因素一致制约着我国学者对我国股市进行深入的实证研究。伴随着我国经济市场化程度
的不断加深，经济发展越来越需要成熟、健康的金融系统来支撑。股票市场作为金融市场
中最为活跃的一个部分，它的有效性直接反映了资本市场合理配置资源的能力，从而间接
地影响到宏观经济是否能够平稳运行。因此，探讨我国股票市场的有效性问题对加深人们
对股票市场发展形态和阶段的认识、为市场投资者提供有 效的策略建议、给予市场管理者
合理的建议从而促进我国股票市场的健康发展都具有重大意义。  
 
二，文献回顾  
从20时机 80年代开始至今，有大量的实证金融研究发现股票或者特定的资产组合的
收益率存在着某种可以预测的模式。它们的未来收益与过去收益存在着某种相关关系。其中
                                     http://www.sinoss.net  
 
 - 2 - 最引人注意的即是动量效应和反转效应。简单来说，动量效应可以定义为一只股票或一个特
定资产组合在一定时期内的收益率呈现正相关关系； 反转效应可定义为一只股票或一个特定
资产组合在一定时期内的收益率呈现负相关关系。  
DeBondt & Thaler  (1985 ) 在Does the Market Overreact? 一文中分析了 1926年至
1982年期间纽约交易所的所有股票交易数据。他们将这期间的股票根据过去三年的累计超
额收益进行排序，将过去三年表现最好的 35只股票与表现最差的 35只股票分别形成两个
投资组合，即赢者组合和输者组合。然后他们重点考察了这两个组合在随后三年里的表现，
最终他们发现，在所考察的时间区间里，平均每年输者组合要比赢者组合收益率高约 8%，
三年累计高达 25%。结合实验心理学的启示，他们认为股票市场上存在着对未预期信息的
过度反应现象，大多数的投资者对未 预期到的信息或重大事件表现出过度反应。股票市场的
价格反转效应也正是由于这一原因所造成的。  
Jegadeesh & Titman ( 1993 ) 在著明的 Return to Buying Winners and Selling Losers: 
Implications for Stock Market Efficiency 一文中首次提出了动量策略的概念。首先，他们将
过去一段时间内股票市场上的所有股票根据收益率进行排序，前 10%为赢者组合，后 10%
为输者组合。他们设计了三种投资策略：持有收益表现较好的组合、卖出表 现较差的组合以
及买入表现较好的组合同时卖出表现较差的组合。 实证结果表明， 股票的收益在检验期为 3-
12个月时能够表现出很强的动量效应。 而且这种动量效应具有普遍性和稳健性。 除此之外，
文章还将超额收益利用单因子模型进行了回归检验， 证明上述投资收益并不能完全被市场收
益所解释。  
类似的结果在美国以外的市场也被广泛发现。 Rouwenhorst (1998) 通过对欧洲股市的
研究发现欧洲投资者倾向于采用动量投资策略。 Chan, Hameed & Tong (2000) 在
Profitability of Momentum  Strategies in the International Equity Markets 一文中验证了在国
际股票市场上采用动量策略的有效性。他们的结果显示了显著的动量策略收益。初次之外他
们还发现动量策略的收益大小与与过往的交易量呈显著的正相关关系。 Chang, McLeavey & 
Rhee  (1995) 发现了在日本市场上反转策略能够获得超额收益。 Chui (2000) 发现日本和韩
国市场上反转策略有显著的超额收益。 Chui, Titman & Wei (2010) 在Individualism and  
Momentum around the world 一文中验证了不同国家文化差异对动量策略收益的影响。他们
在文章中采用了 Geert Hofstede (2001) 所提出的个人主义系数来衡量文化差异，这一系数
基于过度自信（ Overconfidence ）和自我归因偏差 (Self-attribution Bias) 计算。结果他们发
现个人主义程度大小与交易量和交易波动率正相关， 并且与动量策略收益也呈显著的正相关
关系。同时，动量策略收益也与分析师预测传播程度  (Analyst Forecast Dispersion )、交易
成本  (Transaction Cost) 和外国投资者对该市场了解程度  (Familiarity of the Market to 
Foreigners) 呈正相关；与公司规模呈负相关。  
也有不少学者在国内市场上对这两种市场异象进行了研究。林松立和唐旭  (2005)通过
对沪深 A股市场的实证研究发现中国股票市场并不存在动量效应，而在中长期则出现了反
转效应。王永宏，赵学军（ 2001）、杨炘，陈展辉（ 2004）等也发现了类似的结论。杨和陈
（2004）使用 1992 -2001年的沪深 A股市场全样本数据的实证结果 发现中国 A股市场基本
不存在动量现象，而存在显著的反转现象。过去 1到12个月的赢者或者输者在未来的表现
并没有显著差异，“追涨杀跌”的投资策略也并不能够获利。而刘博和皮天雷（ 2007）通过
对1994 -2005年沪深 A股市场的研究发现国内股票在该段时间内并不存在动量效应但是存
在显著的反转效应。 在他们所构建的多种反转策略中赢者组合与输者组合在检验期中的均值
                                     http://www.sinoss.net  
 
 - 3 - 高度一致地表现出反转特征。他们的解释是中国股市存在普遍的反应过度现象，风险补偿理
论对中国股票市场的动量效应和反转效应具有一定程度的解释力。肖军，徐信忠（ 2004）发
现在 A股市场上即使考虑了传统风险因素调整后，反转策略效果依然明显。鲁臻，邹恒甫
（2007）发现中国股票市场的反转效应相较于动量效应要更为明显一些，并且除了中期的
动量效应和长期反转效应外还存在着超短期的动量效应与短期的反转效应； 同时小市值公司
股票相对大市值公司股票的动量趋势较弱更容易产生反转现象， 成交量大的股票相对于成交
量小的股票动量趋势较弱更容易发生反转。朱战宇，吴冲锋，王成炜（ 2003）在对不同检验
周期下中国股市价格动量的盈利性研究中发现随着持有周期的增加， 动量策略的盈利大小不
断减小。潘莉，徐建国（ 2011）在研究中国 A股市场个股回报率时也发现 A股个股在多个
时间频率上存在明显的反转， 而动量效应则仅发生在超短期的日回报率和特定时间段的周回
报率上。他们还发现交易量对动量和反转效应存在着显著影响：交易量小的股票容易发生动
量效应而交易量大的股票容易发生反转效应。 他们的解释时交易量有着促进和加快股票价格
对信息反应速度的作用， 交易量大的股票对信息的反应速度更快也更充分因此不存在反应不
足的问题， 而交易量较小的股票由于对信息反应的速度较慢且又不充分因而容易导致对信息
的反应不足。 Zhou, Geppert & Kong ( 2010) 发现在中国 A股或 B股市场采用动量策略都
只能得到显著的负收益，分解分析表明该负收益主要归因于股票的时序盈利性。  
综合上述文献我们不难发现，对于国内市场而言，学者们普遍认为动量效应并不显著而
反转效应比较明显，且无论是动量效应还是反转效应国内市场周期都较外国市场更短。  
 
三，实证模型  
为了检验股票收益率的序列相关性，我们考虑如下一个模型：  
𝑅𝑛,𝑡=𝛽0𝑡+∑ 𝛽𝑚𝑡∙𝑅𝑛,𝑡−𝑚𝑀
𝑚=1+𝜇̃𝑛,𝑡 
其中，𝑅𝑛,𝑡代表股票 n在第 t月的收益率。  
特别地，在本文中我们考虑这样一个包含 1到12期，24期和 36期月度收益率滞后项
的横截面回归模型：  
𝑅𝑛,𝑡=𝛽0𝑡+∑ 𝛽𝑚𝑡∙𝑅𝑛,𝑡−𝑚12
𝑚=1+𝛽13𝑡∙𝑅𝑛,𝑡−24+ 𝛽14𝑡∙𝑅𝑛,𝑡−36+ 𝜇̃𝑛,𝑡 
其中， 𝑅𝑛,𝑡为股票 n在第 t月的收益率， 𝑅𝑛,𝑡−𝑚为股票 n在第 t-m月的收益率，本文 所使用
的股票月度收益率都为考虑现金红利再投资收益率。  
在该回归模型中， 1到3期滞后项系数项符号代表了短 期内的动量或反转效应， 12期
左右滞后项系数代表了中期内的情况，而 24期和 36期滞后项系数则代表了长期效应。  
在实证回归中我们使用了 Fama -MacBeth 回归方法。该 回归是由 Eugene F. Fama 和
James D. MacBeth 在1973年所提出的。现在这一回归方法被广泛地应用于估计资产定价
模型的参数中。在 Fama -MacBeth 回归中，参数估计是通过两个步骤得到。具体地：  
1）  在每一个时间横截面上对每一个风险资产做关于其风险因子的回归，在这一步中
得到每一个风险因子的贝塔值；  
2） 对所有时间横截面上得到的贝塔值取平均以得到关于某一特定风险因子的平均贝
塔值。  
这里值得注意的是， Fama -MacBeth 回归所提供的标准误仅对第一阶段横截面回归有
                                     http://www.sinoss.net  
 
 - 4 - 效，该标准误并没有考虑时间维度的序列自相关。但是对于股票资产组合来讲这通常并不是
一个问题因为在短期内股票的时间自相关关系通常很弱。  
 
四，实证结果  
本文所选取的数据来源于国泰安数据库（ CSMAR）中“股票市场交易 (CSMAR China 
Stock Market Trading Database) ” 中的公司基本数据和月个股回报率数据。 在总样本 3238
只股票，沪 A市场股票共有 1222只、深 A市场共有 1331只、创业板股票（创业板股票原
则上也属于深圳 A股，由于交易方式上与普通主板及中小板有一些差异，故在样本处理上
将其单独列出。下文再提到 A股时如若不加特殊说明均为剔除创业板后的 A股。）共 571
只、沪 B市场和深 B 市场分别有 55、59只。 
 
表 1 样本中股票所在市场分布  
Tab. 1 Market distribution of sample stocks  
上海 A股 上海 B股 深圳 A股 创业板  深圳 B股 
1222  55 1331  571 59 
 
首先我们将样本中所有数据按市场划分为上海 A股、深圳 A股、创业板、上海 B股以
及深圳 B股。自变量为股票月度收益率，因变量为滞后若干期的股票月度收益率。从 L1至
L36分别表示滞后一期至滞后 36期股票月度收益率。回归结果如下表所示：  
 
表2 各市场全时段全样本回归结果比较  
Tab.2 Comparison between different stock market s among full sample period  
 沪A 深A 创业板  沪B 深B 
L1 -0.0591*** -0.0548*** -0.0908*** 0.0286  0.0031  
 (0.0096)  (0.0103)  (0.0247)  (0.0229)  (0.0225)  
L2 -0.0328*** -0.0150  -0.0169  0.0032  0.0042  
 (0.0075)  (0.0093)  (0.0236)  (0.0276)  (0.0244)  
L3 -0.0060  -0.0045  -0.0267  0.0233  0.0269  
 (0.0073)  (0.0086)  (0.0220)  (0.0220)  (0.0247)  
L4 -0.0085  0.0045  -0.0179  0.0095  -0.0052  
 (0.0073)  (0.0076)  (0.0174)  (0.0190)  (0.0178)  
L5 -0.0072  0.0019  -0.0099  0.0170  0.0437** 
 (0.0071)  (0.0077)  (0.0232)  (0.0213)  (0.0217)  
L6 0.0128* 0.0128* -0.0235  -0.0012  0.0360  
 (0.0068)  (0.0068)  (0.0185)  (0.0214)  (0.0226)  
L7 0.0093  -0.0027  0.0054  0.0165  0.0228  
 (0.0066)  (0.0068)  (0.0303)  (0.0223)  (0.0209)  
L8 0.0001  0.0019  -0.0270  0.0202  0.0099  
                                     http://www.sinoss.net  
 
 - 5 - 续表 2 沪A 深A 创业板  沪B 深B 
 (0.0061)  (0.0061)  (0.0199)  (0.0165)  (0.0167)  
L9 0.0085  0.0093  -0.0867*** 0.0083  0.0245  
 (0.0056)  (0.0059)  (0.0236)  (0.0192)  (0.0202)  
L10 0.0004  -0.0018  -0.0295  -0.0030  -0.0170  
 (0.0062)  (0.0065)  (0.0204)  (0.0204)  (0.0180)  
L11 -0.0018  -0.0008  0.0008  0.0310  0.0188  
 (0.0059)  (0.0061)  (0.0258)  (0.0286)  (0.0196)  
L12 0.0085  0.0075  -0.0173  -0.0023  0.0305* 
 (0.0054)  (0.0054)  (0.0263)  (0.0175)  (0.0164)  
L24 0.0016  0.0038  0.0170  0.0057  0.0234* 
 (0.0055)  (0.0059)  (0.0207)  (0.0157)  (0.0141)  
L36 0.0045  0.0039  0.0221  0.0450** -0.0024  
 (0.0056)  (0.0047)  (0.0207)  (0.0216)  (0.0198)  
Con 0.0110* 0.0129** 0.0424** 0.0022  0.0159* 
 (0.0057)  (0.0062)  (0.0173)  (0.0079)  (0.0089)  
N 127740  105994  7152  9769  9604  
r2 0.1212  0.1315  0.2157  0.4580  0.4651  
F 4.6408  4.0746  2.2844  0.8104  1.4668  
p 0.0000  0.0000  0.0169  0.6574  0.1261  
注：括号内为标准误， ***，**，*分别代表 1%，5%，10%显著性水平，所有下表同  
 
从短期上来说，不难看出在沪 A、深 A 以及创业板市场上都存在收益反转现象，滞后
一阶项系数均在 1%的显著性水平上显著。 在强度方面 （一阶系数绝对值） ， 创业板 （ -0.0908）
大于上海 A股（-0.0591）大于深圳 A股（-0.0548）。不管是沪 B还是深 B却均为表现出
收益反转迹象。 B股数据在滞后前三阶系数都为正，但是都不显著。在中长期（ 12个月以
上），回归中 A股数据系数均为正，表现出一点动量效应的证据，但是其系数都并不显著。  
我们的数据范围从 1997年开始至 2016年结束，时间跨度正 好达 20年。我们将 20等
间距划分为五个部分， 每四年一个时间段。 它们是 1997年至 2000年、2001年至 2004年、
2005年至 2008年、2009年至 2012年、2013年至 2016年，并分别记为 T1，T2，T3，
T4和T5。在各个时间段内我们对所有 A股市场数据做标准 Fama -MacBeth 回归，结果如
表3所示： 
 
表3 A股样本分 5时段回归结果  
Tab.3 Fama -MacBeth regression results of A -stock market in 5 time periods  
 T1 T2 T3 T4 T5 
L1 0.0279  -0.0574**  -0.0497**  -0.0746***  -0.0695***  
 (0.0377)  (0.0234)  (0.0215)  (0.0150)  (0.0171)  
                                     http://www.sinoss.net  
 
 - 6 - 续表 T1 T2 T3 T4 T5 
L2 -0.0065  -0.0325  -0.0117  -0.0367**  -0.0221*  
 (0.0352)  (0.0205)  (0.0141)  (0.0146)  (0.0125)  
L3 0.0003  -0.0008  0.0104  -0.0150  -0.0164  
 (0.0384)  (0.0161)  (0.0185)  (0.0117)  (0.0145)  
L4 0.0151  0.0140  -0.0186  -0.0034  -0.0061  
 (0.0296)  (0.0170)  (0.0139)  (0.0116)  (0.0118)  
L5 0.0055  0.0256*  -0.0043  -0.0273**  -0.0084  
 (0.0300)  (0.0151)  (0.0142)  (0.0121)  (0.0129)  
L6 0.0159  0.0431***  0.0248*  -0.0088  -0.0064  
 (0.0303)  (0.0134)  (0.0134)  (0.0102)  (0.0120)  
L7 0.0005  0.0182  0.0009  -0.0155  0.0093  
 (0.0237)  (0.0119)  (0.0133)  (0.0102)  (0.0117)  
L8 -0.0263  0.0192*  -0.0031  -0.0053  0.0001  
 (0.0244)  (0.0105)  (0.0122)  (0.0115)  (0.0102)  
L9 0.0142  0.0318***  0.0171  -0.0150  0.0027  
 (0.0192)  (0.0111)  (0.0105)  (0.0090)  (0.0088)  
L10 -0.0260  0.0180  0.0054  -0.0067  -0.0160*  
 (0.0273)  (0.0112)  (0.0141)  (0.0119)  (0.0086)  
L11 0.0164  0.0091  0.0042  -0.0084  -0.0110  
 (0.0252)  (0.0098)  (0.0128)  (0.0108)  (0.0105)  
L12 0.0516  0.0223**  0.0051  0.0058  -0.0080  
 (0.0353)  (0.0087)  (0.0107)  (0.0083)  (0.0084)  
L24 -0.0111  0.0044  0.0044  0.0023  0.0091  
 (0.0168)  (0.0086)  (0.0148)  (0.0076)  (0.0089)  
L36 0.0178  -0.0053  0.0059  0.0042  0.0039  
 (0.0123)  (0.0066)  (0.0109)  (0.0054)  (0.0109)  
Cons  0.0623***  -0.0165**  0.0243  0.0086  0.0186  
 (0.0180)  (0.0064)  (0.0181)  (0.0094)  (0.0111)  
N 7415  42787  50322  63134  77228  
r2 0.0837  0.1317  0.1193  0.0955  0.1050  
F 4.6962  6.2530  1.7393  2.5046  2.2914  
p 0.0070  0.0000  0.0791  0.0095  0.0173  
注：括号内为标准误， ***，**，*分

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
