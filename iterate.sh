#!/bin/bash

################################################################################
# AGENT 6: Orchestration - Full Iteration Pipeline
#
# This script runs the complete fine-tuning iteration:
#   1. Train model (Agent 1)
#   2. Export to Ollama (Agent 5)
#   3. Run benchmark (Agent 2)
#   4. Calculate deltas (Agent 3)
#   5. Generate report (Agent 4)
#   6. Log experiment (Agent 6)
#
# TEACHING NOTES:
#
# 1. WHY A SINGLE SCRIPT?
#    - One command to run entire pipeline (reduces friction)
#    - Consistent workflow (no missed steps)
#    - Easy to automate (can run in batch)
#    - Clear success/failure (exit code)
#
# 2. ERROR HANDLING:
#    - set -e: Exit on any error (fail fast)
#    - Check prerequisites before starting
#    - Show clear error messages
#    - Clean up on failure (optional)
#
# 3. TIMING:
#    - Track time for each step
#    - Goal: Complete in <10 minutes
#    - Helps identify bottlenecks
#
# 4. EXPERIMENT TRACKING:
#    - Log every iteration to experiments/log.json
#    - Track: dataset, hyperparameters, results, timing
#    - Compare across iterations
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Start time
START_TIME=$(date +%s)

################################################################################
# Usage
################################################################################

usage() {
    echo -e "${BLUE}Usage: $0 <experiment-name> <dataset-path>${NC}"
    echo ""
    echo "Example:"
    echo "  $0 exp-001 datasets/example-chatbot.json"
    echo ""
    echo "This will:"
    echo "  1. Train model with Unsloth (~3-5 min)"
    echo "  2. Export to Ollama (~30 sec)"
    echo "  3. Run benchmark suite (~1 min)"
    echo "  4. Calculate deltas (instant)"
    echo "  5. Generate HTML report (instant)"
    echo "  6. Log experiment (instant)"
    echo ""
    echo "Total time: ~5-7 minutes"
    exit 1
}

if [ $# -ne 2 ]; then
    usage
fi

EXPERIMENT_NAME="$1"
DATASET_PATH="$2"

# Paths
EXPERIMENT_DIR="experiments/${EXPERIMENT_NAME}"
RESULTS_DIR="benchmark/results"
BASE_MODEL="qwen2.5:0.5b"

################################################################################
# Prerequisites Check
################################################################################

echo -e "${CYAN}================================${NC}"
echo -e "${CYAN}Agent 6: Orchestration${NC}"
echo -e "${CYAN}================================${NC}"
echo ""
echo -e "Experiment: ${GREEN}${EXPERIMENT_NAME}${NC}"
echo -e "Dataset:    ${GREEN}${DATASET_PATH}${NC}"
echo ""

# Check dataset exists
if [ ! -f "$DATASET_PATH" ]; then
    echo -e "${RED}Error: Dataset not found: ${DATASET_PATH}${NC}"
    exit 1
fi

# Check Ollama is running
if ! docker compose exec -T ollama ollama list &> /dev/null; then
    echo -e "${RED}Error: Ollama is not running${NC}"
    echo "Start it with: docker compose up -d"
    exit 1
fi

# Check base model exists
if ! docker compose exec -T ollama ollama list | grep -q "$BASE_MODEL"; then
    echo -e "${YELLOW}Warning: Base model not found: ${BASE_MODEL}${NC}"
    echo "Pulling base model (this may take a minute)..."
    docker compose exec -T ollama ollama pull "$BASE_MODEL"
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

################################################################################
# Step 1: Train Model (Agent 1)
################################################################################

echo -e "${MAGENTA}[1/6] Training model...${NC}"
STEP_START=$(date +%s)

python train.py \
    --dataset "$DATASET_PATH" \
    --output "$EXPERIMENT_DIR"

STEP_END=$(date +%s)
TRAIN_TIME=$((STEP_END - STEP_START))
echo -e "${GREEN}✓ Training complete (${TRAIN_TIME}s)${NC}"
echo ""

################################################################################
# Step 2: Export to Ollama (Agent 5)
################################################################################

echo -e "${MAGENTA}[2/6] Exporting to Ollama...${NC}"
STEP_START=$(date +%s)

./scripts/export_to_ollama.sh "$EXPERIMENT_DIR" "$EXPERIMENT_NAME"

STEP_END=$(date +%s)
EXPORT_TIME=$((STEP_END - STEP_START))
echo -e "${GREEN}✓ Export complete (${EXPORT_TIME}s)${NC}"
echo ""

################################################################################
# Step 3: Run Benchmark (Agent 2)
################################################################################

echo -e "${MAGENTA}[3/6] Running benchmark suite...${NC}"
STEP_START=$(date +%s)

# Clear previous results
rm -f "${RESULTS_DIR}/base.json" "${RESULTS_DIR}/finetuned.json"

python benchmark/run.py \
    --base "$BASE_MODEL" \
    --finetuned "$EXPERIMENT_NAME" \
    --output "$RESULTS_DIR"

STEP_END=$(date +%s)
BENCHMARK_TIME=$((STEP_END - STEP_START))
echo -e "${GREEN}✓ Benchmark complete (${BENCHMARK_TIME}s)${NC}"
echo ""

################################################################################
# Step 4: Calculate Deltas (Agent 3)
################################################################################

echo -e "${MAGENTA}[4/6] Calculating deltas...${NC}"
STEP_START=$(date +%s)

python benchmark/delta.py \
    --output "$RESULTS_DIR"

STEP_END=$(date +%s)
DELTA_TIME=$((STEP_END - STEP_START))
echo -e "${GREEN}✓ Delta calculation complete (${DELTA_TIME}s)${NC}"
echo ""

################################################################################
# Step 5: Generate Report (Agent 4)
################################################################################

echo -e "${MAGENTA}[5/6] Generating HTML report...${NC}"
STEP_START=$(date +%s)

REPORT_PATH="${RESULTS_DIR}/report-${EXPERIMENT_NAME}.html"
python benchmark/visualize.py \
    --output "$RESULTS_DIR" \
    --output-file "$REPORT_PATH"

STEP_END=$(date +%s)
VISUALIZE_TIME=$((STEP_END - STEP_START))
echo -e "${GREEN}✓ Report generated (${VISUALIZE_TIME}s)${NC}"
echo ""

################################################################################
# Step 6: Log Experiment (Agent 6)
################################################################################

echo -e "${MAGENTA}[6/6] Logging experiment...${NC}"

# Extract summary from deltas.json
DELTAS_JSON="${RESULTS_DIR}/deltas.json"
if [ -f "$DELTAS_JSON" ]; then
    # Use Python to extract summary
    SUMMARY=$(python3 << EOF
import json
with open("${DELTAS_JSON}") as f:
    data = json.load(f)
deltas = data["deltas"]
improved = sum(1 for d in deltas if d["assessment"] == "improved")
regressed = sum(1 for d in deltas if d["assessment"] == "regressed")
changed = sum(1 for d in deltas if d["assessment"] == "changed")
similar = sum(1 for d in deltas if d["assessment"] == "similar")
total = len(deltas)
print(json.dumps({
    "improved": improved,
    "regressed": regressed,
    "changed": changed,
    "similar": similar,
    "total": total
}))
EOF
)
else
    SUMMARY='{"improved": 0, "regressed": 0, "changed": 0, "similar": 0, "total": 0}'
fi

# Append to experiment log
LOG_FILE="experiments/log.json"
if [ ! -f "$LOG_FILE" ]; then
    echo "[]" > "$LOG_FILE"
fi

# Create log entry
TOTAL_TIME=$(($(date +%s) - START_TIME))
LOG_ENTRY=$(cat << EOF
{
    "experiment_name": "${EXPERIMENT_NAME}",
    "timestamp": "$(date -Iseconds)",
    "dataset": "${DATASET_PATH}",
    "base_model": "${BASE_MODEL}",
    "timing": {
        "train": ${TRAIN_TIME},
        "export": ${EXPORT_TIME},
        "benchmark": ${BENCHMARK_TIME},
        "delta": ${DELTA_TIME},
        "visualize": ${VISUALIZE_TIME},
        "total": ${TOTAL_TIME}
    },
    "results": ${SUMMARY},
    "report": "${REPORT_PATH}"
}
EOF
)

# Append to log (using Python for proper JSON handling)
python3 << EOF
import json
with open("${LOG_FILE}") as f:
    log = json.load(f)
log.append(${LOG_ENTRY})
with open("${LOG_FILE}", 'w') as f:
    json.dump(log, f, indent=2)
EOF

echo -e "${GREEN}✓ Experiment logged${NC}"
echo ""

################################################################################
# Done!
################################################################################

MINUTES=$((TOTAL_TIME / 60))
SECONDS=$((TOTAL_TIME % 60))

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Iteration Complete! 🎉${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${CYAN}Total time: ${MINUTES}m ${SECONDS}s${NC}"
echo ""
echo -e "${CYAN}Results:${NC}"
echo "$SUMMARY" | python3 -c "import sys, json; data = json.load(sys.stdin); print(f\"  Improved:  {data['improved']}/{data['total']} ({data['improved']/data['total']*100:.1f}%)\"); print(f\"  Regressed: {data['regressed']}/{data['total']} ({data['regressed']/data['total']*100:.1f}%)\"); print(f\"  Changed:   {data['changed']}/{data['total']} ({data['changed']/data['total']*100:.1f}%)\"); print(f\"  Similar:   {data['similar']}/{data['total']} ({data['similar']/data['total']*100:.1f}%)\")"
echo ""
echo -e "${CYAN}View report:${NC}"
echo "  open ${REPORT_PATH}"
echo ""
echo -e "${CYAN}View all experiments:${NC}"
echo "  cat experiments/log.json | python3 -m json.tool"
echo ""
