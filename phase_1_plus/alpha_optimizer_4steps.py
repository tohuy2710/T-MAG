#!/usr/bin/env python3
"""
Phase 1 Plus: 4-Step Alpha Optimization Framework
Triển khai 4 bước tối ưu Alpha từ template gốc:
  BƯỚC 1: Chỉnh Settings (System Configuration Tuning)
  BƯỚC 2: Chỉnh Param trong Expr (Parameter Sweeping)
  BƯỚC 3: Lồng thêm Toán tử Hợp lệ (Operator Nesting & Normalization)
  BƯỚC 4: Phá Logic (Logic Refactor & Multi-Factor Fusion)
"""

import itertools
from typing import List, Tuple, Dict, Any

# ============================================================================
# TEMPLATE GỐC & CẤU HÌNH MẶC ĐỊNH
# ============================================================================

ORIGINAL_TEMPLATE = {
    "expression": "ts_rank(short_term_price_change_2, 3) * (1 - ts_rank(returns, 20))",
    "logic": "Bắt đáy cổ phiếu quá bán dựa trên xác nhận dòng tiền ngắn hạn (CMF)",
    "settings": {
        "region": "GLB",
        "universe": "TOPDIV3000",
        "delay": 1,
        "neutralization": "COUNTRY",  # Valid options: SLOW, FAST, SLOW_AND_FAST, SUBINDUSTRY, CROWDING
        "decay": 10,
        "truncation": 0.08,
        "pasteurization": True,
        "unit_handling": "verify",
        "nan_handling": True,
    }
}

CMF_FIELD = "short_term_price_change_2"


# ============================================================================
# BƯỚC 1: CHỈNH SETTINGS (System Configuration Tuning)
# ============================================================================

def generate_step1_settings_variations() -> List[Dict[str, Any]]:
    """
    Bước 1: Tạo các biến thể cấu hình hệ thống.
    Thay đổi Neutralization, Decay, Truncation để tối ưu performance.
    """
    variations = []
    
    # Biến thể neutralization
    neutralizations = ["SUBINDUSTRY", "MARKET", "INDUSTRY", "NONE"]
    
    # Biến thể decay
    decays = [5, 7, 10, 15, 20]
    
    # Biến thể truncation
    truncations = [0.01, 0.05, 0.08, 0.10, 0.12]
    
    base_expr = ORIGINAL_TEMPLATE["expression"]
    
    for neut, decay, trunc in itertools.product(neutralizations, decays, truncations):
        settings = ORIGINAL_TEMPLATE["settings"].copy()
        settings["neutralization"] = neut
        settings["decay"] = decay
        settings["truncation"] = trunc
        
        variations.append({
            "step": "STEP_1_SETTINGS",
            "expression": base_expr,
            "settings": settings,
            "description": f"Settings: neut={neut}, decay={decay}, trunc={trunc}",
        })
    
    return variations


# ============================================================================
# BƯỚC 2: CHỈNH PARAM TRONG EXPR (Parameter Sweeping)
# ============================================================================

def generate_step2_parameter_variations() -> List[Tuple[str, str]]:
    """
    Bước 2: Giữ nguyên cấu trúc logic, thay đổi các tham số lookback window.
    """
    variations = []
    
    # Khung thời gian CMF
    cmf_windows = [3, 5, 10, 22]
    
    # Khung thời gian Reversal
    reversal_windows = [5, 10, 20, 60]
    
    for cmf_lb, rev_lb in itertools.product(cmf_windows, reversal_windows):
        expr = f"ts_rank({CMF_FIELD}, {cmf_lb}) * (1 - ts_rank(returns, {rev_lb}))"
        desc = f"Param: CMF_window={cmf_lb}, Reversal_window={rev_lb}"
        variations.append((expr, desc))
    
    return variations


# ============================================================================
# BƯỚC 3: LỒNG THÊM TOÁN TỬ HỢP LỆ (Operator Nesting & Normalization)
# ============================================================================

def generate_step3_operator_nesting() -> List[Tuple[str, str]]:
    """
    Bước 3: Lồng các toán tử chuẩn hóa và điều chỉnh rủi ro.
    """
    variations = []
    
    cmf_windows = [3, 5, 10]
    reversal_windows = [10, 20, 60]
    groups = ["industry", "subindustry"]
    volatility_windows = [20, 60]
    
    for cmf_lb, rev_lb, grp in itertools.product(cmf_windows, reversal_windows, groups):
        base_signal = f"ts_rank({CMF_FIELD}, {cmf_lb}) * (1 - ts_rank(returns, {rev_lb}))"
        
        # 3.1: Lồng rank() để chuẩn hóa phân phối
        expr1 = f"rank({base_signal})"
        desc1 = f"Step3.1: rank() normalization | CMF={cmf_lb}, Rev={rev_lb}"
        variations.append((expr1, desc1))
        
        # 3.2: Lồng group_rank() theo nhóm ngành
        expr2 = f"group_rank({base_signal}, {grp})"
        desc2 = f"Step3.2: group_rank({grp}) | CMF={cmf_lb}, Rev={rev_lb}"
        variations.append((expr2, desc2))
        
        # 3.3: Lồng group_neutralize() để triệt tiêu yếu tố ngành
        expr3 = f"group_neutralize({base_signal}, {grp})"
        desc3 = f"Step3.3: group_neutralize({grp}) | CMF={cmf_lb}, Rev={rev_lb}"
        variations.append((expr3, desc3))
        
        # 3.4: Điều chỉnh rủi ro - chia cho volatility
        for vol_lb in volatility_windows:
            expr4 = f"group_neutralize({base_signal} / (ts_stddev(returns, {vol_lb}) + 1e-6), {grp})"
            desc4 = f"Step3.4: Risk-adjusted (vol={vol_lb}) + neutralize({grp}) | CMF={cmf_lb}, Rev={rev_lb}"
            variations.append((expr4, desc4))
        
        # 3.5: Kết hợp rank từng vế riêng biệt
        expr5 = f"group_neutralize(rank(ts_rank({CMF_FIELD}, {cmf_lb})) * rank(1 - ts_rank(returns, {rev_lb})), {grp})"
        desc5 = f"Step3.5: Dual rank + neutralize({grp}) | CMF={cmf_lb}, Rev={rev_lb}"
        variations.append((expr5, desc5))
        
        # 3.6: Làm mượt tín hiệu bằng ts_decay_linear
        expr6 = f"group_neutralize(ts_decay_linear({base_signal}, 5), {grp})"
        desc6 = f"Step3.6: ts_decay_linear smoothing + neutralize({grp}) | CMF={cmf_lb}, Rev={rev_lb}"
        variations.append((expr6, desc6))
    
    return variations


# ============================================================================
# BƯỚC 4: PHÁ LOGIC (Logic Refactor & Multi-Factor Fusion)
# ============================================================================

def generate_step4_logic_refactor() -> List[Tuple[str, str]]:
    """
    Bước 4: Thay đổi hoàn toàn logic gốc để tìm nguồn Alpha mới.
    """
    variations = []
    
    groups = ["industry", "subindustry"]
    
    # === 4.1: Phân kỳ dòng tiền - giá (Money Flow Divergence) ===
    price_fields = ["close", "vwap"]
    divergence_windows = [10, 20, 60]
    
    for p_field, div_lb, grp in itertools.product(price_fields, divergence_windows, groups):
        # Tín hiệu cơ bản: Giá tăng nhưng CMF giảm (phân kỳ âm)
        expr1 = f"group_neutralize(ts_rank({p_field}, {div_lb}) - ts_rank({CMF_FIELD}, {div_lb}), {grp})"
        desc1 = f"Step4.1a: Price-CMF Divergence | field={p_field}, window={div_lb}, group={grp}"
        variations.append((expr1, desc1))
        
        # Tăng trọng số CMF
        expr2 = f"group_neutralize((ts_rank({p_field}, {div_lb}) - ts_rank({CMF_FIELD}, {div_lb})) * ts_mean({CMF_FIELD}, 10), {grp})"
        desc2 = f"Step4.1b: Weighted Divergence | field={p_field}, window={div_lb}, group={grp}"
        variations.append((expr2, desc2))
    
    # === 4.2: Động lượng dòng tiền + Đảo chiều (Momentum + Reversal Combo) ===
    short_windows = [5, 10]
    medium_windows = [20, 60]
    
    for s_lb, m_lb, grp in itertools.product(short_windows, medium_windows, groups):
        expr = f"group_neutralize(ts_mean({CMF_FIELD}, {s_lb}) * (1 - ts_rank(returns, {m_lb})), {grp})"
        desc = f"Step4.2: CMF Momentum + Reversal | CMF_avg={s_lb}, Rev={m_lb}, group={grp}"
        variations.append((expr, desc))
    
    # === 4.3: Đột biến dòng tiền (CMF Spike Detection) ===
    spike_windows = [20, 60]
    volume_fields = ["volume", "adv20"]
    
    for spike_lb, vol_field, grp in itertools.product(spike_windows, volume_fields, groups):
        # Z-score của CMF nhân với khối lượng bất thường
        expr = f"group_neutralize((({CMF_FIELD} - ts_mean({CMF_FIELD}, {spike_lb})) / (ts_stddev({CMF_FIELD}, {spike_lb}) + 1e-6)) * ({vol_field} / (adv20 + 1e-6)), {grp})"
        desc = f"Step4.3: CMF Spike × Volume Anomaly | spike_window={spike_lb}, vol={vol_field}, group={grp}"
        variations.append((expr, desc))
    
    # === 4.4: Dòng tiền + Chất lượng cơ bản (CMF + Fundamentals) ===
    fundamental_fields = [
        ("accruals_percentage_earnings", "low_is_good"),  # Accruals thấp = chất lượng cao
        ("asset_turnover_ratio_2", "delta"),  # Cải thiện hiệu quả tài sản
    ]
    long_windows = [126, 252]
    
    for (fund_field, fund_type), l_lb, grp in itertools.product(fundamental_fields, long_windows, groups):
        if fund_type == "low_is_good":
            expr = f"group_neutralize({CMF_FIELD} * (1 - ts_rank({fund_field}, {l_lb})), {grp})"
            desc = f"Step4.4a: CMF × Quality({fund_field}) | window={l_lb}, group={grp}"
        else:
            expr = f"group_neutralize({CMF_FIELD} * ts_delta({fund_field}, 4), {grp})"
            desc = f"Step4.4b: CMF × Δ{fund_field} | window={l_lb}, group={grp}"
        variations.append((expr, desc))
    
    # === 4.5: Dòng tiền + Kỳ vọng Analyst ===
    analyst_fields = [
        "analyst_revisions_score_2",
        "avg_estimate_change_pct_current_year_eps_14d_long",
    ]
    
    for analyst_field, grp in itertools.product(analyst_fields, groups):
        expr = f"group_neutralize({CMF_FIELD} * {analyst_field}, {grp})"
        desc = f"Step4.5: CMF × Analyst({analyst_field}) | group={grp}"
        variations.append((expr, desc))
    
    # === 4.6: Cross-sectional Momentum của CMF ===
    cs_windows = [5, 10, 20]
    
    for cs_lb, grp in itertools.product(cs_windows, groups):
        expr = f"group_neutralize(rank(ts_delta({CMF_FIELD}, {cs_lb})) * rank(ts_rank({CMF_FIELD}, {cs_lb})), {grp})"
        desc = f"Step4.6: CMF Cross-sectional Momentum | window={cs_lb}, group={grp}"
        variations.append((expr, desc))
    
    # === 4.7: Mean Reversion của CMF extreme ===
    extreme_windows = [20, 60]
    
    for ext_lb, grp in itertools.product(extreme_windows, groups):
        # Bắt cổ phiếu có CMF cực thấp (oversold từ dòng tiền)
        expr = f"group_neutralize(-ts_rank({CMF_FIELD}, {ext_lb}), {grp})"
        desc = f"Step4.7: CMF Mean Reversion (oversold) | window={ext_lb}, group={grp}"
        variations.append((expr, desc))
    
    # === 4.8: Multi-timeframe CMF Consensus ===
    for grp in groups:
        # Consensus qua nhiều khung thời gian
        expr = f"group_neutralize(rank(ts_rank({CMF_FIELD}, 5)) + rank(ts_rank({CMF_FIELD}, 10)) + rank(ts_rank({CMF_FIELD}, 20)), {grp})"
        desc = f"Step4.8: Multi-timeframe CMF Consensus | group={grp}"
        variations.append((expr, desc))
    
    return variations


# ============================================================================
# MAIN GENERATION FUNCTION
# ============================================================================

def generate_all_4_steps(output_file: str = "alphas_4steps_cmf.txt"):
    """
    Sinh toàn bộ 4 bước tối ưu Alpha và ghi vào file.
    """
    all_alphas = []
    
    print("=" * 80)
    print("  Phase 1 Plus: 4-Step Alpha Optimization")
    print("=" * 80)
    print(f"\nTemplate gốc: {ORIGINAL_TEMPLATE['expression']}")
    print(f"Logic: {ORIGINAL_TEMPLATE['logic']}\n")
    
    # BƯỚC 1: Settings variations (chỉ lưu thông tin, không sinh expression)
    print("\n[BƯỚC 1] Chỉnh Settings (System Configuration Tuning)")
    step1_variations = generate_step1_settings_variations()
    print(f"  → Sinh {len(step1_variations)} biến thể settings")
    print("  → NOTE: Bước này chỉnh trên giao diện BRAIN, không thay đổi expression")
    
    # BƯỚC 2: Parameter sweeping
    print("\n[BƯỚC 2] Chỉnh Param trong Expr (Parameter Sweeping)")
    step2_alphas = generate_step2_parameter_variations()
    print(f"  → Sinh {len(step2_alphas)} biến thể")
    for expr, desc in step2_alphas[:3]:
        print(f"    • {desc}")
        print(f"      {expr}")
    if len(step2_alphas) > 3:
        print(f"    ... và {len(step2_alphas) - 3} biến thể khác")
    
    all_alphas.extend(step2_alphas)
    
    # BƯỚC 3: Operator nesting
    print("\n[BƯỚC 3] Lồng thêm Toán tử Hợp lệ (Operator Nesting)")
    step3_alphas = generate_step3_operator_nesting()
    print(f"  → Sinh {len(step3_alphas)} biến thể")
    for expr, desc in step3_alphas[:3]:
        print(f"    • {desc}")
        print(f"      {expr}")
    if len(step3_alphas) > 3:
        print(f"    ... và {len(step3_alphas) - 3} biến thể khác")
    
    all_alphas.extend(step3_alphas)
    
    # BƯỚC 4: Logic refactor
    print("\n[BƯỚC 4] Phá Logic (Logic Refactor & Multi-Factor Fusion)")
    step4_alphas = generate_step4_logic_refactor()
    print(f"  → Sinh {len(step4_alphas)} biến thể")
    
    # Nhóm theo sub-category
    step4_categories = {}
    for expr, desc in step4_alphas:
        category = desc.split(":")[0]
        if category not in step4_categories:
            step4_categories[category] = []
        step4_categories[category].append((expr, desc))
    
    for cat, alphas in sorted(step4_categories.items()):
        print(f"  [{cat}] {len(alphas)} biến thể")
        for expr, desc in alphas[:2]:
            print(f"    • {desc}")
            print(f"      {expr[:100]}{'...' if len(expr) > 100 else ''}")
    
    all_alphas.extend(step4_alphas)
    
    # Ghi ra file
    print(f"\n[OUTPUT] Ghi {len(all_alphas)} expressions vào {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        for expr, desc in all_alphas:
            f.write(f"# {desc}\n")
            f.write(f"{expr}\n\n")
    
    print(f"\n✓ Hoàn thành! File đã lưu tại: {output_file}")
    print(f"  Tổng số expressions: {len(all_alphas)}")
    print(f"    - Bước 2 (Param): {len(step2_alphas)}")
    print(f"    - Bước 3 (Operators): {len(step3_alphas)}")
    print(f"    - Bước 4 (Logic): {len(step4_alphas)}")
    print("\n" + "=" * 80)
    
    return all_alphas


if __name__ == "__main__":
    generate_all_4_steps()
