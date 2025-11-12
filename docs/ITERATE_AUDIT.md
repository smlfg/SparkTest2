# iterate.sh Audit Report - Making It Bulletproof

## Executive Summary

Agent 6 (`iterate.sh`) is the **single point of failure** for the entire system. If this script fails, nothing works. This audit identifies critical issues and provides a hardened version.

---

## Issues Found in Original Version

### 🔴 Critical Issues

1. **Uses `python` instead of `python3`**
   - **Risk**: On systems where `python` points to Python 2, script will fail
   - **Impact**: Complete system failure
   - **Fix**: Explicitly use `python3` and verify version ≥ 3.8

2. **No file existence checks**
   - **Risk**: Scripts called before verifying they exist
   - **Impact**: Cryptic "file not found" errors
   - **Fix**: Check all required files exist before pipeline starts

3. **No executable permission checks**
   - **Risk**: Bash scripts called without execute permission
   - **Impact**: "Permission denied" errors
   - **Fix**: Auto-fix or warn about missing permissions

### 🟡 Medium Issues

4. **Relative path assumptions**
   - **Risk**: Script fails if run from different directory
   - **Impact**: "File not found" for all components
   - **Fix**: Use `$SCRIPT_DIR` to work from any directory

5. **No Python dependency checks**
   - **Risk**: Training fails 3 minutes in due to missing package
   - **Impact**: Wasted time, unclear error
   - **Fix**: Check critical packages upfront

6. **No dataset validation**
   - **Risk**: Invalid JSON dataset causes training failure
   - **Impact**: Wasted 3+ minutes before error
   - **Fix**: Validate JSON before starting pipeline

### 🟢 Minor Issues

7. **No Docker/Ollama health check**
   - **Risk**: Benchmark fails if Ollama crashed mid-pipeline
   - **Impact**: Partial failure, unclear state
   - **Fix**: Verify Ollama responds before benchmark step

8. **Missing timing breakdown**
   - **Risk**: Can't identify bottlenecks
   - **Impact**: No optimization guidance
   - **Fix**: Show per-step timing at end

---

## Comparison: Original vs Bulletproof

| Feature | Original | Bulletproof | Improvement |
|---------|----------|-------------|-------------|
| Python command | `python` | `python3` (detected) | ✅ Python 2/3 safety |
| Version check | ❌ None | ✅ Requires 3.8+ | ✅ Clear error if old Python |
| File checks | ❌ None | ✅ All files validated | ✅ Fail fast with clear list |
| Path handling | ⚠️ Relative | ✅ Absolute via `$SCRIPT_DIR` | ✅ Works from any directory |
| Permission checks | ❌ None | ✅ Auto-fix or warn | ✅ No "permission denied" surprises |
| Dependency checks | ❌ None | ✅ Checks torch, transformers, etc. | ✅ Clear error with pip command |
| Dataset validation | ❌ None | ✅ JSON syntax check | ✅ Saves 3+ minutes on invalid data |
| Ollama health | ⚠️ Basic | ✅ Auto-start + model pull | ✅ Self-healing |
| Error messages | ⚠️ Generic | ✅ Specific + suggestions | ✅ User knows exactly what to fix |
| Timing breakdown | ❌ Total only | ✅ Per-step + total | ✅ Identify bottlenecks |
| set -e | ✅ Yes | ✅ Yes + set -u | ✅ Catch undefined variables too |
| Experiment validation | ❌ None | ✅ Name format + overwrite warning | ✅ Prevent accidents |

---

## Detailed Improvements

### 1. Python Detection & Validation

**Original:**
```bash
python train.py --dataset "$DATASET_PATH" --output "$EXPERIMENT_DIR"
```

**Problem**: What if `python` is Python 2? Or doesn't exist?

**Bulletproof:**
```bash
# Detect Python 3
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Check if python is Python 3
    PYTHON_VERSION=$(python --version 2>&1 | grep -oP '(?<=Python )\d+')
    if [ "$PYTHON_VERSION" -ge 3 ]; then
        PYTHON_CMD="python"
    else
        echo "❌ Error: Python 3 required, but only Python 2 found"
        exit 1
    fi
else
    echo "❌ Error: Python not found"
    echo "Install: sudo apt install python3"
    exit 1
fi

# Verify version ≥ 3.8
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
# ... validation logic ...

$PYTHON_CMD train.py --dataset "$DATASET_PATH" --output "$EXPERIMENT_DIR"
```

**Result**: Clear error with installation instructions, not cryptic failure.

---

### 2. File Existence Checks

**Original:**
```bash
python train.py --dataset "$DATASET_PATH" --output "$EXPERIMENT_DIR"
./scripts/export_to_ollama.sh "$EXPERIMENT_DIR" "$EXPERIMENT_NAME"
python benchmark/run.py --base "$BASE_MODEL" --finetuned "$EXPERIMENT_NAME"
```

**Problem**: If `train.py` is missing, user gets generic "file not found" after waiting for prerequisites.

**Bulletproof:**
```bash
REQUIRED_FILES=(
    "train.py"
    "scripts/export_to_ollama.sh"
    "benchmark/prompts.py"
    "benchmark/run.py"
    "benchmark/delta.py"
    "benchmark/visualize.py"
    "experiments/log_experiment.py"
)

MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "  ❌ Missing: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo "❌ Error: $MISSING_FILES required file(s) missing"
    exit 1
fi
```

**Result**: Immediate failure with **list of all missing files**, not one-by-one discovery.

---

### 3. Path Handling

**Original:**
```bash
#!/bin/bash
set -e

python train.py --dataset "$DATASET_PATH" --output "$EXPERIMENT_DIR"
```

**Problem**: If you run `../iterate.sh exp-001 dataset.json` from a subdirectory, it will fail because `train.py` is not in the current directory.

**Bulletproof:**
```bash
#!/bin/bash
set -e

# Get directory where THIS script lives
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to script directory
cd "$SCRIPT_DIR" || {
    echo "❌ Error: Cannot change to script directory: $SCRIPT_DIR"
    exit 1
}

python3 train.py --dataset "$DATASET_PATH" --output "$EXPERIMENT_DIR"
```

**Result**: Script works from **any directory**, even `/tmp` or `~`.

---

### 4. Dependency Checks

**Original:**
```bash
# (no checks)
python train.py --dataset "$DATASET_PATH" --output "$EXPERIMENT_DIR"
```

**Problem**: Training runs for 3 minutes, then fails with `ModuleNotFoundError: No module named 'unsloth'`.

**Bulletproof:**
```bash
CRITICAL_PACKAGES=("torch" "transformers" "requests" "rich")

for package in "${CRITICAL_PACKAGES[@]}"; do
    if ! python3 -c "import $package" &> /dev/null; then
        echo "  ❌ Missing: $package"
        MISSING_PACKAGES=$((MISSING_PACKAGES + 1))
    fi
done

if [ $MISSING_PACKAGES -gt 0 ]; then
    echo "❌ Error: $MISSING_PACKAGES required package(s) missing"
    echo "Install: pip install -r requirements.txt"
    exit 1
fi
```

**Result**: Failure in **5 seconds**, not 3 minutes. User knows exactly what to install.

---

### 5. Dataset Validation

**Original:**
```bash
if [ ! -f "$DATASET_PATH" ]; then
    echo "Error: Dataset not found: $DATASET_PATH"
    exit 1
fi

python train.py --dataset "$DATASET_PATH" --output "$EXPERIMENT_DIR"
```

**Problem**: Dataset exists but has invalid JSON → training fails after loading model (~1 minute wasted).

**Bulletproof:**
```bash
# Check file exists
if [ ! -f "$DATASET_PATH" ]; then
    echo "❌ Error: Dataset not found: $DATASET_PATH"
    ls -1 datasets/*.json  # Show available datasets
    exit 1
fi

# Check JSON is valid
if ! python3 -c "import json; json.load(open('$DATASET_PATH'))" &> /dev/null; then
    echo "❌ Error: Invalid JSON in dataset: $DATASET_PATH"
    exit 1
fi
```

**Result**: Instant feedback, not wasted time.

---

### 6. Self-Healing Ollama

**Original:**
```bash
if ! docker compose exec -T ollama ollama list &> /dev/null; then
    echo "Error: Ollama is not running"
    echo "Start it with: docker compose up -d"
    exit 1
fi
```

**Problem**: User has to manually run command, then re-run script.

**Bulletproof:**
```bash
if ! docker compose exec -T ollama ollama list &> /dev/null; then
    echo "⚠️  Ollama is not running. Starting..."
    docker compose up -d || {
        echo "❌ Error: Failed to start Ollama"
        exit 1
    }
    echo "Waiting 10 seconds for Ollama to start..."
    sleep 10
fi

# Also auto-pull base model if missing
if ! docker compose exec -T ollama ollama list | grep -q "$BASE_MODEL"; then
    echo "⚠️  Base model not found: ${BASE_MODEL}"
    echo "Pulling model (this may take 1-2 minutes)..."
    docker compose exec -T ollama ollama pull "$BASE_MODEL"
fi
```

**Result**: Script **self-heals**. User doesn't need to intervene.

---

### 7. Timing Breakdown

**Original:**
```bash
TOTAL_TIME=$(($(date +%s) - START_TIME))
MINUTES=$((TOTAL_TIME / 60))
SECONDS=$((TOTAL_TIME % 60))

echo "Total time: ${MINUTES}m ${SECONDS}s"
```

**Problem**: Can't see where time is spent. Is training slow? Export? Benchmark?

**Bulletproof:**
```bash
echo "⏱️  Timing Breakdown:"
echo "  Training:       ${TRAIN_TIME}s"
echo "  Export:         ${EXPORT_TIME}s"
echo "  Benchmark:      ${BENCHMARK_TIME}s"
echo "  Delta Analysis: ${DELTA_TIME}s"
echo "  Visualization:  ${VISUALIZE_TIME}s"
echo "  Logging:        ${LOG_TIME}s"
echo "  Total:          ${MINUTES}m ${SECONDS}s"
```

**Result**: See at a glance which step is the bottleneck.

---

### 8. Error Handling with `set -u`

**Original:**
```bash
set -e
```

**Problem**: Typos in variable names go unnoticed until they cause issues.

**Bulletproof:**
```bash
set -e  # Exit on error
set -u  # Exit on undefined variable
```

**Example:**
```bash
# Typo: EXPEIRMENT_NAME instead of EXPERIMENT_NAME
python train.py --output "experiments/$EXPEIRMENT_NAME"
```

With `set -u`: **Immediate error**: "EXPEIRMENT_NAME: unbound variable"
Without `set -u`: Creates directory `experiments/` (empty string), confusing error later.

---

## Testing the Bulletproof Version

### Test 1: Missing File

```bash
# Simulate missing train.py
mv train.py train.py.bak
./iterate-robust.sh exp-001 datasets/example.json

# Expected output:
# ❌ Missing: train.py
# ❌ Error: 1 required file(s) missing

# Restore
mv train.py.bak train.py
```

### Test 2: Invalid Dataset

```bash
# Create invalid JSON
echo "{ broken json" > datasets/broken.json
./iterate-robust.sh exp-001 datasets/broken.json

# Expected output:
# ❌ Error: Invalid JSON in dataset: datasets/broken.json
```

### Test 3: Missing Python Package

```bash
# Temporarily rename package (simulate missing)
pip uninstall -y rich
./iterate-robust.sh exp-001 datasets/example.json

# Expected output:
# ❌ Missing: rich
# ❌ Error: 1 required package(s) missing
# Install: pip install -r requirements.txt

# Restore
pip install rich
```

### Test 4: Run from Different Directory

```bash
cd /tmp
/home/user/SparkTest2/iterate-robust.sh exp-001 /home/user/SparkTest2/datasets/example.json

# Expected: Works correctly (original would fail)
```

---

## Migration Guide

### Option 1: Replace Original (Recommended)

```bash
# Backup original
cp iterate.sh iterate-original.sh

# Replace with bulletproof version
cp iterate-robust.sh iterate.sh

# Test
./iterate.sh exp-test datasets/example-chatbot.json
```

### Option 2: Use Side-by-Side

```bash
# Keep both versions
# Use original for quick runs (less checks = faster)
./iterate.sh exp-001 datasets/example.json

# Use bulletproof for important runs or debugging
./iterate-robust.sh exp-001 datasets/example.json
```

---

## Checklist for Custom Modifications

If you modify `iterate.sh`, ensure:

- [ ] `set -e` is present (fail fast)
- [ ] `set -u` is present (catch typos)
- [ ] All Python calls use `$PYTHON_CMD`, not hardcoded `python`
- [ ] All file paths are validated before use
- [ ] Error messages include suggestions for fixing
- [ ] New dependencies are added to prerequisite checks
- [ ] Timing is tracked for new steps
- [ ] Script works when called from any directory

---

## Performance Impact

**Bulletproof overhead**: ~5-10 seconds (one-time checks at start)

| Check | Time |
|-------|------|
| Python detection | ~0.5s |
| File existence (7 files) | ~0.1s |
| Dependency checks (4 packages) | ~2-3s |
| JSON validation | ~0.1s |
| Ollama health check | ~1s |
| **Total overhead** | **~4-5s** |

**Tradeoff**: 5 seconds of checks vs. 3+ minutes of wasted training time on error.

**Verdict**: Worth it.

---

## Summary

### What Was Fixed

✅ Python 2/3 compatibility issues
✅ Missing file detection (fail fast with clear list)
✅ Path handling (works from any directory)
✅ Missing dependency detection (before training starts)
✅ Invalid dataset detection (immediate feedback)
✅ Self-healing Ollama (auto-start + model pull)
✅ Better error messages (with fix suggestions)
✅ Timing breakdown (identify bottlenecks)
✅ Undefined variable protection (`set -u`)
✅ Experiment name validation (prevent bad names)
✅ Overwrite protection (warn before replacing experiment)

### Result

**Original `iterate.sh`**:
- Works... if everything is perfect
- Cryptic errors on issues
- Wasted time on preventable failures

**Bulletproof `iterate-robust.sh`**:
- Works even when things go wrong
- Clear errors with fix suggestions
- Fails in 5 seconds, not 3 minutes
- Self-heals common issues

---

## Recommendation

**For production use**: Use `iterate-robust.sh` as the default

**For development**: Original is fine if you know the system well

**For teaching**: Use bulletproof version to show **robustness patterns**

---

## Questions?

**Q: Is the bulletproof version slower?**
A: ~5 seconds slower at start. Saves 3+ minutes on errors.

**Q: Can I skip some checks?**
A: Yes, comment out sections you don't need. But `set -e`, `set -u`, and Python detection should stay.

**Q: What if I want even more checks?**
A: Add checks for:
- GPU availability (`nvidia-smi`)
- Disk space (`df -h`)
- Memory available (`free -h`)
- Network connectivity (for model downloads)

**Q: Should I always use the robust version?**
A: Yes, unless you're actively developing the system and running it 100+ times per day (then overhead matters).

---

**Conclusion**: Agent 6 is too critical to be fragile. The bulletproof version ensures the system **fails fast with clear errors**, not slow cryptic failures.
