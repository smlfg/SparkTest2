#!/usr/bin/env python3

"""
AGENT 2: Benchmark Runner

This script runs benchmark prompts against models via Ollama API.

TEACHING NOTES:

1. WHY OLLAMA API?
   - Consistent inference interface (same API for all models)
   - No need to load models in Python (Ollama handles this)
   - Can run on CPU or GPU transparently
   - Easy to swap models for comparison

2. BENCHMARK METHODOLOGY:
   - Run same prompts on base and fine-tuned models
   - Same temperature/parameters for fair comparison
   - Save raw outputs (no cherry-picking)
   - Track timing (is fine-tuned model slower?)

3. WHAT WE MEASURE:
   - Response content (what does model say?)
   - Response length (is it verbose or concise?)
   - Response time (how fast is inference?)
   - Consistency (same prompt → similar output?)

4. OUTPUT FORMAT:
   - JSON for easy parsing by delta analyzer
   - Includes prompt, response, metadata
   - One file per model (base.json, finetuned.json)
"""

import argparse
import json
import os
import sys
import time
from typing import Dict, List

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from prompts import get_prompts, validate_prompts

console = Console()

################################################################################
# Ollama API Client
################################################################################

class OllamaClient:
    """Simple client for Ollama API."""

    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url

    def generate(self, model: str, prompt: str, temperature: float = 0.7) -> Dict:
        """
        Generate a response from a model.

        Returns:
            {
                "response": str,  # Generated text
                "duration_ms": int,  # Time taken
                "tokens": int  # Number of tokens generated
            }
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False  # Get complete response at once
        }

        start_time = time.time()

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            console.print(f"[red]Error: Cannot connect to Ollama at {self.base_url}[/red]")
            console.print("[yellow]Make sure Ollama is running: docker compose up -d[/yellow]")
            sys.exit(1)
        except requests.exceptions.Timeout:
            console.print(f"[red]Error: Request timed out (>120s)[/red]")
            return {
                "response": "[TIMEOUT]",
                "duration_ms": 120000,
                "tokens": 0
            }
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

        duration_ms = int((time.time() - start_time) * 1000)

        result = response.json()
        return {
            "response": result.get("response", ""),
            "duration_ms": duration_ms,
            "tokens": result.get("eval_count", 0)
        }

    def list_models(self) -> List[str]:
        """List available models."""
        url = f"{self.base_url}/api/tags"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        except Exception as e:
            console.print(f"[red]Error listing models: {e}[/red]")
            return []

    def model_exists(self, model_name: str) -> bool:
        """Check if a model exists."""
        models = self.list_models()
        return model_name in models


################################################################################
# Benchmark Runner
################################################################################

def run_benchmark(client: OllamaClient, model_name: str, prompts: List[Dict],
                  temperature: float = 0.7) -> List[Dict]:
    """
    Run all benchmark prompts against a model.

    Returns:
        List of results, one per prompt
    """
    results = []

    console.print(f"\n[cyan]Running benchmark on model: {model_name}[/cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:

        task = progress.add_task(
            f"Testing {len(prompts)} prompts...",
            total=len(prompts)
        )

        for prompt_data in prompts:
            prompt_id = prompt_data["id"]
            prompt_text = prompt_data["prompt"]

            # Generate response
            result = client.generate(model_name, prompt_text, temperature)

            # Store result with metadata
            results.append({
                "prompt_id": prompt_id,
                "prompt": prompt_text,
                "category": prompt_data["category"],
                "response": result["response"],
                "duration_ms": result["duration_ms"],
                "tokens": result["tokens"],
                "expected_behavior": prompt_data["expected_behavior"]
            })

            progress.update(task, advance=1)

    # Calculate summary stats
    total_time = sum(r["duration_ms"] for r in results) / 1000  # Convert to seconds
    total_tokens = sum(r["tokens"] for r in results)
    avg_time = total_time / len(results)

    console.print(f"[green]✓ Benchmark complete[/green]")
    console.print(f"[dim]  Total time: {total_time:.1f}s | "
                  f"Avg per prompt: {avg_time:.1f}s | "
                  f"Total tokens: {total_tokens}[/dim]")

    return results


################################################################################
# Main Function
################################################################################

def main():
    parser = argparse.ArgumentParser(
        description="Agent 2: Run benchmark suite against models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare base and fine-tuned models
  python benchmark/run.py \\
    --base qwen2.5:0.5b \\
    --finetuned exp-001 \\
    --output benchmark/results/

  # Test only fine-tuned model
  python benchmark/run.py \\
    --finetuned exp-001 \\
    --output benchmark/results/

  # Use custom prompts
  python benchmark/run.py \\
    --base qwen2.5:0.5b \\
    --finetuned exp-001 \\
    --domain medical \\
    --output benchmark/results/
        """
    )

    parser.add_argument(
        "--base",
        type=str,
        help="Base model name (e.g., qwen2.5:0.5b)"
    )
    parser.add_argument(
        "--finetuned",
        type=str,
        help="Fine-tuned model name (e.g., exp-001)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark/results/",
        help="Output directory for results (default: benchmark/results/)"
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="standard",
        choices=["standard", "medical", "coding", "customer_service"],
        help="Prompt domain (default: standard)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)"
    )
    parser.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama API URL (default: http://localhost:11434)"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.base and not args.finetuned:
        console.print("[red]Error: Specify at least one of --base or --finetuned[/red]")
        sys.exit(1)

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    # Load prompts
    prompts = get_prompts(args.domain)
    is_valid, errors = validate_prompts(prompts)
    if not is_valid:
        console.print("[red]Error: Invalid prompts:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        sys.exit(1)

    console.print(f"[cyan]Loaded {len(prompts)} prompts from domain: {args.domain}[/cyan]")

    # Initialize Ollama client
    client = OllamaClient(args.ollama_url)

    # Check models exist
    if args.base:
        if not client.model_exists(args.base):
            console.print(f"[red]Error: Base model not found: {args.base}[/red]")
            console.print(f"[yellow]Available models: {', '.join(client.list_models())}[/yellow]")
            sys.exit(1)

    if args.finetuned:
        if not client.model_exists(args.finetuned):
            console.print(f"[red]Error: Fine-tuned model not found: {args.finetuned}[/red]")
            console.print(f"[yellow]Available models: {', '.join(client.list_models())}[/yellow]")
            console.print(f"[yellow]Did you export it? ./scripts/export_to_ollama.sh[/yellow]")
            sys.exit(1)

    console.print("\n[bold blue]" + "="*60 + "[/bold blue]")
    console.print("[bold blue]Agent 2: Benchmark Runner[/bold blue]")
    console.print("[bold blue]" + "="*60 + "[/bold blue]")

    # Run benchmarks
    if args.base:
        base_results = run_benchmark(client, args.base, prompts, args.temperature)
        base_path = os.path.join(args.output, "base.json")
        with open(base_path, 'w') as f:
            json.dump({
                "model": args.base,
                "domain": args.domain,
                "temperature": args.temperature,
                "results": base_results
            }, f, indent=2)
        console.print(f"[green]Saved base results to {base_path}[/green]")

    if args.finetuned:
        finetuned_results = run_benchmark(client, args.finetuned, prompts, args.temperature)
        finetuned_path = os.path.join(args.output, "finetuned.json")
        with open(finetuned_path, 'w') as f:
            json.dump({
                "model": args.finetuned,
                "domain": args.domain,
                "temperature": args.temperature,
                "results": finetuned_results
            }, f, indent=2)
        console.print(f"[green]Saved fine-tuned results to {finetuned_path}[/green]")

    console.print(f"\n[bold green]Benchmark complete! 🎉[/bold green]")
    console.print(f"\n[cyan]Next steps:[/cyan]")
    console.print(f"  Run delta analysis: [bold]python benchmark/delta.py --output {args.output}[/bold]")


if __name__ == "__main__":
    main()
