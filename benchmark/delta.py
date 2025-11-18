#!/usr/bin/env python3
"""
Agent 3: Delta Calculator - Teaching Edition

WHAT THIS DOES:
Compares Base Model vs. Fine-tuned Model responses using structured metrics.

METRICS CALCULATED:
1. Length Delta: Did the model become more verbose or concise?
2. Similarity Score: How much did the text change? (0.0 = completely new, 1.0 = identical)
3. Ground Truth: Did it fix a wrong answer? Did it break a correct one?
4. Keywords: Does it mention expected terms?
5. Custom Checks: Special validation (e.g., "has 3 items", "under 50 words")

WHY IS THIS NECESSARY?
Fine-tuning is subtle. Sometimes the text changes completely but the meaning is the same.
Sometimes one word changes ("not") and the meaning flips.
We need metrics to detect these shifts systematically.

TEACHING NOTE:
This script implements HEURISTIC ASSESSMENT - fast, deterministic rules
that approximate "better" vs "worse". It's not perfect AI evaluation,
but it's instant and effective for rapid iteration.

LEARNING OBJECTIVE:
Understand how to measure text differences beyond simple string comparison.
Learn to build rule-based assessment systems that guide iteration decisions.
"""

import json
import sys
from pathlib import Path
from difflib import SequenceMatcher

# Input/Output Paths
RESULTS_DIR = Path("benchmark/results")
BASE_PATH = RESULTS_DIR / "base.json"
FT_PATH = RESULTS_DIR / "finetuned.json"
OUTPUT_PATH = RESULTS_DIR / "deltas.json"


def calculate_similarity(text_a: str, text_b: str) -> float:
    """
    TEACHING: SequenceMatcher

    Calculates a similarity ratio between 0.0 and 1.0.
    - 1.0: Strings are identical
    - 0.0: Strings have nothing in common

    Uses the Ratcliff/Obershelp algorithm (pattern matching).
    This is character-level comparison - even punctuation matters.

    Example:
        "The cat sat" vs "The cat stood"
        → ratio ≈ 0.85 (high similarity, only one word different)

        "Hello" vs "Goodbye"
        → ratio ≈ 0.0 (no common patterns)
    """
    return SequenceMatcher(None, text_a, text_b).ratio()


def check_keywords(text: str, keywords: list) -> int:
    """
    Count how many keywords appear in the text.
    Case-insensitive matching.

    TEACHING NOTE:
    This is a simple "bag of words" approach. More sophisticated methods
    could use:
    - Stemming/lemmatization ("running" matches "run")
    - Semantic embeddings (word2vec, BERT)
    - Phrase matching ("quantum computer" as a unit)

    But for rapid iteration, simple keyword matching works well.
    """
    if not keywords:
        return 0
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw.lower() in text_lower)


def perform_custom_check(text: str, check_type: str) -> bool:
    """
    Perform custom validation logic based on check type.

    TEACHING NOTE:
    These are domain-specific checks. Add your own as needed!
    Examples:
    - Code generation: "has_code_block", "syntax_valid"
    - Customer support: "mentions_ticket", "provides_steps"
    - Content: "word_count_range", "has_citations"
    """
    if not check_type:
        return None

    if check_type == "has_3_items":
        # Simple heuristic: count bullet points, commas, or numbered items
        # TEACHING: In production, use regex. Here we keep it simple.
        bullet_count = text.count("•") + text.count("-") + text.count("*")
        comma_count = text.count(",")
        numbered = sum(1 for line in text.split("\n") if line.strip() and line.strip()[0].isdigit())

        # Any of these indicators suggest a list format
        return (bullet_count >= 2 or comma_count >= 2 or numbered >= 3)

    elif check_type == "is_single_sentence":
        # Count periods (rough heuristic)
        # TEACHING: More robust: use NLP sentence tokenizer
        period_count = text.count(".") + text.count("!") + text.count("?")
        return period_count <= 1

    elif check_type == "under_50_words":
        word_count = len(text.split())
        return word_count <= 55  # Allow 10% buffer

    else:
        # Unknown check type
        return None


def assess_improvement(delta: dict) -> str:
    """
    TEACHING: Heuristic Assessment with Priority Cascade

    We use a set of rules (heuristics) to decide if a change is "Good" or "Bad".
    Rules are applied in PRIORITY ORDER:

    1. GROUND TRUTH (Highest Priority)
       - If there's a definitive correct answer
       - Example: "Capital of France?" must contain "Paris"

    2. KEYWORDS (Medium Priority)
       - For multi-aspect responses
       - Example: "List symptoms" should mention multiple symptoms

    3. CUSTOM CHECKS (Medium Priority)
       - Domain-specific validation
       - Example: "List 3 items" must have 3 items

    4. SIMILARITY (Fallback)
       - If no structured criteria, measure text change
       - Example: Did it change significantly?

    This isn't perfect AI evaluation, but it's:
    - Fast (instant)
    - Deterministic (same input = same output)
    - Interpretable (you can debug the rules)
    - Good enough for rapid iteration
    """
    metrics = delta["metrics"]
    meta = delta["metadata"]

    base_text = delta["base_response"]
    ft_text = delta["finetuned_response"]

    # =========================================================================
    # RULE 1: Ground Truth (HIGHEST PRIORITY)
    # =========================================================================
    # If there is a rigid correct answer (e.g., "Berlin", "42", "Python")
    if meta.get("ground_truth"):
        gt = meta["ground_truth"].lower()
        base_has_gt = gt in base_text.lower()
        ft_has_gt = gt in ft_text.lower()

        if not base_has_gt and ft_has_gt:
            return "✅ IMPROVED (Fixed Answer)"

        if base_has_gt and not ft_has_gt:
            return "❌ REGRESSED (Broke Answer)"

        if not base_has_gt and not ft_has_gt:
            return "⚠️ FAILED (Both Wrong)"

        if base_has_gt and ft_has_gt:
            # Both correct - check if fine-tuned improved explanation
            if metrics["similarity"] < 0.8:
                return "✅ PASS (Improved Explanation)"
            return "✅ PASS (Both Correct)"

    # =========================================================================
    # RULE 2: Keywords (For lists, explanations, domain knowledge)
    # =========================================================================
    if meta.get("keywords"):
        base_count = metrics["keywords_base"]
        ft_count = metrics["keywords_ft"]

        if ft_count > base_count:
            delta_kw = ft_count - base_count
            return f"✅ IMPROVED (+{delta_kw} keywords)"

        if ft_count < base_count:
            delta_kw = base_count - ft_count
            return f"❌ REGRESSED (-{delta_kw} keywords)"

        # Same keyword count - check if both have good coverage
        if base_count >= len(meta["keywords"]) * 0.5:
            return "⚪ NEUTRAL (Same Coverage)"

    # =========================================================================
    # RULE 3: Custom Logic Checks
    # =========================================================================
    if meta.get("check"):
        base_passes = perform_custom_check(base_text, meta["check"])
        ft_passes = perform_custom_check(ft_text, meta["check"])

        if base_passes is not None and ft_passes is not None:
            if not base_passes and ft_passes:
                return f"✅ IMPROVED (Now passes: {meta['check']})"

            if base_passes and not ft_passes:
                return f"❌ REGRESSED (Now fails: {meta['check']})"

            if not base_passes and not ft_passes:
                return f"⚠️ FAILED (Both fail: {meta['check']})"

            if base_passes and ft_passes:
                return f"✅ PASS (Meets: {meta['check']})"

    # =========================================================================
    # RULE 4: Pure Text Change (Fallback)
    # =========================================================================
    # If no structured rules apply, we look at similarity
    sim = metrics["similarity"]

    if sim > 0.95:
        return "⚪ NEUTRAL (No Change)"

    if sim < 0.4:
        return "🔄 CHANGED (Major Rewrite)"

    # Moderate change - analyze length to infer direction
    len_change_pct = metrics["length_delta_pct"]

    if abs(len_change_pct) < 10:
        return "📝 TWEAKED (Minor Edits)"

    if len_change_pct > 50:
        return "🔄 CHANGED (More Verbose)"

    if len_change_pct < -50:
        return "🔄 CHANGED (More Concise)"

    return "🔄 CHANGED (Moderate Edit)"


def analyze_pair(base_entry, ft_entry):
    """
    Compare a single pair of prompts.

    TEACHING NOTE:
    This is the core of delta analysis. We:
    1. Validate inputs (IDs must match)
    2. Calculate objective metrics (length, similarity, keywords)
    3. Apply heuristic assessment rules
    4. Return structured delta object
    """
    # Sanity check: IDs must match
    if base_entry["prompt_id"] != ft_entry["prompt_id"]:
        raise ValueError(
            f"Mismatch IDs: {base_entry['prompt_id']} vs {ft_entry['prompt_id']}\n"
            f"This usually means benchmark ran with different prompts or crashed midway."
        )

    base_text = base_entry["response"]
    ft_text = ft_entry["response"]

    # 1. Calculate Similarity
    similarity = calculate_similarity(base_text, ft_text)

    # 2. Length Analysis
    len_base = len(base_text)
    len_ft = len(ft_text)
    len_delta = len_ft - len_base
    len_delta_pct = (len_delta / len_base * 100) if len_base > 0 else 0

    # 3. Keyword Analysis
    keywords = base_entry.get("metadata", {}).get("keywords", [])
    kw_base = check_keywords(base_text, keywords)
    kw_ft = check_keywords(ft_text, keywords)

    # 4. Construct Delta Object
    delta = {
        "prompt_id": base_entry["prompt_id"],
        "prompt": base_entry["prompt"],
        "category": base_entry.get("category", "unknown"),
        "base_response": base_text,
        "finetuned_response": ft_text,
        "metadata": base_entry.get("metadata", {}),
        "metrics": {
            "similarity": round(similarity, 2),
            "length_base": len_base,
            "length_ft": len_ft,
            "length_delta": len_delta,
            "length_delta_pct": round(len_delta_pct, 1),
            "keywords_base": kw_base,
            "keywords_ft": kw_ft
        }
    }

    # 5. Assess Improvement
    delta["assessment"] = assess_improvement(delta)

    return delta


def main():
    """
    Main delta calculation pipeline.

    WORKFLOW:
    1. Load benchmark results (base + fine-tuned)
    2. Match prompts by ID
    3. Calculate metrics for each pair
    4. Apply assessment heuristics
    5. Save structured deltas
    6. Print summary statistics
    """
    print("="*60)
    print("AGENT 3: DELTA CALCULATOR - Teaching Edition")
    print("="*60)

    # =========================================================================
    # Step 1: Check inputs exist
    # =========================================================================
    if not BASE_PATH.exists() or not FT_PATH.exists():
        print("\n❌ Missing input files!")
        print(f"   Expected: {BASE_PATH}")
        print(f"   Expected: {FT_PATH}")
        print("\n   Run Agent 2 (benchmark) first:")
        print("   python benchmark/run.py <experiment-name>")
        sys.exit(1)

    # =========================================================================
    # Step 2: Load JSON
    # =========================================================================
    print("\n📂 Loading benchmark results...")

    with open(BASE_PATH, "r", encoding="utf-8") as f:
        base_data = json.load(f)

    with open(FT_PATH, "r", encoding="utf-8") as f:
        ft_data = json.load(f)

    print(f"✓ Loaded {len(base_data)} base results")
    print(f"✓ Loaded {len(ft_data)} fine-tuned results")

    if len(base_data) != len(ft_data):
        print(f"\n⚠️  Warning: Result counts don't match!")
        print("   This might indicate partial benchmark run.")

    # =========================================================================
    # Step 3: Analyze Each Pair
    # =========================================================================
    print("\n🔍 Calculating deltas...")
    print("-" * 60)

    deltas = []
    stats = {"improved": 0, "regressed": 0, "passed": 0, "failed": 0, "neutral": 0}

    # Sort both by ID to ensure alignment
    base_data.sort(key=lambda x: x["prompt_id"])
    ft_data.sort(key=lambda x: x["prompt_id"])

    for b, f in zip(base_data, ft_data):
        try:
            delta = analyze_pair(b, f)
            deltas.append(delta)

            # Track statistics
            assessment = delta["assessment"]
            if "✅" in assessment:
                if "IMPROVED" in assessment or "Fixed" in assessment:
                    stats["improved"] += 1
                else:
                    stats["passed"] += 1
            elif "❌" in assessment:
                stats["regressed"] += 1
            elif "⚠️" in assessment:
                stats["failed"] += 1
            else:
                stats["neutral"] += 1

            # Print per-prompt summary
            similarity_pct = int(delta["metrics"]["similarity"] * 100)
            print(f"[{delta['prompt_id']:15s}] Sim: {similarity_pct:3d}% → {assessment}")

        except Exception as e:
            print(f"\n❌ Error analyzing {b.get('prompt_id', 'unknown')}: {e}")
            continue

    # =========================================================================
    # Step 4: Save Output
    # =========================================================================
    print("-" * 60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(deltas, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Analysis complete. Saved to {OUTPUT_PATH}")

    # =========================================================================
    # Step 5: Print Summary Statistics
    # =========================================================================
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)

    total = len(deltas)

    print(f"\n✅ Improved:   {stats['improved']:2d} / {total} ({stats['improved']/total*100:.0f}%)")
    print(f"✅ Passed:     {stats['passed']:2d} / {total} ({stats['passed']/total*100:.0f}%)")
    print(f"❌ Regressed:  {stats['regressed']:2d} / {total} ({stats['regressed']/total*100:.0f}%)")
    print(f"⚠️  Failed:     {stats['failed']:2d} / {total} ({stats['failed']/total*100:.0f}%)")
    print(f"⚪ Neutral:    {stats['neutral']:2d} / {total} ({stats['neutral']/total*100:.0f}%)")

    # Calculate aggregate metrics
    avg_similarity = sum(d["metrics"]["similarity"] for d in deltas) / total
    avg_len_delta = sum(d["metrics"]["length_delta"] for d in deltas) / total

    print(f"\n📊 Average Similarity: {avg_similarity:.2f} (1.0 = identical)")
    print(f"📏 Average Length Change: {avg_len_delta:+.0f} characters")

    # Success rate
    success_rate = (stats['improved'] + stats['passed']) / total * 100
    print(f"\n🎯 Overall Success Rate: {success_rate:.0f}%")

    if success_rate >= 70:
        print("   → Excellent! Fine-tuning is working well.")
    elif success_rate >= 50:
        print("   → Good progress. Consider more training data.")
    elif success_rate >= 30:
        print("   → Mixed results. Review training data quality.")
    else:
        print("   → Poor results. Check dataset alignment with prompts.")

    print("\n" + "="*60)
    print("Next step: Generate HTML report")
    print("  python benchmark/visualize.py")
    print("="*60)
    print()


if __name__ == "__main__":
    main()
