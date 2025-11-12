"""
================================================================================
DGX Spark Fast Fine-tuning System
Agent 2: Benchmark Suite - Test Prompts
================================================================================

WHAT: 10 standard test prompts for evaluating model behavior
WHY:  Need consistent prompts to compare base vs fine-tuned models
HOW:  Cover diverse tasks: factual QA, reasoning, creativity, instruction following

USAGE: Import this module to get the benchmark prompts
       from benchmark.prompts import BENCHMARK_PROMPTS

================================================================================
LEARNING OBJECTIVES:
- Why we need diverse test cases (not just training distribution)
- How to design prompts that reveal model capabilities
- Importance of systematic evaluation vs cherry-picking examples
================================================================================
"""

# ===== BENCHMARK PROMPTS =====
# These are designed to test different aspects of model behavior
# After fine-tuning, we expect some to improve, some to stay same, some might regress

BENCHMARK_PROMPTS = [
    # ===== CATEGORY 1: FACTUAL KNOWLEDGE =====
    # Tests if model retained world knowledge after fine-tuning
    {
        "id": "factual-01",
        "category": "factual_knowledge",
        "prompt": "What is the capital of France?",
        "expected_keywords": ["Paris"],
        "reasoning": "Simple factual recall - should not change after fine-tuning"
    },

    {
        "id": "factual-02",
        "category": "factual_knowledge",
        "prompt": "Who wrote 'Romeo and Juliet'?",
        "expected_keywords": ["Shakespeare", "William"],
        "reasoning": "Basic knowledge test - monitors knowledge retention"
    },

    # ===== CATEGORY 2: REASONING =====
    # Tests logical reasoning and problem-solving
    {
        "id": "reasoning-01",
        "category": "reasoning",
        "prompt": "If a train leaves Chicago at 2pm going 60mph, and another leaves New York at 3pm going 80mph, and they're 900 miles apart, when do they meet?",
        "expected_keywords": ["hour", "time", "6", "7"],
        "reasoning": "Math word problem - reveals reasoning capability"
    },

    {
        "id": "reasoning-02",
        "category": "reasoning",
        "prompt": "A farmer has 17 sheep, all but 9 die. How many are left?",
        "expected_keywords": ["9", "nine"],
        "reasoning": "Trick question - tests careful reading"
    },

    # ===== CATEGORY 3: INSTRUCTION FOLLOWING =====
    # Tests if model follows specific instructions
    {
        "id": "instruction-01",
        "category": "instruction_following",
        "prompt": "Write a haiku about programming.",
        "expected_keywords": ["code", "debug", "compile", "5-7-5"],
        "reasoning": "Creative task with format constraints - shows instruction adherence"
    },

    {
        "id": "instruction-02",
        "category": "instruction_following",
        "prompt": "List 3 benefits of exercise in bullet points.",
        "expected_keywords": ["•", "-", "1.", "health", "fitness"],
        "reasoning": "Format + content test - specific structure requested"
    },

    # ===== CATEGORY 4: CONVERSATIONAL =====
    # Tests natural conversation ability
    {
        "id": "conversational-01",
        "category": "conversational",
        "prompt": "Hello! How are you today?",
        "expected_keywords": ["hello", "hi", "good", "fine", "well"],
        "reasoning": "Greeting - tests natural interaction"
    },

    {
        "id": "conversational-02",
        "category": "conversational",
        "prompt": "Can you explain machine learning in simple terms?",
        "expected_keywords": ["learn", "data", "pattern", "algorithm"],
        "reasoning": "Explanation task - tests clarity and helpfulness"
    },

    # ===== CATEGORY 5: DOMAIN-SPECIFIC =====
    # These will show the most change if fine-tuned on domain data
    {
        "id": "domain-01",
        "category": "domain_specific",
        "prompt": "What are the best practices for code review?",
        "expected_keywords": ["review", "code", "feedback", "quality"],
        "reasoning": "Domain knowledge - likely to improve with relevant fine-tuning"
    },

    {
        "id": "domain-02",
        "category": "domain_specific",
        "prompt": "How do I debug a segmentation fault?",
        "expected_keywords": ["debug", "memory", "pointer", "gdb"],
        "reasoning": "Technical troubleshooting - reveals specialized knowledge"
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
    required_fields = ["id", "category", "prompt", "expected_keywords", "reasoning"]
    for p in BENCHMARK_PROMPTS:
        missing = [f for f in required_fields if f not in p]
        if missing:
            issues.append(f"Prompt {p.get('id', 'unknown')} missing fields: {missing}")

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
