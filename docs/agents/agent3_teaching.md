# Agent 3 Teaching Guide: How to Measure "Better"

## What You Built

You built a script that performs **automated judgment**. It doesn't just compare text; it applies rules to decide if the model is learning what we want.

This is a critical component in the iteration loop - without it, you're flying blind. You wouldn't know if your fine-tuning improved the model or made it worse.

---

## The Core Concepts

### 1. Text Similarity (SequenceMatcher)

**The Problem**: How do we know if the model changed its answer?

We can't just use `text_a == text_b` because even a single extra space would return `False`. We need a **similarity metric** that captures "how different" two pieces of text are.

**The Solution**: Similarity Ratio (0.0 to 1.0)

```python
from difflib import SequenceMatcher

ratio = SequenceMatcher(None, text_a, text_b).ratio()
```

**What the Numbers Mean**:

- **1.0**: Identical. (Did the model fail to learn anything?)
- **0.9-0.99**: Minor formatting changes.
- **0.4-0.8**: Significant rewording (The "Delta" zone).
- **<0.3**: Completely new hallucination or topic switch.

**Teaching Point**: In fine-tuning, we usually aim for a "Goldilocks" zone (0.5 - 0.8). We want the model to change, but not lose the original meaning (unless the original was wrong).

**Example**:

```
Text A: "The capital of France is Paris. It's a beautiful city."
Text B: "Paris is the capital of France. It's a lovely city."

Similarity: ~0.75 (same meaning, different wording)
```

```
Text A: "The capital of France is Paris."
Text B: "Paris."

Similarity: ~0.45 (correct but much shorter)
```

```
Text A: "The capital of France is Paris."
Text B: "The capital of France is London."

Similarity: ~0.85 (looks similar but WRONG ANSWER!)
```

**Key Lesson**: Similarity alone isn't enough. A high similarity score can hide a critical error (Paris → London). That's why we need GROUND TRUTH checking.

---

### 2. Heuristic Assessment (The "Rules")

AI evaluation is hard. Full LLM-based judgment is slow and expensive. We use **Heuristics** (Rules of Thumb) to be fast and deterministic.

#### Rule 1: Ground Truth (Highest Priority)

**When to use**: Factual questions with one correct answer.

```python
# Example: "What is the capital of France?"
ground_truth = "Paris"

base_has_answer = "paris" in base_response.lower()
ft_has_answer = "paris" in finetuned_response.lower()

if not base_has_answer and ft_has_answer:
    return "✅ IMPROVED (Fixed Answer)"
```

**Why this matters**: If the prompt asks "Capital of France?" and the Base model says "London" (Wrong) and Fine-tuned says "Paris" (Right), that is the **strongest** signal of improvement.

**Example Scenario**:

```
Prompt: "A farmer has 17 sheep and all but 9 die. How many are left?"

Base Model: "8 sheep are left."  ❌ WRONG
Fine-tuned: "9 sheep are left." ✅ CORRECT

Assessment: "✅ IMPROVED (Fixed Answer)"
```

Without ground truth checking, we'd just see ~50% similarity and say "changed". But we'd miss that the fine-tuned model **fixed a logic error**.

#### Rule 2: Keywords (Medium Priority)

**When to use**: Multi-faceted responses where multiple concepts should be mentioned.

```python
# Example: "List symptoms of the flu"
keywords = ["fever", "cough", "fatigue", "ache"]

base_count = 2  # mentions "fever" and "cough"
ft_count = 4    # mentions all four

return "✅ IMPROVED (+2 keywords)"
```

**Why this matters**: For tasks like "List 3 benefits" or "Explain the symptoms", we want comprehensive coverage. Keyword counting measures completeness.

**Example Scenario**:

```
Prompt: "Describe the color blue to someone who has never seen it."

Base Model: "Blue is a color."
Keywords found: 0 / 6 (like, sky, ocean, water, calm, cool)

Fine-tuned: "Blue is like the calm feeling of looking at the ocean or a clear sky."
Keywords found: 4 / 6

Assessment: "✅ IMPROVED (+4 keywords)"
```

#### Rule 3: Custom Checks (Medium Priority)

**When to use**: Domain-specific validation that can't be captured by keywords alone.

```python
# Example: "List THREE benefits of exercise"
check = "has_3_items"

def perform_custom_check(text, check_type):
    if check_type == "has_3_items":
        bullet_count = text.count("•") + text.count("-")
        return bullet_count >= 2  # Approximately 3 items
```

**Other useful checks**:
- `is_single_sentence`: Check for exactly one sentence
- `under_50_words`: Word count constraint
- `has_code_block`: Must include ``` fenced code
- `mentions_ticket`: Customer support should ask for ticket number

**Example Scenario**:

```
Prompt: "List three benefits of exercise. Use exactly three bullet points."

Base Model: "Exercise is good for health and fitness."
Check: has_3_items → FAIL (no list format)

Fine-tuned: "• Improves heart health\n• Boosts energy\n• Reduces stress"
Check: has_3_items → PASS (has 3 bullets)

Assessment: "✅ IMPROVED (Now passes: has_3_items)"
```

#### Rule 4: Similarity Fallback (Lowest Priority)

**When to use**: When no structured criteria exist.

```python
if similarity > 0.95:
    return "⚪ NEUTRAL (No Change)"
elif similarity < 0.4:
    return "🔄 CHANGED (Major Rewrite)"
else:
    return "📝 TWEAKED (Minor Edits)"
```

**Why this is last**: Without context, we can't tell if a change is good or bad. We just report that *something* changed.

---

### 3. Priority Cascade

**Critical Concept**: Rules are applied in ORDER. Higher priority rules short-circuit lower ones.

```
┌─────────────────────────────────────────┐
│ RULE 1: Ground Truth                   │
│ ✓ HIGHEST PRIORITY                      │
│ If exists, this overrides everything    │
└─────────────────────────────────────────┘
         ↓ (if no ground truth)
┌─────────────────────────────────────────┐
│ RULE 2: Keywords                        │
│ ✓ MEDIUM PRIORITY                       │
│ Check if key concepts are mentioned     │
└─────────────────────────────────────────┘
         ↓ (if no keywords)
┌─────────────────────────────────────────┐
│ RULE 3: Custom Checks                   │
│ ✓ MEDIUM PRIORITY                       │
│ Domain-specific validation              │
└─────────────────────────────────────────┘
         ↓ (if no checks)
┌─────────────────────────────────────────┐
│ RULE 4: Similarity                      │
│ ✓ FALLBACK                              │
│ Just measure how much text changed      │
└─────────────────────────────────────────┘
```

**Why this matters**: If a prompt has a ground truth answer, we don't care about keywords or similarity. Getting the right answer is what counts.

---

## Experiments to Try

These hands-on experiments will deepen your understanding of delta analysis.

### Experiment 1: The "Copycat" Effect

**Setup**: Train for only 1 epoch on very little data (3-5 examples).

**Run**:
```bash
python train.py --name copycat --dataset tiny.json --epochs 1
./scripts/export_to_ollama.sh copycat
python benchmark/run.py copycat
python benchmark/delta.py
```

**Expectation**: High similarity (>0.9). Assessment: "⚪ NEUTRAL".

**Lesson**: The model hasn't learned enough to diverge from its base weights. You'll see that responses are almost identical. This is **underfitting** - not enough training.

**Example Output**:
```
[factual_01] Sim: 98% → ⚪ NEUTRAL (No Change)
[factual_02] Sim: 96% → ⚪ NEUTRAL (No Change)

Summary: 0 Improved | 0 Regressed | 10 Neutral
```

**What to do**: Increase epochs or add more training data.

---

### Experiment 2: Overfitting (The "Parrot")

**Setup**: Train for 10 epochs on a tiny dataset (5 examples).

**Run**:
```bash
python train.py --name parrot --dataset tiny.json --epochs 10
./scripts/export_to_ollama.sh parrot
python benchmark/run.py parrot
python benchmark/delta.py
```

**Expectation**:
- On training prompts: "✅ IMPROVED" (perfect memorization)
- On new prompts: "❌ REGRESSED" or Low Similarity (Gibberish)

**Lesson**: This script detects **overfitting** by showing you where the model broke previously correct answers.

**Example Output**:
```
[factual_01] Sim: 100% → ✅ PASS (Both Correct)  ← Was in training data
[factual_02] Sim: 15% → ❌ REGRESSED (Broke Answer) ← New prompt, gibberish
[reasoning_01] Sim: 8% → 🔄 CHANGED (Major Rewrite) ← Hallucination

Summary: 1 Passed | 3 Regressed | 6 Changed
```

**What to do**: Reduce epochs or add more diverse training examples.

---

### Experiment 3: Targeted Improvement

**Setup**: Identify which prompts the base model fails, then create training data specifically for those.

**Steps**:

1. Run benchmark on base model (without fine-tuning)
2. Look at deltas.json - which prompts have ground truth failures?
3. Create training examples for those specific topics
4. Train and benchmark again

**Expectation**: Ground truth assessments should flip from "⚠️ FAILED" to "✅ IMPROVED".

**Example**:

```
Before fine-tuning:
[reasoning_02] → ⚠️ FAILED (Both Wrong)
  Base says "8", Correct is "9"

After fine-tuning with logic puzzles:
[reasoning_02] → ✅ IMPROVED (Fixed Answer)
  Fine-tuned says "9" ✓
```

**Lesson**: Delta analysis guides you to focus training data where it's needed most.

---

## Debugging Common Issues

### Issue 1: Mismatched IDs

**Error**:
```
ValueError: Mismatch IDs: factual_01 vs reasoning_01
```

**Cause**: `base.json` and `finetuned.json` have different prompts or are out of order.

**Fix**:
1. Check if Agent 2 (benchmark) crashed midway
2. Ensure both runs used the same `prompts.py`
3. Re-run benchmark: `python benchmark/run.py experiment-name`

---

### Issue 2: Similarity: 0.0

**Observation**: All similarity scores are 0.0 or very low.

**Possible Causes**:

1. **Wrong language**: Model outputs Chinese, prompts are English
   ```bash
   # Check responses in base.json and finetuned.json
   cat benchmark/results/base.json | jq '.[0].response'
   ```

2. **Empty responses**: Model not generating anything
   ```bash
   # Look for empty strings
   cat benchmark/results/finetuned.json | jq '.[] | select(.response == "")'
   ```

3. **Hallucination**: Model completely diverged from topic
   - This indicates severe overfitting or wrong training data

**Fix**: Check training data quality and alignment with prompts.

---

### Issue 3: All Neutral

**Observation**: Every assessment is "⚪ NEUTRAL (No Change)".

**Cause**: Model didn't learn anything (Experiment 1: Copycat Effect).

**Diagnosis**:
```bash
# Check training loss - did it decrease?
cat experiments/exp-001/metadata.json | jq .training.final_loss

# Check number of epochs and examples
cat experiments/exp-001/metadata.json | jq .hyperparameters.epochs
```

**Fix**:
- Increase epochs (3 → 5)
- Increase learning rate (2e-4 → 5e-4)
- Add more training examples
- Check if dataset loaded correctly

---

### Issue 4: Conflicting Assessments

**Observation**:
```
[factual_01] → ✅ IMPROVED (+2 keywords)
But looking at responses, the answer is now wrong!
```

**Cause**: Keywords triggered before ground truth was checked (shouldn't happen, but possible if metadata is malformed).

**Fix**: Verify prompt metadata has correct priority:

```python
# In prompts.py
{
    "id": "factual_01",
    "metadata": {
        "ground_truth": "Paris",  # THIS should be checked FIRST
        "keywords": ["France", "capital"]
    }
}
```

**How assessment works**: Ground truth has highest priority. If it exists, it short-circuits keyword checks.

---

## Advanced Topics

### Custom Assessment for Your Domain

Let's say you're building a **code generation** assistant. The default rules don't capture code quality. Here's how to add custom logic:

```python
def assess_code_improvement(delta: dict) -> str:
    """Custom assessment for code generation tasks."""

    base_text = delta["base_response"]
    ft_text = delta["finetuned_response"]

    # Check 1: Does it have code?
    base_has_code = "```" in base_text or "def " in base_text
    ft_has_code = "```" in ft_text or "def " in ft_text

    if not base_has_code and ft_has_code:
        return "✅ IMPROVED (Added Code Block)"

    # Check 2: Syntax valid?
    base_valid = check_python_syntax(base_text)
    ft_valid = check_python_syntax(ft_text)

    if not base_valid and ft_valid:
        return "✅ IMPROVED (Fixed Syntax)"

    if base_valid and not ft_valid:
        return "❌ REGRESSED (Broke Syntax)"

    # Check 3: Tests pass?
    base_tests = run_tests(base_text)
    ft_tests = run_tests(ft_text)

    if base_tests < ft_tests:
        return f"✅ IMPROVED (+{ft_tests - base_tests} tests passed)"

    # ... more checks
```

**Where to add this**: In `assess_improvement()`, add a check for `category == "code_generation"` and call your custom function.

---

### LLM-Based Assessment

For tasks where heuristics aren't enough (creative writing, complex reasoning), use an LLM as a judge.

```python
def llm_judge(base_resp, ft_resp, prompt, expected):
    """Use GPT-4 or Claude to judge which response is better."""

    judge_prompt = f"""
Compare these two responses to: "{prompt}"

Response A (Base Model):
{base_resp}

Response B (Fine-tuned Model):
{ft_resp}

Expected behavior: {expected}

Which response is better? Reply with ONLY:
- IMPROVED (B is better)
- REGRESSED (A is better)
- CHANGED (Different but unclear)
- UNCHANGED (Same quality)

Answer:"""

    # Call LLM API
    result = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": judge_prompt}]
    )

    return result.choices[0].message.content.strip()
```

**Pros**:
- More nuanced judgments
- Understands context and subtlety
- Can judge creative/subjective tasks

**Cons**:
- Slow (2-5 seconds per comparison)
- Costs money ($0.01+ per prompt)
- Non-deterministic (same input might get different assessment)

**When to use**: For final evaluation of your best 2-3 models, not during rapid iteration.

---

### Statistical Significance

If you run the same experiment twice, will you get the same improvement rate? Let's add confidence intervals:

```python
import numpy as np
from scipy import stats

def calculate_confidence_interval(deltas, confidence=0.95):
    """Calculate confidence interval for improvement rate."""

    improvements = [1 if "IMPROVED" in d["assessment"] else 0 for d in deltas]

    mean = np.mean(improvements)
    std_error = stats.sem(improvements)
    ci = stats.t.interval(confidence, len(improvements)-1,
                          loc=mean, scale=std_error)

    return mean, ci

# Usage
mean_improvement, (lower, upper) = calculate_confidence_interval(deltas)

print(f"Improvement rate: {mean_improvement*100:.1f}%")
print(f"95% CI: [{lower*100:.1f}%, {upper*100:.1f}%]")
```

**Interpretation**:
- If CI is wide (e.g., [20%, 80%]), your results are noisy. Run more test prompts.
- If CI is narrow (e.g., [55%, 65%]), you have high confidence.

---

## Integration Points

### Inputs

Agent 3 expects these files from Agent 2:

**benchmark/results/base.json**:
```json
[
  {
    "prompt_id": "factual_01",
    "category": "factual_qa",
    "prompt": "What is the capital of France?",
    "response": "The capital of France is Paris.",
    "metadata": {
      "ground_truth": "Paris",
      "keywords": [],
      "check": null
    }
  }
]
```

**benchmark/results/finetuned.json**:
```json
[
  {
    "prompt_id": "factual_01",
    "category": "factual_qa",
    "prompt": "What is the capital of France?",
    "response": "Paris is the capital city of France.",
    "metadata": {
      "ground_truth": "Paris",
      "keywords": [],
      "check": null
    }
  }
]
```

**Critical Requirements**:
- `prompt_id` must match between files
- `metadata` must include assessment criteria
- Both arrays must have same length

---

### Outputs

Agent 3 produces `benchmark/results/deltas.json` for Agent 4:

```json
[
  {
    "prompt_id": "factual_01",
    "prompt": "What is the capital of France?",
    "category": "factual_qa",
    "base_response": "The capital of France is Paris.",
    "finetuned_response": "Paris is the capital city of France.",
    "metadata": {
      "ground_truth": "Paris",
      "keywords": [],
      "check": null
    },
    "metrics": {
      "similarity": 0.82,
      "length_base": 33,
      "length_ft": 38,
      "length_delta": 5,
      "length_delta_pct": 15.2,
      "keywords_base": 0,
      "keywords_ft": 0
    },
    "assessment": "✅ PASS (Improved Explanation)"
  }
]
```

**What Agent 4 expects**:
- `assessment` field with emoji (✅/❌/⚠️/⚪/🔄)
- `metrics` dictionary with similarity and length
- `base_response` and `finetuned_response` for side-by-side display

---

## Success Criteria

Your Agent 3 implementation is complete when:

✅ `python benchmark/delta.py` runs in < 1 second
✅ `deltas.json` is valid JSON and matches expected schema
✅ Console output shows clear summary (e.g., "3 Improved | 1 Regressed")
✅ Ground truth checking correctly identifies fixed answers
✅ Keywords counting works for multi-faceted responses
✅ Custom checks validate domain-specific requirements
✅ Assessment priorities cascade correctly (ground truth > keywords > similarity)

---

## Key Takeaways

1. **Heuristics are powerful**: Fast, deterministic rules beat slow AI judgment for iteration.

2. **Priority matters**: Ground truth is king. Don't let keyword count override a wrong answer.

3. **Similarity alone is misleading**: High similarity can hide critical errors. Low similarity might be good (if the model fixed something).

4. **Domain-specific checks are essential**: Generic metrics miss domain nuances. Add custom logic for your use case.

5. **Delta analysis guides iteration**: It tells you exactly where to focus your next training data batch.

6. **Perfect is the enemy of good**: These rules aren't perfect AI evaluation, but they're good enough to guide rapid iteration. That's the point.

---

## Next Steps

1. **Run experiments**: Try the Copycat and Parrot experiments to see assessment in action.

2. **Add custom checks**: Extend `perform_custom_check()` for your domain.

3. **Visualize**: Agent 4 turns these metrics into beautiful HTML reports. Run it next!

4. **Iterate**: Use delta analysis to identify weak prompts, add training data, and iterate again.

---

**Remember**: The goal isn't perfect evaluation. The goal is **fast feedback** that guides you toward better models. Agent 3 gives you that feedback in <1 second. Use it, iterate, improve. 🚀
