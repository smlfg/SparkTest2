# Agent 2 Teaching Guide: Understanding Systematic Evaluation

## What You Built

You built a **reproducible testing framework** for ML models. This is the scientific method applied to fine-tuning.

### Before vs After

**Before (Manual Testing)**:
```
Student: "The model seems better... maybe?"
Professor: "How do you know?"
Student: "I tried a few prompts and it felt better?"
Professor: "Show me data."
Student: "..."
```

**After (Your System)**:
```
Student: "The model improved on 7/10 prompts."
Professor: "Show me."
Student: *Opens HTML report with side-by-side comparison*
Professor: "Nice. Which prompts regressed?"
Student: "Prompts 3 and 8. I think because..."
```

**You enabled data-driven iteration.**

---

## Key Concepts

### 1. Why 10 Prompts?

**The Trade-off**:
```
More prompts = Better coverage BUT slower iteration
Fewer prompts = Faster BUT might miss regressions

10 prompts = Sweet spot:
- Covers major categories (QA, translation, code, etc.)
- Runs in ~1 minute
- Enough signal to see patterns
```

**Test Your Understanding**:
- Run benchmark with 5 prompts (subset)
- Run benchmark with 20 prompts (double)
- Compare: Does 20 prompts find issues 10 didn't?
- Is the extra time worth it?

### 2. Ground Truth vs Keywords

**Ground Truth** = Objectively correct answer
```python
{
    "prompt": "Was ist 2+2?",
    "ground_truth": "4"
}
# Easy to check: Is "4" in response? Yes/No
```

**Keywords** = Acceptable terms (more flexible)
```python
{
    "prompt": "Liste Programmiersprachen",
    "keywords": ["Python", "Java", "JavaScript"]
}
# Check: Are at least 3 keywords present?
```

**When to use which**:
- Ground truth: Factual questions, translations, math
- Keywords: Creative tasks, explanations, lists

### 3. Latency Tracking

```python
start_time = time.time()
response = query_ollama(model, prompt)
elapsed = time.time() - start_time
```

**Why track latency?**
- Fine-tuning shouldn't slow down inference
- If fine-tuned model is 2x slower → Problem!
- Usually: latency similar (±10%)

**Test Your Understanding**:
Compare latency: base vs fine-tuned
- Are they similar?
- If fine-tuned is slower, why? (Larger model? Different config?)

### 4. JSON Output Format

**Why JSON?**
```python
# Easy to process programmatically
with open("base.json") as f:
    results = json.load(f)

# Easy to analyze
avg_latency = sum(r["metadata"]["latency_seconds"] for r in results) / len(results)

# Easy for Agent 3 to consume
for base, ft in zip(base_results, finetuned_results):
    compare(base["response"], ft["response"])
```

**Alternative formats and why JSON wins**:
- CSV: Can't handle nested data (metadata)
- TXT: Hard to parse
- YAML: Less universal than JSON
- JSON: ✅ Universal, structured, easy to work with

---

## Experiments to Deepen Understanding

### Experiment 1: Prompt Sensitivity

**Question**: Do small changes in prompts affect results?

```python
# Original prompt
"Was ist die Hauptstadt von Deutschland?"

# Variations
"Nenne die Hauptstadt von Deutschland"
"Deutschland's Hauptstadt ist?"
"Hauptstadt Deutschland?"

# Run benchmark with each variant
# Compare: How consistent are responses?
```

**Learning**: Prompt engineering matters!

### Experiment 2: Temperature Effects

**Question**: Does temperature affect benchmark consistency?

```python
# Modify query_ollama():
options = {
    "temperature": 0.0,  # Deterministic
    # vs
    "temperature": 1.0,  # Creative
}

# Run benchmark 3 times with temp=0.0
# Run benchmark 3 times with temp=1.0
# Compare: Which is more consistent?
```

**Expected**: temp=0.0 gives identical results each run.

### Experiment 3: Model Size

**Question**: Do bigger models always perform better?

```bash
# Benchmark multiple models
python benchmark/run.py --base qwen2.5:0.5b --finetuned exp-001
python benchmark/run.py --base qwen2.5:1.5b --finetuned exp-001
python benchmark/run.py --base qwen2.5:3b --finetuned exp-001

# Compare: Quality vs Latency trade-off
```

---

## Debugging Guide

### Issue: "Model not found in Ollama"

**Symptoms**:
```
❌ Fine-tuned model 'exp-001' not found in Ollama
```

**Cause**: Agent 5 hasn't exported the model yet.

**Solution**:
```bash
# Check available models
curl http://localhost:11434/api/tags

# If model missing, run Agent 5 export
./scripts/export_to_ollama.sh experiments/exp-001/lora exp-001
```

### Issue: Responses are empty

**Symptoms**:
```json
{
  "response": "",
  "metadata": {...}
}
```

**Causes**:
1. Model crashed/out of memory
2. Prompt is malformed
3. Timeout too short

**Debug**:
```bash
# Test manually
curl -X POST http://localhost:11434/api/generate \
  -d '{
    "model": "exp-001",
    "prompt": "Test",
    "stream": false
  }'

# Check Ollama logs
docker logs ollama
```

### Issue: Benchmark is slow (>5 minutes)

**Expected**: 1-2 minutes for 10 prompts × 2 models

**Causes**:
1. Model is too large (not 0.5B)
2. num_predict is too high (>200 tokens)
3. Network latency (Ollama on different machine?)

**Solution**:
```python
# Reduce max tokens
"num_predict": 100,  # Instead of 200

# Or reduce prompts temporarily
BENCHMARK_PROMPTS = BENCHMARK_PROMPTS[:5]  # Test with 5 prompts
```

---

## Integration with Other Agents

### What Agent 1 provides (inputs):
- Trained model (LoRA adapters)

### What Agent 5 provides (inputs):
- Model exported to Ollama
- Model name (e.g., "exp-001")

### What you provide (outputs):
```
benchmark/results/base.json       → Agent 3 reads this
benchmark/results/finetuned.json  → Agent 3 reads this
```

### What Agent 3 expects:
- Both JSON files exist
- Same number of prompts in each
- Same prompt order (prompt_id matches)

---

## Next Steps

After your benchmark runs:
1. **Agent 3** calculates deltas (response differences)
2. **Agent 4** visualizes deltas (HTML report)
3. **User** sees which prompts improved/regressed

**Your contribution**: Objective measurement. No more "feels better", now it's "7/10 prompts improved".

---

## Self-Check Questions

Can you answer these without looking?

1. Why 10 prompts instead of 50?
2. What's the difference between ground_truth and keywords?
3. Why save results as JSON?
4. What happens if Agent 5 didn't export the model?
5. How would you add an 11th prompt?

<details>
<summary>Answers</summary>

1. Trade-off: 10 is fast (~1min) yet covers diverse categories
2. ground_truth = exact answer, keywords = flexible matching
3. JSON is structured, universal, easy to parse programmatically
4. Benchmark fails with "model not found" error
5. Add dict to BENCHMARK_PROMPTS list with required fields
</details>

If you can answer 4/5: ✅ You understand Agent 2's work!

---

## Understanding the Code Flow

### Import Phase
```python
from prompts import BENCHMARK_PROMPTS
# This triggers:
# 1. Load BENCHMARK_PROMPTS list
# 2. Run _validate_prompts()
# 3. Print "✅ Loaded 10 benchmark prompts"
```

### Execution Phase
```python
# 1. Parse command line arguments
args = parser.parse_args()

# 2. Check models exist in Ollama
response = requests.get(f"{args.ollama_url}/api/tags")

# 3. Run benchmark on base model
base_results = run_benchmark_on_model(args.base)
# For each of 10 prompts:
#   - query_ollama(model, prompt)
#   - Record response + metadata
#   - Save to results list

# 4. Save base results to JSON
json.dump(base_results, f, indent=2, ensure_ascii=False)

# 5. Wait 5 seconds (be nice to GPU)
time.sleep(5)

# 6. Run benchmark on fine-tuned model
finetuned_results = run_benchmark_on_model(args.finetuned)

# 7. Save fine-tuned results to JSON
json.dump(finetuned_results, f, indent=2, ensure_ascii=False)
```

### Why the 5-second wait?
```python
time.sleep(5)
```
- Give GPU time to cool down
- Clear VRAM between runs
- Prevents throttling/crashes
- Minimal time cost (5s vs minutes)

---

## Advanced: Customizing for Your Needs

### Add a New Prompt Category

```python
# In prompts.py, add:
{
    "id": "your_category_test",
    "prompt": "Your test prompt here",
    "category": "your_category",
    "ground_truth": "Expected answer",  # OR
    "keywords": ["keyword1", "keyword2"],  # OR
    "check": "custom_function_name",
}
```

### Test Different Temperature Settings

```python
# In run.py, modify query_ollama():
def query_ollama(model_name: str, prompt: str, temperature: float = 0.7):
    payload = {
        ...
        "options": {
            "temperature": temperature,  # Now configurable!
            ...
        }
    }
```

### Add Concurrent Requests (Advanced)

```python
import concurrent.futures

def run_benchmark_on_model_parallel(model_name: str) -> list:
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(query_ollama, model_name, p["prompt"])
            for p in BENCHMARK_PROMPTS
        ]
        results = [f.result() for f in futures]
    return results

# WARNING: Only use if Ollama can handle concurrent requests!
# 3 workers = 3x faster BUT higher GPU memory usage
```

---

## Real-World Usage Examples

### Example 1: Quick Sanity Check
```bash
# Test if export worked
python benchmark/run.py --finetuned exp-001

# Expected: 2 minutes, 10/10 prompts succeed
# If any fail: Check Agent 5 export logs
```

### Example 2: Compare Multiple Experiments
```bash
# Benchmark experiment 1
python benchmark/run.py --finetuned exp-001
mv benchmark/results/finetuned.json benchmark/results/exp-001.json

# Benchmark experiment 2
python benchmark/run.py --finetuned exp-002
mv benchmark/results/finetuned.json benchmark/results/exp-002.json

# Agent 3 can now compare all three:
# - base.json
# - exp-001.json
# - exp-002.json
```

### Example 3: Test Different Base Models
```bash
# Compare against larger base model
python benchmark/run.py \
  --base qwen2.5:1.5b \
  --finetuned exp-001

# Question: Does fine-tuning a 0.5B model beat a 1.5B base model?
```

---

## Performance Optimization Tips

### If benchmarks are too slow:

1. **Reduce max tokens**:
```python
"num_predict": 100,  # Instead of 200
```

2. **Use fewer prompts during development**:
```python
# In prompts.py
BENCHMARK_PROMPTS_DEV = BENCHMARK_PROMPTS[:5]  # First 5 only
```

3. **Lower temperature** (faster inference):
```python
"temperature": 0.1,  # More deterministic = faster
```

### If you need more coverage:

1. **Add domain-specific prompts**:
```python
# For a medical chatbot:
{
    "id": "medical_symptom",
    "prompt": "Liste Symptome von Grippe",
    "category": "medical",
    "keywords": ["Fieber", "Husten", "Kopfschmerzen"],
}
```

2. **Test edge cases**:
```python
# Empty prompt
{"id": "edge_empty", "prompt": "", "category": "edge"}

# Very long prompt
{"id": "edge_long", "prompt": "A" * 1000, "category": "edge"}
```

---

## Conclusion

You've built the foundation for **scientific ML evaluation**:
- ✅ Systematic (same prompts every time)
- ✅ Automated (no manual work)
- ✅ Fast (1-2 minutes)
- ✅ Measurable (JSON output for analysis)

**Next**: Agent 3 will turn these raw results into actionable insights (deltas).

**Your role in the bigger picture**: Without systematic benchmarking, fine-tuning is just guessing. You made it scientific.
