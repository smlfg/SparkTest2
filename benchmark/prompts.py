"""
================================================================================
DGX Spark Fast Fine-tuning System
Agent 2: Benchmark Suite - Test Prompts (IMPROVED v2.0)
================================================================================

WHAT: 10 standard test prompts for evaluating model behavior
WHY:  Need consistent prompts to compare base vs fine-tuned models
HOW:  Strategic mix to show clear improvements after ML fine-tuning

USAGE: Import this module to get the benchmark prompts
       from benchmark.prompts import BENCHMARK_PROMPTS

================================================================================
IMPROVED STRATEGY (v2.0):
- 30% RETENTION: General knowledge/math - should stay SAME
- 30% TRANSFER: Instructions - should stay SIMILAR
- 40% ACQUISITION: ML knowledge - should clearly IMPROVE

Why German prompts? Matches training dataset language, clearer alignment.
Why 40% acquisition? Shows obvious improvements - expect 4-5 improved vs 0-1.
================================================================================
LEARNING OBJECTIVES:
- Why we need diverse test cases (not just training distribution)
- How to design prompts that reveal model capabilities
- Strategic prompt design to demonstrate fine-tuning effectiveness
- Importance of systematic evaluation vs cherry-picking examples
================================================================================
"""

# ===== BENCHMARK PROMPTS v2.0 =====
# Strategic design: 30% retention, 30% transfer, 40% acquisition

BENCHMARK_PROMPTS = [
    # ===== CATEGORY 1: RETENTION (30%) =====
    # General knowledge/math - should NOT change after fine-tuning
    # This tests if we broke basic capabilities
    {
        "id": "retention-math",
        "category": "retention",
        "prompt": "Was ist 15 + 27?",
        "ground_truth": "42",
        "expected_keywords": ["42", "zweiundvierzig"],
        "reasoning": "Basic math - should stay correct after fine-tuning"
    },

    {
        "id": "retention-knowledge",
        "category": "retention",
        "prompt": "Was ist die Hauptstadt von Deutschland?",
        "ground_truth": "Berlin",
        "expected_keywords": ["Berlin"],
        "reasoning": "Factual knowledge - monitors knowledge retention"
    },

    {
        "id": "retention-reasoning",
        "category": "retention",
        "prompt": "Ein Bauer hat 17 Schafe, alle außer 9 sterben. Wie viele bleiben übrig?",
        "ground_truth": "9",
        "expected_keywords": ["9", "neun"],
        "reasoning": "Trick question - tests if reasoning ability degraded"
    },

    # ===== CATEGORY 2: TRANSFER (30%) =====
    # Instruction following - should transfer from base model capabilities
    # These test if instruction-following improved/maintained
    {
        "id": "transfer-format",
        "category": "transfer",
        "prompt": "Nenne 3 Vorteile von regelmäßigem Sport in Stichpunkten.",
        "ground_truth": "Bullet list with 3 benefits",
        "expected_keywords": ["•", "-", "Gesundheit", "Fitness", "Ausdauer"],
        "reasoning": "Format instruction - should maintain/improve adherence"
    },

    {
        "id": "transfer-explain",
        "category": "transfer",
        "prompt": "Erkläre einem Kind, wie ein Kühlschrank funktioniert.",
        "ground_truth": "Simple explanation with analogy",
        "expected_keywords": ["kalt", "Wärme", "einfach"],
        "reasoning": "Explanation task - tests clarity and simplification"
    },

    {
        "id": "transfer-conversation",
        "category": "transfer",
        "prompt": "Hallo! Wie geht es dir?",
        "ground_truth": "Friendly greeting response",
        "expected_keywords": ["Hallo", "gut", "danke"],
        "reasoning": "Conversational - maintains natural interaction"
    },

    # ===== CATEGORY 3: ACQUISITION (40%) =====
    # ML knowledge - SHOULD CLEARLY IMPROVE after fine-tuning
    # These directly test what we trained on
    {
        "id": "acquisition-ml-definition",
        "category": "acquisition",
        "prompt": "Was ist Machine Learning?",
        "ground_truth": "ML ist eine Methode, bei der Computer aus Daten lernen...",
        "expected_keywords": ["Daten", "lernen", "Muster", "Algorithmus", "KI"],
        "reasoning": "Core ML concept - trained extensively, should improve significantly"
    },

    {
        "id": "acquisition-nn-explain",
        "category": "acquisition",
        "prompt": "Erkläre mir Neuronale Netze in 2-3 Sätzen.",
        "ground_truth": "Neural networks sind inspiriert von Gehirn...",
        "expected_keywords": ["Neuronen", "Schichten", "Gewichte", "lernen"],
        "reasoning": "Direct training topic - expect much better explanation"
    },

    {
        "id": "acquisition-supervised",
        "category": "acquisition",
        "prompt": "Was ist der Unterschied zwischen Supervised und Unsupervised Learning?",
        "ground_truth": "Supervised hat Labels, Unsupervised nicht...",
        "expected_keywords": ["Labels", "überwacht", "Klassifikation", "Clustering"],
        "reasoning": "Specific ML concept from training - should show clear improvement"
    },

    {
        "id": "acquisition-overfitting",
        "category": "acquisition",
        "prompt": "Was ist Overfitting und wie verhindert man es?",
        "ground_truth": "Overfitting = zu gut an Trainingsdaten angepasst...",
        "expected_keywords": ["Überanpassung", "Trainingsdaten", "Generalisierung", "Regularisierung"],
        "reasoning": "Advanced ML topic - strongest improvement expected"
    },
]

# ===== HELPER FUNCTIONS =====

def get_prompts_by_category(category):
    """Get all prompts in a specific category."""
    return [p for p in BENCHMARK_PROMPTS if p["category"] == category]


def get_prompt_by_id(prompt_id):
    """Get a specific prompt by ID."""
    for p in BENCHMARK_PROMPTS:
        if p["id"] == prompt_id:
            return p
    return None


def get_all_prompt_texts():
    """Get just the prompt strings (for quick testing)."""
    return [p["prompt"] for p in BENCHMARK_PROMPTS]


def get_categories():
    """Get list of unique categories."""
    return list(set(p["category"] for p in BENCHMARK_PROMPTS))


# ===== VALIDATION =====
def validate_prompts():
    """
    Validate that prompts are well-formed.
    Run this to check for issues in the prompt set.
    """
    issues = []

    # Check for duplicate IDs
    ids = [p["id"] for p in BENCHMARK_PROMPTS]
    if len(ids) != len(set(ids)):
        issues.append("Duplicate prompt IDs found")

    # Check all prompts have required fields
    required_fields = ["id", "category", "prompt", "reasoning"]
    # ground_truth and expected_keywords are both acceptable
    for p in BENCHMARK_PROMPTS:
        missing = [f for f in required_fields if f not in p]
        if missing:
            issues.append(f"Prompt {p.get('id', 'unknown')} missing fields: {missing}")

        # Check that either ground_truth or expected_keywords exists
        if "ground_truth" not in p and "expected_keywords" not in p:
            issues.append(f"Prompt {p.get('id', 'unknown')} missing ground_truth or expected_keywords")

    # Check expected count
    if len(BENCHMARK_PROMPTS) != 10:
        issues.append(f"Expected 10 prompts, found {len(BENCHMARK_PROMPTS)}")

    return issues


# ===== USAGE EXAMPLES =====
if __name__ == "__main__":
    print("=" * 80)
    print("Benchmark Prompt Suite")
    print("=" * 80)

    print(f"\nTotal prompts: {len(BENCHMARK_PROMPTS)}")
    print(f"Categories: {', '.join(get_categories())}")

    # Validate
    issues = validate_prompts()
    if issues:
        print("\n⚠️  Validation issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ All prompts validated successfully")

    # Show summary
    print("\n" + "-" * 80)
    print("Prompt Summary:")
    print("-" * 80)
    for p in BENCHMARK_PROMPTS:
        print(f"\n[{p['id']}] {p['category']}")
        print(f"  Q: {p['prompt']}")
        print(f"  Expected: {', '.join(p['expected_keywords'][:3])}")
        print(f"  Reasoning: {p['reasoning']}")

    # Example usage
    print("\n" + "=" * 80)
    print("Example Usage:")
    print("=" * 80)
    print("""
from benchmark.prompts import BENCHMARK_PROMPTS, get_prompt_by_id

# Get all prompts
for prompt in BENCHMARK_PROMPTS:
    print(prompt['prompt'])

# Get specific prompt
factual = get_prompt_by_id('factual-01')
print(factual['prompt'])

# Get by category
from benchmark.prompts import get_prompts_by_category
reasoning_prompts = get_prompts_by_category('reasoning')
    """)
