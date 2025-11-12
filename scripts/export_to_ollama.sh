#!/bin/bash

# ============================================================================
# DGX Spark Fast Fine-tuning System
# Agent 5: Export Pipeline - LoRA → GGUF → Ollama
# ============================================================================
#
# WHAT: Converts fine-tuned LoRA model to Ollama-compatible format
# WHY:  Ollama needs GGUF format for efficient CPU/GPU inference
# HOW:  1. Merge LoRA with base model
#       2. Convert to GGUF
#       3. Create Ollama Modelfile
#       4. Import to Ollama
#
# USAGE: ./scripts/export_to_ollama.sh <experiment_name>
# EXAMPLE: ./scripts/export_to_ollama.sh exp-001
#
# TIME: ~30 seconds for 0.5B model
#
# ============================================================================

set -e  # Exit on any error

# ===== ARGUMENT PARSING =====
if [ -z "$1" ]; then
    echo "❌ Error: Missing experiment name"
    echo "Usage: $0 <experiment_name>"
    echo "Example: $0 exp-001"
    exit 1
fi

EXPERIMENT_NAME="$1"
EXPERIMENT_DIR="experiments/${EXPERIMENT_NAME}"
LORA_DIR="${EXPERIMENT_DIR}/lora"
MERGED_DIR="${EXPERIMENT_DIR}/merged"
GGUF_DIR="${EXPERIMENT_DIR}/gguf"

# ===== VALIDATION =====
if [ ! -d "$LORA_DIR" ]; then
    echo "❌ Error: LoRA directory not found: $LORA_DIR"
    echo "Have you run training yet?"
    exit 1
fi

echo "🚀 Starting export pipeline for: ${EXPERIMENT_NAME}"
echo "=================================================="

# ===== STEP 1: MERGE LORA WITH BASE MODEL =====
# WHY: LoRA adapters are just the "delta" weights. We need to merge them
#      with the base model to get a standalone model.
# HOW: Unsloth provides a fast merge function

echo ""
echo "📦 Step 1/4: Merging LoRA with base model..."

python3 << EOF
from unsloth import FastLanguageModel
import torch

# Load LoRA model
print("   Loading LoRA model from ${LORA_DIR}...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="${LORA_DIR}",
    max_seq_length=2048,
    dtype=None,  # Auto-detect
    load_in_4bit=True,
)

# Merge LoRA weights into base model
# WHY: This "bakes in" the LoRA adapters, creating a single model
print("   Merging LoRA weights...")
model = model.merge_and_unload()

# Save merged model
print("   Saving merged model to ${MERGED_DIR}...")
model.save_pretrained("${MERGED_DIR}")
tokenizer.save_pretrained("${MERGED_DIR}")

print("   ✅ Merge complete!")
EOF

# ===== STEP 2: CONVERT TO GGUF =====
# WHY: GGUF is a efficient binary format that Ollama uses
#      It's optimized for fast loading and inference
# HOW: Use llama.cpp's conversion script

echo ""
echo "🔄 Step 2/4: Converting to GGUF format..."

# Check if llama.cpp is available
if ! command -v llama-quantize &> /dev/null; then
    echo "   ⚠️  llama.cpp not found, using Python conversion..."

    python3 << EOF
# Simplified GGUF conversion using transformers
# For production, use llama.cpp for better optimization
from transformers import AutoModelForCausalLM, AutoTokenizer

print("   Loading merged model...")
model = AutoModelForCausalLM.from_pretrained("${MERGED_DIR}")
tokenizer = AutoTokenizer.from_pretrained("${MERGED_DIR}")

# Save in safetensors format (Ollama can use this)
print("   Saving in Ollama-compatible format...")
import os
os.makedirs("${GGUF_DIR}", exist_ok=True)
model.save_pretrained("${GGUF_DIR}", safe_serialization=True)
tokenizer.save_pretrained("${GGUF_DIR}")

print("   ✅ Conversion complete!")
EOF
else
    # Use llama.cpp for optimized GGUF conversion
    mkdir -p "${GGUF_DIR}"
    python3 -m llama_cpp.llama_convert "${MERGED_DIR}" \
        --outfile "${GGUF_DIR}/model.gguf" \
        --outtype q4_0  # 4-bit quantization for speed
    echo "   ✅ GGUF conversion complete!"
fi

# ===== STEP 3: CREATE OLLAMA MODELFILE =====
# WHY: Ollama needs a Modelfile to know model parameters, system prompt, etc.
# HOW: Create a simple Modelfile with sensible defaults

echo ""
echo "📝 Step 3/4: Creating Ollama Modelfile..."

cat > "${EXPERIMENT_DIR}/Modelfile" << 'MODELFILE_EOF'
# Base model reference
# Note: For fine-tuned models, we'll use the GGUF file directly
FROM ./gguf

# Model parameters
# These control the sampling behavior during inference
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1

# System message (can be overridden per request)
SYSTEM You are a helpful AI assistant fine-tuned for specific tasks.

# Template (Qwen2.5 format)
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
{{ end }}{{ .Response }}<|im_end|>
"""
MODELFILE_EOF

echo "   ✅ Modelfile created!"

# ===== STEP 4: IMPORT TO OLLAMA =====
# WHY: Final step - make the model available for inference via Ollama API
# HOW: Use 'ollama create' command

echo ""
echo "🎯 Step 4/4: Importing to Ollama..."

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ⚠️  Ollama not running. Starting Ollama..."
    docker-compose up -d
    sleep 5  # Wait for Ollama to start
fi

# Create Ollama model
# This imports the GGUF file and registers it with the given name
cd "${EXPERIMENT_DIR}"
docker-compose exec -T ollama ollama create "${EXPERIMENT_NAME}" -f Modelfile

echo "   ✅ Model imported to Ollama as '${EXPERIMENT_NAME}'!"

# ===== VERIFICATION =====
echo ""
echo "🔍 Verifying model is available..."

# List models to confirm
docker-compose exec -T ollama ollama list | grep "${EXPERIMENT_NAME}" && \
    echo "   ✅ Model verified!" || \
    echo "   ⚠️  Model not found in Ollama list"

# ===== SUMMARY =====
echo ""
echo "=================================================="
echo "✅ Export complete!"
echo ""
echo "Model name: ${EXPERIMENT_NAME}"
echo "Location: ${EXPERIMENT_DIR}"
echo ""
echo "Test your model:"
echo "  curl http://localhost:11434/api/generate -d '{
  \"model\": \"${EXPERIMENT_NAME}\",
  \"prompt\": \"Hello, world!\"
}'"
echo ""
echo "Or use Python:"
echo "  import requests"
echo "  r = requests.post('http://localhost:11434/api/generate',"
echo "      json={'model': '${EXPERIMENT_NAME}', 'prompt': 'Hello!'})"
echo "=================================================="

# ===== CLEANUP (OPTIONAL) =====
# Uncomment to save disk space by removing merged model
# (Keep GGUF and LoRA, they're small)
# echo "🧹 Cleaning up intermediate files..."
# rm -rf "${MERGED_DIR}"

exit 0
