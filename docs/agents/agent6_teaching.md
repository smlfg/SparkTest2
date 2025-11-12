# Agent 6 Teaching Guide: Orchestration (The Conductor)

## What You Built

You didn't build a "Musician" (a component that does ML work), you built the **"Dirigent" (Conductor)**. Your code *produces* no ML, but it *manages* all of it.

This is **Orchestration** – the most important part of making a system reliable and usable.

### Your Deliverables

1. **`iterate.sh`** - The "One-Click Button"
   - Calls all 6 agents in sequence
   - Handles errors (stops if anything fails)
   - Times each step
   - Opens result automatically

2. **`experiments/log_experiment.py`** - The "Lab Notebook Writer"
   - Reads results from Agents 1 and 3
   - Calculates summary statistics
   - Appends to `experiments/log.json`
   - Enables cross-iteration comparison

3. **`experiments/log.json`** - The "Lab Notebook" (generated)
   - JSON file with every experiment
   - Compare configurations
   - Track improvement over time

---

## Core Teaching Concepts

### 1. Bash Scripting & `set -e`

**Why Bash?**
- Native to Linux (no dependencies)
- Perfect for calling other programs
- Simple syntax for automation
- Shell features (pipes, redirects, etc.)

**The Most Important Command: `set -e`**

```bash
set -e  # Exit Immediately on Error
```

This single line is **critical** for reliable automation.

#### Without `set -e` (DANGEROUS):

```bash
#!/bin/bash
# NO set -e

python train.py --dataset data.json  # FAILS (bad data)
./export.sh                           # RUNS (tries to export nothing!)
python benchmark/run.py               # RUNS (benchmarks nothing!)
# Result: Cascade of confusing errors
```

User sees: "Error: Model not found in Ollama"
Reality: Training failed 2 steps ago, but script kept going.

#### With `set -e` (SAFE):

```bash
#!/bin/bash
set -e  # Exit on error

python train.py --dataset data.json  # FAILS (bad data)
# SCRIPT STOPS HERE
# Never tries export, benchmark, etc.
```

User sees: "Error in train.py: Invalid dataset format"
Reality: Same as user sees. Clear error, clear location.

**Lesson**: Every automation script MUST start with `set -e`.

**When NOT to use `set -e`**:
- When you WANT to continue after errors
- When using conditional error handling (`if ! command; then ...`)
- When collecting multiple results (use `|| true` to ignore errors)

---

### 2. The "Lab Notebook" Pattern (`log.json`)

Scientific experiments are only valuable if you record them.

#### Why Log Everything?

Scenario: After 10 iterations, you ask yourself:
- "Was LoRA rank 8 or 16 better?"
- "Did 3 epochs or 5 epochs give better results?"
- "Which dataset produced the best model?"

Without logs: You remember "some were good, some bad" (useless)
With logs: Open `log.json`, compare scores, get answer in 10 seconds.

#### What to Log

Your `log_experiment.py` captures:

```json
{
  "name": "exp-001",
  "timestamp": "2024-01-15T10:30:00",
  "config": {
    "lora_rank": 8,
    "learning_rate": 0.0003,
    "epochs": 3
  },
  "performance": {
    "train_time": 180,
    "train_loss": 0.45
  },
  "summary": {
    "improved": 6,
    "regressed": 1,
    "score": 0.50  // (6-1)/10 = +50%
  }
}
```

Now you can:
- **Sort by score**: Find best experiment
- **Compare configs**: What hyperparameters worked?
- **Track trends**: Are we improving over time?

#### The "Score" Metric

```python
score = (improved - regressed) / total
```

Why this formula?
- Positive score = net improvement
- Negative score = net regression
- Range: -1.0 (all regressed) to +1.0 (all improved)
- Easy to compare: 0.5 > 0.2 = first experiment is better

**Alternative Metrics** (you could implement):
- Weighted score: `(2*improved - 3*regressed) / total` (penalize regressions more)
- Average similarity improvement
- Task-specific: Accuracy for classifier, BLEU for translation

---

### 3. UX (User Experience): The Auto-Open

The last command in `iterate.sh`:

```bash
xdg-open report.html  # Or 'open' on macOS
```

This seems trivial but is **psychologically crucial**.

#### The Psychology of Friction

**Without Auto-Open:**
1. User runs `./iterate.sh`
2. Script finishes
3. User thinks "Where's the report?"
4. User navigates to `benchmark/results/`
5. User finds `report.html`
6. User double-clicks
7. Report opens

Friction points: 4 steps, requires remembering path

**With Auto-Open:**
1. User runs `./iterate.sh`
2. Report pops up automatically

Friction points: 0 steps, instant gratification

**Result**: Users iterate 5-10x more often with auto-open because the feedback loop is immediate.

This is the difference between:
- "I'll try one iteration" (manual)
- "Let me try 10 different configs!" (automated + auto-open)

**Design Principle**: Eliminate every bit of friction in the iteration loop.

---

## Experiments to Try (Hands-On Learning)

### Experiment 1: Simulate a Training Failure

**Goal**: Prove that `set -e` stops the pipeline on errors.

1. Open `train.py`
2. Add this at the very end:
   ```python
   sys.exit(1)  # Simulate failure
   ```
3. Run:
   ```bash
   ./iterate.sh test-fail datasets/example-chatbot.json
   ```

**Expected Result**:
- Training runs
- Script prints "❌ Error" (or similar)
- Script **STOPS** - does NOT run export, benchmark, etc.

**Lesson**: `set -e` works! One failure stops the entire pipeline.

**Cleanup**: Remove the `sys.exit(1)` line.

---

### Experiment 2: Compare Multiple Experiments

**Goal**: Use the log notebook to find the best configuration.

1. Run 3 experiments with different configs:

   ```bash
   # Experiment 1: Default settings
   ./iterate.sh rank-8 datasets/example-chatbot.json

   # Experiment 2: Higher LoRA rank
   # Edit train.py: change LORA_R = 16
   ./iterate.sh rank-16 datasets/example-chatbot.json

   # Experiment 3: More epochs
   # Edit train.py: change back to LORA_R = 8, then add --epochs 5 in iterate.sh
   ./iterate.sh epochs-5 datasets/example-chatbot.json
   ```

2. View the log:
   ```bash
   cat experiments/log.json | python3 -m json.tool
   ```

3. Find the best:
   ```bash
   python3 << EOF
   import json
   log = json.load(open('experiments/log.json'))
   best = max(log, key=lambda x: x['summary']['score'])
   print(f"Best: {best['name']} (score: {best['summary']['score']:.2f})")
   print(f"Config: LoRA rank={best['config']['lora']['r']}, epochs={best['config']['training']['epochs']}")
   EOF
   ```

**Expected Result**:
- You'll see 3 entries in `log.json`
- Script prints which experiment had the highest score
- You now have **data-driven** answer to "which config is best?"

**Lesson**: The log notebook enables scientific iteration, not guesswork.

---

### Experiment 3: Break the Pipeline Intentionally

**Goal**: Understand dependency chains.

1. Run a normal iteration:
   ```bash
   ./iterate.sh exp-001 datasets/example-chatbot.json
   ```

2. Delete the benchmark results:
   ```bash
   rm benchmark/results/deltas.json
   ```

3. Try to run ONLY the visualization (without re-running benchmark):
   ```bash
   python benchmark/visualize.py
   ```

**Expected Result**:
- Script fails: "Error: deltas.json not found"

**Lesson**:
- Agent 4 (visualize) **depends** on Agent 3 (delta)
- Agent 3 depends on Agent 2 (benchmark)
- Agent 2 depends on Agent 5 (export)
- Agent 5 depends on Agent 1 (train)

This is why `iterate.sh` runs them in **exact order**.

---

## Integration Points

### Inputs (What Agent 6 Needs)

**From User:**
- Experiment name (e.g., `exp-001`)
- Dataset path (e.g., `datasets/example.json`)

**From Other Agents:**
- Agent 1: `experiments/{name}/metadata.json` (training config & results)
- Agent 3: `benchmark/results/deltas.json` (comparison results)
- Agent 4: `benchmark/results/report.html` (visual report)

### Outputs (What Agent 6 Produces)

**Primary:**
- `experiments/log.json` - The lab notebook

**Side Effects:**
- Opens browser with report
- Prints summary statistics
- Validates prerequisites (Ollama running, base model exists)

---

## Advanced Topics

### 1. Error Handling Patterns

**Simple (Current):**
```bash
set -e  # Stop on any error
```

**Advanced (With Cleanup):**
```bash
set -e
trap cleanup EXIT  # Run cleanup function on exit (success or failure)

cleanup() {
    # Remove temporary files
    rm -f /tmp/temp_model_*
    # Kill background processes
    # etc.
}
```

**Advanced (With Retries):**
```bash
# Retry a command up to 3 times
retry() {
    local n=1
    local max=3
    while true; do
        "$@" && break || {
            if [[ $n -lt $max ]]; then
                ((n++))
                echo "Command failed. Attempt $n/$max:"
            else
                echo "Command failed after $n attempts."
                return 1
            fi
        }
    done
}

retry python train.py --dataset data.json
```

### 2. Parallel Execution

Currently, agents run sequentially. But some steps could run in parallel:

**Sequential (Current):**
```bash
train.py       # 3 minutes
export.sh      # 30 seconds
benchmark.py   # 1 minute
```
Total: 4.5 minutes

**Parallel (Hypothetical):**
```bash
train.py &     # 3 minutes (background)
other_prep &   # 1 minute (background)
wait           # Wait for both
export.sh      # 30 seconds
benchmark.py   # 1 minute
```
Total: 3.5 minutes (but more complex)

**Tradeoff**: Parallelism saves time but adds complexity. For a 5-minute loop, the sequential approach is simpler and "good enough."

### 3. Configuration Files

Instead of editing `iterate.sh` to change hyperparameters, you could use a config file:

**`configs/experiment-002.yaml`:**
```yaml
experiment:
  name: exp-002
  dataset: datasets/example-chatbot.json

training:
  lora_rank: 16
  epochs: 5
  learning_rate: 0.0005

benchmark:
  prompts: custom_prompts
```

**`iterate.sh` (modified):**
```bash
CONFIG_FILE=$1
python train.py --config $CONFIG_FILE
```

**Benefit**: Easier to track what changed between experiments.

---

## Success Criteria

Your Agent 6 is complete if:

✅ **`iterate.sh` exists and is executable**
   - `chmod +x iterate.sh`

✅ **Running `./iterate.sh exp-001 datasets/example.json` completes all 6 steps**
   - No manual intervention needed

✅ **If train.py fails, iterate.sh stops immediately**
   - Doesn't try to run export, benchmark, etc.

✅ **`experiments/log.json` is created/updated after each run**
   - Can be parsed as valid JSON
   - Contains at least: name, config, summary, score

✅ **HTML report opens automatically in browser**
   - User sees results immediately

✅ **After 3 iterations, can identify best experiment from log**
   - `cat log.json` shows all 3 experiments
   - Scores can be compared

---

## Common Issues & Debugging

### Issue 1: "iterate.sh: Permission denied"

**Cause**: Script not executable

**Fix**:
```bash
chmod +x iterate.sh
```

### Issue 2: "Ollama: connection refused"

**Cause**: Ollama not running

**Fix**:
```bash
docker compose up -d
# Wait 30 seconds
docker compose ps  # Verify it's running
```

### Issue 3: Script continues after error

**Cause**: Missing `set -e`

**Fix**: Add `set -e` at top of script

### Issue 4: Report doesn't auto-open

**Cause**: Platform-specific command not found

**Fix**: Check logs, manually open:
```bash
open benchmark/results/report.html  # macOS
xdg-open benchmark/results/report.html  # Linux
start benchmark/results/report.html  # Windows
```

### Issue 5: "metadata.json not found"

**Cause**: Training failed but error wasn't caught

**Fix**:
1. Check `set -e` is present
2. Review training logs for actual error
3. Fix training issue, re-run

---

## Key Takeaways

### 1. Orchestration is Critical

ML systems aren't just about training models - they're about **workflows**.

- 80% of ML engineer time: Data prep, evaluation, iteration
- 20% of ML engineer time: Model architecture

Good orchestration multiplies your iteration speed by 10x.

### 2. `set -e` is Non-Negotiable

Every production automation script MUST handle errors properly.

Bad error handling = Silent failures = Wasted hours debugging

### 3. Logging Enables Learning

Without logs: "I think this config is better?"
With logs: "Config A scored 0.6, Config B scored 0.3, A is 2x better"

Data beats intuition.

### 4. UX Matters for Iteration Speed

Small UX improvements (auto-open report) make iteration addictive.

Addictive iteration = More experiments = Better models

### 5. Orchestration Patterns are Transferable

The patterns you learned here apply to ANY ML pipeline:
- Data processing pipeline
- Model training pipeline
- Model deployment pipeline
- A/B testing pipeline

Learn once, apply everywhere.

---

## Next Steps

### Immediate

1. Run `./iterate.sh exp-001 datasets/example-chatbot.json`
2. Verify report opens automatically
3. Check `experiments/log.json` was created

### Experiment

1. Try the 3 experiments above
2. Modify `iterate.sh` to add timing logs
3. Add your own validation checks

### Advanced

1. Add retry logic for network-dependent steps
2. Implement parallel execution for independent steps
3. Create a `compare_experiments.py` tool
4. Add Slack/email notifications on completion

---

## Philosophy

> "A scientist without a lab notebook is just guessing."

Your `iterate.sh` + `log_experiment.py` system IS your lab notebook.

Every experiment is recorded. Every configuration is tracked. Every result is comparable.

This transforms random exploration into **systematic scientific iteration**.

That's the difference between hobbyist ML and professional ML engineering.

---

**Congratulations! You've built the orchestration layer that makes rapid iteration possible. This is the foundation of every production ML system.**

🎓 You now understand:
- Bash scripting for automation
- Error handling with `set -e`
- Experiment logging and comparison
- UX design for iteration speed
- The orchestration mindset

**Next**: Read other agent guides to understand what each component does, then start iterating! 🚀
