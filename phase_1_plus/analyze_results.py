#!/usr/bin/env python3
"""
Phân tích kết quả simulation từ phase_1_plus
Tạo báo cáo tổng hợp và chi tiết
"""

import json
from datetime import datetime
from collections import defaultdict
import statistics
import sys

def load_simulation_results(filepath):
    """Đọc file kết quả simulation"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

def analyze_results(data):
    """Phân tích toàn bộ kết quả"""
    
    results = data['results']
    total = data['total']
    timestamp = data['timestamp']
    
    # Tạo list records
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
            'description': result['description'],
            'step': result['step'],
            
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
            
            # Combined score
            'combined_score': is_data.get('sharpe', 0) + is_data.get('fitness', 0)
        }
        
        records.append(record)
    
    return records, timestamp, total

def get_values(records, key):
    """Extract values for a key from records"""
    return [r[key] for r in records if key in r]

def safe_mean(values):
    """Calculate mean safely"""
    return statistics.mean(values) if values else 0

def safe_median(values):
    """Calculate median safely"""
    return statistics.median(values) if values else 0

def safe_stdev(values):
    """Calculate stdev safely"""
    return statistics.stdev(values) if len(values) > 1 else 0

def safe_max(values):
    """Get max safely"""
    return max(values) if values else 0

def safe_min(values):
    """Get min safely"""
    return min(values) if values else 0

def generate_report(records, timestamp, total, output_file):
    """Tạo báo cáo chi tiết"""
    
    report = []
    report.append("=" * 80)
    report.append("BÁO CÁO PHÂN TÍCH KẾT QUẢ SIMULATION - PHASE 1 PLUS")
    report.append("=" * 80)
    report.append(f"\nThời gian: {timestamp}")
    report.append(f"Tổng số alpha: {total}")
    report.append(f"Số alpha hoàn thành: {len(df)}")
    report.append(f"Tỷ lệ thành công: {len(df)/total*100:.1f}%")
    
    # PHẦN 1: TỔNG QUAN HIỆU SUẤT
    report.append("\n" + "=" * 80)
    report.append("PHẦN 1: TỔNG QUAN HIỆU SUẤT")
    report.append("=" * 80)
    
    report.append(f"\n1.1 Sharpe Ratio:")
    report.append(f"   - Trung bình: {df['sharpe'].mean():.3f}")
    report.append(f"   - Median: {df['sharpe'].median():.3f}")
    report.append(f"   - Cao nhất: {df['sharpe'].max():.3f}")
    report.append(f"   - Thấp nhất: {df['sharpe'].min():.3f}")
    report.append(f"   - Std Dev: {df['sharpe'].std():.3f}")
    report.append(f"   - Alpha có Sharpe > 1.8: {(df['sharpe'] > 1.8).sum()}")
    report.append(f"   - Alpha có Sharpe > 1.7: {(df['sharpe'] > 1.7).sum()}")
    report.append(f"   - Alpha có Sharpe > 1.6: {(df['sharpe'] > 1.6).sum()}")
    
    report.append(f"\n1.2 Fitness:")
    report.append(f"   - Trung bình: {df['fitness'].mean():.3f}")
    report.append(f"   - Median: {df['fitness'].median():.3f}")
    report.append(f"   - Cao nhất: {df['fitness'].max():.3f}")
    report.append(f"   - Thấp nhất: {df['fitness'].min():.3f}")
    report.append(f"   - Alpha có Fitness > 0.7: {(df['fitness'] > 0.7).sum()}")
    report.append(f"   - Alpha có Fitness > 0.6: {(df['fitness'] > 0.6).sum()}")
    
    report.append(f"\n1.3 Returns:")
    report.append(f"   - Trung bình: {df['returns'].mean():.4f} ({df['returns'].mean()*100:.2f}%)")
    report.append(f"   - Median: {df['returns'].median():.4f} ({df['returns'].median()*100:.2f}%)")
    report.append(f"   - Cao nhất: {df['returns'].max():.4f} ({df['returns'].max()*100:.2f}%)")
    report.append(f"   - Thấp nhất: {df['returns'].min():.4f} ({df['returns'].min()*100:.2f}%)")
    
    report.append(f"\n1.4 Turnover:")
    report.append(f"   - Trung bình: {df['turnover'].mean():.4f}")
    report.append(f"   - Median: {df['turnover'].median():.4f}")
    report.append(f"   - Cao nhất: {df['turnover'].max():.4f}")
    report.append(f"   - Thấp nhất: {df['turnover'].min():.4f}")
    
    # PHẦN 2: HIỆU SUẤT THEO VÙNG ĐỊA LÝ
    report.append("\n" + "=" * 80)
    report.append("PHẦN 2: HIỆU SUẤT THEO VÙNG ĐỊA LÝ")
    report.append("=" * 80)
    
    report.append(f"\n2.1 Americas (AMER):")
    report.append(f"   - Sharpe TB: {df['glb_amer_sharpe'].mean():.3f}")
    report.append(f"   - Returns TB: {df['glb_amer_returns'].mean():.4f} ({df['glb_amer_returns'].mean()*100:.2f}%)")
    report.append(f"   - Alpha có Sharpe > 1.0: {(df['glb_amer_sharpe'] > 1.0).sum()}")
    
    report.append(f"\n2.2 Asia Pacific (APAC):")
    report.append(f"   - Sharpe TB: {df['glb_apac_sharpe'].mean():.3f}")
    report.append(f"   - Returns TB: {df['glb_apac_returns'].mean():.4f} ({df['glb_apac_returns'].mean()*100:.2f}%)")
    report.append(f"   - Alpha có Sharpe > 1.0: {(df['glb_apac_sharpe'] > 1.0).sum()}")
    
    report.append(f"\n2.3 Europe/Middle East/Africa (EMEA):")
    report.append(f"   - Sharpe TB: {df['glb_emea_sharpe'].mean():.3f}")
    report.append(f"   - Returns TB: {df['glb_emea_returns'].mean():.4f} ({df['glb_emea_returns'].mean()*100:.2f}%)")
    report.append(f"   - Alpha có Sharpe > 1.0: {(df['glb_emea_sharpe'] > 1.0).sum()}")
    
    # PHẦN 3: TOP PERFORMERS
    report.append("\n" + "=" * 80)
    report.append("PHẦN 3: TOP 20 ALPHA THEO SHARPE RATIO")
    report.append("=" * 80)
    
    top_sharpe = df.nlargest(20, 'sharpe')
    report.append(f"\n{'Rank':<5} {'Alpha ID':<12} {'Sharpe':<8} {'Fitness':<9} {'Returns':<10} {'Turnover':<10} {'Expression'}")
    report.append("-" * 150)
    
    for idx, row in enumerate(top_sharpe.itertuples(), 1):
        expr_short = row.expression[:60] + "..." if len(row.expression) > 60 else row.expression
        report.append(f"{idx:<5} {row.alpha_id:<12} {row.sharpe:<8.3f} {row.fitness:<9.3f} {row.returns*100:<9.2f}% {row.turnover:<10.4f} {expr_short}")
    
    # PHẦN 4: TOP PERFORMERS BY FITNESS
    report.append("\n" + "=" * 80)
    report.append("PHẦN 4: TOP 20 ALPHA THEO FITNESS")
    report.append("=" * 80)
    
    top_fitness = df.nlargest(20, 'fitness')
    report.append(f"\n{'Rank':<5} {'Alpha ID':<12} {'Fitness':<9} {'Sharpe':<8} {'Returns':<10} {'Turnover':<10} {'Expression'}")
    report.append("-" * 150)
    
    for idx, row in enumerate(top_fitness.itertuples(), 1):
        expr_short = row.expression[:60] + "..." if len(row.expression) > 60 else row.expression
        report.append(f"{idx:<5} {row.alpha_id:<12} {row.fitness:<9.3f} {row.sharpe:<8.3f} {row.returns*100:<9.2f}% {row.turnover:<10.4f} {expr_short}")
    
    # PHẦN 5: BALANCED PERFORMERS (Sharpe + Fitness)
    report.append("\n" + "=" * 80)
    report.append("PHẦN 5: TOP 20 ALPHA CÂN BẰNG (SHARPE + FITNESS)")
    report.append("=" * 80)
    
    df['combined_score'] = df['sharpe'] + df['fitness']
    top_balanced = df.nlargest(20, 'combined_score')
    report.append(f"\n{'Rank':<5} {'Alpha ID':<12} {'Combined':<10} {'Sharpe':<8} {'Fitness':<9} {'Returns':<10} {'Expression'}")
    report.append("-" * 150)
    
    for idx, row in enumerate(top_balanced.itertuples(), 1):
        expr_short = row.expression[:60] + "..." if len(row.expression) > 60 else row.expression
        combined = row.sharpe + row.fitness
        report.append(f"{idx:<5} {row.alpha_id:<12} {combined:<10.3f} {row.sharpe:<8.3f} {row.fitness:<9.3f} {row.returns*100:<9.2f}% {expr_short}")
    
    # PHẦN 6: PHÂN TÍCH CẢNH BÁO
    report.append("\n" + "=" * 80)
    report.append("PHẦN 6: PHÂN TÍCH CẢNH BÁO VÀ KIỂM TRA")
    report.append("=" * 80)
    
    report.append(f"\nSố cảnh báo trung bình mỗi alpha: {df['warnings'].mean():.2f}")
    report.append(f"Số kiểm tra PASS trung bình: {df['passes'].mean():.2f}")
    report.append(f"Alpha ít cảnh báo nhất: {df['warnings'].min()} cảnh báo")
    report.append(f"Alpha nhiều cảnh báo nhất: {df['warnings'].max()} cảnh báo")
    
    # PHẦN 7: PHÂN TÍCH THEO STEP
    report.append("\n" + "=" * 80)
    report.append("PHẦN 7: PHÂN TÍCH THEO STEP")
    report.append("=" * 80)
    
    step_analysis = df.groupby('step').agg({
        'sharpe': ['count', 'mean', 'std', 'max'],
        'fitness': ['mean', 'max'],
        'returns': ['mean', 'max']
    })
    
    report.append("\nThống kê theo Step:")
    report.append(step_analysis.to_string())
    
    # PHẦN 8: INVESTABILITY & RISK METRICS
    report.append("\n" + "=" * 80)
    report.append("PHẦN 8: INVESTABILITY & RISK NEUTRALIZATION")
    report.append("=" * 80)
    
    report.append(f"\n8.1 Investability Constrained:")
    report.append(f"   - Sharpe TB: {df['investability_sharpe'].mean():.3f}")
    report.append(f"   - Returns TB: {df['investability_returns'].mean():.4f} ({df['investability_returns'].mean()*100:.2f}%)")
    report.append(f"   - Turnover TB: {df['investability_turnover'].mean():.4f}")
    report.append(f"   - Sharpe degradation từ baseline: {(df['sharpe'].mean() - df['investability_sharpe'].mean()):.3f}")
    
    report.append(f"\n8.2 Risk Neutralized:")
    report.append(f"   - Sharpe TB: {df['risk_neutralized_sharpe'].mean():.3f}")
    report.append(f"   - Returns TB: {df['risk_neutralized_returns'].mean():.4f} ({df['risk_neutralized_returns'].mean()*100:.2f}%)")
    report.append(f"   - Sharpe degradation từ baseline: {(df['sharpe'].mean() - df['risk_neutralized_sharpe'].mean()):.3f}")
    
    # PHẦN 9: PHÂN TÍCH CORRELATION GIỮA CÁC METRICS
    report.append("\n" + "=" * 80)
    report.append("PHẦN 9: CORRELATION GIỮA CÁC METRICS CHÍNH")
    report.append("=" * 80)
    
    key_metrics = ['sharpe', 'fitness', 'returns', 'turnover', 'drawdown']
    corr_matrix = df[key_metrics].corr()
    report.append("\n" + corr_matrix.to_string())
    
    # PHẦN 10: RECOMMENDATION
    report.append("\n" + "=" * 80)
    report.append("PHẦN 10: KHUYẾN NGHỊ VÀ ĐÁNH GIÁ")
    report.append("=" * 80)
    
    # Lọc alpha xuất sắc
    excellent_alphas = df[(df['sharpe'] > 1.7) & (df['fitness'] > 0.6)]
    good_alphas = df[(df['sharpe'] > 1.6) & (df['fitness'] > 0.5)]
    
    report.append(f"\n10.1 Alpha Xuất Sắc (Sharpe > 1.7 và Fitness > 0.6):")
    report.append(f"   - Số lượng: {len(excellent_alphas)}")
    if len(excellent_alphas) > 0:
        report.append(f"   - Sharpe TB: {excellent_alphas['sharpe'].mean():.3f}")
        report.append(f"   - Fitness TB: {excellent_alphas['fitness'].mean():.3f}")
        report.append(f"   - Returns TB: {excellent_alphas['returns'].mean()*100:.2f}%")
        report.append("\n   Danh sách:")
        for idx, row in enumerate(excellent_alphas.itertuples(), 1):
            report.append(f"   {idx}. {row.alpha_id}: Sharpe={row.sharpe:.3f}, Fitness={row.fitness:.3f}")
    
    report.append(f"\n10.2 Alpha Tốt (Sharpe > 1.6 và Fitness > 0.5):")
    report.append(f"   - Số lượng: {len(good_alphas)}")
    if len(good_alphas) > 0:
        report.append(f"   - Sharpe TB: {good_alphas['sharpe'].mean():.3f}")
        report.append(f"   - Fitness TB: {good_alphas['fitness'].mean():.3f}")
    
    # Phân tích vùng địa lý
    best_region_alphas = df[
        (df['glb_amer_sharpe'] > 1.0) & 
        (df['glb_apac_sharpe'] > 1.0) & 
        (df['glb_emea_sharpe'] > 0.5)
    ]
    
    report.append(f"\n10.3 Alpha cân bằng giữa các vùng địa lý:")
    report.append(f"   - Số lượng: {len(best_region_alphas)}")
    report.append(f"   (Tiêu chí: AMER > 1.0, APAC > 1.0, EMEA > 0.5)")
    
    # Đánh giá chung
    report.append(f"\n10.4 Đánh giá chung:")
    avg_sharpe = df['sharpe'].mean()
    avg_fitness = df['fitness'].mean()
    
    if avg_sharpe > 1.6 and avg_fitness > 0.6:
        rating = "XUẤT SẮC"
    elif avg_sharpe > 1.5 and avg_fitness > 0.5:
        rating = "TỐT"
    elif avg_sharpe > 1.4:
        rating = "KHÁ"
    else:
        rating = "TRUNG BÌNH"
    
    report.append(f"   - Đánh giá tổng thể: {rating}")
    report.append(f"   - Sharpe trung bình: {avg_sharpe:.3f}")
    report.append(f"   - Fitness trung bình: {avg_fitness:.3f}")
    report.append(f"   - Tỷ lệ thành công cao")
    
    report.append("\n10.5 Khuyến nghị tiếp theo:")
    report.append("   1. Tập trung vào các alpha có Sharpe > 1.7 và Fitness > 0.6")
    report.append("   2. Kiểm tra độ tương quan giữa các alpha tốt nhất")
    report.append("   3. Xem xét tăng cường hiệu suất vùng EMEA (thường yếu nhất)")
    report.append("   4. Thử nghiệm các biến thể của top performers")
    report.append("   5. Cân nhắc ensemble các alpha không tương quan cao")
    
    report.append("\n" + "=" * 80)
    report.append("KẾT THÚC BÁO CÁO")
    report.append("=" * 80)
    
    # Ghi báo cáo ra file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    return '\n'.join(report)

def export_top_alphas_csv(df, output_dir):
    """Export các alpha tốt nhất ra CSV"""
    
    # Top 50 by Sharpe
    top_sharpe = df.nlargest(50, 'sharpe')
    top_sharpe.to_csv(f"{output_dir}/top_50_by_sharpe.csv", index=False)
    
    # Top 50 by Fitness
    top_fitness = df.nlargest(50, 'fitness')
    top_fitness.to_csv(f"{output_dir}/top_50_by_fitness.csv", index=False)
    
    # Top 50 combined
    df['combined_score'] = df['sharpe'] + df['fitness']
    top_combined = df.nlargest(50, 'combined_score')
    top_combined.to_csv(f"{output_dir}/top_50_combined.csv", index=False)
    
    # Excellent alphas
    excellent = df[(df['sharpe'] > 1.7) & (df['fitness'] > 0.6)]
    excellent.to_csv(f"{output_dir}/excellent_alphas.csv", index=False)
    
    print(f"✓ Exported CSV files to {output_dir}")

def main():
    # Paths
    input_file = "output/simulation_results.json"
    output_report = "output/ANALYSIS_REPORT.txt"
    output_dir = "output"
    
    print("Đang đọc dữ liệu simulation...")
    data = load_simulation_results(input_file)
    
    print("Đang phân tích kết quả...")
    df, timestamp, total = analyze_results(data)
    
    print(f"Đã phân tích {len(df)} alphas thành công")
    
    print("\nĐang tạo báo cáo...")
    report = generate_report(df, timestamp, total, output_report)
    
    print(f"\n✓ Báo cáo đã được lưu tại: {output_report}")
    
    print("\nĐang export CSV files...")
    export_top_alphas_csv(df, output_dir)
    
    # In tóm tắt ra console
    print("\n" + "=" * 80)
    print("TÓM TẮT KẾT QUẢ")
    print("=" * 80)
    print(f"Tổng số alpha: {total}")
    print(f"Hoàn thành: {len(df)}")
    print(f"Sharpe trung bình: {df['sharpe'].mean():.3f}")
    print(f"Fitness trung bình: {df['fitness'].mean():.3f}")
    print(f"Alpha xuất sắc (Sharpe>1.7, Fitness>0.6): {len(df[(df['sharpe'] > 1.7) & (df['fitness'] > 0.6)])}")
    print(f"Alpha tốt (Sharpe>1.6, Fitness>0.5): {len(df[(df['sharpe'] > 1.6) & (df['fitness'] > 0.5)])}")
    print("=" * 80)
    
    return df

if __name__ == "__main__":
    df = main()
