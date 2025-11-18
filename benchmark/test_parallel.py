#!/usr/bin/env python3
"""
Test script to verify parallel execution works

Run this BEFORE using with real training to ensure setup is correct

WHAT THIS DOES:
1. Runs all 10 coding prompts in parallel
2. Measures total execution time
3. Calculates speedup vs sequential
4. Verifies results are saved correctly

SUCCESS CRITERIA:
✅ Completes in < 10 seconds
✅ All 10 responses are non-empty
✅ Files are saved to results/epoch_0_baseline/
✅ Speedup is > 2x

USAGE:
    python benchmark/test_parallel.py
"""

import time
from pathlib import Path
from parallel_runner import CodingTestRunner

def test_parallel_speedup():
    """
    Verify that parallel execution is actually faster

    Expected:
    - Sequential: ~20 seconds (10 prompts × 2s)
    - Parallel: ~3-5 seconds
    - Speedup: 4-6x
    """
    print("="*70)
    print("  TESTING PARALLEL EXECUTION")
    print("="*70)

    runner = CodingTestRunner()

    # Test with base model
    model = "qwen2.5:0.5b"

    print(f"\nTesting with model: {model}")
    print("Running 10 coding prompts in parallel...")
    print("="*70)

    start = time.time()
    output_dir = runner.run_test_suite(model, epoch=0, model_type="test")
    elapsed = time.time() - start

    # Analysis
    print(f"\n{'='*70}")
    print(f"  RESULTS")
    print(f"{'='*70}")
    print(f"Total time:          {elapsed:.1f} seconds")
    print(f"Sequential estimate: ~20 seconds")
    print(f"Speedup:             {20/elapsed:.1f}x faster")

    # Check files
    test_files = list(output_dir.glob("test_*.txt"))
    print(f"\nFiles created:       {len(test_files)}/10")

    # Check file contents
    non_empty = 0
    for f in test_files:
        content = f.read_text()
        if "RESPONSE:" in content and len(content) > 500:  # Has response section + content
            non_empty += 1

    print(f"Non-empty responses: {non_empty}/10")

    # Verdict
    print(f"\n{'='*70}")
    print(f"  VERDICT")
    print(f"{'='*70}")

    passed = []
    failed = []

    # Test 1: Time
    if elapsed < 10:
        passed.append("✅ Parallel execution working (< 10 seconds)")
    else:
        failed.append(f"❌ Too slow ({elapsed:.1f}s). Check Ollama performance.")

    # Test 2: Files
    if len(test_files) == 10:
        passed.append("✅ All 10 files created")
    else:
        failed.append(f"❌ Only {len(test_files)}/10 files created")

    # Test 3: Non-empty responses
    if non_empty >= 8:  # At least 80% should have content
        passed.append(f"✅ {non_empty}/10 responses have content")
    else:
        failed.append(f"❌ Only {non_empty}/10 responses have content")

    # Test 4: Speedup
    speedup = 20 / elapsed
    if speedup >= 2:
        passed.append(f"✅ Good speedup ({speedup:.1f}x)")
    else:
        failed.append(f"❌ Low speedup ({speedup:.1f}x). Expected > 2x")

    # Print results
    for p in passed:
        print(p)
    for f in failed:
        print(f)

    # Overall
    print(f"\n{'='*70}")
    if len(failed) == 0:
        print("  ✅ ALL TESTS PASSED - System ready for use!")
    else:
        print(f"  ⚠️  {len(failed)} TEST(S) FAILED - Check above for details")
    print(f"{'='*70}")

    # Next steps
    print("\nNext steps:")
    print("1. Inspect output files:")
    print(f"   ls -lh {output_dir}")
    print(f"   cat {output_dir}/test_01_fizzbuzz.txt")
    print("\n2. If tests passed, you're ready to:")
    print("   - Use with Agent 1 training")
    print("   - Test after each epoch")
    print("   - Compare results with Agent 3")

    return len(failed) == 0

def cleanup_test_files():
    """
    Optional: Clean up test files

    Run after testing to remove test_*.txt files
    """
    test_dir = Path("results/epoch_0_baseline")
    if test_dir.exists():
        test_files = list(test_dir.glob("test_*.txt"))
        if test_files:
            print(f"\nCleaning up {len(test_files)} test files...")
            for f in test_files:
                f.unlink()
            print("✅ Cleanup complete")

if __name__ == "__main__":
    success = test_parallel_speedup()

    # Ask if user wants to clean up
    print("\n" + "="*70)
    response = input("Clean up test files? (y/N): ").strip().lower()
    if response == 'y':
        cleanup_test_files()

    # Exit code
    exit(0 if success else 1)
