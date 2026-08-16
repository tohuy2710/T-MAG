# Phase 1 Setup Complete ✓

## Summary

Phase 1 đã được thiết lập thành công để simulate hàng loạt alpha với template **Return Reversal**.

**Môi trường:** GLB / TOPDIV3000 / Delay 1  
**Auto-submit:** DISABLED (chỉ simulate, không tự động submit)

## Template: quarterly_return_reversal

### Description
Conditional price reversal với multiple lookback periods và neutralization groups. Test reversal effects across different timeframes (3-20 days) và group structures để tìm optimal mean-reversion parameters.

### Skeleton
```
group_rank(-ts_delta({field}, {lookback}), {group})
```

### Parameters
- **field**: close, returns, vwap, open (4 options)
- **lookback**: 3, 5, 10, 20 days (4 options)
- **group**: industry, subindustry, sector (3 options)
- **decay**: 0, 4, 8 (3 options)
- **truncation**: 0.08, 0.10 (2 options)
- **neutralization**: SLOW, FAST, SLOW_AND_FAST, SUBINDUSTRY, CROWDING (5 from target)

### Total Possible Combinations
4 fields × 4 lookbacks × 3 groups × 3 decays × 2 truncations × 5 neutralizations = **1,440 possible candidates**

## File Structure

```
phase_1/
├── PHASE_1_SETUP_COMPLETE.md      # This file
├── README_PHASE_1.md              # Detailed documentation
├── QUICK_START.md                 # Quick start guide
├── __init__.py                    # Module init
├── phase_1_config.py              # Configuration
├── phase_1_sim.py                 # Main simulation script
├── phase_1_utils.py               # Utility functions
└── output/                        # Output directory
    ├── simulation_results.json    # Will be created after simulation
    └── individual/                # Individual alpha results
```

## Quick Commands

### 1. Run default simulation (20 candidates)
```bash
cd /home/tohuy2710/T-MAG/phase_1
python3 phase_1_sim.py
```

### 2. Run với 50 candidates
```bash
python3 phase_1_sim.py --max-per-template 50 --batch-size 20
```

### 3. High throughput (100 candidates, high concurrency)
```bash
python3 phase_1_sim.py --max-per-template 100 --batch-size 25 --max-concurrent 5
```

### 4. View results
```bash
# Summary stats
cat output/simulation_results.json | jq '{total:.total_simulated, passed:.passed, failed:.failed}'

# Top 10 by Sharpe
cat output/simulation_results.json | jq -r '.results[] | select(.status=="COMPLETE") | [.alpha_id, .sim_data.is.sharpe, .sim_data.is.fitness, .sim_data.is.turnover] | @tsv' | sort -k2 -rn | head -10
```

## Verification Checklist

- [x] Template file created: `templates/quarterly_return_reversal.json`
- [x] Phase 1 directory structure created
- [x] Configuration file with proper defaults
- [x] Simulation script with batch processing
- [x] Utility functions for results management
- [x] Documentation (README, QUICK_START)
- [x] Template loads successfully
- [x] Candidate generation works (tested with 10 candidates)
- [x] Field validator integration
- [x] Research target configured (GLB/TOPDIV3000/Delay1)
- [x] Auto-submit DISABLED

## Expected Behavior

### Candidate Generation
- Generates combinations of field, lookback, group, decay, truncation
- Each combination is tested with multiple neutralizations from target config
- Field validator ensures all fields exist in data reference
- Max candidates controlled by `--max-per-template` flag

### Simulation
- Batches candidates for efficient processing
- Streams results as they complete
- Saves individual results to `output/individual/<alpha_id>.json`
- Aggregates all results to `output/simulation_results.json`
- Prints top performers at the end

### Output Format
Each result includes:
- `expression`: The alpha expression
- `template_id`: quarterly_return_reversal
- `status`: COMPLETE or error status
- `alpha_id`: BRAIN-assigned alpha ID
- `sim_data.is.sharpe`: In-sample Sharpe ratio
- `sim_data.is.fitness`: Fitness score
- `sim_data.is.turnover`: Turnover metric
- `simulated_at`: Timestamp

## Next Steps

1. **Run initial batch**:
   ```bash
   cd /home/tohuy2710/T-MAG/phase_1
   python3 phase_1_sim.py --max-per-template 30
   ```

2. **Review results**:
   - Check success rate
   - Identify top performers by Sharpe
   - Analyze parameter patterns (which lookbacks/groups work best)

3. **Manual submission** (if desired):
   - Identify alphas with Sharpe > threshold (e.g., 1.5)
   - Submit manually using BRAIN interface or submit script
   - Track submitted alphas

4. **Iterate**:
   - Adjust template parameters based on findings
   - Create variations (e.g., volume-weighted reversals)
   - Expand to phase_2 with new templates

## Troubleshooting

### No candidates generated
```bash
# Verify template
cat ../templates/quarterly_return_reversal.json | jq .

# Check field reference
python3 -c "from scripts.research_target import load_target; print(load_target().require_fields_reference())"
```

### Simulation failures
```bash
# Check BRAIN API
cd ../scripts
python3 check_quota.py

# Verify credentials
cat ../.env | grep BRAIN
```

### Import errors
```bash
# Ensure you're in phase_1 directory
cd /home/tohuy2710/T-MAG/phase_1

# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"
```

## Configuration Override

Use environment variables to override defaults:

```bash
export PHASE_1_BATCH_SIZE=20
export PHASE_1_MAX_PER_TEMPLATE=50
export PHASE_1_MAX_CONCURRENT=5
export PHASE_1_LOG_LEVEL=DEBUG

python3 phase_1_sim.py
```

## Notes

- Template đã được simplify từ seasonal/quarterly conditional thành multi-parameter reversal vì không có `quarter_indicator_code` field trong data
- Template vẫn test comprehensive parameter space cho reversal strategies
- Dựa trên proven patterns từ BRAIN public examples (tương tự ashare_short_reversal)
- GLB/TOPDIV3000 environment có thể có reversal effects khác A-shares, cần experimental validation

---

**Status**: ✓ Ready for simulation  
**Created**: 2026-08-15  
**Last Updated**: 2026-08-15
