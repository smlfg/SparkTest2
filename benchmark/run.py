#!/usr/bin/env python3
"""
Agent 2: Benchmark Runner

This script runs all test prompts through both base and fine-tuned models,
then saves responses for delta analysis.

WORKFLOW:
1. Load benchmark prompts
2. Test base model (qwen2.5:0.5b)
3. Test fine-tuned model (experiment name)
4. Save results as JSON
5. Pass to Agent 3 for delta calculation

WHY TEST BASE MODEL TOO?
- Shows what changed (delta analysis)
- Catches regressions (fine-tuning made things worse)
- Proves improvements are real, not placebo

TIME: ~1 minute for 10 prompts (both models)

LEARNING OBJECTIVE:
Always compare against a baseline. Without it, you can't know
if your fine-tuning actually helped.
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import requests
from tqdm import tqdm

# Import benchmark prompts
from prompts import get_prompts


class OllamaClient:
    """
    Simple client for Ollama API.

    TEACHING NOTE:
    Ollama provides a simple REST API at http://localhost:11434
    Main endpoint: POST /api/generate
    - Takes: model name, prompt, options
    - Returns: generated text (streaming or complete)
    """

    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"

    def generate(self, model, prompt, temperature=0.7, max_tokens=512):
        """
        Generate response from model.

        Args:
            model: Model name (e.g., "qwen2.5:0.5b", "exp-001")
            prompt: Input text
            temperature: Sampling temperature (0=deterministic, 1=creative)
            max_tokens: Maximum response length

        Returns:
            dict with 'response' and 'metadata'
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,  # Get complete response, not streaming
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        try:
            start_time = time.time()
            response = requests.post(self.generate_url, json=payload, timeout=60)
            response.raise_for_status()
            elapsed = time.time() - start_time

            data = response.json()

            return {
                "response": data["response"],
                "metadata": {
                    "model": model,
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_time_seconds": elapsed,
                }
            }

        except requests.exceptions.RequestException as e:
            return {
                "response": f"ERROR: {str(e)}",
                "metadata": {
                    "model": model,
                    "error": str(e),
                }
            }

    def check_health(self):
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def list_models(self):
        """List available models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except:
            return []


def run_benchmark(client, model_name, prompts, description=""):
    """
    Run all prompts through a model.

    Returns:
        List of results with prompt, response, and metadata
    """
    print(f"\n🧪 Benchmarking: {model_name}")
    if description:
        print(f"   {description}")

    results = []

    for prompt_info in tqdm(prompts, desc=f"Testing {model_name}"):
        # Generate response
        result = client.generate(
            model=model_name,
            prompt=prompt_info["prompt"],
            temperature=0.7,  # Consistent temperature for fair comparison
            max_tokens=512,
        )

        # Combine prompt info with result
        full_result = {
            "prompt_id": prompt_info["id"],
            "category": prompt_info["category"],
            "prompt": prompt_info["prompt"],
            "expected": prompt_info.get("expected", ""),
            "response": result["response"],
            "metadata": result["metadata"],
            "timestamp": datetime.now().isoformat(),
        }

        results.append(full_result)

        # Brief delay to avoid overwhelming the API
        time.sleep(0.1)

    return results


def save_results(results, output_path):
    """Save benchmark results as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✓ Results saved to {output_path}")


def print_summary(results, model_name):
    """Print quick summary of results."""
    print(f"\n📊 Summary for {model_name}:")

    total_tokens = sum(
        r["metadata"].get("completion_tokens", 0)
        for r in results
    )
    total_time = sum(
        r["metadata"].get("total_time_seconds", 0)
        for r in results
    )

    avg_response_length = sum(len(r["response"]) for r in results) / len(results)

    print(f"   Prompts tested: {len(results)}")
    print(f"   Total tokens generated: {total_tokens}")
    print(f"   Total time: {total_time:.1f}s")
    print(f"   Avg time per prompt: {total_time/len(results):.1f}s")
    print(f"   Avg response length: {avg_response_length:.0f} chars")

    # Check for errors
    errors = [r for r in results if "ERROR" in r["response"]]
    if errors:
        print(f"   ⚠️  Errors: {len(errors)}")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run benchmark suite on base and fine-tuned models"
    )

    parser.add_argument(
        "experiment_name",
        type=str,
        help="Experiment name (must exist in Ollama)"
    )

    parser.add_argument(
        "--base-model",
        type=str,
        default="qwen2.5:0.5b",
        help="Base model name (default: qwen2.5:0.5b)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="benchmark/results",
        help="Output directory (default: benchmark/results)"
    )

    parser.add_argument(
        "--skip-base",
        action="store_true",
        help="Skip base model testing (use existing results)"
    )

    return parser.parse_args()


def main():
    """Main benchmark pipeline."""
    print("=" * 60)
    print("Agent 2: Benchmark Runner")
    print("=" * 60)

    # Parse arguments
    args = parse_args()

    # Setup
    client = OllamaClient()
    output_dir = Path(args.output_dir)

    # Check Ollama is running
    print("\n🔍 Checking Ollama status...")
    if not client.check_health():
        print("❌ Error: Ollama is not running")
        print("Start it with: docker-compose up -d")
        return 1

    print("✓ Ollama is running")

    # List available models
    available_models = client.list_models()
    print(f"✓ Available models: {len(available_models)}")

    # Verify models exist
    if args.base_model not in available_models and not args.skip_base:
        print(f"❌ Error: Base model '{args.base_model}' not found")
        print(f"Pull it with: docker exec ollama ollama pull {args.base_model}")
        return 1

    if args.experiment_name not in available_models:
        print(f"❌ Error: Experiment model '{args.experiment_name}' not found")
        print(f"Export it with: ./scripts/export_to_ollama.sh {args.experiment_name}")
        return 1

    # Load prompts
    prompts = get_prompts()
    print(f"\n✓ Loaded {len(prompts)} benchmark prompts")

    # Run benchmarks
    start_time = time.time()

    # Base model
    if not args.skip_base:
        base_results = run_benchmark(
            client,
            args.base_model,
            prompts,
            description="Baseline (unmodified model)"
        )
        save_results(base_results, output_dir / "base.json")
        print_summary(base_results, args.base_model)
    else:
        print(f"\n⏭️  Skipping base model (using existing results)")

    # Fine-tuned model
    finetuned_results = run_benchmark(
        client,
        args.experiment_name,
        prompts,
        description="Fine-tuned model"
    )
    save_results(finetuned_results, output_dir / "finetuned.json")
    print_summary(finetuned_results, args.experiment_name)

    # Overall summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("✅ Benchmark complete!")
    print(f"⏱️  Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"📁 Results:")
    if not args.skip_base:
        print(f"   Base: {output_dir / 'base.json'}")
    print(f"   Fine-tuned: {output_dir / 'finetuned.json'}")
    print("\nNext steps:")
    print("  1. Calculate deltas: python benchmark/delta.py")
    print("  2. Generate report: python benchmark/visualize.py")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
