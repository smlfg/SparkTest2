# 🚀 Parallel Coding Test System

**Test 10 coding prompts in 3-5 seconds (instead of 20+ seconds sequential)**

---

## What This Is

A **fast, parallel testing system** that runs 10 Python coding prompts simultaneously to measure model improvement after each training epoch.

```
Sequential:  10 prompts × 2s each = 20 seconds
Parallel:    10 prompts at once  = 3-5 seconds (4-6x faster!)
```

---

## Quick Start

### 1. Install Dependencies
```bash
pip install aiohttp
```

### 2. Test the System
```bash
python benchmark/test_parallel.py
```

**Expected output**:
```
TESTING PARALLEL EXECUTION
============================================================
Running 10 coding prompts in parallel...

🔄 Starte parallele Ausführung...
💡 Alle 10 Prompts werden GLEICHZEITIG gesendet
✅ Alle Prompts fertig in 4.2 Sekunden
→ Speedup: 4.8x schneller!

VERDICT
============================================================
✅ Parallel execution working (< 10 seconds)
✅ All 10 files created
✅ 10/10 responses have content
✅ Good speedup (4.8x)

✅ ALL TESTS PASSED - System ready for use!
```

### 3. Use in Training (Agent 1 Integration)
```python
from benchmark.test_both_models import run_tests_for_epoch

# After each epoch:
run_tests_for_epoch(
    base_model="qwen2.5:0.5b",
    finetuned_model="exp-001-epoch-1",
    epoch=1
)
```

---

## System Components

```
benchmark/
├── coding_prompts.py       # 10 coding test prompts
├── parallel_runner.py      # Async execution engine
├── test_both_models.py     # Integration helper
└── test_parallel.py        # Testing script

results/
├── epoch_0_baseline/
│   └── base_01_fizzbuzz.txt  (10 files)
├── epoch_1/
│   ├── base_01_fizzbuzz.txt
│   └── finetuned_01_fizzbuzz.txt  (20 files)
└── epoch_2/...
```

---

## The 10 Coding Tests

| ID | Prompt | Category | Difficulty |
|----|--------|----------|------------|
| `fizzbuzz` | FizzBuzz implementation | algorithms | easy |
| `palindrome` | Check if string is palindrome | strings | easy |
| `reverse_list` | Reverse list without `reverse()` | data_structures | easy |
| `factorial` | Recursive factorial | recursion | medium |
| `fibonacci` | Recursive Fibonacci | recursion | medium |
| `merge_dicts` | Merge two dictionaries | data_structures | easy |
| `count_words` | Word frequency counter | strings | medium |
| `list_comprehension` | Squares 1-10 with list comprehension | pythonic | easy |
| `safe_divide` | Division with error handling | error_handling | medium |
| `read_file` | Read file with context manager | io | medium |

**Why these?**
- Representative of real coding tasks
- Test different Python concepts
- Suitable for 0.5B model
- Easy to validate (keyword checking)

---

## Usage Examples

### Test Baseline (Before Training)
```bash
python benchmark/test_both_models.py baseline
```

Creates: `results/epoch_0_baseline/base_*.txt`

### Test After Epoch (Automated)
```python
# In Agent 1 training loop:
from benchmark.test_both_models import run_tests_for_epoch

for epoch in range(3):
    # ... training code ...

    # Test after epoch
    run_tests_for_epoch(
        base_model="qwen2.5:0.5b",
        finetuned_model=f"exp-001-epoch-{epoch+1}",
        epoch=epoch+1
    )
```

### Test Both Models (Manual)
```bash
python benchmark/test_both_models.py both \
    --base qwen2.5:0.5b \
    --finetuned exp-001 \
    --epoch 1
```

---

## How It Works

### 1. **Parallel Execution** (async/await)
```python
# Sequential (SLOW):
for prompt in prompts:
    result = query_ollama(prompt)  # Wait 2s
# Total: 10 × 2s = 20s

# Parallel (FAST):
tasks = [query_ollama(p) for p in prompts]  # Start all
results = await asyncio.gather(*tasks)       # Wait for all
# Total: max(all) ≈ 4s
```

### 2. **Individual .txt Files** (not JSON)
Each response is saved as a separate file:
```
results/epoch_1/finetuned_01_fizzbuzz.txt:

======================================================================
CODING TEST RESPONSE
======================================================================

Prompt ID:   fizzbuzz
Model:       finetuned
Epoch:       1
Category:    algorithms
Difficulty:  easy
...

----------------------------------------------------------------------
RESPONSE:
----------------------------------------------------------------------
def fizzbuzz():
    for i in range(1, 101):
        if i % 15 == 0:
            print("FizzBuzz")
        elif i % 3 == 0:
            print("Fizz")
        ...
```

**Why individual files?**
- Easy to `diff` between epochs
- Easy to inspect manually
- Agent 3 can process one by one
- Clear organization

### 3. **Quick Analysis** (immediate feedback)
```
✅ fizzbuzz: 5/5 keywords found
✅ palindrome: 4/4 keywords found
⚠️ factorial: 2/4 keywords found
```

---

## Integration with Other Agents

### Agent 1 (Training)
```python
# After each epoch:
from benchmark.test_both_models import run_tests_for_epoch

run_tests_for_epoch(
    base_model="qwen2.5:0.5b",
    finetuned_model=exported_model_name,
    epoch=current_epoch
)
```

### Agent 3 (Delta Analysis)
```python
# Compare files:
base_file = "results/epoch_1/base_01_fizzbuzz.txt"
ft_file = "results/epoch_1/finetuned_01_fizzbuzz.txt"

# Extract response sections
# Calculate diff
# Determine: improved, regressed, or unchanged
```

### Agent 5 (Export)
- Must export model to Ollama before testing
- Model name format: `exp-001-epoch-N`

---

## Performance

**On DGX Spark with Qwen2.5-0.5B:**
```
Sequential:  ~20 seconds
Parallel:    ~3-5 seconds
Speedup:     4-6x

File I/O:    < 1 second
Total:       < 10 seconds ✅
```

**Why is it fast?**
- Ollama GPU can handle multiple requests concurrently
- asyncio + aiohttp for non-blocking I/O
- No waiting between requests

---

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'aiohttp'`
```bash
pip install aiohttp
```

### Error: Responses are empty
**Cause**: Ollama not running or model not loaded

**Fix**:
```bash
docker ps  # Check Ollama running
curl http://localhost:11434/api/tags  # Check models
```

### Slow Performance (>10 seconds)
**Possible causes**:
1. GPU throttling
2. Model too large (not 0.5B)
3. Ollama overwhelmed

**Debug**:
```bash
nvidia-smi  # Check GPU usage
docker logs ollama  # Check Ollama logs
```

### Files not created
**Cause**: Permission issues or path problems

**Fix**:
```bash
# Ensure results/ directory exists
mkdir -p results

# Check permissions
ls -ld results
```

---

## Advanced Usage

### Custom Prompts
Edit `benchmark/coding_prompts.py`:
```python
CODING_TEST_PROMPTS.append({
    "id": "my_test",
    "prompt": "Your custom Python coding task",
    "category": "custom",
    "difficulty": "medium",
    "expected_keywords": ["def", "return"],
    "expected_concepts": ["functions"],
})
```

### Different Timeout
```python
runner = CodingTestRunner()

# Modify timeout in parallel_runner.py:
async def query_ollama_async(..., timeout: int = 120):  # 120s instead of 60s
```

### Test Subset of Prompts
```python
# In coding_prompts.py:
CODING_TEST_PROMPTS_SUBSET = CODING_TEST_PROMPTS[:5]  # First 5 only

# In parallel_runner.py:
self.prompts = CODING_TEST_PROMPTS_SUBSET
```

---

## Comparison: Sequential vs Parallel

### System 1: benchmark/run.py (Sequential)
- **Purpose**: Compare base vs fine-tuned (German prompts)
- **Mode**: Sequential (one at a time)
- **Time**: 1-2 minutes
- **Output**: JSON files
- **Use case**: End-to-end benchmark

### System 2: parallel_runner.py (Parallel)
- **Purpose**: Test coding ability after each epoch
- **Mode**: Parallel (all at once)
- **Time**: 3-5 seconds
- **Output**: Individual .txt files
- **Use case**: Fast iteration feedback

**Both are needed!** Different purposes, complementary systems.

---

## Testing Checklist

Before using in production:

- [ ] `pip install aiohttp` completed
- [ ] `python benchmark/test_parallel.py` passes all tests
- [ ] Files created in `results/epoch_0_baseline/`
- [ ] Files have non-empty responses
- [ ] Total time < 10 seconds
- [ ] Speedup > 2x

---

## Next Steps

1. **Test the system**: `python benchmark/test_parallel.py`
2. **Run baseline**: `python benchmark/test_both_models.py baseline`
3. **Wait for Agent 1**: Training system will call this automatically
4. **Check results**: `ls -lh results/epoch_*/`
5. **Agent 3**: Will compare results and show improvements

---

**Built for speed! Test 10 prompts in the time it takes to make coffee ☕**
