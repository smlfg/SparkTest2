#!/bin/bash

# ============================================================================
# DGX Spark Fast Fine-tuning System
# Agent 6: Orchestration - One-Command Iteration
# ============================================================================
#
# WHAT: Run complete iteration loop from training to visualization
# WHY:  Single command for maximum iteration speed
# HOW:  Chain all agents: Train → Export → Benchmark → Delta → Visualize
#
# USAGE: ./iterate.sh <experiment_name> <dataset_path> [epochs]
#
# EXAMPLE: ./iterate.sh exp-001 datasets/example-chatbot.json 3
#
# TIME: ~5-10 minutes total
#
# ============================================================================

set -e  # Exit on any error

# ===== COLORS FOR OUTPUT =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ===== ARGUMENT PARSING =====
if [ -z "$1" ] || [ -z "$2" ]; then
    echo -e "${RED}❌ Error: Missing required arguments${NC}"
    echo ""
    echo "Usage: $0 <experiment_name> <dataset_path> [epochs]"
    echo ""
    echo "Examples:"
    echo "  $0 exp-001 datasets/example-chatbot.json"
    echo "  $0 exp-002 datasets/example-chatbot.json 5"
    echo ""
    exit 1
fi

EXPERIMENT_NAME="$1"
DATASET_PATH="$2"
EPOCHS="${3:-3}"  # Default to 3 epochs if not specified

# Validate dataset exists
if [ ! -f "$DATASET_PATH" ]; then
    echo -e "${RED}❌ Error: Dataset not found: $DATASET_PATH${NC}"
    exit 1
fi

# ===== BANNER =====
echo ""
echo "============================================================================"
echo -e "${PURPLE}🚀 DGX SPARK FAST FINE-TUNING ITERATION${NC}"
echo "============================================================================"
echo ""
echo -e "${CYAN}Experiment:${NC}  $EXPERIMENT_NAME"
echo -e "${CYAN}Dataset:${NC}     $DATASET_PATH"
echo -e "${CYAN}Epochs:${NC}      $EPOCHS"
echo ""
echo "This will run the complete pipeline:"
echo "  1. Train model (Agent 1)         ~3-5 min"
echo "  2. Export to Ollama (Agent 5)    ~30 sec"
echo "  3. Run benchmark (Agent 2)       ~1 min"
echo "  4. Calculate deltas (Agent 3)    ~instant"
echo "  5. Generate report (Agent 4)     ~instant"
echo ""
echo "Total estimated time: 5-10 minutes"
echo "============================================================================"
echo ""

# Ask for confirmation
read -p "Continue? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Aborted."
    exit 0
fi

# Start timer
START_TIME=$(date +%s)

# ===== STEP 1: TRAIN MODEL (Agent 1) =====
echo ""
echo "============================================================================"
echo -e "${GREEN}[1/5] 🧠 TRAINING MODEL${NC}"
echo "============================================================================"
echo ""

python3 train.py "$EXPERIMENT_NAME" "$DATASET_PATH" --epochs "$EPOCHS"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Training failed!${NC}"
    exit 1
fi

TRAIN_END=$(date +%s)
TRAIN_TIME=$((TRAIN_END - START_TIME))

echo ""
echo -e "${GREEN}✅ Training complete in ${TRAIN_TIME}s${NC}"

# ===== STEP 2: EXPORT TO OLLAMA (Agent 5) =====
echo ""
echo "============================================================================"
echo -e "${GREEN}[2/5] 📦 EXPORTING TO OLLAMA${NC}"
echo "============================================================================"
echo ""

./scripts/export_to_ollama.sh "$EXPERIMENT_NAME"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Export failed!${NC}"
    exit 1
fi

EXPORT_END=$(date +%s)
EXPORT_TIME=$((EXPORT_END - TRAIN_END))

echo ""
echo -e "${GREEN}✅ Export complete in ${EXPORT_TIME}s${NC}"

# ===== STEP 3: ENSURE BASE MODEL EXISTS =====
echo ""
echo "============================================================================"
echo -e "${GREEN}[3/5] 🔍 RUNNING BENCHMARK${NC}"
echo "============================================================================"
echo ""

# Check if base model is pulled
echo "Checking for base model (qwen2.5:0.5b)..."
if ! docker-compose exec -T ollama ollama list | grep -q "qwen2.5:0.5b"; then
    echo -e "${YELLOW}⚠️  Base model not found. Pulling qwen2.5:0.5b...${NC}"
    docker-compose exec -T ollama ollama pull qwen2.5:0.5b

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to pull base model!${NC}"
        exit 1
    fi
fi

# Run benchmark
python3 benchmark/run.py "$EXPERIMENT_NAME"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Benchmark failed!${NC}"
    exit 1
fi

BENCHMARK_END=$(date +%s)
BENCHMARK_TIME=$((BENCHMARK_END - EXPORT_END))

echo ""
echo -e "${GREEN}✅ Benchmark complete in ${BENCHMARK_TIME}s${NC}"

# ===== STEP 4: CALCULATE DELTAS (Agent 3) =====
echo ""
echo "============================================================================"
echo -e "${GREEN}[4/5] 📊 CALCULATING DELTAS${NC}"
echo "============================================================================"
echo ""

python3 benchmark/delta.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Delta calculation failed!${NC}"
    exit 1
fi

DELTA_END=$(date +%s)
DELTA_TIME=$((DELTA_END - BENCHMARK_END))

echo ""
echo -e "${GREEN}✅ Deltas calculated in ${DELTA_TIME}s${NC}"

# ===== STEP 5: GENERATE VISUALIZATION (Agent 4) =====
echo ""
echo "============================================================================"
echo -e "${GREEN}[5/5] 🎨 GENERATING REPORT${NC}"
echo "============================================================================"
echo ""

python3 benchmark/visualize.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Visualization failed!${NC}"
    exit 1
fi

VIZ_END=$(date +%s)
VIZ_TIME=$((VIZ_END - DELTA_END))

echo ""
echo -e "${GREEN}✅ Report generated in ${VIZ_TIME}s${NC}"

# ===== STEP 6: LOG EXPERIMENT (Agent 6) =====
echo ""
echo "============================================================================"
echo -e "${GREEN}[6/6] 📝 LOGGING EXPERIMENT${NC}"
echo "============================================================================"
echo ""

# Create log file if it doesn't exist
LOG_FILE="experiments/log.json"
if [ ! -f "$LOG_FILE" ]; then
    echo "[]" > "$LOG_FILE"
fi

# Add experiment entry
TOTAL_TIME=$((VIZ_END - START_TIME))

python3 << EOF
import json
from datetime import datetime
from pathlib import Path

log_file = Path("$LOG_FILE")
with open(log_file) as f:
    log = json.load(f)

# Load metadata from experiment
metadata_file = Path("experiments/$EXPERIMENT_NAME/metadata.json")
if metadata_file.exists():
    with open(metadata_file) as f:
        metadata = json.load(f)
else:
    metadata = {}

# Load delta summary
deltas_file = Path("benchmark/results/deltas.json")
if deltas_file.exists():
    with open(deltas_file) as f:
        deltas = json.load(f)

    # Calculate summary stats
    assessments = [d["overall_assessment"] for d in deltas]
    improved = assessments.count("improved")
    regressed = assessments.count("regressed")
    unchanged = assessments.count("unchanged")
    changed = len(deltas) - improved - regressed - unchanged
else:
    improved = regressed = unchanged = changed = 0

# Add entry
entry = {
    "experiment_name": "$EXPERIMENT_NAME",
    "timestamp": datetime.now().isoformat(),
    "dataset": "$DATASET_PATH",
    "epochs": $EPOCHS,
    "timing": {
        "total_seconds": $TOTAL_TIME,
        "total_minutes": round($TOTAL_TIME / 60, 1),
        "train_seconds": $TRAIN_TIME,
        "export_seconds": $EXPORT_TIME,
        "benchmark_seconds": $BENCHMARK_TIME,
        "delta_seconds": $DELTA_TIME,
        "viz_seconds": $VIZ_TIME,
    },
    "results": {
        "improved": improved,
        "regressed": regressed,
        "changed": changed,
        "unchanged": unchanged,
    },
    "metadata": metadata,
    "report_path": "benchmark/results/report.html",
}

log.append(entry)

with open(log_file, 'w') as f:
    json.dump(log, f, indent=2)

print(f"   ✅ Logged to {log_file}")
EOF

# ===== FINAL SUMMARY =====
TOTAL_END=$(date +%s)
TOTAL_TIME=$((TOTAL_END - START_TIME))
TOTAL_MINUTES=$((TOTAL_TIME / 60))
TOTAL_SECONDS=$((TOTAL_TIME % 60))

echo ""
echo "============================================================================"
echo -e "${PURPLE}✅ ITERATION COMPLETE!${NC}"
echo "============================================================================"
echo ""
echo -e "${CYAN}Experiment:${NC}     $EXPERIMENT_NAME"
echo -e "${CYAN}Total time:${NC}     ${TOTAL_MINUTES}m ${TOTAL_SECONDS}s"
echo ""
echo -e "${CYAN}Timing breakdown:${NC}"
echo "  Training:     ${TRAIN_TIME}s"
echo "  Export:       ${EXPORT_TIME}s"
echo "  Benchmark:    ${BENCHMARK_TIME}s"
echo "  Deltas:       ${DELTA_TIME}s"
echo "  Visualization: ${VIZ_TIME}s"
echo ""
echo -e "${CYAN}Results:${NC}"
echo "  LoRA weights:  experiments/$EXPERIMENT_NAME/lora/"
echo "  Metadata:      experiments/$EXPERIMENT_NAME/metadata.json"
echo "  Report:        benchmark/results/report.html"
echo "  Experiment log: experiments/log.json"
echo ""
echo -e "${CYAN}View results:${NC}"
echo "  open benchmark/results/report.html"
echo ""
echo -e "${CYAN}Next iteration:${NC}"
echo "  ./iterate.sh exp-002 datasets/another-dataset.json"
echo ""
echo "============================================================================"
echo ""

# Optional: Open report automatically (uncomment if desired)
# open benchmark/results/report.html  # macOS
# xdg-open benchmark/results/report.html  # Linux

exit 0
