#!/usr/bin/env python3
"""
================================================================================
DGX Spark Fast Fine-tuning System
Agent 2: Benchmark Runner - Automated Testing
================================================================================

WHAT: Run benchmark prompts against base and fine-tuned models
WHY:  Need systematic comparison to measure fine-tuning impact
HOW:  1. Load 10 test prompts
      2. Query base model (qwen2.5:0.5b)
      3. Query fine-tuned model
      4. Save results as JSON

USAGE: python benchmark/run.py <experiment_name>

EXAMPLE: python benchmark/run.py exp-001

TIME: ~1 minute for 10 prompts (2 models)

OUTPUT:
  - benchmark/results/base.json
  - benchmark/results/finetuned.json

================================================================================
LEARNING OBJECTIVES:
- How to use Ollama API for inference
- Why we test both models (need baseline for comparison)
- Importance of reproducible evaluation
- How to structure benchmark results
================================================================================
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List

import requests
from tqdm import tqdm

from prompts import BENCHMARK_PROMPTS

# ===== CONFIGURATION =====
OLLAMA_API_URL = "http://localhost:11434/api/generate"
BASE_MODEL = "qwen2.5:0.5b"  # Must be pulled: ollama pull qwen2.5:0.5b
RESULTS_DIR = Path("benchmark/results")

# Inference settings
TEMPERATURE = 0.7  # Randomness (0=deterministic, 1=creative)
MAX_TOKENS = 500  # Maximum response length
TOP_P = 0.9  # Nucleus sampling


# ===== HELPER FUNCTIONS =====

def check_ollama_running():
    """Check if Ollama server is accessible."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def check_model_exists(model_name):
    """Check if a model is available in Ollama."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(m["name"] == model_name for m in models)
    except requests.exceptions.RequestException:
        pass
    return False


def query_ollama(model_name: str, prompt: str, temperature: float = TEMPERATURE) -> Dict:
    """
    Send a prompt to Ollama and get response.

    WHY STREAMING=FALSE? We want the complete response at once for easier processing.
    In production, you might stream for better UX.

    Returns:
        dict with 'response', 'time_ms', 'tokens'
    """
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,  # Get complete response
        "options": {
            "temperature": temperature,
            "num_predict": MAX_TOKENS,
            "top_p": TOP_P,
        }
    }

    start_time = time.time()

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status()

        elapsed_ms = (time.time() - start_time) * 1000
        result = response.json()

        return {
            "response": result.get("response", ""),
            "time_ms": elapsed_ms,
            "tokens": result.get("eval_count", 0),
            "error": None
        }

    except requests.exceptions.RequestException as e:
        return {
            "response": "",
            "time_ms": 0,
            "tokens": 0,
            "error": str(e)
        }


def run_benchmark(model_name: str, model_type: str) -> List[Dict]:
    """
    Run all benchmark prompts against a model.

    Args:
        model_name: Ollama model name
        model_type: "base" or "finetuned" (for labeling)

    Returns:
        List of results, one per prompt
    """
    print(f"\n🔍 Testing {model_type} model: {model_name}")
    print("-" * 80)

    results = []

    for prompt_data in tqdm(BENCHMARK_PROMPTS, desc=f"Running {model_type}"):
        # Extract prompt
        prompt_id = prompt_data["id"]
        prompt_text = prompt_data["prompt"]
        category = prompt_data["category"]

        # Query model
        result = query_ollama(model_name, prompt_text)

        # Store result with metadata
        results.append({
            # Prompt metadata
            "prompt_id": prompt_id,
            "category": category,
            "prompt": prompt_text,
            "expected_keywords": prompt_data["expected_keywords"],

            # Model response
            "model": model_name,
            "model_type": model_type,
            "response": result["response"],

            # Performance metrics
            "time_ms": result["time_ms"],
            "tokens": result["tokens"],
            "tokens_per_second": result["tokens"] / (result["time_ms"] / 1000) if result["time_ms"] > 0 else 0,

            # Error handling
            "error": result["error"],
        })

        # Small delay to avoid overwhelming Ollama
        time.sleep(0.1)

    return results


def save_results(results: List[Dict], output_file: Path):
    """Save benchmark results to JSON file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_DIR / output_file

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"   ✅ Saved to: {output_path}")


def print_summary(results: List[Dict], model_type: str):
    """Print quick summary of results."""
    total_prompts = len(results)
    errors = sum(1 for r in results if r["error"])
    avg_time = sum(r["time_ms"] for r in results) / total_prompts if total_prompts > 0 else 0
    avg_tokens = sum(r["tokens"] for r in results) / total_prompts if total_prompts > 0 else 0

    print(f"\n📊 {model_type.upper()} Summary:")
    print(f"   Total prompts: {total_prompts}")
    print(f"   Successful: {total_prompts - errors}")
    print(f"   Errors: {errors}")
    print(f"   Avg time: {avg_time:.0f}ms")
    print(f"   Avg tokens: {avg_tokens:.0f}")


# ===== MAIN FUNCTION =====

def main(experiment_name: str):
    """
    Main benchmark workflow.

    Steps:
        1. Validate Ollama is running
        2. Check base model exists
        3. Check fine-tuned model exists
        4. Run benchmark on base model
        5. Run benchmark on fine-tuned model
        6. Save results
    """
    print("=" * 80)
    print("🚀 Starting Benchmark Suite")
    print("=" * 80)

    # ===== STEP 1: VALIDATE OLLAMA =====
    print("\n🔧 Checking prerequisites...")

    if not check_ollama_running():
        print("❌ Error: Ollama is not running!")
        print("   Start it with: docker-compose up -d")
        sys.exit(1)
    print("   ✅ Ollama is running")

    # ===== STEP 2: CHECK BASE MODEL =====
    if not check_model_exists(BASE_MODEL):
        print(f"❌ Error: Base model '{BASE_MODEL}' not found!")
        print(f"   Pull it with: docker-compose exec ollama ollama pull {BASE_MODEL}")
        sys.exit(1)
    print(f"   ✅ Base model '{BASE_MODEL}' available")

    # ===== STEP 3: CHECK FINE-TUNED MODEL =====
    finetuned_model = experiment_name

    if not check_model_exists(finetuned_model):
        print(f"❌ Error: Fine-tuned model '{finetuned_model}' not found!")
        print(f"   Export it with: ./scripts/export_to_ollama.sh {experiment_name}")
        sys.exit(1)
    print(f"   ✅ Fine-tuned model '{finetuned_model}' available")

    # ===== STEP 4: RUN BENCHMARK ON BASE MODEL =====
    base_results = run_benchmark(BASE_MODEL, "base")
    print_summary(base_results, "base")
    save_results(base_results, "base.json")

    # ===== STEP 5: RUN BENCHMARK ON FINE-TUNED MODEL =====
    finetuned_results = run_benchmark(finetuned_model, "finetuned")
    print_summary(finetuned_results, "finetuned")
    save_results(finetuned_results, "finetuned.json")

    # ===== SUMMARY =====
    print("\n" + "=" * 80)
    print("✅ Benchmark Complete!")
    print("=" * 80)
    print(f"\nResults saved to: {RESULTS_DIR}")
    print(f"  - base.json: {BASE_MODEL}")
    print(f"  - finetuned.json: {finetuned_model}")
    print(f"\nNext steps:")
    print(f"  1. Calculate deltas: python benchmark/delta.py")
    print(f"  2. Generate report: python benchmark/visualize.py")
    print(f"  3. View results: open benchmark/results/report.html")
    print("=" * 80)


# ===== ENTRY POINT =====

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run benchmark suite against base and fine-tuned models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run benchmark for experiment exp-001
  python benchmark/run.py exp-001

  # Run benchmark for different experiment
  python benchmark/run.py chatbot-v2

Prerequisites:
  1. Ollama must be running: docker-compose up -d
  2. Base model must be pulled: ollama pull qwen2.5:0.5b
  3. Fine-tuned model must be exported: ./scripts/export_to_ollama.sh <name>

Output:
  - benchmark/results/base.json: Base model responses
  - benchmark/results/finetuned.json: Fine-tuned model responses

Tips:
  - If queries are slow, check GPU is enabled for Ollama
  - If model not found, verify with: ollama list
  - Results are deterministic (temperature controls randomness)
        """
    )

    parser.add_argument(
        "experiment_name",
        help="Name of the experiment (matches fine-tuned model name)"
    )

    args = parser.parse_args()

    # Run benchmark
    main(args.experiment_name)
