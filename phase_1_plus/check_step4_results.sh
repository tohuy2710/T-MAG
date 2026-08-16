#!/bin/bash
# Check Step 4 results after completion

echo "======================================================================="
echo "  STEP 4 RESULTS ANALYSIS"
echo "======================================================================="
echo ""

if ! [ -f "output/simulation_results.json" ]; then
    echo "✗ Results file not found!"
    exit 1
fi

# Overall summary
echo "=== OVERALL SUMMARY ==="
cat output/simulation_results.json | jq '.results | group_by(.step) | map({
  step: .[0].step,
  total: length,
  complete: map(select(.status=="COMPLETE")) | length,
  error: map(select(.status=="ERROR")) | length
})'

echo ""
echo "=== STEP 4 DETAILED ==="

STEP4_COMPLETE=$(cat output/simulation_results.json | jq '[.results[] | select(.step==4 and .status=="COMPLETE")] | length')
STEP4_TOTAL=$(cat output/simulation_results.json | jq '[.results[] | select(.step==4)] | length')

echo "Step 4: $STEP4_COMPLETE / $STEP4_TOTAL successful"

if [ "$STEP4_COMPLETE" -gt 0 ]; then
    echo ""
    echo "=== TOP 10 STEP 4 ALPHAS ==="
    cat output/simulation_results.json | jq '.results[] | select(.step==4 and .status=="COMPLETE") | {
      alpha_id,
      sharpe: .sim_data.is.sharpe,
      fitness: .sim_data.is.fitness,
      turnover: .sim_data.is.turnover,
      description
    }' | jq -s 'sort_by(-.fitness) | .[0:10]'
    
    echo ""
    echo "=== COMPARE BEST FROM EACH STEP ==="
    for step in 2 3 4; do
        echo ""
        echo "--- STEP $step ---"
        cat output/simulation_results.json | jq ".results[] | select(.step==$step and .status==\"COMPLETE\")" | jq -s 'sort_by(-.sim_data.is.fitness) | .[0] | {
          alpha_id,
          sharpe: .sim_data.is.sharpe,
          fitness: .sim_data.is.fitness,
          turnover: .sim_data.is.turnover,
          description: .description[:80]
        }'
    done
else
    echo ""
    echo "✗ No successful Step 4 alphas"
    echo ""
    echo "Error analysis needed. Check:"
    echo "  tail -100 step4_new.log | grep ERROR"
fi

echo ""
echo "======================================================================="
