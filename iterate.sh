#!/bin/bash

# Agent 6: Orchestration Script
#
# This script orchestrates the complete iteration pipeline:
# Train → Export → Benchmark → Delta → Visualize → Track
#
# WHY ONE SCRIPT?
# - Single command for full iteration
# - Consistent workflow across experiments
# - Error handling at each stage
# - Progress tracking and timing
# - Automatic logging to experiment history
#
# GOAL: Complete one iteration in <10 minutes
#
# USAGE:
#   ./iterate.sh <experiment-name> <dataset-path>
#
# EXAMPLE:
#   ./iterate.sh exp-001 datasets/example-chatbot.json
#
# LEARNING OBJECTIVE:
# Understand end-to-end ML experimentation workflow.
# Each stage builds on the previous, creating a feedback loop.

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          DGX FAST FINE-TUNING ITERATION LAB                   ║"
echo "║          Agent 6: Orchestration Pipeline                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Parse arguments
if [ "$#" -ne 2 ]; then
    echo -e "${RED}Usage: $0 <experiment-name> <dataset-path>${NC}"
    echo ""
    echo "Example:"
    echo "  $0 exp-001 datasets/example-chatbot.json"
    echo ""
    exit 1
fi

EXPERIMENT_NAME=$1
DATASET_PATH=$2
BASE_MODEL="qwen2.5:0.5b"

# Validate inputs
if [ ! -f "$DATASET_PATH" ]; then
    echo -e "${RED}Error: Dataset not found at ${DATASET_PATH}${NC}"
    exit 1
fi

# Start timing
ITERATION_START=$(date +%s)

echo -e "${BLUE}Configuration:${NC}"
echo "  Experiment: ${EXPERIMENT_NAME}"
echo "  Dataset: ${DATASET_PATH}"
echo "  Base model: ${BASE_MODEL}"
echo ""

# =============================================================================
# STAGE 1: TRAINING
# =============================================================================
echo -e "${MAGENTA}[Stage 1/6] Training with Agent 1${NC}"
echo -e "${YELLOW}Expected time: 3-5 minutes${NC}"
echo ""

STAGE_START=$(date +%s)

python3 train.py \
    --name "${EXPERIMENT_NAME}" \
    --dataset "${DATASET_PATH}" \
    --epochs 3 \
    --lr 2e-4 \
    --batch-size 4 \
    --lora-rank 8

STAGE_END=$(date +%s)
TRAIN_TIME=$((STAGE_END - STAGE_START))

echo ""
echo -e "${GREEN}✓ Stage 1 complete in ${TRAIN_TIME}s${NC}"
echo ""

# =============================================================================
# STAGE 2: EXPORT TO OLLAMA
# =============================================================================
echo -e "${MAGENTA}[Stage 2/6] Exporting to Ollama with Agent 5${NC}"
echo -e "${YELLOW}Expected time: 30-60 seconds${NC}"
echo ""

STAGE_START=$(date +%s)

# Check Ollama is running
if ! docker ps | grep -q ollama; then
    echo -e "${YELLOW}Starting Ollama container...${NC}"
    docker-compose up -d
    sleep 5
fi

# Check base model exists
if ! docker exec ollama ollama list | grep -q "${BASE_MODEL}"; then
    echo -e "${YELLOW}Pulling base model ${BASE_MODEL}...${NC}"
    docker exec ollama ollama pull "${BASE_MODEL}"
fi

# Export fine-tuned model
./scripts/export_to_ollama.sh "${EXPERIMENT_NAME}"

STAGE_END=$(date +%s)
EXPORT_TIME=$((STAGE_END - STAGE_START))

echo ""
echo -e "${GREEN}✓ Stage 2 complete in ${EXPORT_TIME}s${NC}"
echo ""

# =============================================================================
# STAGE 3: BENCHMARK
# =============================================================================
echo -e "${MAGENTA}[Stage 3/6] Running Benchmark with Agent 2${NC}"
echo -e "${YELLOW}Expected time: 1-2 minutes${NC}"
echo ""

STAGE_START=$(date +%s)

python3 benchmark/run.py \
    "${EXPERIMENT_NAME}" \
    --base-model "${BASE_MODEL}"

STAGE_END=$(date +%s)
BENCHMARK_TIME=$((STAGE_END - STAGE_START))

echo ""
echo -e "${GREEN}✓ Stage 3 complete in ${BENCHMARK_TIME}s${NC}"
echo ""

# =============================================================================
# STAGE 4: DELTA CALCULATION
# =============================================================================
echo -e "${MAGENTA}[Stage 4/6] Calculating Deltas with Agent 3${NC}"
echo -e "${YELLOW}Expected time: <5 seconds${NC}"
echo ""

STAGE_START=$(date +%s)

python3 benchmark/delta.py

STAGE_END=$(date +%s)
DELTA_TIME=$((STAGE_END - STAGE_START))

echo ""
echo -e "${GREEN}✓ Stage 4 complete in ${DELTA_TIME}s${NC}"
echo ""

# =============================================================================
# STAGE 5: VISUALIZATION
# =============================================================================
echo -e "${MAGENTA}[Stage 5/6] Generating HTML Report with Agent 4${NC}"
echo -e "${YELLOW}Expected time: <5 seconds${NC}"
echo ""

STAGE_START=$(date +%s)

python3 benchmark/visualize.py

STAGE_END=$(date +%s)
VIZ_TIME=$((STAGE_END - STAGE_START))

echo ""
echo -e "${GREEN}✓ Stage 5 complete in ${VIZ_TIME}s${NC}"
echo ""

# =============================================================================
# STAGE 6: EXPERIMENT TRACKING
# =============================================================================
echo -e "${MAGENTA}[Stage 6/6] Logging Experiment${NC}"
echo ""

STAGE_START=$(date +%s)

# Calculate total iteration time
ITERATION_END=$(date +%s)
TOTAL_TIME=$((ITERATION_END - ITERATION_START))

# Create log entry
LOG_FILE="experiments/log.json"
TIMESTAMP=$(date -Iseconds)

# Parse metrics from delta results
DELTAS_FILE="benchmark/results/deltas.json"

if [ -f "$DELTAS_FILE" ]; then
    # Extract key metrics using Python
    METRICS=$(python3 <<EOF
import json
import sys

with open("${DELTAS_FILE}", 'r') as f:
    deltas = json.load(f)

total = len(deltas)
improved = sum(1 for d in deltas if d["assessment"] == "IMPROVED")
regressed = sum(1 for d in deltas if d["assessment"] == "REGRESSED")
changed = sum(1 for d in deltas if d["assessment"] == "CHANGED")
unchanged = sum(1 for d in deltas if d["assessment"] == "UNCHANGED")

print(json.dumps({
    "total": total,
    "improved": improved,
    "regressed": regressed,
    "changed": changed,
    "unchanged": unchanged
}))
EOF
)
else
    METRICS='{"total":0,"improved":0,"regressed":0,"changed":0,"unchanged":0}'
fi

# Create or update log
if [ ! -f "$LOG_FILE" ]; then
    echo "[]" > "$LOG_FILE"
fi

# Add entry
python3 <<EOF
import json
import sys

# Load existing log
with open("${LOG_FILE}", 'r') as f:
    log = json.load(f)

# Parse metrics
metrics = json.loads('''${METRICS}''')

# Create entry
entry = {
    "experiment_name": "${EXPERIMENT_NAME}",
    "timestamp": "${TIMESTAMP}",
    "dataset": "${DATASET_PATH}",
    "base_model": "${BASE_MODEL}",
    "timing": {
        "train_seconds": ${TRAIN_TIME},
        "export_seconds": ${EXPORT_TIME},
        "benchmark_seconds": ${BENCHMARK_TIME},
        "delta_seconds": ${DELTA_TIME},
        "visualization_seconds": ${VIZ_TIME},
        "total_seconds": ${TOTAL_TIME},
        "total_minutes": round(${TOTAL_TIME} / 60, 1)
    },
    "results": {
        "total_prompts": metrics["total"],
        "improved": metrics["improved"],
        "regressed": metrics["regressed"],
        "changed": metrics["changed"],
        "unchanged": metrics["unchanged"],
        "improvement_rate": round(metrics["improved"] / metrics["total"] * 100, 1) if metrics["total"] > 0 else 0
    },
    "outputs": {
        "lora_dir": f"experiments/${EXPERIMENT_NAME}/lora",
        "report": "benchmark/results/report.html",
        "deltas": "benchmark/results/deltas.json"
    }
}

# Append
log.append(entry)

# Save
with open("${LOG_FILE}", 'w') as f:
    json.dump(log, f, indent=2)

print(f"✓ Logged experiment: {entry['experiment_name']}")
print(f"  Improvement rate: {entry['results']['improvement_rate']}%")
print(f"  Total time: {entry['timing']['total_minutes']} minutes")
EOF

STAGE_END=$(date +%s)
LOG_TIME=$((STAGE_END - STAGE_START))

echo ""
echo -e "${GREEN}✓ Stage 6 complete in ${LOG_TIME}s${NC}"
echo ""

# =============================================================================
# FINAL SUMMARY
# =============================================================================
echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    ITERATION COMPLETE! 🎉                     ║${NC}"
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo ""

echo -e "${GREEN}Timing Breakdown:${NC}"
echo "  Training:       ${TRAIN_TIME}s ($(echo "scale=1; ${TRAIN_TIME}/60" | bc)m)"
echo "  Export:         ${EXPORT_TIME}s"
echo "  Benchmark:      ${BENCHMARK_TIME}s ($(echo "scale=1; ${BENCHMARK_TIME}/60" | bc)m)"
echo "  Delta:          ${DELTA_TIME}s"
echo "  Visualization:  ${VIZ_TIME}s"
echo "  Logging:        ${LOG_TIME}s"
echo "  ─────────────────────────────────"
echo "  TOTAL:          ${TOTAL_TIME}s ($(echo "scale=1; ${TOTAL_TIME}/60" | bc)m)"
echo ""

echo -e "${GREEN}Outputs:${NC}"
echo "  📊 HTML Report:    benchmark/results/report.html"
echo "  📈 Delta Analysis: benchmark/results/deltas.json"
echo "  🤖 LoRA Adapters:  experiments/${EXPERIMENT_NAME}/lora/"
echo "  📋 Experiment Log: experiments/log.json"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. View report:  open benchmark/results/report.html"
echo "  2. Test model:   docker exec ollama ollama run ${EXPERIMENT_NAME} \"Your prompt\""
echo "  3. Next iteration: ./iterate.sh exp-002 datasets/improved-data.json"
echo ""

# Check if goal met
if [ ${TOTAL_TIME} -lt 600 ]; then
    echo -e "${GREEN}✨ SUCCESS: Iteration completed in <10 minutes!${NC}"
else
    echo -e "${YELLOW}⚠️  Note: Iteration took >${TOTAL_TIME}s (target: <600s)${NC}"
    echo "Consider: smaller model, fewer epochs, or faster hardware"
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

exit 0
