#!/usr/bin/env python3
"""
================================================================================
DGX Spark Fast Fine-tuning System
Agent 2: Benchmark Runner - Automated Testing
================================================================================

WHAT: Run benchmark prompts against base and fine-tuned models
WHY:  Need systematic comparison to measure fine-tuning impact
HOW:  1. Load 10 test prompts
      2. Query base model
      3. Query fine-tuned model
      4. Save results as JSON

USAGE: python benchmark/run.py --finetuned <model_name>

EXAMPLE: python benchmark/run.py --finetuned exp-001

TIME: ~1 minute for 10 prompts (2 models)

OUTPUT:
  - benchmark/results/base.json
  - benchmark/results/finetuned.json
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
RESULTS_DIR = Path("benchmark/results")

# Inference settings
TEMPERATURE = 0.7  # Randomness (0=deterministic, 1=creative)
MAX_TOKENS = 500  # Maximum response length
TOP_P = 0.9  # Nucleus sampling


# ===== HELPER FUNCTIONS =====

def check_ollama_running(url: str):
    """Check if Ollama server is accessible."""
    try:
        response = requests.get(f"{url}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def check_model_exists(url: str, model_name: str):
    """Check if a model is available in Ollama."""
    try:
        response = requests.get(f"{url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(m["name"] == model_name for m in models)
    except requests.exceptions.RequestException:
        pass
    return False


def query_ollama(url: str, model_name: str, prompt: str, temperature: float = TEMPERATURE) -> Dict:
    """
    Send a prompt to Ollama and get response.
    """
    api_url = f"{url}/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": MAX_TOKENS,
            "top_p": TOP_P,
        }
    }

    start_time = time.time()

    try:
        response = requests.post(api_url, json=payload, timeout=60)
        response.raise_for_status()

        elapsed = time.time() - start_time
        result = response.json()

        return {
            "response": result.get("response", ""),
            "latency_seconds": elapsed,
            "response_length": len(result.get("response", "")),
            "error": None
        }

    except requests.exceptions.RequestException as e:
        return {
            "response": "",
            "latency_seconds": 0,
            "response_length": 0,
            "error": str(e)
        }


def run_benchmark_on_model(url: str, model_name: str, model_type: str) -> List[Dict]:
    """
    Run all benchmark prompts against a model.
    """
    print(f"\n🔍 Testing {model_type} model: {model_name}")
    print("-" * 80)

    results = []

    for prompt_data in tqdm(BENCHMARK_PROMPTS, desc=f"Running {model_type}"):
        prompt_id = prompt_data["id"]
        prompt_text = prompt_data["prompt"]

        # Query model
        response_data = query_ollama(url, model_name, prompt_text)

        # Store result
        result = {
            "prompt_id": prompt_id,
            "prompt": prompt_text,
            "response": response_data["response"],
            "metadata": {
                "category": prompt_data["category"],
                "ground_truth": prompt_data.get("ground_truth"),
                "keywords": prompt_data.get("keywords"),
                "latency_seconds": response_data["latency_seconds"],
                "response_length": response_data["response_length"],
            }
        }
        results.append(result)
        time.sleep(0.1)

    return results


def save_results(results: List[Dict], output_file: Path):
    """Save benchmark results to JSON file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / output_file
    with open(output_path, 'w', encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"   ✅ Saved to: {output_path}")


def print_summary(results: List[Dict], model_type: str):
    """Print quick summary of results."""
    total_prompts = len(results)
    errors = sum(1 for r in results if r.get("error"))
    avg_time = sum(r["metadata"]["latency_seconds"] for r in results) / total_prompts if total_prompts > 0 else 0
    avg_len = sum(r["metadata"]["response_length"] for r in results) / total_prompts if total_prompts > 0 else 0

    print(f"\n📊 {model_type.upper()} Summary:")
    print(f"   Total prompts: {total_prompts}")
    print(f"   Successful: {total_prompts - errors}")
    print(f"   Errors: {errors}")
    print(f"   Avg time: {avg_time:.2f}s")
    print(f"   Avg length: {avg_len:.0f} chars")


# ===== MAIN FUNCTION =====

def main(args):
    """
    Main benchmark workflow.
    """
    print("=" * 80)
    print("🚀 Starting Benchmark Suite")
    print("=" * 80)
    print(f"Base model:       {args.base}")
    print(f"Fine-tuned model: {args.finetuned}")
    print(f"Ollama URL:       {args.ollama_url}")

    # ===== STEP 1: VALIDATE OLLAMA =====
    print("\n🔧 Checking prerequisites...")

    if not check_ollama_running(args.ollama_url):
        print(f"❌ Error: Ollama is not running at {args.ollama_url}!")
        print("   Start it with: docker-compose up -d")
        sys.exit(1)
    print("   ✅ Ollama is running")

    # ===== STEP 2: CHECK MODELS =====
    if not check_model_exists(args.ollama_url, args.base):
        print(f"❌ Error: Base model '{args.base}' not found!")
        print(f"   Pull it with: ollama pull {args.base}")
        sys.exit(1)
    print(f"   ✅ Base model '{args.base}' available")

    if not check_model_exists(args.ollama_url, args.finetuned):
        print(f"❌ Error: Fine-tuned model '{args.finetuned}' not found!")
        print(f"   Export it from your experiment directory.")
        sys.exit(1)
    print(f"   ✅ Fine-tuned model '{args.finetuned}' available")

    # ===== STEP 3: RUN BENCHMARK ON BASE MODEL =====
    base_results = run_benchmark_on_model(args.ollama_url, args.base, "base")
    print_summary(base_results, "base")
    save_results(base_results, Path("base.json"))

    # ===== STEP 4: RUN BENCHMARK ON FINE-TUNED MODEL =====
    finetuned_results = run_benchmark_on_model(args.ollama_url, args.finetuned, "finetuned")
    print_summary(finetuned_results, "finetuned")
    save_results(finetuned_results, Path("finetuned.json"))

    # ===== SUMMARY =====
    print("\n" + "=" * 80)
    print("✅ Benchmark Complete!")
    print("=" * 80)
    print(f"\nResults saved to: {RESULTS_DIR}")
    print(f"  - base.json: {args.base}")
    print(f"  - finetuned.json: {args.finetuned}")
    print(f"\nNext steps:")
    print(f"  1. Calculate deltas: python benchmark/delta.py")
    print(f"  2. Generate report: python benchmark/visualize.py")
    print("=" * 80)


# ===== ENTRY POINT =====

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run benchmark suite against base and fine-tuned models.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--base", default="qwen2.5:0.5b", help="Base model name in Ollama")
    parser.add_argument("--finetuned", required=True, help="Fine-tuned model name in Ollama")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama API URL")
    
    args = parser.parse_args()
    main(args)

