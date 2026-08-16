import itertools

# --- KHAI BÁO FIELD & THAM SỐ CHUẨN DỮ LIỆU ---
cmf_field = 'short_term_price_change_2'

# Fields giá & khối lượng
price_fields = ['close', 'vwap']
volume_fields = ['volume', 'adv20']

# Fundamental & Analyst fields sẵn có
fundamental_fields = ['accruals_percentage_earnings', 'asset_turnover_ratio_2']
analyst_fields = ['analyst_revisions_score_2', 'avg_estimate_change_pct_current_year_eps_14d_long']

# Khung thời gian Lookback
short_lbs = [5, 10]
medium_lbs = [20, 60]
long_lbs = [126, 252]

groups = ['subindustry', 'industry']

alpha_list = []

# --- TEMPLATE 1: Phân kỳ dòng tiền với giá (Money Flow Divergence) ---
for p_f, lb, g in itertools.product(price_fields, medium_lbs, groups):
    # Cú pháp cơ bản & Cú pháp có gia tăng trọng số CMF
    expr1 = f"group_neutralize(ts_rank({p_f}, {lb}) - ts_rank({cmf_field}, {lb}), {g})"
    expr2 = f"group_neutralize((ts_rank({p_f}, {lb}) - ts_rank({cmf_field}, {lb})) * ts_mean({cmf_field}, 10), {g})"
    alpha_list.append(("T1_Divergence_Basic", expr1))
    alpha_list.append(("T1_Divergence_Weighted", expr2))

# --- TEMPLATE 2: Động lượng dòng tiền + Đảo chiều ngắn hạn ---
for p_f, s_lb, m_lb, g in itertools.product(price_fields, short_lbs, medium_lbs, groups):
    expr = f"group_neutralize(ts_mean({cmf_field}, {s_lb}) * (1 - ts_rank({p_f} / ts_delay({p_f}, 1) - 1, {m_lb})), {g})"
    alpha_list.append(("T2_Momentum_Reversal", expr))

# --- TEMPLATE 3: Đột biến dòng tiền (CMF Spike) ---
for m_lb, v_f, g in itertools.product(medium_lbs, volume_fields, groups):
    expr = f"group_neutralize((({cmf_field} - ts_mean({cmf_field}, {m_lb})) / (ts_stddev({cmf_field}, {m_lb}) + 1e-6)) * ({v_f} / (adv20 + 1e-6)), {g})"
    alpha_list.append(("T3_CMF_Spike", expr))

# --- TEMPLATE 4: Dòng tiền + Chất lượng cơ bản (Fundamental Quality) ---
for fund_f, l_lb, g in itertools.product(fundamental_fields, long_lbs, groups):
    if fund_f == 'accruals_percentage_earnings':
        # Accruals càng thấp chất lượng càng cao -> (1 - ts_rank)
        expr = f"group_neutralize({cmf_field} * (1 - ts_rank({fund_f}, {l_lb})), {g})"
    else:
        # Asset turnover delta
        expr = f"group_neutralize({cmf_field} * ts_delta({fund_f}, 4), {g})"
    alpha_list.append(("T4_CMF_Fundamental", expr))

# --- TEMPLATE 5: Dòng tiền + Kỳ vọng Analyst ---
for analyst_f, g in itertools.product(analyst_fields, groups):
    expr = f"group_neutralize({cmf_field} * {analyst_f}, {g})"
    alpha_list.append(("T5_CMF_Analyst", expr))

# --- XUẤT OUT FILE ---
output_filename = "alphas_cmf_updated.txt"
with open(output_filename, "w", encoding="utf-8") as f:
    for name, expr in alpha_list:
        f.write(f"{expr}\n")

print(f"===> ĐÃ SINH THÀNH CÔNG {len(alpha_list)} BIỂU THỨC ALPHA!")
print(f"===> File kết quả đã lưu tại: {output_filename}\n")

print("--- MẪU BIỂU THỨC TIÊU BIỂU CHO MỖI TEMPLATE ---")
for name, expr in alpha_list[:10]:
    print(f"[{name}] -> {expr}")