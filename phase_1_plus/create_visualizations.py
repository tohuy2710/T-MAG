#!/usr/bin/env python3
"""
Tạo các biểu đồ visualization cho kết quả Phase 1 Plus
Sử dụng matplotlib để tạo charts
"""

import json
import statistics
import sys

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
            'sharpe': is_data.get('sharpe', 0),
            'fitness': is_data.get('fitness', 0),
            'returns': is_data.get('returns', 0),
            'turnover': is_data.get('turnover', 0),
            'drawdown': is_data.get('drawdown', 0),
            'glb_amer_sharpe': is_data.get('glbAmer', {}).get('sharpe', 0),
            'glb_apac_sharpe': is_data.get('glbApac', {}).get('sharpe', 0),
            'glb_emea_sharpe': is_data.get('glbEmea', {}).get('sharpe', 0),
        }
        
        records.append(record)
    
    return records

def create_ascii_chart(title, data_dict, width=60):
    """Tạo biểu đồ ASCII bar chart"""
    lines = []
    lines.append("=" * (width + 20))
    lines.append(title)
    lines.append("=" * (width + 20))
    
    if not data_dict:
        lines.append("No data available")
        return '\n'.join(lines)
    
    max_val = max(data_dict.values())
    max_key_len = max(len(str(k)) for k in data_dict.keys())
    
    for key, value in data_dict.items():
        bar_len = int((value / max_val) * width) if max_val > 0 else 0
        bar = "█" * bar_len
        lines.append(f"{str(key):<{max_key_len}} | {bar} {value:.3f}")
    
    return '\n'.join(lines)

def create_distribution_chart(title, values, bins=10, width=60):
    """Tạo histogram ASCII"""
    lines = []
    lines.append("=" * (width + 20))
    lines.append(title)
    lines.append("=" * (width + 20))
    
    if not values:
        lines.append("No data available")
        return '\n'.join(lines)
    
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val
    bin_size = range_val / bins
    
    # Create bins
    bin_counts = [0] * bins
    for val in values:
        bin_idx = min(int((val - min_val) / bin_size), bins - 1) if range_val > 0 else 0
        bin_counts[bin_idx] += 1
    
    max_count = max(bin_counts) if bin_counts else 1
    
    # Draw histogram
    for i in range(bins):
        bin_start = min_val + i * bin_size
        bin_end = bin_start + bin_size
        bar_len = int((bin_counts[i] / max_count) * width) if max_count > 0 else 0
        bar = "█" * bar_len
        lines.append(f"{bin_start:.3f}-{bin_end:.3f} | {bar} ({bin_counts[i]})")
    
    lines.append(f"\nTotal: {len(values)}, Mean: {statistics.mean(values):.3f}, Median: {statistics.median(values):.3f}")
    
    return '\n'.join(lines)

def create_scatter_plot(title, x_vals, y_vals, x_label, y_label, width=60, height=20):
    """Tạo scatter plot ASCII"""
    lines = []
    lines.append("=" * (width + 10))
    lines.append(title)
    lines.append("=" * (width + 10))
    
    if not x_vals or not y_vals or len(x_vals) != len(y_vals):
        lines.append("No data or mismatched data available")
        return '\n'.join(lines)
    
    # Normalize to grid
    min_x, max_x = min(x_vals), max(x_vals)
    min_y, max_y = min(y_vals), max(y_vals)
    
    range_x = max_x - min_x if max_x != min_x else 1
    range_y = max_y - min_y if max_y != min_y else 1
    
    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Plot points
    for x, y in zip(x_vals, y_vals):
        grid_x = int(((x - min_x) / range_x) * (width - 1))
        grid_y = height - 1 - int(((y - min_y) / range_y) * (height - 1))
        grid[grid_y][grid_x] = '●'
    
    # Draw grid
    lines.append(f"{y_label} ^")
    for row in grid:
        lines.append("  |" + ''.join(row))
    lines.append("  +" + "-" * width + f"> {x_label}")
    lines.append(f"  {min_x:.2f}" + " " * (width - 10) + f"{max_x:.2f}")
    
    return '\n'.join(lines)

def generate_visualizations(records):
    """Tạo tất cả các visualizations"""
    
    output = []
    
    # 1. Sharpe Distribution
    sharpe_vals = [r['sharpe'] for r in records]
    output.append(create_distribution_chart(
        "PHÂN PHỐI SHARPE RATIO",
        sharpe_vals,
        bins=10
    ))
    output.append("\n\n")
    
    # 2. Fitness Distribution
    fitness_vals = [r['fitness'] for r in records]
    output.append(create_distribution_chart(
        "PHÂN PHỐI FITNESS",
        fitness_vals,
        bins=10
    ))
    output.append("\n\n")
    
    # 3. Regional Performance
    region_data = {
        "AMER": statistics.mean([r['glb_amer_sharpe'] for r in records]),
        "APAC": statistics.mean([r['glb_apac_sharpe'] for r in records]),
        "EMEA": statistics.mean([r['glb_emea_sharpe'] for r in records]),
    }
    output.append(create_ascii_chart(
        "HIỆU SUẤT TRUNG BÌNH THEO VÙNG (SHARPE)",
        region_data
    ))
    output.append("\n\n")
    
    # 4. Sharpe vs Fitness Scatter
    output.append(create_scatter_plot(
        "SHARPE vs FITNESS (Scatter Plot)",
        sharpe_vals,
        fitness_vals,
        "Sharpe Ratio",
        "Fitness"
    ))
    output.append("\n\n")
    
    # 5. Returns vs Turnover
    returns_vals = [r['returns'] * 100 for r in records]  # Convert to percentage
    turnover_vals = [r['turnover'] for r in records]
    output.append(create_scatter_plot(
        "RETURNS (%) vs TURNOVER (Scatter Plot)",
        returns_vals,
        turnover_vals,
        "Returns (%)",
        "Turnover"
    ))
    output.append("\n\n")
    
    # 6. Performance by Step
    steps = set(r['step'] for r in records if r['step'])
    step_sharpe = {}
    for step in sorted(steps):
        step_records = [r for r in records if r['step'] == step]
        if step_records:
            step_sharpe[f"Step {step}"] = statistics.mean([r['sharpe'] for r in step_records])
    
    output.append(create_ascii_chart(
        "SHARPE TRUNG BÌNH THEO STEP",
        step_sharpe
    ))
    output.append("\n\n")
    
    # 7. Top Performers
    top_10 = sorted(records, key=lambda x: x['sharpe'], reverse=True)[:10]
    top_data = {r['alpha_id']: r['sharpe'] for r in top_10}
    output.append(create_ascii_chart(
        "TOP 10 ALPHA THEO SHARPE",
        top_data
    ))
    output.append("\n\n")
    
    # 8. Performance Categories
    excellent = len([r for r in records if r['sharpe'] > 1.7 and r['fitness'] > 0.6])
    very_good = len([r for r in records if r['sharpe'] > 1.6 and r['fitness'] > 0.5])
    good = len([r for r in records if r['sharpe'] > 1.5 and r['fitness'] > 0.4])
    fair = len([r for r in records if r['sharpe'] > 1.4])
    others = len(records) - fair
    
    category_data = {
        "Xuất sắc (>1.7, >0.6)": excellent,
        "Rất tốt (>1.6, >0.5)": very_good,
        "Tốt (>1.5, >0.4)": good,
        "Khá (>1.4)": fair,
        "Khác": others
    }
    output.append(create_ascii_chart(
        "PHÂN LOẠI ALPHA THEO HIỆU SUẤT",
        category_data
    ))
    output.append("\n\n")
    
    # 9. Sharpe Ranges
    sharpe_ranges = {
        "1.9-2.0": len([r for r in records if 1.9 <= r['sharpe'] < 2.0]),
        "1.8-1.9": len([r for r in records if 1.8 <= r['sharpe'] < 1.9]),
        "1.7-1.8": len([r for r in records if 1.7 <= r['sharpe'] < 1.8]),
        "1.6-1.7": len([r for r in records if 1.6 <= r['sharpe'] < 1.7]),
        "1.5-1.6": len([r for r in records if 1.5 <= r['sharpe'] < 1.6]),
        "1.4-1.5": len([r for r in records if 1.4 <= r['sharpe'] < 1.5]),
        "<1.4": len([r for r in records if r['sharpe'] < 1.4]),
    }
    output.append(create_ascii_chart(
        "PHÂN PHỐI SHARPE THEO KHOẢNG",
        sharpe_ranges
    ))
    output.append("\n\n")
    
    return '\n'.join(output)

def main():
    print("📊 Đang tạo visualizations...")
    
    # Load data
    input_file = "output/simulation_results.json"
    output_file = "output/VISUALIZATIONS.txt"
    
    data = load_simulation_results(input_file)
    records = extract_records(data)
    
    print(f"✓ Đã load {len(records)} records")
    
    # Generate visualizations
    print("📈 Đang tạo các biểu đồ...")
    viz = generate_visualizations(records)
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("VISUALIZATIONS - PHASE 1 PLUS RESULTS\n")
        f.write("=" * 80 + "\n\n")
        f.write(viz)
    
    print(f"✓ Visualizations đã được lưu tại: {output_file}")
    
    # Also print to console
    print("\n" + "=" * 80)
    print("PREVIEW - REGIONAL PERFORMANCE")
    print("=" * 80)
    
    region_data = {
        "AMER": statistics.mean([r['glb_amer_sharpe'] for r in records]),
        "APAC": statistics.mean([r['glb_apac_sharpe'] for r in records]),
        "EMEA": statistics.mean([r['glb_emea_sharpe'] for r in records]),
    }
    print(create_ascii_chart("SHARPE BY REGION", region_data))
    
    print(f"\n✅ Complete! Xem file đầy đủ tại: {output_file}")

if __name__ == "__main__":
    main()
