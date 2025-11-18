"""
Agent 2: Benchmark Suite - Test Prompts

This module defines 10 standard test prompts used to evaluate fine-tuned models.

WHY STANDARDIZED PROMPTS?
- Consistent evaluation across iterations
- Covers diverse tasks (QA, reasoning, creativity, etc.)
- Easy to compare: did the model improve or regress?
- Can customize for your domain

PROMPT CATEGORIES:
1. Factual QA (tests knowledge retention)
2. Reasoning (tests logic)
3. Creative (tests generation quality)
4. Instruction following (tests adherence)
5. Summarization (tests comprehension)

HOW TO CUSTOMIZE:
Replace these prompts with ones relevant to your fine-tuning goal.
For example:
- Customer support: "How do I reset my password?"
- Code generation: "Write a function to reverse a string"
- Medical: "What are the symptoms of diabetes?"

LEARNING OBJECTIVE:
Good benchmarks test if your model improved on YOUR specific task,
not general capabilities. Tailor these prompts to match your training data.
"""

# Standard benchmark prompts (Teaching Edition)
# Each prompt is a dict with:
#   - id: unique identifier
#   - category: type of task
#   - prompt: the actual test input
#   - metadata: structured evaluation criteria
#       - ground_truth: exact answer that must appear (highest priority)
#       - keywords: list of terms that should be mentioned
#       - check: custom validation logic

BENCHMARK_PROMPTS = [
    {
        "id": "factual_01",
        "category": "factual_qa",
        "prompt": "What is the capital of France?",
        "metadata": {
            "category": "factual_qa",
            "ground_truth": "Paris",  # Exact answer - HIGHEST PRIORITY
            "keywords": [],
            "check": None
        }
    },
    {
        "id": "factual_02",
        "category": "factual_qa",
        "prompt": "Who wrote 'Romeo and Juliet'?",
        "metadata": {
            "category": "factual_qa",
            "ground_truth": "Shakespeare",  # Partial match OK
            "keywords": ["William", "Shakespeare"],
            "check": None
        }
    },
    {
        "id": "reasoning_01",
        "category": "reasoning",
        "prompt": "If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly?",
        "metadata": {
            "category": "reasoning",
            "ground_truth": None,
            "keywords": ["cannot conclude", "invalid", "not necessarily", "no", "false"],
            "check": None
        }
    },
    {
        "id": "reasoning_02",
        "category": "reasoning",
        "prompt": "A farmer has 17 sheep and all but 9 die. How many are left?",
        "metadata": {
            "category": "reasoning",
            "ground_truth": "9",  # Must contain the number 9
            "keywords": [],
            "check": None
        }
    },
    {
        "id": "creative_01",
        "category": "creative",
        "prompt": "Write a one-sentence story about a robot learning to paint.",
        "metadata": {
            "category": "creative",
            "ground_truth": None,
            "keywords": ["robot", "paint"],
            "check": "is_single_sentence"
        }
    },
    {
        "id": "creative_02",
        "category": "creative",
        "prompt": "Describe the color blue to someone who has never seen it.",
        "metadata": {
            "category": "creative",
            "ground_truth": None,
            "keywords": ["like", "sky", "ocean", "water", "calm", "cool"],
            "check": None
        }
    },
    {
        "id": "instruction_01",
        "category": "instruction_following",
        "prompt": "List three benefits of exercise. Use exactly three bullet points.",
        "metadata": {
            "category": "instruction_following",
            "ground_truth": None,
            "keywords": ["health", "exercise", "benefit", "fitness"],
            "check": "has_3_items"  # Special check for list format
        }
    },
    {
        "id": "instruction_02",
        "category": "instruction_following",
        "prompt": "Explain quantum computing in simple terms. Limit your response to 50 words.",
        "metadata": {
            "category": "instruction_following",
            "ground_truth": None,
            "keywords": ["quantum", "qubit", "superposition", "computer"],
            "check": "under_50_words"
        }
    },
    {
        "id": "summarization_01",
        "category": "summarization",
        "prompt": "Summarize this in one sentence: 'Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. It uses algorithms to identify patterns and make decisions.'",
        "metadata": {
            "category": "summarization",
            "ground_truth": None,
            "keywords": ["machine learning", "learn", "data", "algorithm"],
            "check": "is_single_sentence"
        }
    },
    {
        "id": "open_ended_01",
        "category": "open_ended",
        "prompt": "What's the most important thing someone should know about learning a new skill?",
        "metadata": {
            "category": "open_ended",
            "ground_truth": None,
            "keywords": ["practice", "patience", "consistent", "time", "effort"],
            "check": None
        }
    },
]


def get_prompts():
    """Return all benchmark prompts."""
    return BENCHMARK_PROMPTS


def get_prompt_by_id(prompt_id):
    """Get specific prompt by ID."""
    for prompt in BENCHMARK_PROMPTS:
        if prompt["id"] == prompt_id:
            return prompt
    return None


def get_prompts_by_category(category):
    """Get all prompts in a category."""
    return [p for p in BENCHMARK_PROMPTS if p["category"] == category]


def get_categories():
    """Return list of all categories."""
    return list(set(p["category"] for p in BENCHMARK_PROMPTS))


# Example: Custom prompts for specific domains
DOMAIN_EXAMPLES = {
    "customer_support": [
        {
            "id": "support_01",
            "category": "troubleshooting",
            "prompt": "My order hasn't arrived. What should I do?",
            "expected": "Should ask for order number and provide tracking help"
        },
        {
            "id": "support_02",
            "category": "product_info",
            "prompt": "What's your return policy?",
            "expected": "Should provide clear return policy details"
        },
    ],

    "code_generation": [
        {
            "id": "code_01",
            "category": "python",
            "prompt": "Write a Python function to check if a string is a palindrome.",
            "expected": "Should provide working Python code with explanation"
        },
        {
            "id": "code_02",
            "category": "debugging",
            "prompt": "This code has a bug: `def add(a, b): return a + b + 1`. Fix it.",
            "expected": "Should identify and fix the +1 bug"
        },
    ],

    "medical": [
        {
            "id": "medical_01",
            "category": "symptoms",
            "prompt": "What are common symptoms of the flu?",
            "expected": "Should list accurate symptoms with disclaimer"
        },
        {
            "id": "medical_02",
            "category": "prevention",
            "prompt": "How can I prevent catching a cold?",
            "expected": "Should provide evidence-based prevention tips"
        },
    ],
}


def get_domain_prompts(domain):
    """
    Get example prompts for a specific domain.

    Usage:
        prompts = get_domain_prompts("customer_support")

    Then modify benchmark/prompts.py to use these instead of defaults.
    """
    return DOMAIN_EXAMPLES.get(domain, [])


if __name__ == "__main__":
    # Test: print all prompts
    print("Standard Benchmark Prompts")
    print("=" * 60)

    for i, prompt in enumerate(BENCHMARK_PROMPTS, 1):
        print(f"\n{i}. {prompt['id']} ({prompt['category']})")
        print(f"   Prompt: {prompt['prompt']}")
        print(f"   Expected: {prompt['expected']}")

    print(f"\n\nTotal: {len(BENCHMARK_PROMPTS)} prompts")
    print(f"Categories: {', '.join(get_categories())}")

    print("\n\nDomain Examples Available:")
    for domain in DOMAIN_EXAMPLES.keys():
        print(f"  - {domain}: {len(DOMAIN_EXAMPLES[domain])} prompts")
