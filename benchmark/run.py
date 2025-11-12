#!/usr/bin/env python3
"""
Automated Benchmark Runner

WHAT THIS DOES:
1. Loads 10 standard prompts
2. Runs each prompt on TWO models:
   - Base model (e.g., qwen2.5:0.5b)
   - Fine-tuned model (e.g., exp-001)
3. Saves responses to JSON files

WHY AUTOMATED?
- Manual testing: 10 prompts × 2 models = 20 copy-pastes (5+ minutes, error-prone)
- Automated: One command, 1-2 minutes, perfectly consistent

OUTPUT:
benchmark/results/base.json       → Base model responses
benchmark/results/finetuned.json  → Fine-tuned model responses

Next step: Agent 3 compares these files
"""

import requests
import json
import time
import argparse
from pathlib import Path
from prompts import BENCHMARK_PROMPTS

# ============================================================
# CONFIGURATION
# ============================================================
parser = argparse.ArgumentParser(description="Run benchmark suite")
parser.add_argument("--base", default="qwen2.5:0.5b", help="Base model name in Ollama")
parser.add_argument("--finetuned", required=True, help="Fine-tuned model name in Ollama")
parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama API URL")
args = parser.parse_args()

# Output directory
RESULTS_DIR = Path("benchmark/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# OLLAMA API HELPER
# ============================================================
def query_ollama(model_name: str, prompt: str, max_tokens: int = 200) -> dict:
    """
    TEACHING: API interaction

    Ollama provides a local API (like OpenAI's but free and local):
    POST http://localhost:11434/api/generate

    Request format:
    {
      "model": "qwen2.5:0.5b",
      "prompt": "What is 2+2?",
      "stream": false
    }

    Response format:
    {
      "model": "qwen2.5:0.5b",
      "response": "4",
      "done": true,
      ...
    }
    """
    url = f"{args.ollama_url}/api/generate"

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,  # TEACHING: stream=False gets complete response at once
        "options": {
            "temperature": 0.7,  # TEACHING: 0.7 = balanced creativity vs consistency
            "num_predict": max_tokens,  # TEACHING: Max tokens to generate
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()  # TEACHING: Raises exception if HTTP error
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"      ❌ Error querying {model_name}: {e}")
        return {"error": str(e), "response": ""}

# ============================================================
# BENCHMARK EXECUTION
# ============================================================
def run_benchmark_on_model(model_name: str) -> list:
    """
    Run all 10 prompts on one model

    Returns: List of dicts with prompt + response
    """
    results = []

    print(f"\n{'='*60}")
    print(f"BENCHMARKING: {model_name}")
    print(f"{'='*60}")

    for i, prompt_data in enumerate(BENCHMARK_PROMPTS, 1):
        prompt_id = prompt_data["id"]
        prompt_text = prompt_data["prompt"]

        print(f"[{i}/10] {prompt_id}...", end=" ", flush=True)

        # Query model
        start_time = time.time()
        response_data = query_ollama(model_name, prompt_text)
        elapsed = time.time() - start_time

        # Extract response text
        response_text = response_data.get("response", "")

        # Store result
        result = {
            "prompt_id": prompt_id,
            "prompt": prompt_text,
            "response": response_text,
            "metadata": {
                "category": prompt_data["category"],
                "ground_truth": prompt_data.get("ground_truth"),
                "keywords": prompt_data.get("keywords"),
                "latency_seconds": elapsed,
                "response_length": len(response_text),
            }
        }

        results.append(result)

        print(f"✅ ({elapsed:.1f}s, {len(response_text)} chars)")

    return results

# ============================================================
# MAIN EXECUTION
# ============================================================
def main():
    print("="*60)
    print("BENCHMARK SUITE")
    print("="*60)
    print(f"Base model:       {args.base}")
    print(f"Fine-tuned model: {args.finetuned}")
    print(f"Prompts:          {len(BENCHMARK_PROMPTS)}")
    print(f"Ollama URL:       {args.ollama_url}")

    # TEACHING: Why check model exists first?
    # Better to fail fast with clear error than run half a benchmark
    print("\nChecking if models exist...")
    try:
        # Check base model
        response = requests.get(f"{args.ollama_url}/api/tags")
        available_models = [m["name"] for m in response.json().get("models", [])]

        if args.base not in available_models:
            print(f"❌ Base model '{args.base}' not found in Ollama")
            print(f"   Available models: {', '.join(available_models)}")
            return

        if args.finetuned not in available_models:
            print(f"❌ Fine-tuned model '{args.finetuned}' not found in Ollama")
            print(f"   Available models: {', '.join(available_models)}")
            print(f"   Did Agent 5 export it?")
            return

        print("✅ Both models found")
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        print(f"   Is Ollama running? Try: docker-compose ps")
        return

    # Run benchmark on base model
    print("\n" + "="*60)
    print("PHASE 1: Base Model")
    print("="*60)
    base_results = run_benchmark_on_model(args.base)

    # Save base results
    base_path = RESULTS_DIR / "base.json"
    with open(base_path, "w", encoding="utf-8") as f:
        json.dump(base_results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Base results saved to {base_path}")

    # Small delay between benchmarks (be nice to GPU)
    print("\nWaiting 5 seconds before next benchmark...")
    time.sleep(5)

    # Run benchmark on fine-tuned model
    print("\n" + "="*60)
    print("PHASE 2: Fine-tuned Model")
    print("="*60)
    finetuned_results = run_benchmark_on_model(args.finetuned)

    # Save fine-tuned results
    finetuned_path = RESULTS_DIR / "finetuned.json"
    with open(finetuned_path, "w", encoding="utf-8") as f:
        json.dump(finetuned_results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Fine-tuned results saved to {finetuned_path}")

    # Summary
    print("\n" + "="*60)
    print("BENCHMARK COMPLETE")
    print("="*60)
    print(f"Base results:       {base_path}")
    print(f"Fine-tuned results: {finetuned_path}")
    print(f"\nNext step: Run Agent 3 to calculate deltas")
    print(f"Command: python benchmark/delta.py")
    print("="*60)

if __name__ == "__main__":
    main()

# TEACHING: What did we build?
"""
BEFORE (Manual Testing):
1. Open Ollama WebUI
2. Type prompt 1
3. Copy response
4. Switch to fine-tuned model
5. Type prompt 1 again
6. Copy response
7. Compare in head (subjective!)
8. Repeat 9 more times
Time: 10-15 minutes, error-prone

AFTER (Automated):
1. python benchmark/run.py --finetuned exp-001
Time: 1-2 minutes, perfectly consistent

BENEFITS:
- Reproducible (same prompts every time)
- Fast (automated)
- Objective (saves raw responses for analysis)
- Scalable (add more prompts easily)
"""
