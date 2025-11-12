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

CATEGORIES:
- Factual QA: Tests knowledge retention
- Translation: Tests language understanding
- Instruction following: Tests behavior alignment
- Classification: Tests reasoning
- Code generation: Tests structured output
"""

# TEACHING: This is a Python module (not a script)
# Other scripts will import: from benchmark.prompts import BENCHMARK_PROMPTS

BENCHMARK_PROMPTS = [
    # ========================================
    # CATEGORY: Factual QA
    # ========================================
    {
        "id": "factual_capital",
        "prompt": "Was ist die Hauptstadt von Deutschland?",
        "category": "factual",
        "ground_truth": "Berlin",
        # TEACHING: ground_truth = objectively correct answer
        # Agent 3 will check if this appears in response
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
        # TEACHING: Exact match not required, but should be close
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
        # TEACHING: keywords = acceptable answers (any 3 should appear)
        "check": "has_3_items",
        # TEACHING: check = custom validation function
    },
    {
        "id": "instruction_greeting",
        "prompt": "Schreibe eine freundliche Begrüßung",
        "category": "instruction",
        "keywords": ["Hallo", "Hi", "Guten Tag", "Willkommen"],
        # TEACHING: At least one keyword should appear
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
        # TEACHING: Check for basic structure, not perfect syntax
    },

    # ========================================
    # CATEGORY: Explanation
    # ========================================
    {
        "id": "explanation_ml",
        "prompt": "Erkläre in einem Satz was Machine Learning ist",
        "category": "explanation",
        "keywords": ["lernen", "Daten", "Muster", "Computer"],
        # TEACHING: Should contain ML-related terms
        "min_length": 20,
        # TEACHING: At least 20 characters (filters out "Ja", "Nein")
    },
]

# TEACHING: Why use a list of dicts?
# - Easy to iterate: for prompt in BENCHMARK_PROMPTS
# - Easy to filter: [p for p in BENCHMARK_PROMPTS if p["category"] == "factual"]
# - Easy to extend: Just add more dicts
# - JSON-compatible: Can save/load easily

# Validation check (run at import time)
def _validate_prompts():
    """
    TEACHING: Defensive programming
    Check that prompts are well-formed before using them
    """
    ids_seen = set()
    for i, prompt in enumerate(BENCHMARK_PROMPTS):
        # Check required fields
        required = ["id", "prompt", "category"]
        for field in required:
            assert field in prompt, f"Prompt {i} missing '{field}'"

        # Check unique IDs
        assert prompt["id"] not in ids_seen, f"Duplicate ID: {prompt['id']}"
        ids_seen.add(prompt["id"])

        # Check at least one evaluation method
        has_eval = any(k in prompt for k in ["ground_truth", "keywords", "check"])
        assert has_eval, f"Prompt {prompt['id']} has no evaluation method"

# Run validation when module is imported
_validate_prompts()

# TEACHING: This runs when you do: from benchmark.prompts import BENCHMARK_PROMPTS
# If validation fails, import fails → Catches errors early

print(f"✅ Loaded {len(BENCHMARK_PROMPTS)} benchmark prompts")
