#!/usr/bin/env python3
"""
Helper to test BOTH base and fine-tuned models

This is what Agent 1 will call after each epoch.

USAGE (from Agent 1 training script):
    from benchmark.test_both_models import run_tests_for_epoch

    run_tests_for_epoch(
        base_model="qwen2.5:0.5b",
        finetuned_model="exp-001-epoch-1",
        epoch=1
    )

WHAT IT DOES:
1. Tests base model (unchanged)
2. Tests fine-tuned model (after epoch N)
3. Saves results to results/epoch_N/
4. Provides summary

OUTPUT:
results/epoch_1/
├── base_01_fizzbuzz.txt
├── base_02_palindrome.txt
├── ...
├── finetuned_01_fizzbuzz.txt
├── finetuned_02_palindrome.txt
└── ...

Next step: Agent 3 compares base vs finetuned
"""

from parallel_runner import CodingTestRunner

def test_baseline(base_model="qwen2.5:0.5b"):
    """
    Test baseline (epoch 0) before any training

    Run this ONCE before starting training

    Args:
        base_model: Base model name in Ollama
    """
    print("\n" + "="*70)
    print("  🧪 BASELINE TEST (Epoch 0)")
    print("="*70)
    print("  This establishes the starting point before training.")
    print("  We'll compare all future epochs against this baseline.")
    print("="*70)

    runner = CodingTestRunner()
    output_dir = runner.run_test_suite(
        model_name=base_model,
        epoch=0,
        model_type="base"
    )

    print("\n" + "="*70)
    print("  ✅ BASELINE COMPLETE")
    print("="*70)
    print(f"Results: {output_dir}")
    print("Next: Start training with Agent 1")
    print("="*70)

    return output_dir

def test_after_epoch(finetuned_model: str, epoch: int):
    """
    Test fine-tuned model after training epoch N

    Called by Agent 1 after each epoch completes

    Args:
        finetuned_model: Name of fine-tuned model in Ollama
        epoch: Which epoch just finished (1, 2, 3, ...)
    """
    print("\n" + "="*70)
    print(f"  🧪 TESTING AFTER EPOCH {epoch}")
    print("="*70)

    runner = CodingTestRunner()
    output_dir = runner.run_test_suite(
        model_name=finetuned_model,
        epoch=epoch,
        model_type="finetuned"
    )

    print("\n" + "="*70)
    print(f"  ✅ EPOCH {epoch} TEST COMPLETE")
    print("="*70)
    print(f"Results: {output_dir}")
    print("="*70)

    return output_dir

# ============================================================
# MAIN INTEGRATION FUNCTION (for Agent 1)
# ============================================================

def run_tests_for_epoch(base_model: str, finetuned_model: str, epoch: int):
    """
    Called by Agent 1 after each training epoch

    Tests BOTH models for comparison:
    - Base model (unchanged, for reference)
    - Fine-tuned model (after epoch N)

    Args:
        base_model: Base model name (e.g., "qwen2.5:0.5b")
        finetuned_model: Fine-tuned model name (e.g., "exp-001-epoch-1")
        epoch: Which epoch just finished

    Returns:
        Tuple of (base_dir, finetuned_dir)
    """
    print("\n" + "="*70)
    print(f"  🧪 TESTING SUITE - EPOCH {epoch}")
    print("="*70)
    print("  Testing both models to measure improvement...")
    print("="*70)

    runner = CodingTestRunner()

    # Test base model (reference)
    print("\n[1/2] Testing BASE model...")
    base_dir = runner.run_test_suite(base_model, epoch, "base")

    # Test fine-tuned model (this epoch)
    print("\n[2/2] Testing FINE-TUNED model...")
    ft_dir = runner.run_test_suite(finetuned_model, epoch, "finetuned")

    # Summary
    print("\n" + "="*70)
    print("  ✅ TESTING COMPLETE")
    print("="*70)
    print(f"\nResults saved:")
    print(f"  Base:       {base_dir}")
    print(f"  Fine-tuned: {ft_dir}")
    print(f"\nNext: Agent 3 will compare these results")
    print(f"      to show which prompts improved/regressed")
    print("="*70)

    return base_dir, ft_dir

# ============================================================
# STANDALONE CLI
# ============================================================

def main():
    """
    Command-line interface for manual testing

    Usage:
        # Test baseline
        python test_both_models.py baseline

        # Test after epoch
        python test_both_models.py epoch --finetuned exp-001-epoch-1 --epoch 1

        # Test both
        python test_both_models.py both --base qwen2.5:0.5b --finetuned exp-001 --epoch 1
    """
    import argparse

    parser = argparse.ArgumentParser(description="Test base and fine-tuned models")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Baseline command
    baseline_parser = subparsers.add_parser("baseline", help="Test baseline (epoch 0)")
    baseline_parser.add_argument("--base", default="qwen2.5:0.5b", help="Base model name")

    # Epoch command
    epoch_parser = subparsers.add_parser("epoch", help="Test after epoch")
    epoch_parser.add_argument("--finetuned", required=True, help="Fine-tuned model name")
    epoch_parser.add_argument("--epoch", type=int, required=True, help="Epoch number")

    # Both command
    both_parser = subparsers.add_parser("both", help="Test both models")
    both_parser.add_argument("--base", default="qwen2.5:0.5b", help="Base model name")
    both_parser.add_argument("--finetuned", required=True, help="Fine-tuned model name")
    both_parser.add_argument("--epoch", type=int, required=True, help="Epoch number")

    args = parser.parse_args()

    if args.command == "baseline":
        test_baseline(args.base)
    elif args.command == "epoch":
        test_after_epoch(args.finetuned, args.epoch)
    elif args.command == "both":
        run_tests_for_epoch(args.base, args.finetuned, args.epoch)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
