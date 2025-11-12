#!/usr/bin/env python3
"""
Automated Benchmark Runner (HARDENED VERSION)

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

ROBUSTNESS FEATURES:
- Retry logic with exponential backoff (3 attempts)
- Extended timeout for cold starts (60s → 120s)
- Model warmup to prevent first-query slowness
- Empty response detection and warnings
- Comprehensive error reporting
"""

import requests
import json
import time
import argparse
import sys
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
# OLLAMA API HELPERS
# ============================================================
def query_ollama_with_retry(model_name: str, prompt: str, max_tokens: int = 200, max_retries: int = 3) -> dict:
    """
    TEACHING: Robust API interaction with retry logic

    WHY RETRY?
    - Cold start: First query can take 60s+ as Ollama loads model into VRAM
    - Network glitches: Transient connection issues
    - GPU throttling: Temporary slowdowns

    RETRY STRATEGY:
    - Attempt 1: 60s timeout (normal operation)
    - Attempt 2: 120s timeout (cold start or slow GPU)
    - Attempt 3: 180s timeout (last resort)
    - Exponential backoff: Wait 2s, 4s between retries

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

    # TEACHING: Progressive timeout strategy
    # First attempt: assume warm start (60s)
    # Later attempts: assume cold start or slow system (120s, 180s)
    timeouts = [60, 120, 180]

    last_error = None
    for attempt in range(max_retries):
        timeout = timeouts[min(attempt, len(timeouts) - 1)]

        try:
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()  # TEACHING: Raises exception if HTTP error

            result = response.json()

            # TEACHING: Defensive check - did we actually get a response?
            if "response" not in result:
                raise ValueError(f"Ollama returned malformed JSON (missing 'response' field)")

            return result

        except requests.exceptions.Timeout as e:
            last_error = f"Timeout after {timeout}s"
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 2s, 4s
                print(f"⏱️  Timeout (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...", flush=True)
                time.sleep(wait_time)
            continue

        except requests.exceptions.ConnectionError as e:
            last_error = f"Connection failed: {e}"
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"🔌 Connection error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...", flush=True)
                time.sleep(wait_time)
            continue

        except requests.exceptions.RequestException as e:
            last_error = f"Request error: {e}"
            # Non-retryable error (e.g., 404 model not found)
            print(f"      ❌ Error querying {model_name}: {e}")
            return {"error": str(e), "response": "", "retryable": False}

        except ValueError as e:
            last_error = f"Invalid response: {e}"
            print(f"      ❌ Error: {e}")
            return {"error": str(e), "response": "", "retryable": False}

    # All retries exhausted
    print(f"      ❌ Failed after {max_retries} attempts: {last_error}")
    return {"error": last_error, "response": "", "retries_exhausted": True}


def warmup_model(model_name: str) -> bool:
    """
    TEACHING: Model warmup

    WHY WARMUP?
    - First inference is always slowest (10-60s) as Ollama loads model into VRAM
    - Subsequent inferences are fast (0.5-2s)
    - Warmup prevents first benchmark prompt from having unfair latency

    HOW IT WORKS:
    - Send a dummy prompt ("Hi")
    - Wait for response (or timeout)
    - Ignore result, but now model is loaded in memory
    """
    print(f"   Warming up model '{model_name}'...", end=" ", flush=True)

    try:
        result = query_ollama_with_retry(model_name, "Hi", max_tokens=10, max_retries=2)

        if "error" in result and result.get("response") == "":
            print(f"❌ Warmup failed: {result['error']}")
            return False

        print(f"✅ Ready")
        return True

    except Exception as e:
        print(f"❌ Warmup failed: {e}")
        return False

# ============================================================
# BENCHMARK EXECUTION
# ============================================================
def run_benchmark_on_model(model_name: str) -> tuple[list, dict]:
    """
    Run all 10 prompts on one model

    Returns:
        - results: List of dicts with prompt + response
        - stats: Dict with error/warning counts
    """
    results = []
    stats = {
        "total": len(BENCHMARK_PROMPTS),
        "success": 0,
        "errors": 0,
        "empty_responses": 0,
        "warnings": [],
    }

    print(f"\n{'='*60}")
    print(f"BENCHMARKING: {model_name}")
    print(f"{'='*60}")

    for i, prompt_data in enumerate(BENCHMARK_PROMPTS, 1):
        prompt_id = prompt_data["id"]
        prompt_text = prompt_data["prompt"]

        print(f"[{i}/{stats['total']}] {prompt_id}...", end=" ", flush=True)

        # Query model with retry logic
        start_time = time.time()
        response_data = query_ollama_with_retry(model_name, prompt_text)
        elapsed = time.time() - start_time

        # Extract response text
        response_text = response_data.get("response", "")

        # TEACHING: Defensive check for empty responses
        has_error = "error" in response_data and response_text == ""
        is_empty = response_text.strip() == ""

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
                "had_error": has_error,
                "is_empty": is_empty,
            }
        }

        # Add error details if present
        if has_error:
            result["metadata"]["error"] = response_data.get("error")

        results.append(result)

        # Update statistics and print status
        if has_error:
            stats["errors"] += 1
            print(f"❌ ERROR ({elapsed:.1f}s)")
            stats["warnings"].append(f"Prompt {i} ({prompt_id}): {response_data.get('error')}")
        elif is_empty:
            stats["empty_responses"] += 1
            stats["success"] += 1  # Technically succeeded, but suspicious
            print(f"⚠️  EMPTY ({elapsed:.1f}s)")
            stats["warnings"].append(f"Prompt {i} ({prompt_id}): Empty response")
        else:
            stats["success"] += 1
            print(f"✅ ({elapsed:.1f}s, {len(response_text)} chars)")

    return results, stats

# ============================================================
# MAIN EXECUTION
# ============================================================
def main():
    print("="*60)
    print("BENCHMARK SUITE (HARDENED)")
    print("="*60)
    print(f"Base model:       {args.base}")
    print(f"Fine-tuned model: {args.finetuned}")
    print(f"Prompts:          {len(BENCHMARK_PROMPTS)}")
    print(f"Ollama URL:       {args.ollama_url}")

    # TEACHING: Why check model exists first?
    # Better to fail fast with clear error than run half a benchmark
    print("\nChecking Ollama connection...")
    for attempt in range(3):
        try:
            # Check connection with timeout
            response = requests.get(f"{args.ollama_url}/api/tags", timeout=10)
            response.raise_for_status()
            available_models = [m["name"] for m in response.json().get("models", [])]

            if args.base not in available_models:
                print(f"❌ Base model '{args.base}' not found in Ollama")
                print(f"   Available models: {', '.join(available_models) if available_models else '(none)'}")
                print(f"   Pull it with: ollama pull {args.base}")
                sys.exit(1)

            if args.finetuned not in available_models:
                print(f"❌ Fine-tuned model '{args.finetuned}' not found in Ollama")
                print(f"   Available models: {', '.join(available_models) if available_models else '(none)'}")
                print(f"   Did Agent 5 export it? Run: ./scripts/export_to_ollama.sh")
                sys.exit(1)

            print(f"✅ Connected! Found {len(available_models)} models")
            print(f"   Base: {args.base}")
            print(f"   Fine-tuned: {args.finetuned}")
            break

        except requests.exceptions.ConnectionError as e:
            if attempt < 2:
                wait = 2 ** attempt
                print(f"🔌 Connection failed (attempt {attempt + 1}/3), retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"❌ Cannot connect to Ollama at {args.ollama_url}")
                print(f"   Is Ollama running? Try:")
                print(f"   - docker-compose ps")
                print(f"   - docker-compose up -d ollama")
                sys.exit(1)

        except Exception as e:
            print(f"❌ Error connecting to Ollama: {e}")
            print(f"   Check if Ollama is running at {args.ollama_url}")
            sys.exit(1)

    # Warm up models (load into VRAM)
    print("\n" + "="*60)
    print("WARMING UP MODELS")
    print("="*60)
    print("   TEACHING: First inference loads model into VRAM (slow).")
    print("   Warmup ensures fair latency measurements.\n")

    if not warmup_model(args.base):
        print(f"⚠️  Warning: Base model warmup failed. First query will be slow.")

    if not warmup_model(args.finetuned):
        print(f"⚠️  Warning: Fine-tuned model warmup failed. First query will be slow.")

    # Run benchmark on base model
    print("\n" + "="*60)
    print("PHASE 1: Base Model")
    print("="*60)
    base_results, base_stats = run_benchmark_on_model(args.base)

    # Save base results
    base_path = RESULTS_DIR / "base.json"
    with open(base_path, "w", encoding="utf-8") as f:
        json.dump(base_results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Base results saved to {base_path}")

    # Print base model statistics
    print(f"\nBase Model Statistics:")
    print(f"   Success: {base_stats['success']}/{base_stats['total']}")
    print(f"   Errors: {base_stats['errors']}")
    print(f"   Empty responses: {base_stats['empty_responses']}")
    if base_stats['warnings']:
        print(f"   Warnings:")
        for warning in base_stats['warnings']:
            print(f"      - {warning}")

    # Small delay between benchmarks (be nice to GPU)
    print("\nWaiting 5 seconds before next benchmark...")
    time.sleep(5)

    # Run benchmark on fine-tuned model
    print("\n" + "="*60)
    print("PHASE 2: Fine-tuned Model")
    print("="*60)
    finetuned_results, finetuned_stats = run_benchmark_on_model(args.finetuned)

    # Save fine-tuned results
    finetuned_path = RESULTS_DIR / "finetuned.json"
    with open(finetuned_path, "w", encoding="utf-8") as f:
        json.dump(finetuned_results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Fine-tuned results saved to {finetuned_path}")

    # Print fine-tuned model statistics
    print(f"\nFine-tuned Model Statistics:")
    print(f"   Success: {finetuned_stats['success']}/{finetuned_stats['total']}")
    print(f"   Errors: {finetuned_stats['errors']}")
    print(f"   Empty responses: {finetuned_stats['empty_responses']}")
    if finetuned_stats['warnings']:
        print(f"   Warnings:")
        for warning in finetuned_stats['warnings']:
            print(f"      - {warning}")

    # Overall summary
    print("\n" + "="*60)
    print("BENCHMARK COMPLETE")
    print("="*60)
    print(f"Base results:       {base_path}")
    print(f"Fine-tuned results: {finetuned_path}")

    total_errors = base_stats['errors'] + finetuned_stats['errors']
    total_empty = base_stats['empty_responses'] + finetuned_stats['empty_responses']

    if total_errors > 0:
        print(f"\n⚠️  WARNING: {total_errors} prompts failed with errors!")
        print(f"   Check logs above for details. Agent 3 may have incomplete data.")

    if total_empty > 0:
        print(f"\n⚠️  WARNING: {total_empty} prompts returned empty responses!")
        print(f"   This may indicate model issues or prompt problems.")

    if total_errors == 0 and total_empty == 0:
        print(f"\n✅ All prompts succeeded with non-empty responses!")

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
