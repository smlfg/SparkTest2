#!/usr/bin/env python3

"""
AGENT 3: Delta Calculator

This script compares base vs fine-tuned model responses and calculates deltas.

TEACHING NOTES:

1. WHAT IS A "DELTA"?
   - Delta = difference between base and fine-tuned responses
   - Not just "better" or "worse" - we want to understand HOW they differ
   - Example: Is fine-tuned more concise? More technical? More accurate?

2. METRICS WE CALCULATE:
   - Length: Response length in characters and words
   - Similarity: How similar are the responses? (0-1 scale)
   - Keywords: Does fine-tuned use domain-specific terms?
   - Correctness: Does response match expected behavior?

3. ASSESSMENT LOGIC:
   - "improved": Fine-tuned is clearly better (more accurate, better format)
   - "regressed": Fine-tuned is worse (wrong answer, off-topic)
   - "changed": Different but not clearly better/worse
   - "similar": Minimal difference

4. WHY THIS MATTERS:
   - Systematic: Not subjective "looks better"
   - Actionable: Shows specific improvements to make
   - Trackable: Can measure progress across iterations

5. LIMITATIONS:
   - Automated metrics != human judgment
   - Some changes are hard to quantify (tone, style)
   - Use this as a starting point, then manually review interesting cases
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Tuple

from rich.console import Console
from rich.table import Table

console = Console()

################################################################################
# Metrics Calculators
################################################################################

def calculate_length_metrics(base_response: str, finetuned_response: str) -> Dict:
    """
    Calculate length-based metrics.

    Returns:
        {
            "base_length": int,
            "finetuned_length": int,
            "length_delta": int,
            "length_delta_pct": float
        }
    """
    base_len = len(base_response)
    finetuned_len = len(finetuned_response)
    delta = finetuned_len - base_len
    delta_pct = (delta / base_len * 100) if base_len > 0 else 0

    return {
        "base_length": base_len,
        "finetuned_length": finetuned_len,
        "length_delta": delta,
        "length_delta_pct": round(delta_pct, 1)
    }


def calculate_word_overlap(base_response: str, finetuned_response: str) -> float:
    """
    Calculate word overlap (Jaccard similarity).

    Returns:
        Float between 0 (no overlap) and 1 (identical)
    """
    # Normalize and tokenize
    base_words = set(re.findall(r'\w+', base_response.lower()))
    finetuned_words = set(re.findall(r'\w+', finetuned_response.lower()))

    if not base_words and not finetuned_words:
        return 1.0  # Both empty
    if not base_words or not finetuned_words:
        return 0.0  # One empty

    intersection = base_words & finetuned_words
    union = base_words | finetuned_words

    return len(intersection) / len(union)


def calculate_character_similarity(base_response: str, finetuned_response: str) -> float:
    """
    Calculate character-level similarity (simple ratio).

    This is faster than word-based metrics and works well for short responses.
    """
    base = base_response.lower().strip()
    finetuned = finetuned_response.lower().strip()

    if base == finetuned:
        return 1.0

    # Simple character overlap
    base_chars = set(base)
    finetuned_chars = set(finetuned)

    if not base_chars or not finetuned_chars:
        return 0.0

    intersection = base_chars & finetuned_chars
    union = base_chars | finetuned_chars

    return len(intersection) / len(union)


def detect_keywords(response: str, domain_keywords: List[str]) -> List[str]:
    """
    Detect domain-specific keywords in response.

    Args:
        response: The response text
        domain_keywords: List of important domain keywords

    Returns:
        List of found keywords
    """
    response_lower = response.lower()
    found = []
    for keyword in domain_keywords:
        if keyword.lower() in response_lower:
            found.append(keyword)
    return found


def assess_correctness(response: str, expected_behavior: str) -> Tuple[str, str]:
    """
    Assess if response matches expected behavior.

    Returns:
        (assessment, explanation)
        assessment: "correct", "incorrect", "partial", "unclear"
    """
    response_lower = response.lower().strip()
    expected_lower = expected_behavior.lower().strip()

    # Simple heuristics (can be improved with NLP models)

    # Check for explicit numbers/facts
    if re.search(r'\d+', expected_lower):
        expected_numbers = re.findall(r'\d+', expected_lower)
        response_numbers = re.findall(r'\d+', response_lower)
        if set(expected_numbers) == set(response_numbers):
            return "correct", "Contains expected numbers"
        elif set(expected_numbers) & set(response_numbers):
            return "partial", "Contains some expected numbers"
        else:
            return "incorrect", "Missing expected numbers"

    # Check for key terms
    expected_words = set(re.findall(r'\w+', expected_lower))
    response_words = set(re.findall(r'\w+', response_lower))

    overlap = len(expected_words & response_words) / len(expected_words) if expected_words else 0

    if overlap > 0.7:
        return "correct", "Contains most expected terms"
    elif overlap > 0.3:
        return "partial", "Contains some expected terms"
    else:
        return "unclear", "Hard to assess automatically"


################################################################################
# Delta Calculation
################################################################################

def calculate_delta(base_result: Dict, finetuned_result: Dict,
                   domain_keywords: List[str] = None) -> Dict:
    """
    Calculate delta between base and fine-tuned responses.

    Args:
        base_result: Result from base model
        finetuned_result: Result from fine-tuned model
        domain_keywords: Optional list of domain-specific keywords

    Returns:
        Delta dictionary with metrics and assessment
    """
    if domain_keywords is None:
        domain_keywords = []

    base_resp = base_result["response"]
    finetuned_resp = finetuned_result["response"]

    # Calculate metrics
    length_metrics = calculate_length_metrics(base_resp, finetuned_resp)
    word_overlap = calculate_word_overlap(base_resp, finetuned_resp)
    char_similarity = calculate_character_similarity(base_resp, finetuned_resp)

    # Keyword detection
    base_keywords = detect_keywords(base_resp, domain_keywords)
    finetuned_keywords = detect_keywords(finetuned_resp, domain_keywords)

    # Correctness assessment
    base_correctness, base_explanation = assess_correctness(
        base_resp, base_result["expected_behavior"]
    )
    finetuned_correctness, finetuned_explanation = assess_correctness(
        finetuned_resp, finetuned_result["expected_behavior"]
    )

    # Overall assessment
    assessment = assess_change(
        base_correctness, finetuned_correctness,
        word_overlap, length_metrics["length_delta_pct"]
    )

    return {
        "prompt_id": base_result["prompt_id"],
        "prompt": base_result["prompt"],
        "category": base_result["category"],

        # Responses
        "base_response": base_resp,
        "finetuned_response": finetuned_resp,

        # Metrics
        "metrics": {
            "length": length_metrics,
            "word_overlap": round(word_overlap, 3),
            "char_similarity": round(char_similarity, 3),
            "base_keywords": base_keywords,
            "finetuned_keywords": finetuned_keywords,
            "keyword_delta": len(finetuned_keywords) - len(base_keywords)
        },

        # Correctness
        "correctness": {
            "base": {"assessment": base_correctness, "explanation": base_explanation},
            "finetuned": {"assessment": finetuned_correctness, "explanation": finetuned_explanation}
        },

        # Overall assessment
        "assessment": assessment["label"],
        "assessment_reason": assessment["reason"],

        # Performance
        "base_duration_ms": base_result["duration_ms"],
        "finetuned_duration_ms": finetuned_result["duration_ms"],
        "duration_delta_ms": finetuned_result["duration_ms"] - base_result["duration_ms"]
    }


def assess_change(base_correctness: str, finetuned_correctness: str,
                  similarity: float, length_delta_pct: float) -> Dict:
    """
    Assess whether fine-tuned model improved, regressed, or just changed.

    Returns:
        {"label": str, "reason": str}
    """
    # Correctness change
    correctness_map = {"correct": 3, "partial": 2, "unclear": 1, "incorrect": 0}
    base_score = correctness_map[base_correctness]
    finetuned_score = correctness_map[finetuned_correctness]

    # Improved: More correct
    if finetuned_score > base_score:
        return {
            "label": "improved",
            "reason": f"Correctness improved: {base_correctness} → {finetuned_correctness}"
        }

    # Regressed: Less correct
    if finetuned_score < base_score:
        return {
            "label": "regressed",
            "reason": f"Correctness regressed: {base_correctness} → {finetuned_correctness}"
        }

    # Similar responses
    if similarity > 0.8:
        return {
            "label": "similar",
            "reason": f"Responses very similar (similarity: {similarity:.2f})"
        }

    # Changed but not clearly better/worse
    if abs(length_delta_pct) > 50:
        direction = "longer" if length_delta_pct > 0 else "shorter"
        return {
            "label": "changed",
            "reason": f"Response significantly {direction} ({length_delta_pct:+.0f}%)"
        }

    return {
        "label": "changed",
        "reason": "Response changed but unclear if better"
    }


################################################################################
# Main Function
################################################################################

def main():
    parser = argparse.ArgumentParser(
        description="Agent 3: Calculate deltas between base and fine-tuned models",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--output",
        type=str,
        default="benchmark/results/",
        help="Directory containing base.json and finetuned.json (default: benchmark/results/)"
    )
    parser.add_argument(
        "--keywords",
        type=str,
        nargs="+",
        help="Domain-specific keywords to track (optional)"
    )

    args = parser.parse_args()

    # Load results
    base_path = os.path.join(args.output, "base.json")
    finetuned_path = os.path.join(args.output, "finetuned.json")

    if not os.path.exists(base_path):
        console.print(f"[red]Error: Base results not found: {base_path}[/red]")
        sys.exit(1)

    if not os.path.exists(finetuned_path):
        console.print(f"[red]Error: Fine-tuned results not found: {finetuned_path}[/red]")
        sys.exit(1)

    with open(base_path) as f:
        base_data = json.load(f)

    with open(finetuned_path) as f:
        finetuned_data = json.load(f)

    console.print("\n[bold blue]" + "="*60 + "[/bold blue]")
    console.print("[bold blue]Agent 3: Delta Calculator[/bold blue]")
    console.print("[bold blue]" + "="*60 + "[/bold blue]\n")

    console.print(f"[cyan]Base model: {base_data['model']}[/cyan]")
    console.print(f"[cyan]Fine-tuned model: {finetuned_data['model']}[/cyan]\n")

    # Calculate deltas
    base_results = base_data["results"]
    finetuned_results = finetuned_data["results"]

    if len(base_results) != len(finetuned_results):
        console.print("[red]Error: Different number of results in base and fine-tuned[/red]")
        sys.exit(1)

    deltas = []
    for base_result, finetuned_result in zip(base_results, finetuned_results):
        delta = calculate_delta(base_result, finetuned_result, args.keywords or [])
        deltas.append(delta)

    # Save deltas
    deltas_path = os.path.join(args.output, "deltas.json")
    with open(deltas_path, 'w') as f:
        json.dump({
            "base_model": base_data["model"],
            "finetuned_model": finetuned_data["model"],
            "domain": base_data.get("domain", "unknown"),
            "deltas": deltas
        }, f, indent=2)

    console.print(f"[green]✓ Calculated {len(deltas)} deltas[/green]")
    console.print(f"[green]Saved to {deltas_path}[/green]\n")

    # Summary table
    table = Table(title="Delta Summary")
    table.add_column("Assessment", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Percentage", justify="right")

    assessment_counts = {}
    for delta in deltas:
        label = delta["assessment"]
        assessment_counts[label] = assessment_counts.get(label, 0) + 1

    for label in ["improved", "regressed", "changed", "similar"]:
        count = assessment_counts.get(label, 0)
        pct = count / len(deltas) * 100 if deltas else 0

        # Color code
        if label == "improved":
            style = "green"
        elif label == "regressed":
            style = "red"
        elif label == "changed":
            style = "yellow"
        else:
            style = "dim"

        table.add_row(
            f"[{style}]{label.upper()}[/{style}]",
            str(count),
            f"{pct:.1f}%"
        )

    console.print(table)

    # Show interesting cases
    console.print("\n[bold]Notable Changes:[/bold]\n")

    improved = [d for d in deltas if d["assessment"] == "improved"]
    regressed = [d for d in deltas if d["assessment"] == "regressed"]

    if improved:
        console.print(f"[green]✓ Improved ({len(improved)}):[/green]")
        for delta in improved[:3]:  # Show top 3
            console.print(f"  • {delta['prompt_id']}: {delta['assessment_reason']}")

    if regressed:
        console.print(f"\n[red]✗ Regressed ({len(regressed)}):[/red]")
        for delta in regressed[:3]:  # Show top 3
            console.print(f"  • {delta['prompt_id']}: {delta['assessment_reason']}")

    console.print(f"\n[cyan]Next steps:[/cyan]")
    console.print(f"  Generate HTML report: [bold]python benchmark/visualize.py --output {args.output}[/bold]")


if __name__ == "__main__":
    main()
