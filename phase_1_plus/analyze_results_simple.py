#!/usr/bin/env python3
"""
Phân tích kết quả simulation từ phase_1_plus
Tạo báo cáo tổng hợp và chi tiết - Phiên bản đơn giản không dùng pandas
"""

import json
import statistics
from collections import defaultdict

def load_simulation_results(filepath):
    """Đọc file kết quả simulation"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

def extract_records(data):
    """Trích xuất dữ liệu từ simulation results"""
    results = data['results']
    records = []
    
    for result in results:
        if result['status'] != 'COMPLETE' or not result.get('sim_data'):
            continue
            
        sim_data = result['sim_data']
        is_data = sim_data.get('is', {})
        
        if not is_data:
            continue
        
        record = {
            'alpha_id': result['alpha_id'],
            'expression': result['expression'],
            'description': result.get('description', ''),
            'step': result.get('step', 0),
            
            # Metrics chính
            'sharpe': is_data.get('sharpe', 0),
            'fitness': is_data.get('fitness', 0),
            'returns': is_data.get('returns', 0),
            'turnover': is_data.get('turnover', 0),
            'drawdown': is_data.get('drawdown', 0),
            'margin': is_data.get('margin', 0),
            'pnl': is_data.get('pnl', 0),
            
            # Regional metrics
            'glb_amer_sharpe': is_data.get('glbAmer', {}).get('sharpe', 0),
            'glb_apac_sharpe': is_data.get('glbApac', {}).get('sharpe', 0),
            'glb_emea_sharpe': is_data.get('glbEmea', {}).get('sharpe', 0),
            
            'glb_amer_returns': is_data.get('glbAmer', {}).get('returns', 0),
            'glb_apac_returns': is_data.get('glbApac', {}).get('returns', 0),
            'glb_emea_returns': is_data.get('glbEmea', {}).get('returns', 0),
            
            # Constrained metrics
            'investability_sharpe': is_data.get('investabilityConstrained', {}).get('sharpe', 0),
            'investability_returns': is_data.get('investabilityConstrained', {}).get('returns', 0),
            'investability_turnover': is_data.get('investabilityConstrained', {}).get('turnover', 0),
            
            'risk_neutralized_sharpe': is_data.get('riskNeutralized', {}).get('sharpe', 0),
            'risk_neutralized_returns': is_data.get('riskNeutralized', {}).get('returns', 0),
            
            # Checks summary
            'warnings': sum(1 for check in is_data.get('checks', []) if check.get('result') == 'WARNING'),
            'passes': sum(1 for check in is_data.get('checks', []) if check.get('result') == 'PASS'),
        }
        
        # Combined score
        record['combined_score'] = record['sharpe'] + record['fitness']
        
        records.append(record)
    
    return records

def get_stats(values):
    """Tính toán thống kê cơ bản"""
    if not values:
        return {'mean': 0, 'median': 0, 'max': 0, 'min': 0, 'std': 0}
    
    return {
        'mean': statistics.mean(values),
        'median': statistics.median(values),
        'max': max(values),
        'min': min(values),
        'std': statistics.stdev(values) if len(values) > 1 else 0
    }

def count_condition(records, key, threshold, compare='gt'):
    """Đếm số records thỏa điều kiện"""
    if compare == 'gt':
        return sum(1 for r in records if r[key] > threshold)
    elif compare == 'lt':
        return sum(1 for r in records if r[key] < threshold)
    elif compare == 'gte':
        return sum(1 for r in records if r[key] >= threshold)
    elif compare == 'lte':
        return sum(1 for r in records if r[key] <= threshold)
    return 0

def sort_records(records, key, reverse=True):
    """Sắp xếp records theo key"""
    return sorted(records, key=lambda x: x[key], reverse=reverse)

def generate_report(records, timestamp, total):
    """Tạo báo cáo chi tiết"""
    
    report = []
    report.append("=" * 100)
    report.append("BÁO CÁO PHÂN TÍCH KẾT QUẢ SIMULATION - PHASE 1 PLUS")
    report.append("=" * 100)
    report.append(f"\nThời gian simulation: {timestamp}")
    report.append(f"Tổng số alpha đã chạy: {total}")
    report.append(f"Số alpha hoàn thành: {len(records)}")
    report.append(f"Tỷ lệ thành công: {len(records)/total*100:.1f}%")
    
    # Extract values for analysis
    sharpe_vals = [r['sharpe'] for r in records]
    fitness_vals = [r['fitness'] for r in records]
    returns_vals = [r['returns'] for r in records]
    turnover_vals = [r['turnover'] for r in records]
    
    sharpe_stats = get_stats(sharpe_vals)
    fitness_stats = get_stats(fitness_vals)
    returns_stats = get_stats(returns_vals)
    turnover_stats = get_stats(turnover_vals)
    
    # PHẦN 1: TỔNG QUAN HIỆU SUẤT
    report.append("\n" + "=" * 100)
    report.append("PHẦN 1: TỔNG QUAN HIỆU SUẤT")
    report.append("=" * 100)
    
    report.append(f"\n1.1 Sharpe Ratio:")
    report.append(f"   - Trung bình: {sharpe_stats['mean']:.3f}")
    report.append(f"   - Median: {sharpe_stats['median']:.3f}")
    report.append(f"   - Cao nhất: {sharpe_stats['max']:.3f}")
    report.append(f"   - Thấp nhất: {sharpe_stats['min']:.3f}")
    report.append(f"   - Std Dev: {sharpe_stats['std']:.3f}")
    report.append(f"   - Alpha có Sharpe > 1.8: {count_condition(records, 'sharpe', 1.8)}")
    report.append(f"   - Alpha có Sharpe > 1.7: {count_condition(records, 'sharpe', 1.7)}")
    report.append(f"   - Alpha có Sharpe > 1.6: {count_condition(records, 'sharpe', 1.6)}")
    report.append(f"   - Alpha có Sharpe > 1.5: {count_condition(records, 'sharpe', 1.5)}")
    
    report.append(f"\n1.2 Fitness:")
    report.append(f"   - Trung bình: {fitness_stats['mean']:.3f}")
    report.append(f"   - Median: {fitness_stats['median']:.3f}")
    report.append(f"   - Cao nhất: {fitness_stats['max']:.3f}")
    report.append(f"   - Thấp nhất: {fitness_stats['min']:.3f}")
    report.append(f"   - Alpha có Fitness > 0.7: {count_condition(records, 'fitness', 0.7)}")
    report.append(f"   - Alpha có Fitness > 0.6: {count_condition(records, 'fitness', 0.6)}")
    report.append(f"   - Alpha có Fitness > 0.5: {count_condition(records, 'fitness', 0.5)}")
    
    report.append(f"\n1.3 Returns:")
    report.append(f"   - Trung bình: {returns_stats['mean']:.4f} ({returns_stats['mean']*100:.2f}%)")
    report.append(f"   - Median: {returns_stats['median']:.4f} ({returns_stats['median']*100:.2f}%)")
    report.append(f"   - Cao nhất: {returns_stats['max']:.4f} ({returns_stats['max']*100:.2f}%)")
    report.append(f"   - Thấp nhất: {returns_stats['min']:.4f} ({returns_stats['min']*100:.2f}%)")
    
    report.append(f"\n1.4 Turnover:")
    report.append(f"   - Trung bình: {turnover_stats['mean']:.4f}")
    report.append(f"   - Median: {turnover_stats['median']:.4f}")
    report.append(f"   - Cao nhất: {turnover_stats['max']:.4f}")
    report.append(f"   - Thấp nhất: {turnover_stats['min']:.4f}")
    
    # PHẦN 2: HIỆU SUẤT THEO VÙNG ĐỊA LÝ
    report.append("\n" + "=" * 100)
    report.append("PHẦN 2: HIỆU SUẤT THEO VÙNG ĐỊA LÝ")
    report.append("=" * 100)
    
    amer_sharpe = get_stats([r['glb_amer_sharpe'] for r in records])
    apac_sharpe = get_stats([r['glb_apac_sharpe'] for r in records])
    emea_sharpe = get_stats([r['glb_emea_sharpe'] for r in records])
    
    amer_returns = get_stats([r['glb_amer_returns'] for r in records])
    apac_returns = get_stats([r['glb_apac_returns'] for r in records])
    emea_returns = get_stats([r['glb_emea_returns'] for r in records])
    
    report.append(f"\n2.1 Americas (AMER):")
    report.append(f"   - Sharpe TB: {amer_sharpe['mean']:.3f}")
    report.append(f"   - Sharpe Max: {amer_sharpe['max']:.3f}")
    report.append(f"   - Returns TB: {amer_returns['mean']:.4f} ({amer_returns['mean']*100:.2f}%)")
    report.append(f"   - Alpha có Sharpe > 1.0: {count_condition(records, 'glb_amer_sharpe', 1.0)}")
    
    report.append(f"\n2.2 Asia Pacific (APAC):")
    report.append(f"   - Sharpe TB: {apac_sharpe['mean']:.3f}")
    report.append(f"   - Sharpe Max: {apac_sharpe['max']:.3f}")
    report.append(f"   - Returns TB: {apac_returns['mean']:.4f} ({apac_returns['mean']*100:.2f}%)")
    report.append(f"   - Alpha có Sharpe > 1.0: {count_condition(records, 'glb_apac_sharpe', 1.0)}")
    
    report.append(f"\n2.3 Europe/Middle East/Africa (EMEA):")
    report.append(f"   - Sharpe TB: {emea_sharpe['mean']:.3f}")
    report.append(f"   - Sharpe Max: {emea_sharpe['max']:.3f}")
    report.append(f"   - Returns TB: {emea_returns['mean']:.4f} ({emea_returns['mean']*100:.2f}%)")
    report.append(f"   - Alpha có Sharpe > 1.0: {count_condition(records, 'glb_emea_sharpe', 1.0)}")
    
    # PHẦN 3: TOP PERFORMERS BY SHARPE
    report.append("\n" + "=" * 100)
    report.append("PHẦN 3: TOP 20 ALPHA THEO SHARPE RATIO")
    report.append("=" * 100)
    
    top_sharpe = sort_records(records, 'sharpe')[:20]
    report.append(f"\n{'#':<4} {'Alpha ID':<13} {'Sharpe':<8} {'Fitness':<9} {'Returns':<10} {'Turnover':<10} {'Description'}")
    report.append("-" * 100)
    
    for idx, rec in enumerate(top_sharpe, 1):
        desc_short = (rec['description'][:40] + "...") if len(rec['description']) > 40 else rec['description']
        report.append(f"{idx:<4} {rec['alpha_id']:<13} {rec['sharpe']:<8.3f} {rec['fitness']:<9.3f} {rec['returns']*100:<9.2f}% {rec['turnover']:<10.4f} {desc_short}")
    
    # PHẦN 4: TOP PERFORMERS BY FITNESS
    report.append("\n" + "=" * 100)
    report.append("PHẦN 4: TOP 20 ALPHA THEO FITNESS")
    report.append("=" * 100)
    
    top_fitness = sort_records(records, 'fitness')[:20]
    report.append(f"\n{'#':<4} {'Alpha ID':<13} {'Fitness':<9} {'Sharpe':<8} {'Returns':<10} {'Turnover':<10} {'Description'}")
    report.append("-" * 100)
    
    for idx, rec in enumerate(top_fitness, 1):
        desc_short = (rec['description'][:40] + "...") if len(rec['description']) > 40 else rec['description']
        report.append(f"{idx:<4} {rec['alpha_id']:<13} {rec['fitness']:<9.3f} {rec['sharpe']:<8.3f} {rec['returns']*100:<9.2f}% {rec['turnover']:<10.4f} {desc_short}")
    
    # PHẦN 5: TOP BALANCED (Combined Score)
    report.append("\n" + "=" * 100)
    report.append("PHẦN 5: TOP 20 ALPHA CÂN BẰNG (SHARPE + FITNESS)")
    report.append("=" * 100)
    
    top_combined = sort_records(records, 'combined_score')[:20]
    report.append(f"\n{'#':<4} {'Alpha ID':<13} {'Combined':<11} {'Sharpe':<8} {'Fitness':<9} {'Returns':<10} {'Description'}")
    report.append("-" * 100)
    
    for idx, rec in enumerate(top_combined, 1):
        desc_short = (rec['description'][:40] + "...") if len(rec['description']) > 40 else rec['description']
        report.append(f"{idx:<4} {rec['alpha_id']:<13} {rec['combined_score']:<11.3f} {rec['sharpe']:<8.3f} {rec['fitness']:<9.3f} {rec['returns']*100:<9.2f}% {desc_short}")
    
    # PHẦN 6: INVESTABILITY & RISK METRICS
    report.append("\n" + "=" * 100)
    report.append("PHẦN 6: INVESTABILITY & RISK NEUTRALIZATION")
    report.append("=" * 100)
    
    invest_sharpe = get_stats([r['investability_sharpe'] for r in records])
    invest_returns = get_stats([r['investability_returns'] for r in records])
    invest_turnover = get_stats([r['investability_turnover'] for r in records])
    
    risk_sharpe = get_stats([r['risk_neutralized_sharpe'] for r in records])
    risk_returns = get_stats([r['risk_neutralized_returns'] for r in records])
    
    report.append(f"\n6.1 Investability Constrained:")
    report.append(f"   - Sharpe TB: {invest_sharpe['mean']:.3f}")
    report.append(f"   - Returns TB: {invest_returns['mean']:.4f} ({invest_returns['mean']*100:.2f}%)")
    report.append(f"   - Turnover TB: {invest_turnover['mean']:.4f}")
    report.append(f"   - Degradation từ baseline: {(sharpe_stats['mean'] - invest_sharpe['mean']):.3f}")
    
    report.append(f"\n6.2 Risk Neutralized:")
    report.append(f"   - Sharpe TB: {risk_sharpe['mean']:.3f}")
    report.append(f"   - Returns TB: {risk_returns['mean']:.4f} ({risk_returns['mean']*100:.2f}%)")
    report.append(f"   - Degradation từ baseline: {(sharpe_stats['mean'] - risk_sharpe['mean']):.3f}")
    
    # PHẦN 7: PHÂN LOẠI ALPHA
    report.append("\n" + "=" * 100)
    report.append("PHẦN 7: PHÂN LOẠI VÀ ĐÁNH GIÁ")
    report.append("=" * 100)
    
    excellent = [r for r in records if r['sharpe'] > 1.7 and r['fitness'] > 0.6]
    very_good = [r for r in records if r['sharpe'] > 1.6 and r['fitness'] > 0.5]
    good = [r for r in records if r['sharpe'] > 1.5 and r['fitness'] > 0.4]
    
    report.append(f"\n7.1 Alpha XUẤT SẮC (Sharpe > 1.7 và Fitness > 0.6):")
    report.append(f"   - Số lượng: {len(excellent)} ({len(excellent)/len(records)*100:.1f}%)")
    if excellent:
        exc_sharpe = statistics.mean([r['sharpe'] for r in excellent])
        exc_fitness = statistics.mean([r['fitness'] for r in excellent])
        exc_returns = statistics.mean([r['returns'] for r in excellent])
        report.append(f"   - Sharpe TB: {exc_sharpe:.3f}")
        report.append(f"   - Fitness TB: {exc_fitness:.3f}")
        report.append(f"   - Returns TB: {exc_returns*100:.2f}%")
        report.append(f"\n   Danh sách Alpha Xuất Sắc:")
        for idx, rec in enumerate(sort_records(excellent, 'sharpe')[:10], 1):
            report.append(f"   {idx:2d}. {rec['alpha_id']:12s} - Sharpe: {rec['sharpe']:.3f}, Fitness: {rec['fitness']:.3f}, Returns: {rec['returns']*100:.2f}%")
    
    report.append(f"\n7.2 Alpha RẤT TỐT (Sharpe > 1.6 và Fitness > 0.5):")
    report.append(f"   - Số lượng: {len(very_good)} ({len(very_good)/len(records)*100:.1f}%)")
    if very_good:
        vg_sharpe = statistics.mean([r['sharpe'] for r in very_good])
        vg_fitness = statistics.mean([r['fitness'] for r in very_good])
        report.append(f"   - Sharpe TB: {vg_sharpe:.3f}")
        report.append(f"   - Fitness TB: {vg_fitness:.3f}")
    
    report.append(f"\n7.3 Alpha TỐT (Sharpe > 1.5 và Fitness > 0.4):")
    report.append(f"   - Số lượng: {len(good)} ({len(good)/len(records)*100:.1f}%)")
    
    # Alpha cân bằng các vùng
    balanced_region = [r for r in records if 
                      r['glb_amer_sharpe'] > 1.0 and 
                      r['glb_apac_sharpe'] > 1.0 and 
                      r['glb_emea_sharpe'] > 0.5]
    
    report.append(f"\n7.4 Alpha cân bằng vùng địa lý:")
    report.append(f"   - Số lượng: {len(balanced_region)} ({len(balanced_region)/len(records)*100:.1f}%)")
    report.append(f"   (Tiêu chí: AMER > 1.0, APAC > 1.0, EMEA > 0.5)")
    
    # PHẦN 8: ĐÁNH GIÁ TỔNG THỂ
    report.append("\n" + "=" * 100)
    report.append("PHẦN 8: ĐÁNH GIÁ TỔNG THỂ VÀ KHUYẾN NGHỊ")
    report.append("=" * 100)
    
    avg_sharpe = sharpe_stats['mean']
    avg_fitness = fitness_stats['mean']
    
    if avg_sharpe > 1.6 and avg_fitness > 0.6:
        rating = "XUẤT SẮC ⭐⭐⭐⭐⭐"
    elif avg_sharpe > 1.5 and avg_fitness > 0.5:
        rating = "TỐT ⭐⭐⭐⭐"
    elif avg_sharpe > 1.4 and avg_fitness > 0.4:
        rating = "KHÁ ⭐⭐⭐"
    else:
        rating = "TRUNG BÌNH ⭐⭐"
    
    report.append(f"\n8.1 Đánh giá tổng thể:")
    report.append(f"   - Xếp hạng: {rating}")
    report.append(f"   - Sharpe trung bình: {avg_sharpe:.3f}")
    report.append(f"   - Fitness trung bình: {avg_fitness:.3f}")
    report.append(f"   - Returns trung bình: {returns_stats['mean']*100:.2f}%")
    report.append(f"   - Tỷ lệ thành công: {len(records)/total*100:.1f}%")
    
    report.append(f"\n8.2 Điểm nổi bật:")
    report.append(f"   ✓ Có {len(excellent)} alpha xuất sắc (Sharpe > 1.7, Fitness > 0.6)")
    report.append(f"   ✓ Có {len(very_good)} alpha rất tốt (Sharpe > 1.6, Fitness > 0.5)")
    report.append(f"   ✓ Sharpe cao nhất: {sharpe_stats['max']:.3f}")
    report.append(f"   ✓ Fitness cao nhất: {fitness_stats['max']:.3f}")
    report.append(f"   ✓ {len(balanced_region)} alpha cân bằng trên các vùng địa lý")
    
    report.append(f"\n8.3 Điểm cần cải thiện:")
    if emea_sharpe['mean'] < 0.8:
        report.append(f"   • Hiệu suất vùng EMEA còn yếu (Sharpe TB: {emea_sharpe['mean']:.3f})")
    if avg_sharpe < 1.6:
        report.append(f"   • Sharpe trung bình chưa đạt ngưỡng xuất sắc (< 1.6)")
    if avg_fitness < 0.6:
        report.append(f"   • Fitness trung bình cần cải thiện thêm (< 0.6)")
    
    report.append(f"\n8.4 Khuyến nghị tiếp theo:")
    report.append(f"   1. ⭐ Ưu tiên {len(excellent)} alpha xuất sắc cho production")
    report.append(f"   2. 🔍 Phân tích correlation giữa các top alpha để tránh overlap")
    report.append(f"   3. 🌍 Cải thiện hiệu suất vùng EMEA (hiện tại yếu nhất)")
    report.append(f"   4. 🧪 Thử nghiệm các biến thể của top 10 performers")
    report.append(f"   5. 🎯 Xem xét ensemble các alpha có low correlation")
    report.append(f"   6. 📊 Backtest chi tiết trên các thời kỳ khác nhau")
    report.append(f"   7. ⚡ Optimize turnover cho các alpha có turnover > 0.45")
    
    report.append("\n" + "=" * 100)
    report.append("KẾT THÚC BÁO CÁO")
    report.append("=" * 100)
    report.append(f"\nBáo cáo được tạo tự động từ {len(records)} alpha")
    report.append(f"Timestamp: {timestamp}")
    
    return '\n'.join(report)

def export_csv(records, output_dir):
    """Export các alpha tốt nhất ra CSV"""
    
    # Top 50 by Sharpe
    top_sharpe = sort_records(records, 'sharpe')[:50]
    with open(f"{output_dir}/top_50_by_sharpe.csv", 'w') as f:
        # Header
        f.write("alpha_id,sharpe,fitness,returns,turnover,expression,description\n")
        for rec in top_sharpe:
            expr = rec['expression'].replace(',', ';').replace('"', "'")
            desc = rec['description'].replace(',', ';').replace('"', "'")
            f.write(f"{rec['alpha_id']},{rec['sharpe']:.4f},{rec['fitness']:.4f},{rec['returns']:.6f},{rec['turnover']:.6f},\"{expr}\",\"{desc}\"\n")
    
    # Top 50 by Fitness
    top_fitness = sort_records(records, 'fitness')[:50]
    with open(f"{output_dir}/top_50_by_fitness.csv", 'w') as f:
        f.write("alpha_id,fitness,sharpe,returns,turnover,expression,description\n")
        for rec in top_fitness:
            expr = rec['expression'].replace(',', ';').replace('"', "'")
            desc = rec['description'].replace(',', ';').replace('"', "'")
            f.write(f"{rec['alpha_id']},{rec['fitness']:.4f},{rec['sharpe']:.4f},{rec['returns']:.6f},{rec['turnover']:.6f},\"{expr}\",\"{desc}\"\n")
    
    # Top 50 Combined
    top_combined = sort_records(records, 'combined_score')[:50]
    with open(f"{output_dir}/top_50_combined.csv", 'w') as f:
        f.write("alpha_id,combined_score,sharpe,fitness,returns,turnover,expression,description\n")
        for rec in top_combined:
            expr = rec['expression'].replace(',', ';').replace('"', "'")
            desc = rec['description'].replace(',', ';').replace('"', "'")
            f.write(f"{rec['alpha_id']},{rec['combined_score']:.4f},{rec['sharpe']:.4f},{rec['fitness']:.4f},{rec['returns']:.6f},{rec['turnover']:.6f},\"{expr}\",\"{desc}\"\n")
    
    # Excellent alphas
    excellent = [r for r in records if r['sharpe'] > 1.7 and r['fitness'] > 0.6]
    with open(f"{output_dir}/excellent_alphas.csv", 'w') as f:
        f.write("alpha_id,sharpe,fitness,returns,turnover,glb_amer_sharpe,glb_apac_sharpe,glb_emea_sharpe,expression,description\n")
        for rec in excellent:
            expr = rec['expression'].replace(',', ';').replace('"', "'")
            desc = rec['description'].replace(',', ';').replace('"', "'")
            f.write(f"{rec['alpha_id']},{rec['sharpe']:.4f},{rec['fitness']:.4f},{rec['returns']:.6f},{rec['turnover']:.6f},{rec['glb_amer_sharpe']:.4f},{rec['glb_apac_sharpe']:.4f},{rec['glb_emea_sharpe']:.4f},\"{expr}\",\"{desc}\"\n")
    
    print(f"✓ Exported {len(top_sharpe)} alphas to top_50_by_sharpe.csv")
    print(f"✓ Exported {len(top_fitness)} alphas to top_50_by_fitness.csv")
    print(f"✓ Exported {len(top_combined)} alphas to top_50_combined.csv")
    print(f"✓ Exported {len(excellent)} alphas to excellent_alphas.csv")

def main():
    # Paths
    input_file = "output/simulation_results.json"
    output_report = "output/ANALYSIS_REPORT.txt"
    output_dir = "output"
    
    print("🔍 Đang đọc dữ liệu simulation...")
    data = load_simulation_results(input_file)
    
    print("📊 Đang phân tích kết quả...")
    records = extract_records(data)
    timestamp = data['timestamp']
    total = data['total']
    
    print(f"✓ Đã phân tích {len(records)}/{total} alphas thành công")
    
    print("\n📝 Đang tạo báo cáo...")
    report = generate_report(records, timestamp, total)
    
    # Save report
    with open(output_report, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✓ Báo cáo đã được lưu tại: {output_report}")
    
    print("\n💾 Đang export CSV files...")
    export_csv(records, output_dir)
    
    # Print summary
    sharpe_vals = [r['sharpe'] for r in records]
    fitness_vals = [r['fitness'] for r in records]
    excellent = [r for r in records if r['sharpe'] > 1.7 and r['fitness'] > 0.6]
    very_good = [r for r in records if r['sharpe'] > 1.6 and r['fitness'] > 0.5]
    
    print("\n" + "=" * 80)
    print("TÓM TẮT KẾT QUẢ")
    print("=" * 80)
    print(f"📈 Tổng số alpha: {total}")
    print(f"✅ Hoàn thành: {len(records)} ({len(records)/total*100:.1f}%)")
    print(f"⭐ Sharpe trung bình: {statistics.mean(sharpe_vals):.3f}")
    print(f"💪 Fitness trung bình: {statistics.mean(fitness_vals):.3f}")
    print(f"🏆 Alpha xuất sắc (Sharpe>1.7, Fitness>0.6): {len(excellent)}")
    print(f"🥇 Alpha rất tốt (Sharpe>1.6, Fitness>0.5): {len(very_good)}")
    print(f"🔝 Sharpe cao nhất: {max(sharpe_vals):.3f}")
    print(f"💎 Fitness cao nhất: {max(fitness_vals):.3f}")
    print("=" * 80)
    print(f"\n✅ Hoàn thành! Xem báo cáo chi tiết tại: {output_report}")
    
    return records

if __name__ == "__main__":
    records = main()
