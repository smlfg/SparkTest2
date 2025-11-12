#!/usr/bin/env python3
"""
================================================================================
DGX Spark Fast Fine-tuning System
Agent 3: Delta Calculator - Response Comparison
================================================================================

WHAT: Compare base vs fine-tuned model responses and calculate metrics
WHY:  Need quantitative measures to assess fine-tuning impact
HOW:  Calculate 4 types of metrics:
      1. Length delta (response verbosity)
      2. Keyword matching (expected terms present)
      3. Semantic similarity (meaning preserved)
      4. Overall assessment (improved/regressed/changed)

USAGE: python benchmark/delta.py

INPUT:  benchmark/results/base.json
        benchmark/results/finetuned.json

OUTPUT: benchmark/results/deltas.json

TIME: ~instant (no model inference)

================================================================================
LEARNING OBJECTIVES:
- How to measure model changes objectively
- Different metrics reveal different aspects
- Trade-offs: speed vs semantic understanding
- Why we need multiple metrics (no single "score")
================================================================================
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ===== CONFIGURATION =====
RESULTS_DIR = Path("benchmark/results")
BASE_FILE = RESULTS_DIR / "base.json"
FINETUNED_FILE = RESULTS_DIR / "finetuned.json"
OUTPUT_FILE = RESULTS_DIR / "deltas.json"


# ===== METRIC FUNCTIONS =====

def calculate_length_delta(base_response: str, finetuned_response: str) -> Dict:
    """
    Calculate length-based metrics.

    WHY LENGTH MATTERS:
    - Too verbose → might be rambling
    - Too short → might be incomplete
    - "Just right" depends on task
    """
    base_len = len(base_response)
    finetuned_len = len(finetuned_response)

    delta = finetuned_len - base_len
    ratio = finetuned_len / base_len if base_len > 0 else 0

    return {
        "base_length": base_len,
        "finetuned_length": finetuned_len,
        "delta": delta,
        "ratio": ratio,
        "assessment": (
            "shorter" if ratio < 0.8 else
            "longer" if ratio > 1.2 else
            "similar"
        )
    }


def calculate_keyword_match(response: str, expected_keywords: List[str]) -> Dict:
    """
    Check if expected keywords appear in response.

    WHY KEYWORD MATCHING:
    - Fast and interpretable
    - Checks if model addresses key concepts
    - Not semantic (misses synonyms), but good first pass
    """
    response_lower = response.lower()
    matches = [kw for kw in expected_keywords if kw.lower() in response_lower]

    return {
        "expected_keywords": expected_keywords,
        "matched_keywords": matches,
        "match_count": len(matches),
        "match_rate": len(matches) / len(expected_keywords) if expected_keywords else 0,
    }


def calculate_similarity(base_response: str, finetuned_response: str) -> Dict:
    """
    Calculate semantic similarity using TF-IDF + cosine similarity.

    WHY TF-IDF?
    - Fast (no model inference)
    - Captures word importance
    - Works well for comparing similar texts

    INTERPRETATION:
    - similarity=1.0: Identical responses
    - similarity=0.8-0.9: Very similar
    - similarity=0.5-0.7: Somewhat similar
    - similarity<0.5: Different responses
    """
    if not base_response or not finetuned_response:
        return {
            "similarity": 0.0,
            "assessment": "error"
        }

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([base_response, finetuned_response])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except:
        similarity = 0.0

    return {
        "similarity": float(similarity),
        "assessment": (
            "nearly_identical" if similarity > 0.9 else
            "very_similar" if similarity > 0.7 else
            "somewhat_similar" if similarity > 0.5 else
            "different"
        )
    }


def assess_overall_change(
    length_delta: Dict,
    keyword_match_base: Dict,
    keyword_match_finetuned: Dict,
    similarity: Dict
) -> str:
    """
    Holistic assessment: Did fine-tuning improve this response?

    LOGIC:
    - Improved: More keywords matched, length reasonable, not too similar (showing change)
    - Regressed: Fewer keywords matched, or too short, or error
    - Changed: Different but not clearly better/worse
    - Unchanged: Nearly identical responses

    NOTE: This is heuristic! Domain experts should review.
    """
    # Keyword improvement
    keyword_delta = keyword_match_finetuned["match_rate"] - keyword_match_base["match_rate"]

    # Length reasonableness
    length_reasonable = 0.5 < length_delta["ratio"] < 2.0

    # Similarity
    too_similar = similarity["similarity"] > 0.95
    very_different = similarity["similarity"] < 0.3

    # Decision tree
    if too_similar:
        return "unchanged"
    elif keyword_delta > 0.2 and length_reasonable:
        return "improved"
    elif keyword_delta < -0.2 or not length_reasonable:
        return "regressed"
    elif very_different:
        return "changed_significantly"
    else:
        return "changed_slightly"


# ===== MAIN COMPARISON FUNCTION =====

def compare_results() -> List[Dict]:
    """
    Main function: Load both result files, compare each prompt pair.

    Returns:
        List of delta dictionaries, one per prompt
    """
    # Load results
    if not BASE_FILE.exists():
        print(f"❌ Error: Base results not found: {BASE_FILE}")
        print("   Run: python benchmark/run.py <experiment_name>")
        sys.exit(1)

    if not FINETUNED_FILE.exists():
        print(f"❌ Error: Fine-tuned results not found: {FINETUNED_FILE}")
        print("   Run: python benchmark/run.py <experiment_name>")
        sys.exit(1)

    with open(BASE_FILE) as f:
        base_results = json.load(f)

    with open(FINETUNED_FILE) as f:
        finetuned_results = json.load(f)

    # Validate same prompts
    if len(base_results) != len(finetuned_results):
        print(f"⚠️  Warning: Different number of results!")
        print(f"   Base: {len(base_results)}, Fine-tuned: {len(finetuned_results)}")

    # Compare each prompt
    deltas = []

    print(f"\n🔍 Comparing {len(base_results)} prompts...")
    print("-" * 80)

    for base_result, finetuned_result in zip(base_results, finetuned_results):
        # Validate same prompt
        assert base_result["prompt_id"] == finetuned_result["prompt_id"], \
            f"Prompt mismatch: {base_result['prompt_id']} vs {finetuned_result['prompt_id']}"

        prompt_id = base_result["prompt_id"]
        base_response = base_result["response"]
        finetuned_response = finetuned_result["response"]
        expected_keywords = base_result["expected_keywords"]

        # Calculate metrics
        length_delta = calculate_length_delta(base_response, finetuned_response)
        keyword_match_base = calculate_keyword_match(base_response, expected_keywords)
        keyword_match_finetuned = calculate_keyword_match(finetuned_response, expected_keywords)
        similarity = calculate_similarity(base_response, finetuned_response)

        # Overall assessment
        overall = assess_overall_change(
            length_delta,
            keyword_match_base,
            keyword_match_finetuned,
            similarity
        )

        # Compile delta
        delta = {
            # Metadata
            "prompt_id": prompt_id,
            "category": base_result["category"],
            "prompt": base_result["prompt"],

            # Responses
            "base_response": base_response,
            "finetuned_response": finetuned_response,

            # Metrics
            "length": length_delta,
            "keywords": {
                "base": keyword_match_base,
                "finetuned": keyword_match_finetuned,
                "improvement": keyword_match_finetuned["match_rate"] - keyword_match_base["match_rate"]
            },
            "similarity": similarity,

            # Assessment
            "overall_assessment": overall,
        }

        deltas.append(delta)

        # Print quick summary
        print(f"[{prompt_id}] {overall.upper()}")
        print(f"  Keywords: {keyword_match_base['match_count']}/{len(expected_keywords)} → "
              f"{keyword_match_finetuned['match_count']}/{len(expected_keywords)}")
        print(f"  Length: {length_delta['base_length']} → {length_delta['finetuned_length']} "
              f"({length_delta['assessment']})")
        print(f"  Similarity: {similarity['similarity']:.2f} ({similarity['assessment']})")
        print()

    return deltas


def save_deltas(deltas: List[Dict]):
    """Save delta results to JSON."""
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(deltas, f, indent=2)

    print(f"💾 Saved deltas to: {OUTPUT_FILE}")


def print_summary(deltas: List[Dict]):
    """Print high-level summary statistics."""
    total = len(deltas)

    # Count assessments
    assessments = [d["overall_assessment"] for d in deltas]
    improved = assessments.count("improved")
    regressed = assessments.count("regressed")
    unchanged = assessments.count("unchanged")
    changed = sum(1 for a in assessments if "changed" in a)

    # Average keyword improvement
    avg_keyword_improvement = sum(d["keywords"]["improvement"] for d in deltas) / total

    # Average similarity
    avg_similarity = sum(d["similarity"]["similarity"] for d in deltas) / total

    print("=" * 80)
    print("📊 DELTA SUMMARY")
    print("=" * 80)
    print(f"\nTotal prompts analyzed: {total}")
    print(f"\nOverall assessments:")
    print(f"  ✅ Improved:         {improved:2d} ({improved/total*100:.0f}%)")
    print(f"  ❌ Regressed:        {regressed:2d} ({regressed/total*100:.0f}%)")
    print(f"  ➡️  Changed:          {changed:2d} ({changed/total*100:.0f}%)")
    print(f"  ⏸️  Unchanged:        {unchanged:2d} ({unchanged/total*100:.0f}%)")
    print(f"\nAverage metrics:")
    print(f"  Keyword improvement: {avg_keyword_improvement:+.2f}")
    print(f"  Similarity:          {avg_similarity:.2f}")
    print("\nInterpretation:")
    if improved > regressed:
        print("  ✅ Fine-tuning appears to have positive impact overall")
    elif regressed > improved:
        print("  ⚠️  Fine-tuning may have regressed model performance")
    else:
        print("  ℹ️  Mixed results - review individual prompts")
    print("=" * 80)


# ===== MAIN =====

def main():
    """Main entry point."""
    print("=" * 80)
    print("🚀 Delta Calculator")
    print("=" * 80)

    # Load and compare
    deltas = compare_results()

    # Save results
    save_deltas(deltas)

    # Print summary
    print()
    print_summary(deltas)

    # Next steps
    print(f"\nNext step:")
    print(f"  python benchmark/visualize.py")
    print(f"  open benchmark/results/report.html")
    print()


if __name__ == "__main__":
    main()
