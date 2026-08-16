#!/bin/bash
# Script kiểm tra tiến độ simulation

LOG_FILE="full_simulation_3x.log"

echo "================================================"
echo "  PHASE 1 PLUS - SIMULATION PROGRESS"
echo "================================================"
echo ""

# Kiểm tra process đang chạy
if pgrep -f "phase_1_plus_sim.py" > /dev/null; then
    echo "✓ Simulation đang chạy"
    PID=$(pgrep -f "phase_1_plus_sim.py")
    echo "  PID: $PID"
else
    echo "✗ Simulation không chạy"
fi

echo ""

# Đếm số alphas đã hoàn thành
if [ -f "$LOG_FILE" ]; then
    TOTAL=$(grep "Đã load" "$LOG_FILE" | tail -1 | grep -oP '\d+(?= candidates)')
    COMPLETED=$(grep -c "Batch simulate stream complete" "$LOG_FILE")
    SUCCESS=$(grep -c "✓" "$LOG_FILE" | head -1)
    ERROR=$(grep -c "✗ ERROR" "$LOG_FILE")
    
    echo "Tổng số alphas: $TOTAL"
    echo "Đã xử lý: $COMPLETED / $TOTAL"
    
    if [ ! -z "$SUCCESS" ] && [ "$SUCCESS" -gt 0 ]; then
        echo "  ✓ Thành công: $SUCCESS"
    fi
    
    if [ ! -z "$ERROR" ] && [ "$ERROR" -gt 0 ]; then
        echo "  ✗ Lỗi: $ERROR"
    fi
    
    # Tính % hoàn thành
    if [ ! -z "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
        PERCENT=$((COMPLETED * 100 / TOTAL))
        echo "  Tiến độ: ${PERCENT}%"
    fi
    
    echo ""
    echo "Log cuối cùng:"
    echo "---"
    tail -5 "$LOG_FILE" | grep -v "INFO"
else
    echo "Log file không tồn tại: $LOG_FILE"
fi

echo ""
echo "================================================"
echo "Commands:"
echo "  tail -f $LOG_FILE     # Theo dõi realtime"
echo "  pkill -f phase_1_plus_sim.py    # Dừng simulation"
echo "================================================"
