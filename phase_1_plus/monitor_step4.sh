#!/bin/bash
# Monitor Step 4 simulation

LOG="step4_new.log"

echo "================================================"
echo "  STEP 4 SIMULATION MONITOR"
echo "================================================"
echo ""

if pgrep -f "phase_1_plus_sim.py" > /dev/null; then
    echo "✓ Running (PID: $(pgrep -f phase_1_plus_sim.py))"
else
    echo "✗ Not running"
fi

echo ""

if [ -f "$LOG" ]; then
    BATCHES=$(grep -c "Batch simulate stream complete" "$LOG")
    TOTAL_BATCHES=22  # 64 alphas / 3 = 21.33 → 22 batches
    
    echo "Progress: $BATCHES / $TOTAL_BATCHES batches"
    
    if [ "$BATCHES" -gt 0 ]; then
        PERCENT=$((BATCHES * 100 / TOTAL_BATCHES))
        echo "Complete: ${PERCENT}%"
    fi
    
    echo ""
    echo "Recent results:"
    tail -20 "$LOG" | grep -E "✓|✗" | tail -5
    
    echo ""
    echo "Latest log:"
    tail -3 "$LOG" | grep -v "INFO"
else
    echo "Log file not found: $LOG"
fi

echo ""
echo "================================================"
echo "Commands:"
echo "  tail -f $LOG"
echo "  pkill -f phase_1_plus_sim.py"
echo "================================================"
