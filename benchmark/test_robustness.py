#!/usr/bin/env python3
"""
Robustness Test Suite for Agent 3 & Agent 4

Tests edge cases:
- Empty data
- Mismatched prompts
- Division by zero
- XSS attacks
- Malformed JSON
- Missing fields
"""

import json
import os
import shutil
from pathlib import Path

RESULTS_DIR = Path("benchmark/results")
TEST_BACKUP_DIR = Path("benchmark/results_backup")

def backup_results():
    """Backup existing results before testing."""
    if RESULTS_DIR.exists():
        if TEST_BACKUP_DIR.exists():
            shutil.rmtree(TEST_BACKUP_DIR)
        shutil.copytree(RESULTS_DIR, TEST_BACKUP_DIR)
        print("✅ Backed up existing results")

def restore_results():
    """Restore backed up results after testing."""
    if TEST_BACKUP_DIR.exists():
        if RESULTS_DIR.exists():
            shutil.rmtree(RESULTS_DIR)
        shutil.copytree(TEST_BACKUP_DIR, RESULTS_DIR)
        shutil.rmtree(TEST_BACKUP_DIR)
        print("✅ Restored original results")

def cleanup_test_files():
    """Clean up test files."""
    if RESULTS_DIR.exists():
        for file in ['base.json', 'finetuned.json', 'deltas.json', 'report.html']:
            path = RESULTS_DIR / file
            if path.exists():
                path.unlink()

def run_test(test_name, base_data, finetuned_data):
    """Run a single test case."""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")

    # Create test data
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(RESULTS_DIR / "base.json", "w") as f:
        if isinstance(base_data, str):
            f.write(base_data)  # Raw string (for malformed JSON tests)
        else:
            json.dump(base_data, f, indent=2)

    with open(RESULTS_DIR / "finetuned.json", "w") as f:
        if isinstance(finetuned_data, str):
            f.write(finetuned_data)  # Raw string (for malformed JSON tests)
        else:
            json.dump(finetuned_data, f, indent=2)

    # Run Agent 3
    print("\n--- Running Agent 3 (Delta Calculator) ---")
    exit_code_3 = os.system("python3 benchmark/delta.py")

    # Run Agent 4
    print("\n--- Running Agent 4 (Visualizer) ---")
    exit_code_4 = os.system("python3 benchmark/visualize.py")

    # Check results
    report_exists = (RESULTS_DIR / "report.html").exists()
    deltas_exists = (RESULTS_DIR / "deltas.json").exists()

    print(f"\n--- Test Results ---")
    print(f"Agent 3 exit code: {exit_code_3}")
    print(f"Agent 4 exit code: {exit_code_4}")
    print(f"deltas.json created: {'✅' if deltas_exists else '❌'}")
    print(f"report.html created: {'✅' if report_exists else '❌'}")

    if report_exists:
        size = (RESULTS_DIR / "report.html").stat().st_size
        print(f"report.html size: {size} bytes")

    return report_exists

print("="*60)
print("ROBUSTNESS TEST SUITE")
print("="*60)

# Backup existing results
backup_results()

try:
    all_passed = True

    # TEST 1: Empty arrays
    cleanup_test_files()
    passed = run_test(
        "Empty Arrays",
        [],
        []
    )
    all_passed &= passed

    # TEST 2: Mismatched lengths (base has 3, finetuned has 1)
    cleanup_test_files()
    passed = run_test(
        "Mismatched Lengths",
        [
            {"prompt_id": "p1", "prompt": "Test 1", "response": "Base 1"},
            {"prompt_id": "p2", "prompt": "Test 2", "response": "Base 2"},
            {"prompt_id": "p3", "prompt": "Test 3", "response": "Base 3"},
        ],
        [
            {"prompt_id": "p1", "prompt": "Test 1", "response": "Finetuned 1"},
        ]
    )
    all_passed &= passed

    # TEST 3: Completely different prompt IDs (no matches)
    cleanup_test_files()
    passed = run_test(
        "No Matching IDs",
        [
            {"prompt_id": "p1", "prompt": "Test 1", "response": "Base 1"},
        ],
        [
            {"prompt_id": "p99", "prompt": "Test 99", "response": "Finetuned 99"},
        ]
    )
    all_passed &= passed

    # TEST 4: Division by zero scenarios
    cleanup_test_files()
    passed = run_test(
        "Division by Zero (Empty Responses)",
        [
            {"prompt_id": "p1", "prompt": "Test", "response": ""},
        ],
        [
            {"prompt_id": "p1", "prompt": "Test", "response": "Now has content"},
        ]
    )
    all_passed &= passed

    # TEST 5: XSS attack in prompt
    cleanup_test_files()
    passed = run_test(
        "XSS Attack in Prompt",
        [
            {
                "prompt_id": "p1",
                "prompt": "<script>alert('XSS')</script>",
                "response": "Safe response",
                "category": "security"
            },
        ],
        [
            {
                "prompt_id": "p1",
                "prompt": "<script>alert('XSS')</script>",
                "response": "<img src=x onerror='alert(1)'>",
                "category": "security"
            },
        ]
    )
    all_passed &= passed

    # Check that XSS is escaped in HTML
    if passed:
        with open(RESULTS_DIR / "report.html", "r") as f:
            html = f.read()
            if "<script>" in html.lower() and "&lt;script&gt;" not in html.lower():
                print("⚠️  WARNING: XSS attack NOT properly escaped!")
                all_passed = False
            else:
                print("✅ XSS properly escaped in HTML")

    # TEST 6: Missing fields
    cleanup_test_files()
    passed = run_test(
        "Missing Fields",
        [
            {"prompt_id": "p1"},  # No prompt or response
        ],
        [
            {"prompt_id": "p1", "response": "Something"},  # No prompt
        ]
    )
    all_passed &= passed

    # TEST 7: Malformed JSON (Agent 3)
    cleanup_test_files()
    passed = run_test(
        "Malformed JSON",
        "{this is not valid json}",
        "[]"
    )
    all_passed &= passed

    # TEST 8: Non-list JSON (Agent 3)
    cleanup_test_files()
    passed = run_test(
        "Non-List JSON",
        {"error": "This is a dict, not a list"},
        []
    )
    all_passed &= passed

    # TEST 9: Reordered prompts (different order in base vs finetuned)
    cleanup_test_files()
    passed = run_test(
        "Reordered Prompts",
        [
            {"prompt_id": "p1", "prompt": "First", "response": "Base 1"},
            {"prompt_id": "p2", "prompt": "Second", "response": "Base 2"},
            {"prompt_id": "p3", "prompt": "Third", "response": "Base 3"},
        ],
        [
            {"prompt_id": "p3", "prompt": "Third", "response": "FT 3"},
            {"prompt_id": "p1", "prompt": "First", "response": "FT 1"},
            {"prompt_id": "p2", "prompt": "Second", "response": "FT 2"},
        ]
    )
    all_passed &= passed

    # TEST 10: Unicode and emoji
    cleanup_test_files()
    passed = run_test(
        "Unicode and Emoji",
        [
            {"prompt_id": "p1", "prompt": "Test 🚀", "response": "Hello 世界"},
        ],
        [
            {"prompt_id": "p1", "prompt": "Test 🚀", "response": "Hello 世界 with more detail 🎉"},
        ]
    )
    all_passed &= passed

    # FINAL SUMMARY
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("   Agents 3 & 4 are ROBUST.")
    else:
        print("❌ SOME TESTS FAILED")
        print("   Check output above for details.")
    print("="*60)

finally:
    # Restore original results
    restore_results()
    print("\nTest complete. Original results restored.")
