#!/usr/bin/env python3
"""
Parallel Coding Test Runner

WHY PARALLEL?
Sequential: 10 prompts × 2s each = 20 seconds
Parallel:   10 prompts at once = 3-5 seconds

HOW IT WORKS:
- Uses asyncio + aiohttp for concurrent requests
- Sends all 10 prompts to Ollama simultaneously
- Ollama processes them in parallel (GPU can handle it)
- Results come back ~4x faster

TEACHING NOTES:
This is a practical example of async programming in Python!

USAGE:
    from parallel_runner import CodingTestRunner

    runner = CodingTestRunner()
    runner.run_test_suite("qwen2.5:0.5b", epoch=0, model_type="base")
"""

import asyncio
import aiohttp
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from coding_prompts import CODING_TEST_PROMPTS

# ============================================================
# TEACHING PRINTER
# ============================================================

class TeachingPrinter:
    """Pedagogical output helpers"""

    @staticmethod
    def section(title):
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)

    @staticmethod
    def explain(text, indent=2):
        spaces = " " * indent
        print(f"{spaces}💡 {text}")

    @staticmethod
    def fact(label, value, indent=2):
        spaces = " " * indent
        print(f"{spaces}📊 {label}: {value}")

    @staticmethod
    def success(text, indent=2):
        spaces = " " * indent
        print(f"{spaces}✅ {text}")

    @staticmethod
    def progress(text, indent=2):
        spaces = " " * indent
        print(f"{spaces}🔄 {text}")

teach = TeachingPrinter()

# ============================================================
# PARALLEL EXECUTION ENGINE
# ============================================================

async def query_ollama_async(session: aiohttp.ClientSession,
                             model: str,
                             prompt: str,
                             prompt_id: str,
                             timeout: int = 60) -> Dict:
    """
    TEACHING: Async query to Ollama

    What's happening:
    - This function doesn't BLOCK waiting for response
    - While waiting for Ollama, other prompts can be sent
    - Result: 10 requests happen "at the same time"

    async/await magic:
    - async def = this function can pause and resume
    - await = pause here, let other tasks run
    - asyncio schedules all tasks concurrently
    """
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 300,  # Max tokens for code
        }
    }

    try:
        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        async with session.post(url, json=payload, timeout=timeout_obj) as response:
            result = await response.json()
            return {
                "prompt_id": prompt_id,
                "response": result.get("response", ""),
                "success": True,
                "error": None
            }
    except asyncio.TimeoutError:
        return {
            "prompt_id": prompt_id,
            "response": "",
            "success": False,
            "error": f"Timeout after {timeout}s"
        }
    except Exception as e:
        return {
            "prompt_id": prompt_id,
            "response": "",
            "success": False,
            "error": str(e)
        }

async def run_all_prompts_parallel(model_name: str,
                                   prompts: List[Dict]) -> List[Dict]:
    """
    TEACHING: Run all prompts in parallel

    Sequential would be:
      for prompt in prompts:
          result = query(prompt)  # Wait for each
      Total: 10 × 2s = 20s

    Parallel is:
      tasks = [query(p) for p in prompts]  # Start all
      results = await all_tasks            # Wait for all
      Total: max(all queries) ≈ 3-5s

    The key: asyncio.gather(*tasks)
    - Runs all tasks concurrently
    - Waits for ALL to complete
    - Returns results in original order
    """
    teach.progress("Starte parallele Ausführung...")
    teach.explain("Alle 10 Prompts werden GLEICHZEITIG gesendet")
    teach.explain("GPU kann mehrere Prompts parallel verarbeiten")

    start_time = time.time()

    # Create session
    async with aiohttp.ClientSession() as session:
        # Create all tasks
        tasks = [
            query_ollama_async(
                session,
                model_name,
                prompt_data["prompt"],
                prompt_data["id"]
            )
            for prompt_data in prompts
        ]

        teach.fact("Tasks erstellt", len(tasks))
        teach.progress("Warte auf Responses...")

        # Execute all in parallel
        results = await asyncio.gather(*tasks)

    elapsed = time.time() - start_time

    teach.success(f"Alle Prompts fertig in {elapsed:.1f} Sekunden")
    teach.explain(f"→ Sequentiell wären das ~{len(prompts) * 2} Sekunden gewesen")
    teach.explain(f"→ Speedup: {(len(prompts) * 2) / elapsed:.1f}x schneller!")

    return results

# ============================================================
# FILE OUTPUT MANAGER
# ============================================================

def save_responses_to_files(results: List[Dict],
                            model_type: str,
                            epoch: int,
                            prompts_metadata: List[Dict]):
    """
    TEACHING: Save each response as individual .txt file

    Why individual files?
    - Easy to diff between epochs (diff tool)
    - Easy to inspect manually
    - One file per test = clear organization
    - Agent 3 can process them individually

    File structure:
    results/
    ├── epoch_0_baseline/
    │   ├── base_01_fizzbuzz.txt
    │   ├── base_02_palindrome.txt
    │   └── ... (10 files)
    ├── epoch_1/
    │   ├── base_01_fizzbuzz.txt
    │   ├── finetuned_01_fizzbuzz.txt
    │   └── ... (20 files total)
    """
    teach.progress("Speichere Responses als .txt Dateien...")

    # Create output directory
    if epoch == 0:
        output_dir = Path(f"results/epoch_0_baseline")
    else:
        output_dir = Path(f"results/epoch_{epoch}")

    output_dir.mkdir(parents=True, exist_ok=True)

    teach.fact("Output Verzeichnis", str(output_dir))

    # Save each response
    saved_count = 0
    for i, (result, prompt_meta) in enumerate(zip(results, prompts_metadata), 1):
        # Filename format: {model_type}_{number}_{id}.txt
        filename = f"{model_type}_{i:02d}_{result['prompt_id']}.txt"
        filepath = output_dir / filename

        # Write file with metadata header
        with open(filepath, "w", encoding="utf-8") as f:
            # Header
            f.write("="*70 + "\n")
            f.write(f"CODING TEST RESPONSE\n")
            f.write("="*70 + "\n\n")

            # Metadata
            f.write(f"Prompt ID:   {result['prompt_id']}\n")
            f.write(f"Model:       {model_type}\n")
            f.write(f"Epoch:       {epoch}\n")
            f.write(f"Category:    {prompt_meta['category']}\n")
            f.write(f"Difficulty:  {prompt_meta['difficulty']}\n")
            f.write(f"Timestamp:   {datetime.now().isoformat()}\n")
            f.write(f"Success:     {result['success']}\n")
            if result['error']:
                f.write(f"Error:       {result['error']}\n")

            f.write("\n" + "-"*70 + "\n")
            f.write("PROMPT:\n")
            f.write("-"*70 + "\n")
            f.write(prompt_meta['prompt'])
            f.write("\n\n" + "-"*70 + "\n")
            f.write("RESPONSE:\n")
            f.write("-"*70 + "\n")
            f.write(result['response'] if result['response'] else "(Empty response)")
            f.write("\n")

        if result['success']:
            saved_count += 1
        else:
            teach.explain(f"⚠️  Prompt {i} ({result['prompt_id']}) failed: {result['error']}")

    teach.success(f"Gespeichert: {saved_count}/{len(results)} Dateien")
    teach.fact("Location", str(output_dir))

    return output_dir

# ============================================================
# MAIN TEST RUNNER
# ============================================================

class CodingTestRunner:
    """
    Main class that orchestrates testing

    This is what Agent 1 will call after each epoch.
    """

    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        self.prompts = CODING_TEST_PROMPTS

    def run_test_suite(self, model_name: str, epoch: int, model_type: str = "base"):
        """
        Run complete test suite on one model

        Args:
            model_name: Ollama model name (e.g., "qwen2.5:0.5b")
            epoch: Which epoch we're testing (0 = baseline)
            model_type: "base" or "finetuned"

        Returns:
            Path to output directory
        """
        teach.section(f"🧪 CODING TEST SUITE - {model_type.upper()}")

        if epoch == 0:
            teach.explain("Dies ist der BASELINE Test (vor Training)")
        else:
            teach.explain(f"Dies ist der Test nach Epoch {epoch}")

        teach.fact("Model", model_name)
        teach.fact("Anzahl Tests", len(self.prompts))
        teach.fact("Modus", "PARALLEL (alle gleichzeitig)")

        # Run parallel
        results = asyncio.run(
            run_all_prompts_parallel(model_name, self.prompts)
        )

        # Analyze
        self._show_quick_analysis(results)

        # Save to files
        output_dir = save_responses_to_files(
            results,
            model_type,
            epoch,
            self.prompts
        )

        return output_dir

    def _show_quick_analysis(self, results: List[Dict]):
        """
        Quick analysis of responses

        TEACHING: This gives immediate feedback
        - Which tests succeeded?
        - Which responses contain expected keywords?
        """
        teach.progress("Erste Analyse...")

        success_count = sum(1 for r in results if r['success'])
        total = len(results)

        teach.fact("Erfolgreiche Queries", f"{success_count}/{total}")

        # Check for keywords in responses
        print()
        for result, prompt_meta in zip(results, self.prompts):
            if not result['success']:
                print(f"    ❌ {result['prompt_id']}: FAILED ({result['error']})")
                continue

            response = result['response'].lower()
            keywords = prompt_meta.get('expected_keywords', [])

            found_keywords = [kw for kw in keywords if kw.lower() in response]

            # Status: ✅ if >= 50% keywords found, ⚠️ otherwise
            if len(found_keywords) >= len(keywords) * 0.5:
                status = "✅"
            else:
                status = "⚠️"

            print(f"    {status} {result['prompt_id']}: {len(found_keywords)}/{len(keywords)} keywords found")

# ============================================================
# CLI INTERFACE
# ============================================================

def main():
    """
    Command-line interface

    Usage:
        python parallel_runner.py --model qwen2.5:0.5b --epoch 0 --type base
    """
    import argparse

    parser = argparse.ArgumentParser(description="Parallel Coding Test Runner")
    parser.add_argument("--model", required=True, help="Ollama model name")
    parser.add_argument("--epoch", type=int, required=True, help="Epoch number (0=baseline)")
    parser.add_argument("--type", choices=["base", "finetuned"], default="base",
                       help="Model type")

    args = parser.parse_args()

    runner = CodingTestRunner()
    output_dir = runner.run_test_suite(
        model_name=args.model,
        epoch=args.epoch,
        model_type=args.type
    )

    print(f"\n{'='*70}")
    print(f"  ✅ COMPLETE")
    print(f"{'='*70}")
    print(f"Results: {output_dir}")

if __name__ == "__main__":
    main()
