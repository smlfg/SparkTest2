"""
10 Standard Test Prompts

WHY 10 PROMPTS?
- More than 10: Takes too long to run (>2 minutes)
- Fewer than 10: Not enough coverage
- 10 is the sweet spot for rapid iteration

PROMPT DESIGN PRINCIPLES:
1. Diverse: Cover different task types (QA, translation, code, etc.)
2. Measurable: Have clear right/wrong answers when possible
3. Simple: Suited for 0.5B model capabilities
4. Consistent: Same prompts every iteration (enables comparison)
"""

BENCHMARK_PROMPTS = [
    # ========================================
    # CATEGORY: Factual QA
    # ========================================
    {
        "id": "factual_capital",
        "prompt": "Was ist die Hauptstadt von Deutschland?",
        "category": "factual",
        "ground_truth": "Berlin",
    },
    {
        "id": "factual_math",
        "prompt": "Was ist 15 + 27?",
        "category": "factual",
        "ground_truth": "42",
    },
    # ========================================
    # CATEGORY: Translation
    # ========================================
    {
        "id": "translation_en_de",
        "prompt": "Übersetze ins Deutsche: 'Good morning, how are you?'",
        "category": "translation",
        "ground_truth": "Guten Morgen, wie geht es dir?",
    },
    {
        "id": "translation_de_en",
        "prompt": "Übersetze ins Englische: 'Ich lerne Machine Learning'",
        "category": "translation",
        "ground_truth": "I am learning Machine Learning",
    },
    # ========================================
    # CATEGORY: Instruction Following
    # ========================================
    {
        "id": "instruction_list",
        "prompt": "Liste 3 Programmiersprachen auf",
        "category": "instruction",
        "keywords": ["Python", "Java", "JavaScript", "C++", "C#"],
        "check": "has_3_items",
    },
    {
        "id": "instruction_greeting",
        "prompt": "Schreibe eine freundliche Begrüßung",
        "category": "instruction",
        "keywords": ["Hallo", "Hi", "Guten Tag", "Willkommen"],
    },
    # ========================================
    # CATEGORY: Classification
    # ========================================
    {
        "id": "sentiment_positive",
        "prompt": "Ist dieser Satz positiv oder negativ? 'Das Wetter ist heute wunderbar!'",
        "category": "classification",
        "ground_truth": "positiv",
    },
    {
        "id": "sentiment_negative",
        "prompt": "Ist dieser Satz positiv oder negativ? 'Das Essen war furchtbar.'",
        "category": "classification",
        "ground_truth": "negativ",
    },
    # ========================================
    # CATEGORY: Simple Code Generation
    # ========================================
    {
        "id": "code_function",
        "prompt": "Schreibe eine Python Funktion die zwei Zahlen addiert",
        "category": "code",
        "keywords": ["def", "return", "+"],
    },
    # ========================================
    # CATEGORY: Explanation
    # ========================================
    {
        "id": "explanation_ml",
        "prompt": "Erkläre in einem Satz was Machine Learning ist",
        "category": "explanation",
        "keywords": ["lernen", "Daten", "Muster", "Computer"],
        "min_length": 20,
    },
]

def _validate_prompts():
    ids_seen = set()
    for i, prompt in enumerate(BENCHMARK_PROMPTS):
        required = ["id", "prompt", "category"]
        for field in required:
            assert field in prompt, f"Prompt {i} missing '{field}'"
        assert prompt["id"] not in ids_seen, f"Duplicate ID: {prompt['id']}"
        ids_seen.add(prompt["id"])
        has_eval = any(k in prompt for k in ["ground_truth", "keywords", "check"])
        assert has_eval, f"Prompt {prompt['id']} has no evaluation method"

_validate_prompts()

def get_categories():
    """Get list of unique categories."""
    return sorted(list(set(p["category"] for p in BENCHMARK_PROMPTS)))

if __name__ == "__main__":
    print("=" * 80)
    print("Benchmark Prompt Suite")
    print("=" * 80)
    print(f"\nTotal prompts: {len(BENCHMARK_PROMPTS)}")
    print(f"Categories: {', '.join(get_categories())}")
    print("\n✅ All prompts validated successfully on import.")
    print("\n" + "-" * 80)
    print("Prompt Summary:")
    print("-" * 80)
    for p in BENCHMARK_PROMPTS:
        eval_method = "N/A"
        if "ground_truth" in p:
            eval_method = f"Exact match: '{p['ground_truth']}'"
        elif "keywords" in p:
            eval_method = f"Keywords: {p['keywords']}"
        
        print(f"\n[{p['id']}] ({p['category']})")
        print(f"  Q: {p['prompt']}")
        print(f"  A: {eval_method}")
