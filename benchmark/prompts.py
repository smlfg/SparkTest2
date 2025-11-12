"""
AGENT 2: Benchmark Prompts

This module defines standard test prompts for evaluating fine-tuned models.

TEACHING NOTES:

1. WHY STANDARD PROMPTS?
   - Consistent evaluation across iterations
   - Track improvements/regressions systematically
   - Compare multiple experiments fairly

2. PROMPT DESIGN PRINCIPLES:
   - Diverse: Test different capabilities (factual, creative, reasoning)
   - Relevant: Match your fine-tuning domain
   - Clear: Unambiguous, measurable responses
   - Balanced: Mix easy/hard, short/long

3. WHAT TO TEST:
   - Factual accuracy (does model know facts?)
   - Following instructions (does it do what you ask?)
   - Consistency (similar inputs → similar outputs?)
   - Domain knowledge (specialized vocabulary, concepts)
   - Style/tone (formal, casual, technical)

4. HOW TO CUSTOMIZE:
   - Replace these prompts with domain-specific ones
   - Add more prompts as you identify edge cases
   - Remove prompts that don't apply to your use case
"""

################################################################################
# Standard Benchmark Prompts
################################################################################

# These are generic prompts that work for most models.
# CUSTOMIZE THESE based on your fine-tuning domain!

STANDARD_PROMPTS = [
    {
        "id": "greeting",
        "category": "basic",
        "prompt": "Hello! How are you?",
        "expected_behavior": "Polite, brief response",
        "why": "Tests basic conversational ability and tone"
    },
    {
        "id": "math_simple",
        "category": "reasoning",
        "prompt": "What is 15 + 27?",
        "expected_behavior": "Correct answer: 42",
        "why": "Tests basic arithmetic reasoning"
    },
    {
        "id": "math_word",
        "category": "reasoning",
        "prompt": "If I have 3 apples and buy 5 more, how many do I have in total?",
        "expected_behavior": "Correct answer: 8, with reasoning",
        "why": "Tests word problem comprehension"
    },
    {
        "id": "factual_capital",
        "category": "knowledge",
        "prompt": "What is the capital of France?",
        "expected_behavior": "Correct answer: Paris",
        "why": "Tests factual knowledge retention"
    },
    {
        "id": "instruction_list",
        "category": "instruction_following",
        "prompt": "List three primary colors.",
        "expected_behavior": "Lists red, blue, yellow (or similar)",
        "why": "Tests ability to follow instructions and format"
    },
    {
        "id": "creative_short",
        "category": "creative",
        "prompt": "Write a one-sentence story about a robot.",
        "expected_behavior": "Single creative sentence",
        "why": "Tests creative generation with constraints"
    },
    {
        "id": "explanation",
        "category": "reasoning",
        "prompt": "Explain why the sky is blue in simple terms.",
        "expected_behavior": "Clear, simplified explanation",
        "why": "Tests ability to explain complex concepts simply"
    },
    {
        "id": "comparison",
        "category": "reasoning",
        "prompt": "What's the difference between a cat and a dog?",
        "expected_behavior": "Multiple distinguishing features",
        "why": "Tests comparative reasoning"
    },
    {
        "id": "instruction_complex",
        "category": "instruction_following",
        "prompt": "Write a haiku about winter.",
        "expected_behavior": "3 lines with 5-7-5 syllables, winter theme",
        "why": "Tests following complex format instructions"
    },
    {
        "id": "open_ended",
        "category": "creative",
        "prompt": "What's your favorite color and why?",
        "expected_behavior": "Picks a color with reasoning",
        "why": "Tests personality/consistency in open-ended responses"
    }
]


################################################################################
# Domain-Specific Prompt Templates
################################################################################

# Add your own domain-specific prompts here!
# Examples:

MEDICAL_PROMPTS = [
    {
        "id": "symptom_check",
        "category": "medical",
        "prompt": "What are common symptoms of the flu?",
        "expected_behavior": "Lists fever, cough, fatigue, etc.",
        "why": "Tests medical knowledge"
    }
]

CODING_PROMPTS = [
    {
        "id": "explain_code",
        "category": "coding",
        "prompt": "Explain what a for loop does in Python.",
        "expected_behavior": "Clear explanation with example",
        "why": "Tests technical explanation ability"
    }
]

CUSTOMER_SERVICE_PROMPTS = [
    {
        "id": "return_policy",
        "category": "customer_service",
        "prompt": "What is your return policy?",
        "expected_behavior": "Polite, informative response about returns",
        "why": "Tests domain-specific knowledge and tone"
    }
]


################################################################################
# Helper Functions
################################################################################

def get_prompts(domain="standard"):
    """
    Get prompts for a specific domain.

    Args:
        domain: "standard", "medical", "coding", "customer_service"

    Returns:
        List of prompt dictionaries
    """
    if domain == "standard":
        return STANDARD_PROMPTS
    elif domain == "medical":
        return MEDICAL_PROMPTS
    elif domain == "coding":
        return CODING_PROMPTS
    elif domain == "customer_service":
        return CUSTOMER_SERVICE_PROMPTS
    else:
        raise ValueError(f"Unknown domain: {domain}")


def get_prompt_by_id(prompt_id, domain="standard"):
    """Get a specific prompt by ID."""
    prompts = get_prompts(domain)
    for p in prompts:
        if p["id"] == prompt_id:
            return p
    return None


def get_prompt_categories(domain="standard"):
    """Get all unique categories in a domain."""
    prompts = get_prompts(domain)
    return list(set(p["category"] for p in prompts))


################################################################################
# Validation
################################################################################

def validate_prompts(prompts):
    """
    Validate that prompts have required fields.

    Returns: (is_valid, errors)
    """
    required_fields = ["id", "category", "prompt", "expected_behavior", "why"]
    errors = []

    # Check for duplicate IDs
    ids = [p["id"] for p in prompts]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate prompt IDs found")

    # Check each prompt
    for i, p in enumerate(prompts):
        for field in required_fields:
            if field not in p:
                errors.append(f"Prompt {i} missing field: {field}")

        # Check prompt is not empty
        if "prompt" in p and not p["prompt"].strip():
            errors.append(f"Prompt {i} has empty prompt text")

    return len(errors) == 0, errors


# Self-test
if __name__ == "__main__":
    # Validate standard prompts
    is_valid, errors = validate_prompts(STANDARD_PROMPTS)

    if is_valid:
        print(f"✓ {len(STANDARD_PROMPTS)} standard prompts validated successfully")
        print("\nPrompt categories:")
        for category in get_prompt_categories():
            count = len([p for p in STANDARD_PROMPTS if p["category"] == category])
            print(f"  - {category}: {count} prompts")
    else:
        print("✗ Validation errors:")
        for error in errors:
            print(f"  - {error}")
