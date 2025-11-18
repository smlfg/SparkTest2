#!/bin/bash

################################################################################
# AGENT 6: Orchestration - Full Iteration Pipeline (BULLETPROOF VERSION)
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
#
# ROBUSTNESS IMPROVEMENTS (AUDIT VERSION):
#
# 5. FILE EXISTENCE CHECKS:
#    - Verify all required scripts exist before running
#    - Check if files are readable/executable
#    - Fail with clear error if dependencies missing
#
# 6. PYTHON INTERPRETER:
#    - Use `python3` explicitly (not `python`)
#    - Verify Python 3.8+ is available
#    - Check required packages are installed
#
# 7. PATH HANDLING:
#    - Use absolute paths based on script location
#    - Don't assume current working directory
#    - Work correctly no matter where script is called from
################################################################################

# TEACHING: `set -e` is the most important command in automation
# It means "stop immediately if anything goes wrong"
set -e  # Exit on error

# ROBUSTNESS: Also exit on undefined variables
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

################################################################################
# SELF-CHECK: Determine script directory
################################################################################

# TEACHING: Get the directory where THIS script lives
# This allows the script to work from any directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# TEACHING: Change to script directory
# This ensures all relative paths work correctly
cd "$SCRIPT_DIR" || {
    echo -e "${RED}❌ Error: Cannot change to script directory: $SCRIPT_DIR${NC}"
    exit 1
}

echo -e "${CYAN}📁 Working directory: $(pwd)${NC}"

################################################################################
# SELF-CHECK: Verify this script is executable
################################################################################

# TEACHING: Check if script has execute permissions
if [ ! -x "$0" ]; then
    echo -e "${YELLOW}⚠️  Warning: This script is not executable!${NC}"
    echo -e "${YELLOW}Run this command to fix:${NC}"
    echo -e "  ${CYAN}chmod +x iterate.sh${NC}"
    echo ""
    echo -e "${YELLOW}The script will continue, but you should fix this for future runs.${NC}"
    sleep 2
fi

################################################################################
# PREREQUISITE CHECK: Python
################################################################################

# TEACHING: Prefer python3 over python (python might be Python 2)
PYTHON_CMD=""

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Check if python is Python 3
    PYTHON_VERSION=$(python --version 2>&1 | grep -oP '(?<=Python )\d+')
    if [ "$PYTHON_VERSION" -ge 3 ]; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}❌ Error: Python 3 required, but only Python 2 found${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Error: Python not found${NC}"
    echo -e "${YELLOW}Install Python 3.8+:${NC}"
    echo -e "  Ubuntu/Debian: sudo apt install python3"
    echo -e "  macOS: brew install python3"
    exit 1
fi

# Verify Python version is 3.8+
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}❌ Error: Python 3.8+ required, found Python $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python: $PYTHON_CMD $PYTHON_VERSION${NC}"

################################################################################
# PREREQUISITE CHECK: Required Files
################################################################################

# TEACHING: Define all required files
# If any are missing, fail fast with clear error
REQUIRED_FILES=(
    "train.py"
    "scripts/export_to_ollama.sh"
    "benchmark/prompts.py"
    "benchmark/run.py"
    "benchmark/delta.py"
    "benchmark/visualize.py"
    "experiments/log_experiment.py"
)

echo -e "\n${CYAN}🔍 Checking required files...${NC}"

MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}  ❌ Missing: $file${NC}"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        # Check if file is readable
        if [ ! -r "$file" ]; then
            echo -e "${RED}  ❌ Not readable: $file${NC}"
            MISSING_FILES=$((MISSING_FILES + 1))
        else
            echo -e "${GREEN}  ✓ $file${NC}"
        fi
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo -e "\n${RED}❌ Error: $MISSING_FILES required file(s) missing or not readable${NC}"
    echo -e "${YELLOW}Make sure you're in the correct directory and all files are present.${NC}"
    exit 1
fi

# Check if bash scripts are executable
REQUIRED_SCRIPTS=(
    "scripts/export_to_ollama.sh"
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [ ! -x "$script" ]; then
        echo -e "${YELLOW}⚠️  Warning: $script is not executable${NC}"
        echo -e "${YELLOW}Fixing: chmod +x $script${NC}"
        chmod +x "$script" || {
            echo -e "${RED}❌ Error: Cannot make $script executable${NC}"
            exit 1
        }
    fi
done

################################################################################
# PREREQUISITE CHECK: Required Directories
################################################################################

echo -e "\n${CYAN}📁 Checking directories...${NC}"

REQUIRED_DIRS=(
    "datasets"
    "benchmark"
    "benchmark/results"
    "experiments"
    "scripts"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}⚠️  Creating missing directory: $dir${NC}"
        mkdir -p "$dir" || {
            echo -e "${RED}❌ Error: Cannot create directory: $dir${NC}"
            exit 1
        }
    fi
    echo -e "${GREEN}  ✓ $dir${NC}"
done

################################################################################
# PREREQUISITE CHECK: Python Dependencies
################################################################################

echo -e "\n${CYAN}🐍 Checking Python dependencies...${NC}"

# Check critical Python packages
CRITICAL_PACKAGES=(
    "torch"
    "transformers"
    "requests"
    "rich"
)

MISSING_PACKAGES=0
for package in "${CRITICAL_PACKAGES[@]}"; do
    if ! $PYTHON_CMD -c "import $package" &> /dev/null; then
        echo -e "${RED}  ❌ Missing: $package${NC}"
        MISSING_PACKAGES=$((MISSING_PACKAGES + 1))
    else
        echo -e "${GREEN}  ✓ $package${NC}"
    fi
done

if [ $MISSING_PACKAGES -gt 0 ]; then
    echo -e "\n${RED}❌ Error: $MISSING_PACKAGES required package(s) missing${NC}"
    echo -e "${YELLOW}Install dependencies:${NC}"
    echo -e "  ${CYAN}pip install -r requirements.txt${NC}"
    exit 1
fi

################################################################################
# Usage and Argument Validation
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
    echo -e "${RED}❌ Error: Wrong number of arguments${NC}"
    usage
fi

EXPERIMENT_NAME="$1"

# Validate experiment name (no special characters)
if ! [[ "$EXPERIMENT_NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo -e "${RED}❌ Error: Invalid experiment name: $EXPERIMENT_NAME${NC}"
    echo -e "${YELLOW}Use only letters, numbers, hyphens, and underscores${NC}"
    echo -e "${CYAN}Good examples: exp-001, test_run, iteration-v2${NC}"
    exit 1
fi

################################################################################
# Interactive Dataset Selection
################################################################################

if [ $# -eq 1 ]; then
    # No dataset provided - show interactive selection

    echo ""
    echo -e "${CYAN}================================${NC}"
    echo -e "${CYAN}📂 Dataset Selection${NC}"
    echo -e "${CYAN}================================${NC}"
    echo ""

    # Find all JSON files in datasets/
    # Temporarily disable set -u for array expansion
    set +u
    DATASETS=(datasets/*.json)
    set -u

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
        NUM_EXAMPLES=$($PYTHON_CMD -c "import json; data=json.load(open('$dataset')); print(len(data))" 2>/dev/null || echo "?")

        # Get file size
        SIZE=$(du -h "$dataset" | cut -f1)

        # Show dataset info
        echo -e "  ${GREEN}[$idx]${NC} $(basename $dataset)"
        echo -e "      📊 Examples: ${NUM_EXAMPLES}  |  💾 Size: ${SIZE}"

        # Show first user message as preview
        PREVIEW=$($PYTHON_CMD -c "import json; data=json.load(open('$dataset')); print(data[0]['messages'][0]['content'][:60] + ('...' if len(data[0]['messages'][0]['content']) > 60 else ''))" 2>/dev/null || echo "")
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

    # Check if dataset file exists
    if [ ! -f "$DATASET_PATH" ]; then
        echo -e "${RED}❌ Error: Dataset not found: $DATASET_PATH${NC}"
        echo -e "${YELLOW}Available datasets:${NC}"
        if [ -d "datasets" ]; then
            ls -1 datasets/*.json 2>/dev/null || echo "  (No datasets found in datasets/)"
        fi
        exit 1
    fi
fi

# Validate dataset is valid JSON
if ! $PYTHON_CMD -c "import json; json.load(open('$DATASET_PATH'))" &> /dev/null; then
    echo -e "${RED}❌ Error: Invalid JSON in dataset: $DATASET_PATH${NC}"
    exit 1
fi

# Paths
EXPERIMENT_DIR="experiments/${EXPERIMENT_NAME}"
RESULTS_DIR="benchmark/results"
BASE_MODEL="qwen2.5:0.5b"

# Check if experiment already exists
if [ -d "$EXPERIMENT_DIR" ]; then
    echo -e "${YELLOW}⚠️  Warning: Experiment directory already exists: $EXPERIMENT_DIR${NC}"
    echo -e "${YELLOW}This will overwrite existing results. Continue? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}Aborted. Choose a different experiment name.${NC}"
        exit 0
    fi
fi

# Start time
START_TIME=$(date +%s)

################################################################################
# Display Configuration
################################################################################

echo ""
echo -e "${CYAN}================================${NC}"
echo -e "${CYAN}🚀 DGX FAST ITERATION PIPELINE${NC}"
echo -e "${CYAN}================================${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Experiment:  ${GREEN}${EXPERIMENT_NAME}${NC}"
echo -e "  Dataset:     ${GREEN}${DATASET_PATH}${NC}"
echo -e "  Output:      ${GREEN}${EXPERIMENT_DIR}${NC}"
echo -e "  Python:      ${GREEN}$PYTHON_CMD $PYTHON_VERSION${NC}"
echo -e "  Base Model:  ${GREEN}${BASE_MODEL}${NC}"
echo ""

################################################################################
# Docker/Ollama Check
################################################################################

echo -e "${CYAN}🐋 Checking Ollama...${NC}"

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker not found${NC}"
    echo -e "${YELLOW}Install Docker: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo -e "${RED}❌ Error: Docker daemon not running${NC}"
    echo -e "${YELLOW}Start Docker Desktop or run: sudo systemctl start docker${NC}"
    exit 1
fi

# Check if Ollama container is running
if ! docker compose exec -T ollama ollama list &> /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama is not running. Starting...${NC}"
    docker compose up -d || {
        echo -e "${RED}❌ Error: Failed to start Ollama${NC}"
        exit 1
    }
    echo -e "${YELLOW}Waiting 10 seconds for Ollama to start...${NC}"
    sleep 10
fi

# Check if base model exists
if ! docker compose exec -T ollama ollama list | grep -q "$BASE_MODEL"; then
    echo -e "${YELLOW}⚠️  Base model not found: ${BASE_MODEL}${NC}"
    echo -e "${YELLOW}Pulling model (this may take 1-2 minutes)...${NC}"
    docker compose exec -T ollama ollama pull "$BASE_MODEL" || {
        echo -e "${RED}❌ Error: Failed to pull base model${NC}"
        exit 1
    }
fi

echo -e "${GREEN}✓ Ollama ready${NC}"
echo ""

################################################################################
# PIPELINE EXECUTION
################################################################################

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🎬 Starting Pipeline${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

################################################################################
# Step 1: Train Model (Agent 1)
################################################################################

echo -e "${MAGENTA}[1/6] 🏋️  Training model with Unsloth...${NC}"
STEP_START=$(date +%s)

$PYTHON_CMD train.py \
    --dataset "$DATASET_PATH" \
    --output "$EXPERIMENT_DIR" || {
    echo -e "${RED}❌ Error: Training failed${NC}"
    echo -e "${YELLOW}Check train.py output above for details${NC}"
    exit 1
}

STEP_END=$(date +%s)
TRAIN_TIME=$((STEP_END - STEP_START))
echo -e "${GREEN}✓ Training complete (${TRAIN_TIME}s)${NC}"
echo ""

################################################################################
# Step 2: Export to Ollama (Agent 5)
################################################################################

echo -e "${MAGENTA}[2/6] 📦 Exporting to Ollama...${NC}"
STEP_START=$(date +%s)

./scripts/export_to_ollama.sh "$EXPERIMENT_DIR" "$EXPERIMENT_NAME" || {
    echo -e "${RED}❌ Error: Export failed${NC}"
    exit 1
}

STEP_END=$(date +%s)
EXPORT_TIME=$((STEP_END - STEP_START))
echo -e "${GREEN}✓ Export complete (${EXPORT_TIME}s)${NC}"
echo ""

################################################################################
# Step 3: Run Benchmark (Agent 2)
################################################################################

echo -e "${MAGENTA}[3/6] 🧪 Running benchmark suite...${NC}"
STEP_START=$(date +%s)

# Clear previous results
rm -f "${RESULTS_DIR}/base.json" "${RESULTS_DIR}/finetuned.json" "${RESULTS_DIR}/deltas.json"

$PYTHON_CMD benchmark/run.py \
    --base "$BASE_MODEL" \
    --finetuned "$EXPERIMENT_NAME" \
    --output "$RESULTS_DIR" || {
    echo -e "${RED}❌ Error: Benchmark failed${NC}"
    exit 1
}

STEP_END=$(date +%s)
BENCHMARK_TIME=$((STEP_END - STEP_START))
echo -e "${GREEN}✓ Benchmark complete (${BENCHMARK_TIME}s)${NC}"
echo ""

################################################################################
# Step 4: Calculate Deltas (Agent 3)
################################################################################

echo -e "${MAGENTA}[4/6] 📊 Calculating deltas...${NC}"
STEP_START=$(date +%s)

$PYTHON_CMD benchmark/delta.py \
    --output "$RESULTS_DIR" || {
    echo -e "${RED}❌ Error: Delta calculation failed${NC}"
    exit 1
}

STEP_END=$(date +%s)
DELTA_TIME=$((STEP_END - STEP_START))
echo -e "${GREEN}✓ Delta calculation complete (${DELTA_TIME}s)${NC}"
echo ""

################################################################################
# Step 5: Generate Report (Agent 4)
################################################################################

echo -e "${MAGENTA}[5/6] 📝 Generating HTML report...${NC}"
STEP_START=$(date +%s)

REPORT_PATH="${RESULTS_DIR}/report-${EXPERIMENT_NAME}.html"
$PYTHON_CMD benchmark/visualize.py \
    --output "$RESULTS_DIR" \
    --output-file "$REPORT_PATH" || {
    echo -e "${RED}❌ Error: Visualization failed${NC}"
    exit 1
}

STEP_END=$(date +%s)
VISUALIZE_TIME=$((STEP_END - STEP_START))
echo -e "${GREEN}✓ Report generated (${VISUALIZE_TIME}s)${NC}"
echo ""

################################################################################
# Step 6: Log Experiment (Agent 6)
################################################################################

echo -e "${MAGENTA}[6/6] 📖 Logging experiment...${NC}"
STEP_START=$(date +%s)

$PYTHON_CMD experiments/log_experiment.py "$EXPERIMENT_NAME" --report "$REPORT_PATH" || {
    echo -e "${RED}❌ Error: Logging failed${NC}"
    exit 1
}

STEP_END=$(date +%s)
LOG_TIME=$((STEP_END - STEP_START))
echo -e "${GREEN}✓ Experiment logged (${LOG_TIME}s)${NC}"
echo ""

################################################################################
# Done! Open Report in Browser
################################################################################

TOTAL_TIME=$(($(date +%s) - START_TIME))
MINUTES=$((TOTAL_TIME / 60))
SECONDS=$((TOTAL_TIME % 60))

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🎉🎉🎉 Iteration Complete! 🎉🎉🎉${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${CYAN}⏱️  Timing Breakdown:${NC}"
echo -e "  Training:       ${TRAIN_TIME}s"
echo -e "  Export:         ${EXPORT_TIME}s"
echo -e "  Benchmark:      ${BENCHMARK_TIME}s"
echo -e "  Delta Analysis: ${DELTA_TIME}s"
echo -e "  Visualization:  ${VISUALIZE_TIME}s"
echo -e "  Logging:        ${LOG_TIME}s"
echo -e "  ${GREEN}Total:          ${MINUTES}m ${SECONDS}s${NC}"
echo ""
echo -e "${CYAN}📊 Opening report in browser...${NC}"
echo -e "   ${REPORT_PATH}"
echo ""

# TEACHING: Cross-platform browser opening
# xdg-open (Linux), open (macOS), start (Windows)
OPENED=false

if command -v xdg-open &> /dev/null; then
    if xdg-open "$REPORT_PATH" &> /dev/null; then
        OPENED=true
    fi
elif command -v open &> /dev/null; then
    if open "$REPORT_PATH" 2>/dev/null; then
        OPENED=true
    fi
elif command -v start &> /dev/null; then
    if start "$REPORT_PATH" 2>/dev/null; then
        OPENED=true
    fi
fi

if [ "$OPENED" = false ]; then
    echo -e "${YELLOW}⚠️  Could not auto-open browser. Please open manually:${NC}"
    echo -e "   file://$(pwd)/$REPORT_PATH"
    echo ""
fi

echo -e "${CYAN}💡 Next steps:${NC}"
echo -e "  ${GREEN}View report:${NC}        open $REPORT_PATH"
echo -e "  ${GREEN}View all logs:${NC}      cat experiments/log.json | $PYTHON_CMD -m json.tool"
echo -e "  ${GREEN}Find best model:${NC}    $PYTHON_CMD -c \"import json; log=json.load(open('experiments/log.json')); best=max(log, key=lambda x: x['summary']['score']); print(f'Best: {best[\\\"name\\\"]} (score: {best[\\\"summary\\\"][\\\"score\\\"]:.2f})')\""
echo -e "  ${GREEN}Next iteration:${NC}     ./iterate.sh exp-002 datasets/improved.json"
echo ""

exit 0
