#!/bin/bash

################################################################################
# AGENT 6: Orchestration - Full Iteration Pipeline
# DGX SPARK FAST ITERATION SCRIPT
#
# WAS DIESES SKRIPT MACHT (TEACHING):
# Dies ist der "Dirigent" des Projekts. Es ruft alle anderen Skripte
# (die "Musiker") in der exakt richtigen Reihenfolge auf.
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
#    - User doesn't have to remember 6 commands in order
#
# 2. ERROR HANDLING WITH `set -e`:
#    THIS IS THE MOST IMPORTANT LINE IN THIS SCRIPT!
#    - `set -e` means "Exit Immediately on Error"
#    - Without it: If train.py fails, export would try to export a non-existent model
#    - With it: Script stops immediately, showing exactly where the problem is
#    - Lesson: Always use `set -e` in automation scripts
#
# 3. TIMING:
#    - Track time for each step with $(date +%s)
#    - Goal: Complete in <10 minutes
#    - Helps identify bottlenecks (is training slow? benchmark slow?)
#
# 4. EXPERIMENT TRACKING (The "Lab Notebook"):
#    - Log every iteration to experiments/log.json
#    - Track: dataset, hyperparameters, results, timing
#    - Compare across iterations to find best configuration
#    - After 10 iterations: "Which was best?" → Check log.json
################################################################################

# TEACHING: `set -e` is the most important command in automation
# It means "stop immediately if anything goes wrong"
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
    echo -e "${BLUE}Usage: $0 <experiment-name> [dataset-path]${NC}"
    echo ""
    echo "Examples:"
    echo -e "  ${CYAN}# Interactive dataset selection:${NC}"
    echo "  $0 exp-001"
    echo ""
    echo -e "  ${CYAN}# Direct dataset path:${NC}"
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

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    usage
fi

EXPERIMENT_NAME="$1"

################################################################################
# Interactive Dataset Selection
################################################################################

if [ $# -eq 1 ]; then
    # No dataset provided - show interactive selection

    echo -e "${CYAN}================================${NC}"
    echo -e "${CYAN}📂 Dataset Selection${NC}"
    echo -e "${CYAN}================================${NC}"
    echo ""

    # Find all JSON files in datasets/
    DATASETS=(datasets/*.json)

    # Check if any datasets exist
    if [ ! -e "${DATASETS[0]}" ]; then
        echo -e "${RED}❌ Error: No datasets found in datasets/ directory${NC}"
        echo ""
        echo "Create a dataset first. Example:"
        echo -e "${CYAN}cat > datasets/my-dataset.json << 'EOF'"
        echo '[
  {
    "messages": [
      {"role": "user", "content": "Hello!"},
      {"role": "assistant", "content": "Hi there!"}
    ]
  }
]
EOF${NC}"
        exit 1
    fi

    # Display available datasets with preview
    echo -e "${YELLOW}Available datasets:${NC}"
    echo ""

    idx=1
    declare -A DATASET_MAP
    for dataset in "${DATASETS[@]}"; do
        DATASET_MAP[$idx]="$dataset"

        # Get number of examples
        NUM_EXAMPLES=$(python3 -c "import json; data=json.load(open('$dataset')); print(len(data))" 2>/dev/null || echo "?")

        # Get file size
        SIZE=$(du -h "$dataset" | cut -f1)

        # Show dataset info
        echo -e "  ${GREEN}[$idx]${NC} $(basename $dataset)"
        echo -e "      📊 Examples: ${NUM_EXAMPLES}  |  💾 Size: ${SIZE}"

        # Show first user message as preview
        PREVIEW=$(python3 -c "import json; data=json.load(open('$dataset')); print(data[0]['messages'][0]['content'][:60] + ('...' if len(data[0]['messages'][0]['content']) > 60 else ''))" 2>/dev/null || echo "")
        if [ -n "$PREVIEW" ]; then
            echo -e "      ${CYAN}Preview: \"${PREVIEW}\"${NC}"
        fi
        echo ""

        idx=$((idx + 1))
    done

    # Prompt user for selection
    echo -e "${YELLOW}Select dataset [1-$((idx-1))]:${NC} "
    read -r SELECTION

    # Validate selection
    if ! [[ "$SELECTION" =~ ^[0-9]+$ ]] || [ "$SELECTION" -lt 1 ] || [ "$SELECTION" -ge $idx ]; then
        echo -e "${RED}❌ Invalid selection: $SELECTION${NC}"
        exit 1
    fi

    # Get selected dataset
    DATASET_PATH="${DATASET_MAP[$SELECTION]}"

    echo ""
    echo -e "${GREEN}✓ Selected: $(basename $DATASET_PATH)${NC}"
    echo ""

else
    # Dataset path provided as argument
    DATASET_PATH="$2"
fi

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

# TEACHING: This step creates our "Lab Notebook" (experiments/log.json)
# Why? After 10 iterations, we want to compare: Which config was best?
# The log_experiment.py script reads metadata.json and deltas.json,
# creates a summary, and appends it to log.json

echo -e "${MAGENTA}[6/6] Logging experiment...${NC}"
STEP_START=$(date +%s)

python experiments/log_experiment.py "$EXPERIMENT_NAME" --report "$REPORT_PATH"

STEP_END=$(date +%s)
LOG_TIME=$((STEP_END - STEP_START))
echo -e "${GREEN}✓ Experiment logged (${LOG_TIME}s)${NC}"
echo ""

################################################################################
# Done! Open Report in Browser
################################################################################

# TEACHING: The final UX touch - auto-open the report
# This seems trivial but is psychologically crucial:
# - Without auto-open: User has to find file, double-click (friction)
# - With auto-open: Instant feedback, dopamine hit, want to iterate again!
# This makes the difference between "I'll do one iteration" and "I'll do 10"

TOTAL_TIME=$(($(date +%s) - START_TIME))
MINUTES=$((TOTAL_TIME / 60))
SECONDS=$((TOTAL_TIME % 60))

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🎉🎉🎉 Iteration Complete! 🎉🎉🎉${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${CYAN}Total time: ${MINUTES}m ${SECONDS}s${NC}"
echo ""
echo -e "${CYAN}📊 Opening report in browser...${NC}"
echo "   ${REPORT_PATH}"
echo ""

# TEACHING: Cross-platform browser opening
# xdg-open (Linux), open (macOS), start (Windows)
if command -v xdg-open &> /dev/null; then
    xdg-open "$REPORT_PATH" &> /dev/null || echo "  (Could not auto-open. Please open manually)"
elif command -v open &> /dev/null; then
    open "$REPORT_PATH" || echo "  (Could not auto-open. Please open manually)"
elif command -v start &> /dev/null; then
    start "$REPORT_PATH" || echo "  (Could not auto-open. Please open manually)"
else
    echo "  ⚠️  Auto-open not available. Please open manually:"
    echo "  file://$(pwd)/$REPORT_PATH"
fi

echo ""
echo -e "${CYAN}💡 Next steps:${NC}"
echo "  View all experiments:  cat experiments/log.json | python3 -m json.tool"
echo "  Compare experiments:   python experiments/log_experiment.py --compare"
echo "  Run next iteration:    ./iterate.sh exp-002 datasets/improved.json"
echo ""
