#!/usr/bin/env python3
"""
Model Export Pipeline - Agent 5

TEACHING: The Bridge from Training to Production
============================================================================

This script is the CRITICAL link between Agent 1 (training) and Agent 2 (benchmarking).

WITHOUT this script:
- Agent 1 produces LoRA adapter files (just weight deltas)
- These files are useless on their own - you can't query them
- No way to test the model

WITH this script:
- LoRA adapters are merged with the base model
- The merged model is converted to GGUF format (Ollama's native format)
- A Modelfile is created (tells Ollama how to use the model)
- The model is registered in Ollama's registry
- Result: curl http://localhost:11434/api/generate -d '{"model": "exp-001", ...}'

============================================================================
THE PIPELINE
============================================================================

Step 1: Load LoRA Adapters
    - Use Unsloth to load the trained adapters
    - These are small files (~10-50MB for rank=8 LoRA)

Step 2: Merge with Base Model
    - Base Model: Qwen2.5-0.5B-Instruct (500M parameters)
    - LoRA Adapters: Our fine-tuned weights
    - Merge: A_base + B_lora = C_final
    - Result: A complete model with our customizations baked in

Step 3: Convert to GGUF
    - GGUF = GPT-Generated Unified Format
    - Binary format optimized for llama.cpp (used by Ollama)
    - Supports quantization (we use q4_k_m = 4-bit)
    - Result: A single .gguf file (~400MB for 0.5B model)

Step 4: Create Modelfile
    - Like a Dockerfile for LLMs
    - Specifies: weights location, chat template, stop tokens
    - Critical: Chat template MUST match training format

Step 5: Register with Ollama
    - Run: ollama create exp-001 -f Modelfile
    - Ollama indexes the model
    - Now available via API: {"model": "exp-001"}

============================================================================
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from typing import Optional

# TEACHING: Why these imports?
# - unsloth: Load LoRA adapters and convert to GGUF (specialized tool)
# - subprocess: Run shell commands (docker exec ollama create)
# - json: Save metadata about the export
try:
    from unsloth import FastLanguageModel
except ImportError:
    print("❌ Error: Unsloth not installed!")
    print("   Install: pip install unsloth")
    sys.exit(1)


def check_docker_running() -> bool:
    """
    TEACHING: Defensive Programming

    Before we try to export, we should check if Ollama is actually running.
    This gives a better error message than letting the script fail later.
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=ollama", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )
        return "ollama" in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_lora_exists(lora_path: str) -> bool:
    """
    TEACHING: Fail Fast Principle

    Check if the LoRA files exist before starting the heavy computation.
    Saves time if Agent 1 didn't run yet.
    """
    required_files = ["adapter_config.json", "adapter_model.safetensors"]
    for file in required_files:
        if not os.path.exists(os.path.join(lora_path, file)):
            return False
    return True


def export_model(
    experiment_name: str,
    quantization: str = "q4_k_m",
    base_model: str = "unsloth/Qwen2.5-0.5B-Instruct"
):
    """
    Main Export Function

    Args:
        experiment_name: Name of the experiment (e.g., "exp-001")
        quantization: GGUF quantization method
            - "q4_k_m": 4-bit (small, fast, good quality) ✅ Default
            - "q8_0": 8-bit (larger, slower, better quality)
            - "f16": 16-bit float (largest, slowest, best quality)
        base_model: HuggingFace model ID (must match Agent 1's training)

    TEACHING: Quantization Trade-offs
    ----------------------------------------------------------------------------
    Quantization reduces model size by using fewer bits per parameter.

    Original: 32-bit floats (4 bytes per param)
    q8_0:     8-bit integers (1 byte per param) → 4x smaller
    q4_k_m:   4-bit integers (0.5 bytes per param) → 8x smaller

    For a 0.5B parameter model:
    - f16:    ~1 GB
    - q8_0:   ~500 MB
    - q4_k_m: ~250 MB

    Quality loss: Minimal for 0.5B models at q4_k_m
    Speed gain: Significant (less data to transfer to GPU)
    ----------------------------------------------------------------------------
    """

    print("=" * 80)
    print(f"🚀 MODEL EXPORT PIPELINE - {experiment_name}")
    print("=" * 80)

    # Define paths
    lora_path = f"experiments/{experiment_name}/lora"
    output_path = f"experiments/{experiment_name}/gguf"
    modelfile_path = f"experiments/{experiment_name}/Modelfile"
    metadata_path = f"experiments/{experiment_name}/export_metadata.json"

    print(f"\n📂 Paths:")
    print(f"   Input:  {lora_path}")
    print(f"   Output: {output_path}")
    print(f"   Model:  {experiment_name} (in Ollama)")

    # ========================================================================
    # VALIDATION: Check prerequisites
    # ========================================================================
    print(f"\n🔍 [0/5] Validation...")

    if not check_docker_running():
        print("   ❌ Ollama container is not running!")
        print("   → Start it: docker-compose up -d")
        print("   → Check:    docker ps | grep ollama")
        sys.exit(1)
    print("   ✅ Ollama container is running")

    if not check_lora_exists(lora_path):
        print(f"   ❌ LoRA adapters not found at: {lora_path}")
        print("   → Run Agent 1 (train.py) first to create the adapters")
        sys.exit(1)
    print(f"   ✅ LoRA adapters found")

    # ========================================================================
    # STEP 1: Load LoRA Adapters
    # ========================================================================
    print(f"\n📥 [1/5] Loading LoRA adapters...")
    print(f"   Base model: {base_model}")
    print(f"   Adapters:   {lora_path}")

    try:
        # TEACHING: Why these parameters?
        # - max_seq_length: Must match training (Agent 1 uses 2048)
        # - dtype=None: Auto-detect optimal dtype for this hardware
        # - load_in_4bit: Load in quantized form (saves VRAM)
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=lora_path,  # Load FROM the LoRA directory (not base)
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
        )
        print("   ✅ Model loaded successfully")

        # Display model info
        param_count = sum(p.numel() for p in model.parameters())
        print(f"   📊 Parameters: {param_count:,}")

    except Exception as e:
        print(f"   ❌ Error loading model: {e}")
        print("\n   Troubleshooting:")
        print("   1. Check if adapter_config.json exists in LoRA path")
        print("   2. Verify base_model matches what Agent 1 used")
        print("   3. Ensure enough VRAM (need ~2GB for loading)")
        sys.exit(1)

    # ========================================================================
    # STEP 2 & 3: Merge LoRA + Convert to GGUF
    # ========================================================================
    print(f"\n🔄 [2/5] Merging LoRA weights...")
    print(f"   Operation: base_model + lora_adapters → merged_model")

    print(f"\n💾 [3/5] Converting to GGUF...")
    print(f"   Quantization: {quantization}")
    print(f"   Target:       {output_path}")

    # Ensure output directory exists
    Path(output_path).mkdir(parents=True, exist_ok=True)

    try:
        # TEACHING: This single function does TWO things:
        # 1. Merges the LoRA weights into the base model (in-memory)
        # 2. Converts the merged model to GGUF format (saves to disk)
        #
        # Why one function? Efficiency. No need to save an intermediate model.
        # We go straight from "LoRA adapters" to "GGUF file".

        model.save_pretrained_gguf(
            output_path,
            tokenizer,
            quantization_method=quantization,
        )

        # Find the generated GGUF file
        # Unsloth typically names it like: unsloth.Q4_K_M.gguf
        gguf_files = list(Path(output_path).glob("*.gguf"))
        if not gguf_files:
            raise Exception("No GGUF file generated!")

        gguf_file = gguf_files[0]
        gguf_filename = gguf_file.name
        gguf_size_mb = gguf_file.stat().st_size / (1024 * 1024)

        print(f"   ✅ GGUF created: {gguf_filename}")
        print(f"   📏 Size: {gguf_size_mb:.1f} MB")

    except Exception as e:
        print(f"   ❌ Error during GGUF conversion: {e}")
        sys.exit(1)

    # ========================================================================
    # STEP 4: Create Modelfile
    # ========================================================================
    print(f"\n📝 [4/5] Creating Modelfile...")

    # TEACHING: The Modelfile Format
    # ----------------------------------------------------------------------------
    # A Modelfile has three key sections:
    #
    # 1. FROM: Path to the GGUF file (absolute path inside Docker container)
    #    - We mounted ./experiments to /experiments in docker-compose.yml
    #    - So: ./experiments/exp-001/gguf/model.gguf
    #      becomes: /experiments/exp-001/gguf/model.gguf (in container)
    #
    # 2. TEMPLATE: The chat format (CRITICAL!)
    #    - Qwen uses ChatML format: <|im_start|>role\ntext<|im_end|>
    #    - If this doesn't match training format, the model will be confused
    #    - Structure:
    #      <|im_start|>system\n{system_prompt}<|im_end|>
    #      <|im_start|>user\n{user_message}<|im_end|>
    #      <|im_start|>assistant\n{response}<|im_end|>
    #
    # 3. PARAMETER: Generation settings
    #    - stop: Tokens that end generation (prevent infinite output)
    #    - temperature, top_p, etc. can be added here
    # ----------------------------------------------------------------------------

    modelfile_content = f'''FROM /experiments/{experiment_name}/gguf/{gguf_filename}

# TEACHING: ChatML Template for Qwen2.5
# This tells Ollama how to format multi-turn conversations.
# The template MUST match what the model was trained on.
TEMPLATE """{{{{ if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}{{{{ if .Prompt }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
{{{{ end }}}}<|im_start|>assistant
{{{{ .Response }}}}<|im_end|>
"""

# TEACHING: Stop Tokens
# These tokens tell Ollama when to STOP generating text.
# Without these, the model might continue generating the user's next message!
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"

# Optional: Default generation parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
'''

    with open(modelfile_path, "w") as f:
        f.write(modelfile_content)

    print(f"   ✅ Modelfile created: {modelfile_path}")
    print(f"   📋 Template: ChatML (Qwen format)")

    # ========================================================================
    # STEP 5: Register with Ollama
    # ========================================================================
    print(f"\n🔧 [5/5] Registering model with Ollama...")
    print(f"   Model name: {experiment_name}")

    # TEACHING: Why 'docker exec'?
    # ----------------------------------------------------------------------------
    # The 'ollama create' command needs to run INSIDE the Docker container,
    # because:
    # 1. Ollama's registry is inside the container
    # 2. The Modelfile path (/experiments/...) is relative to the container
    #
    # Alternative: Install Ollama natively on host (but then no isolation)
    # ----------------------------------------------------------------------------

    cmd = [
        "docker", "exec", "ollama",  # Run inside the 'ollama' container
        "ollama", "create", experiment_name,  # Create model with this name
        "-f", f"/experiments/{experiment_name}/Modelfile"  # Using this Modelfile
    ]

    print(f"   Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"   ✅ Model '{experiment_name}' created in Ollama!")

        # Show Ollama's response
        if result.stdout:
            print(f"   📄 Ollama output: {result.stdout.strip()}")

    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to create model in Ollama")
        print(f"   Error: {e.stderr}")
        print("\n   Troubleshooting:")
        print("   1. Ensure Ollama container is running: docker ps")
        print("   2. Check Modelfile syntax: cat experiments/.../Modelfile")
        print("   3. Verify GGUF file exists: ls experiments/.../gguf/")
        print("   4. Check Docker logs: docker logs ollama")
        sys.exit(1)

    # ========================================================================
    # Save Export Metadata
    # ========================================================================
    metadata = {
        "experiment_name": experiment_name,
        "base_model": base_model,
        "quantization": quantization,
        "gguf_file": gguf_filename,
        "gguf_size_mb": round(gguf_size_mb, 2),
        "ollama_model_name": experiment_name,
        "modelfile_path": modelfile_path,
        "export_timestamp": subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip()
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # ========================================================================
    # Success Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("✅ EXPORT COMPLETE!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   Model:        {experiment_name}")
    print(f"   Format:       GGUF ({quantization})")
    print(f"   Size:         {gguf_size_mb:.1f} MB")
    print(f"   Location:     {output_path}/{gguf_filename}")
    print(f"   Ollama:       Registered as '{experiment_name}'")

    print(f"\n🧪 Test Commands:")
    print(f"   # List models in Ollama")
    print(f"   docker exec ollama ollama list")
    print()
    print(f"   # Quick test")
    print(f"   curl http://localhost:11434/api/generate -d '{{")
    print(f"     \"model\": \"{experiment_name}\",")
    print(f"     \"prompt\": \"Hello! Who are you?\"")
    print(f"   }}'")
    print()
    print(f"   # Detailed test")
    print(f"   docker exec ollama ollama run {experiment_name}")

    print(f"\n📁 Files Created:")
    print(f"   • {output_path}/{gguf_filename}")
    print(f"   • {modelfile_path}")
    print(f"   • {metadata_path}")

    print(f"\n➡️  Next: Run Agent 2 (benchmark) to test this model")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Export LoRA adapters to Ollama (Agent 5)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (uses q4_k_m quantization)
  python scripts/export_to_ollama.py exp-001

  # Use 8-bit quantization (higher quality, larger file)
  python scripts/export_to_ollama.py exp-001 --quantization q8_0

  # Use full precision (largest file, best quality)
  python scripts/export_to_ollama.py exp-001 --quantization f16

  # Export with custom base model
  python scripts/export_to_ollama.py exp-001 --base-model unsloth/Qwen2.5-1.5B

TEACHING: When to Use Different Quantization Levels
  q4_k_m (default):  Fast, small, good for iteration. Use this 90% of the time.
  q8_0:              Larger, slightly better quality. Use for final evaluation.
  f16:               Full precision. Use only for comparing max quality.
        """
    )

    parser.add_argument(
        "experiment_name",
        help="Name of the experiment (e.g., exp-001)"
    )

    parser.add_argument(
        "--quantization",
        choices=["q4_k_m", "q8_0", "f16"],
        default="q4_k_m",
        help="GGUF quantization method (default: q4_k_m)"
    )

    parser.add_argument(
        "--base-model",
        default="unsloth/Qwen2.5-0.5B-Instruct",
        help="HuggingFace model ID (must match training)"
    )

    args = parser.parse_args()

    export_model(
        experiment_name=args.experiment_name,
        quantization=args.quantization,
        base_model=args.base_model
    )


if __name__ == "__main__":
    main()
