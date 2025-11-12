#!/usr/bin/env python3
"""
Delta Calculator - Agent 3

WHAT THIS DOES:
1. Loads benchmark results from Agent 2 (base.json and finetuned.json)
2. Compares responses for each prompt
3. Calculates metrics (similarity, length, keywords)
4. Assesses whether fine-tuning improved or regressed each prompt
5. Outputs deltas.json for Agent 4 (visualization)

ROBUSTNESS DESIGN:
- Matches prompts by ID, not array index (handles missing/reordered prompts)
- Graceful degradation when data is missing or malformed
- Safe division (handles zero-length strings, zero keyword counts)
- Always produces valid output, even with partial data
"""

import json
from pathlib import Path
from difflib import SequenceMatcher
import re

# Input/Output Paths
RESULTS_DIR = Path("benchmark/results")
BASE_PATH = RESULTS_DIR / "base.json"
FINETUNED_PATH = RESULTS_DIR / "finetuned.json"
DELTA_PATH = RESULTS_DIR / "deltas.json"

def calculate_similarity(text1: str, text2: str) -> float:
    """
    TEACHING: Similarity Calculation

    Uses Python's difflib.SequenceMatcher to calculate how similar
    two strings are (0.0 = completely different, 1.0 = identical).

    ROBUSTNESS: Handles empty strings gracefully.
    """
    if not text1 and not text2:
        return 1.0  # Both empty = identical
    if not text1 or not text2:
        return 0.0  # One empty = completely different

    return SequenceMatcher(None, text1, text2).ratio()

def count_keywords(text: str, keywords: list = None) -> int:
    """
    TEACHING: Keyword Extraction

    Counts important keywords in the response. Default keywords are
    technical/informative terms that indicate detailed responses.

    ROBUSTNESS: Handles None/empty text, case-insensitive matching.
    """
    if not text:
        return 0

    # Default keywords for technical responses
    if keywords is None:
        keywords = [
            # Programming terms
            'function', 'class', 'method', 'variable', 'import', 'return',
            'def', 'if', 'for', 'while', 'try', 'except', 'with',
            # Explanatory terms
            'because', 'therefore', 'however', 'example', 'specifically',
            'means', 'refers', 'indicates', 'demonstrates', 'shows',
            # Structural terms
            'first', 'second', 'third', 'finally', 'additionally',
            'moreover', 'furthermore', 'also', 'note', 'important'
        ]

    text_lower = text.lower()
    count = 0
    for keyword in keywords:
        count += text_lower.count(keyword.lower())

    return count

def calculate_length_delta(base_len: int, ft_len: int) -> float:
    """
    TEACHING: Percentage Change Calculation

    Calculates how much the response length changed as a percentage.
    Positive = longer response, Negative = shorter response.

    ROBUSTNESS: Handles division by zero!
    If base length is 0, we can't calculate a percentage change.
    We return a special value or handle it differently.
    """
    if base_len == 0:
        # EDGE CASE: Base response was empty
        if ft_len == 0:
            return 0.0  # Both empty, no change
        else:
            return 100.0  # Went from nothing to something = +100%

    # Normal case: percentage change formula
    return ((ft_len - base_len) / base_len) * 100

def assess_change(base_response: str, ft_response: str, metrics: dict) -> str:
    """
    TEACHING: Assessment Logic

    This is the "intelligence" of Agent 3. We look at multiple signals
    to decide if the fine-tuning helped:

    1. Similarity: Too similar (>95%) means no real change
    2. Length: Longer responses often (but not always) indicate more detail
    3. Keywords: More keywords suggest more technical depth

    The emoji indicators:
    ✅ IMPROVED - Clear improvement
    ❌ REGRESSED - Clear regression
    ⚠️ CHANGED - Different but unclear if better
    ⚪ NEUTRAL - Minimal or no change
    """
    sim = metrics['similarity']
    len_delta = metrics['length_delta_pct']
    kw_base = metrics['keywords_base']
    kw_ft = metrics['keywords_ft']

    # Check for minimal change
    if sim > 0.95:
        return "⚪ NEUTRAL (minimal change)"

    # IMPROVED: Longer response with more keywords
    if len_delta > 20 and kw_ft > kw_base:
        return "✅ IMPROVED (more detailed)"

    # IMPROVED: Significantly more keywords even if shorter
    if kw_ft > kw_base * 1.5:
        return "✅ IMPROVED (more informative)"

    # REGRESSED: Much shorter with fewer keywords
    if len_delta < -50 and kw_ft < kw_base:
        return "❌ REGRESSED (less detailed)"

    # REGRESSED: Significantly fewer keywords
    if kw_base > 0 and kw_ft < kw_base * 0.5:
        return "❌ REGRESSED (less informative)"

    # CHANGED: Different but not clearly better/worse
    if sim < 0.6:
        return "⚠️ CHANGED (different approach)"

    # Default: Neutral
    return "⚪ NEUTRAL (minor variations)"

def load_benchmark_results(path: Path) -> dict:
    """
    ROBUSTNESS: Safe JSON loading with error handling.
    Returns empty dict with error flag if file doesn't exist or is invalid.
    """
    if not path.exists():
        print(f"⚠️  Warning: {path.name} not found")
        return {"error": f"{path.name} not found", "results": []}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate structure
        if not isinstance(data, list):
            print(f"⚠️  Warning: {path.name} is not a list")
            return {"error": f"{path.name} has invalid format", "results": []}

        return {"results": data}

    except json.JSONDecodeError as e:
        print(f"⚠️  Warning: {path.name} has invalid JSON: {e}")
        return {"error": f"JSON decode error in {path.name}", "results": []}
    except Exception as e:
        print(f"⚠️  Warning: Error reading {path.name}: {e}")
        return {"error": str(e), "results": []}

def create_prompt_id_map(results: list) -> dict:
    """
    TEACHING: ID-Based Matching

    This is CRITICAL for robustness! Instead of assuming both arrays
    have the same order/length, we:
    1. Build a dictionary mapping prompt_id → full result
    2. Match by ID, not by index

    This handles:
    - Missing prompts (base has prompt_001, but finetuned doesn't)
    - Reordered prompts
    - Different array lengths
    """
    id_map = {}
    for result in results:
        if 'prompt_id' in result:
            id_map[result['prompt_id']] = result
        else:
            # Fallback: use prompt text as key if no ID
            prompt_text = result.get('prompt', '')
            if prompt_text:
                id_map[prompt_text] = result

    return id_map

def main():
    print("="*60)
    print("DELTA CALCULATOR")
    print("="*60)

    # 1. Load both result sets
    base_data = load_benchmark_results(BASE_PATH)
    ft_data = load_benchmark_results(FINETUNED_PATH)

    base_results = base_data.get('results', [])
    ft_results = ft_data.get('results', [])

    print(f"Loaded {len(base_results)} base results")
    print(f"Loaded {len(ft_results)} finetuned results")

    # ROBUSTNESS CHECK: Can we proceed?
    if not base_results and not ft_results:
        print("❌ No data to compare!")
        print("   Creating empty deltas.json...")
        with open(DELTA_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        print(f"✅ Empty deltas saved to: {DELTA_PATH}")
        print("   (Agent 4 will show 'No data' message)")
        return

    # 2. Create ID-based maps for matching
    print("\n" + "="*60)
    print("MATCHING BY PROMPT ID (not index)")
    print("="*60)

    base_map = create_prompt_id_map(base_results)
    ft_map = create_prompt_id_map(ft_results)

    # Find all unique prompt IDs from both sets
    all_ids = set(base_map.keys()) | set(ft_map.keys())
    print(f"Found {len(all_ids)} unique prompt IDs across both sets")

    # 3. Calculate deltas for each prompt
    deltas = []
    matched_count = 0
    missing_base = 0
    missing_ft = 0

    for prompt_id in sorted(all_ids):
        base_result = base_map.get(prompt_id)
        ft_result = ft_map.get(prompt_id)

        # ROBUSTNESS: Handle missing data
        if not base_result:
            print(f"⚠️  {prompt_id}: Missing in base results (skipping)")
            missing_base += 1
            continue

        if not ft_result:
            print(f"⚠️  {prompt_id}: Missing in finetuned results (skipping)")
            missing_ft += 1
            continue

        matched_count += 1

        # Extract data with fallbacks
        prompt_text = base_result.get('prompt', '')
        category = base_result.get('category', 'unknown')
        base_response = base_result.get('response', '')
        ft_response = ft_result.get('response', '')

        # Calculate metrics
        similarity = calculate_similarity(base_response, ft_response)
        len_delta_pct = calculate_length_delta(len(base_response), len(ft_response))
        kw_base = count_keywords(base_response)
        kw_ft = count_keywords(ft_response)

        metrics = {
            'similarity': similarity,
            'length_delta_pct': len_delta_pct,
            'keywords_base': kw_base,
            'keywords_ft': kw_ft
        }

        # Assess the change
        assessment = assess_change(base_response, ft_response, metrics)

        # Build delta entry
        delta = {
            'prompt_id': prompt_id,
            'category': category,
            'prompt': prompt_text,
            'base_response': base_response,
            'finetuned_response': ft_response,
            'assessment': assessment,
            'metrics': metrics
        }

        deltas.append(delta)

    # 4. Report statistics
    print("\n" + "="*60)
    print("MATCHING STATISTICS")
    print("="*60)
    print(f"✅ Successfully matched: {matched_count}")
    if missing_base > 0:
        print(f"⚠️  Missing in base: {missing_base}")
    if missing_ft > 0:
        print(f"⚠️  Missing in finetuned: {missing_ft}")

    # 5. Save deltas
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(DELTA_PATH, "w", encoding="utf-8") as f:
        json.dump(deltas, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print(f"✅ Deltas saved to: {DELTA_PATH}")
    print("   Ready for Agent 4 (visualization)")
    print("="*60)

if __name__ == "__main__":
    main()
