#!/usr/bin/env python3
"""
Agent 3: Delta Calculator

This script compares base vs fine-tuned model responses and calculates
meaningful metrics to determine if fine-tuning improved the model.

WHAT IS A "DELTA"?
Delta = the difference between base and fine-tuned responses.
We measure multiple dimensions:
- Length (did responses get longer/shorter?)
- Similarity (how different are they?)
- Keywords (does fine-tuned use domain-specific terms?)
- Correctness (subjective, but we can check for expected patterns)

ASSESSMENT CATEGORIES:
- IMPROVED: Fine-tuned response is objectively better
- REGRESSED: Fine-tuned response is worse
- CHANGED: Different but not clearly better/worse
- UNCHANGED: Essentially the same response

WHY THIS MATTERS:
Without delta analysis, you're just guessing if fine-tuning worked.
This gives you concrete metrics to track improvement over iterations.

LEARNING OBJECTIVE:
Learn to quantify model improvements beyond "feels better".
Good metrics drive good iteration decisions.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any

# Text similarity
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class DeltaCalculator:
    """
    Calculate deltas between base and fine-tuned responses.

    TEACHING NOTE:
    Each metric answers a specific question:
    - Length: Did fine-tuning make responses more/less verbose?
    - Similarity: How different are the responses?
    - TF-IDF cosine: Are they semantically similar?
    - Sequence ratio: Character-level similarity
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer()

    def calculate_length_delta(self, base_resp: str, ft_resp: str) -> Dict:
        """
        Calculate length difference.

        Returns:
            dict with char_delta, word_delta, percent_change
        """
        base_chars = len(base_resp)
        ft_chars = len(ft_resp)
        base_words = len(base_resp.split())
        ft_words = len(ft_resp.split())

        char_delta = ft_chars - base_chars
        word_delta = ft_words - base_words

        # Percent change
        char_pct = (char_delta / base_chars * 100) if base_chars > 0 else 0
        word_pct = (word_delta / base_words * 100) if base_words > 0 else 0

        return {
            "base_chars": base_chars,
            "finetuned_chars": ft_chars,
            "char_delta": char_delta,
            "char_percent_change": round(char_pct, 1),
            "base_words": base_words,
            "finetuned_words": ft_words,
            "word_delta": word_delta,
            "word_percent_change": round(word_pct, 1),
        }

    def calculate_similarity(self, base_resp: str, ft_resp: str) -> Dict:
        """
        Calculate text similarity using multiple methods.

        TEACHING NOTE:
        - SequenceMatcher: Character-level edit distance (like diff)
        - TF-IDF Cosine: Semantic similarity based on word importance
        High similarity = responses are very similar
        Low similarity = fine-tuning changed the response significantly
        """
        # Sequence matcher (character-level)
        seq_ratio = SequenceMatcher(None, base_resp, ft_resp).ratio()

        # TF-IDF cosine similarity (semantic)
        try:
            tfidf_matrix = self.vectorizer.fit_transform([base_resp, ft_resp])
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except:
            cosine_sim = 0.0

        return {
            "sequence_ratio": round(seq_ratio, 3),
            "cosine_similarity": round(float(cosine_sim), 3),
            "interpretation": self._interpret_similarity(seq_ratio, cosine_sim)
        }

    def _interpret_similarity(self, seq_ratio: float, cosine_sim: float) -> str:
        """Interpret similarity scores."""
        avg = (seq_ratio + cosine_sim) / 2

        if avg > 0.9:
            return "Very similar (>90%)"
        elif avg > 0.7:
            return "Similar (70-90%)"
        elif avg > 0.4:
            return "Moderately different (40-70%)"
        else:
            return "Very different (<40%)"

    def check_keywords(self, response: str, keywords: List[str]) -> Dict:
        """
        Check if response contains specific keywords.

        TEACHING NOTE:
        Useful for checking if fine-tuning added domain knowledge.
        Example: After training on customer support, does model now
        mention "ticket number", "refund policy", etc.?
        """
        response_lower = response.lower()

        found = []
        missing = []

        for keyword in keywords:
            if keyword.lower() in response_lower:
                found.append(keyword)
            else:
                missing.append(keyword)

        return {
            "found": found,
            "missing": missing,
            "coverage": round(len(found) / len(keywords) * 100, 1) if keywords else 0
        }

    def assess_change(
        self,
        length_delta: Dict,
        similarity: Dict,
        expected: str,
        base_resp: str,
        ft_resp: str
    ) -> str:
        """
        Assess if change is improvement, regression, or neutral.

        TEACHING NOTE:
        This is a heuristic assessment. Adjust logic based on your goals.
        Current logic:
        - IMPROVED: Response changed significantly and matches expected behavior
        - REGRESSED: Response became error or much shorter without reason
        - CHANGED: Response changed but unclear if better
        - UNCHANGED: Essentially the same response

        For production: Consider adding LLM-based assessment or human labeling.
        """
        # Check if responses are essentially the same
        if similarity["cosine_similarity"] > 0.95:
            return "UNCHANGED"

        # Check for errors
        if "ERROR" in ft_resp and "ERROR" not in base_resp:
            return "REGRESSED"

        # Check for suspicious length changes
        if abs(length_delta["char_percent_change"]) > 200:
            # Dramatic change - could be good or bad
            if length_delta["char_delta"] < 0:
                return "REGRESSED"  # Became much shorter

        # Check if expected behavior is mentioned
        if expected:
            expected_lower = expected.lower()
            # Simple keyword check
            expected_keywords = [
                word for word in expected_lower.split()
                if len(word) > 4  # Only meaningful words
            ]

            base_matches = sum(
                1 for kw in expected_keywords
                if kw in base_resp.lower()
            )
            ft_matches = sum(
                1 for kw in expected_keywords
                if kw in ft_resp.lower()
            )

            if ft_matches > base_matches:
                return "IMPROVED"
            elif ft_matches < base_matches:
                return "REGRESSED"

        # Significant change, but unclear direction
        if similarity["cosine_similarity"] < 0.7:
            return "CHANGED"

        # Minor change
        return "CHANGED"


def load_results(base_path: Path, finetuned_path: Path):
    """Load benchmark results."""
    with open(base_path, 'r') as f:
        base_results = json.load(f)

    with open(finetuned_path, 'r') as f:
        finetuned_results = json.load(f)

    return base_results, finetuned_results


def calculate_deltas(base_results: List[Dict], finetuned_results: List[Dict]) -> List[Dict]:
    """
    Calculate deltas for all prompt responses.

    Returns:
        List of delta objects with metrics and assessment
    """
    calculator = DeltaCalculator()
    deltas = []

    # Match base and fine-tuned results by prompt_id
    for base_r in base_results:
        # Find matching fine-tuned result
        ft_r = next(
            (r for r in finetuned_results if r["prompt_id"] == base_r["prompt_id"]),
            None
        )

        if not ft_r:
            print(f"⚠️  Warning: No fine-tuned result for {base_r['prompt_id']}")
            continue

        # Calculate metrics
        length_delta = calculator.calculate_length_delta(
            base_r["response"],
            ft_r["response"]
        )

        similarity = calculator.calculate_similarity(
            base_r["response"],
            ft_r["response"]
        )

        # Assess change
        assessment = calculator.assess_change(
            length_delta,
            similarity,
            base_r.get("expected", ""),
            base_r["response"],
            ft_r["response"]
        )

        # Compile delta
        delta = {
            "prompt_id": base_r["prompt_id"],
            "category": base_r["category"],
            "prompt": base_r["prompt"],
            "expected": base_r.get("expected", ""),
            "base_response": base_r["response"],
            "finetuned_response": ft_r["response"],
            "metrics": {
                "length": length_delta,
                "similarity": similarity,
            },
            "assessment": assessment,
        }

        deltas.append(delta)

    return deltas


def print_summary(deltas: List[Dict]):
    """Print summary statistics."""
    print("\n📊 Delta Analysis Summary")
    print("=" * 60)

    # Count assessments
    assessments = [d["assessment"] for d in deltas]
    improved = assessments.count("IMPROVED")
    regressed = assessments.count("REGRESSED")
    changed = assessments.count("CHANGED")
    unchanged = assessments.count("UNCHANGED")

    print(f"\nOverall Assessment:")
    print(f"  ✅ IMPROVED:  {improved:2d} / {len(deltas)} ({improved/len(deltas)*100:.0f}%)")
    print(f"  ❌ REGRESSED: {regressed:2d} / {len(deltas)} ({regressed/len(deltas)*100:.0f}%)")
    print(f"  🔄 CHANGED:   {changed:2d} / {len(deltas)} ({changed/len(deltas)*100:.0f}%)")
    print(f"  ⚪ UNCHANGED: {unchanged:2d} / {len(deltas)} ({unchanged/len(deltas)*100:.0f}%)")

    # Average metrics
    avg_char_delta = np.mean([d["metrics"]["length"]["char_delta"] for d in deltas])
    avg_similarity = np.mean([d["metrics"]["similarity"]["cosine_similarity"] for d in deltas])

    print(f"\nAverage Metrics:")
    print(f"  Length change: {avg_char_delta:+.0f} characters")
    print(f"  Similarity: {avg_similarity:.2f} (1.0 = identical, 0.0 = completely different)")

    # By category
    categories = list(set(d["category"] for d in deltas))
    print(f"\nBy Category:")
    for cat in categories:
        cat_deltas = [d for d in deltas if d["category"] == cat]
        cat_improved = sum(1 for d in cat_deltas if d["assessment"] == "IMPROVED")
        print(f"  {cat:20s}: {cat_improved}/{len(cat_deltas)} improved")

    print("\n" + "=" * 60)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate deltas between base and fine-tuned responses"
    )

    parser.add_argument(
        "--base",
        type=str,
        default="benchmark/results/base.json",
        help="Path to base model results"
    )

    parser.add_argument(
        "--finetuned",
        type=str,
        default="benchmark/results/finetuned.json",
        help="Path to fine-tuned model results"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="benchmark/results/deltas.json",
        help="Output path for deltas"
    )

    return parser.parse_args()


def main():
    """Main delta calculation pipeline."""
    print("=" * 60)
    print("Agent 3: Delta Calculator")
    print("=" * 60)

    # Parse arguments
    args = parse_args()

    # Check files exist
    base_path = Path(args.base)
    finetuned_path = Path(args.finetuned)

    if not base_path.exists():
        print(f"❌ Error: Base results not found at {base_path}")
        return 1

    if not finetuned_path.exists():
        print(f"❌ Error: Fine-tuned results not found at {finetuned_path}")
        return 1

    # Load results
    print(f"\n📂 Loading results...")
    print(f"   Base: {base_path}")
    print(f"   Fine-tuned: {finetuned_path}")

    base_results, finetuned_results = load_results(base_path, finetuned_path)

    print(f"✓ Loaded {len(base_results)} base results")
    print(f"✓ Loaded {len(finetuned_results)} fine-tuned results")

    # Calculate deltas
    print(f"\n🔍 Calculating deltas...")
    deltas = calculate_deltas(base_results, finetuned_results)

    print(f"✓ Calculated {len(deltas)} deltas")

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(deltas, f, indent=2)

    print(f"✓ Saved to {output_path}")

    # Print summary
    print_summary(deltas)

    print("\nNext steps:")
    print("  1. Generate HTML report: python benchmark/visualize.py")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
