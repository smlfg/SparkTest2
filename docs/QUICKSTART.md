# 🚀 Quick Start Guide

Get your first fine-tuning iteration running in 10 minutes.

---

## Prerequisites

### Hardware
- NVIDIA DGX Spark (or compatible GPU system)
- 16GB+ GPU VRAM recommended
- 32GB+ system RAM

### Software
- Python 3.9+
- Docker & Docker Compose
- CUDA 11.8+ or 12.1+
- Git

### Check Your Setup

```bash
# Check Python
python3 --version  # Should be 3.9+

# Check CUDA
nvidia-smi  # Should show your GPU

# Check Docker
docker --version
docker-compose --version
```

---

## Step 1: Installation (2 minutes)

### Clone & Navigate

```bash
cd /path/to/dgx-fast-iteration
```

### Install Python Dependencies

```bash
# Install PyTorch first (if not already installed on DGX)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Install all dependencies
pip install -r requirements.txt

# Verify Unsloth installed correctly
python -c "from unsloth import FastLanguageModel; print('✅ Unsloth ready!')"
```

**Troubleshooting**:
- If Unsloth fails: `pip install --upgrade pip packaging ninja` then retry
- If bitsandbytes fails: `pip install bitsandbytes --no-build-isolation`

---

## Step 2: Start Ollama (30 seconds)

Ollama handles model inference for benchmarking.

```bash
# Start Ollama container
docker-compose up -d

# Wait a few seconds for startup
sleep 5

# Verify it's running
curl http://localhost:11434/api/tags

# Should return: {"models":[]}
```

### Pull Base Model

```bash
# Download Qwen2.5-0.5B (takes ~1 minute, only do once)
docker-compose exec ollama ollama pull qwen2.5:0.5b

# Verify
docker-compose exec ollama ollama list
# Should show: qwen2.5:0.5b
```

---

## Step 3: Your First Iteration (5-10 minutes)

### Option A: One Command (Recommended)

```bash
./iterate.sh exp-001 datasets/example-chatbot.json
```

This runs the complete pipeline:
1. Training (3-5 min)
2. Export (30 sec)
3. Benchmark (1 min)
4. Analysis (instant)
5. Report generation (instant)

When done, open `benchmark/results/report.html` to see results!

### Option B: Step-by-Step (For Learning)

```bash
# 1. Train the model
python train.py exp-001 datasets/example-chatbot.json --epochs 3

# 2. Export to Ollama
./scripts/export_to_ollama.sh exp-001

# 3. Run benchmark
python benchmark/run.py exp-001

# 4. Calculate deltas
python benchmark/delta.py

# 5. Generate visualization
python benchmark/visualize.py

# 6. View report
open benchmark/results/report.html
```

---

## Step 4: Understand the Results (1 minute)

Open `benchmark/results/report.html` in your browser.

### What to Look For

**Summary Dashboard** (top):
- **Improved**: Responses got better (more keywords, better quality)
- **Regressed**: Responses got worse
- **Changed**: Different but not clearly better/worse
- **Unchanged**: Nearly identical to base model

**Individual Prompts**:
- **Left column**: Base model (qwen2.5:0.5b)
- **Right column**: Your fine-tuned model
- **Metrics**: Keyword match, length change, similarity score

### Example Interpretation

```
Improved: 6 prompts
Regressed: 1 prompt
Changed: 2 prompts
Unchanged: 1 prompt
```

**Interpretation**: Fine-tuning had positive impact on 60% of prompts. Review the regressed prompt to understand what went wrong.

---

## Step 5: Your Second Iteration (Optional)

Now try a different dataset or configuration!

### Try Different Dataset

```bash
./iterate.sh exp-002 datasets/example-classifier.json
```

### Try More Epochs

```bash
./iterate.sh exp-003 datasets/example-chatbot.json 5
# Uses 5 epochs instead of default 3
```

### Compare Results

```bash
# View experiment log
cat experiments/log.json | python -m json.tool

# Or use Python
python -c "
import json
with open('experiments/log.json') as f:
    log = json.load(f)
    for exp in log:
        r = exp['results']
        print(f\"{exp['experiment_name']}: {r['improved']}↑ {r['regressed']}↓\")
"
```

---

## Common Issues

### Issue: Training is slow

**Cause**: GPU not being used or insufficient VRAM

**Solution**:
```bash
# Check GPU usage during training
nvidia-smi -l 1

# If GPU not used, check CUDA installation
python -c "import torch; print(torch.cuda.is_available())"

# Reduce batch size if OOM
# Edit train.py: Change BATCH_SIZE = 4 to BATCH_SIZE = 2
```

### Issue: Ollama connection failed

**Cause**: Ollama container not running

**Solution**:
```bash
# Check container status
docker-compose ps

# Restart Ollama
docker-compose restart ollama

# View logs
docker-compose logs -f ollama
```

### Issue: Model not found in Ollama

**Cause**: Export didn't complete or model name mismatch

**Solution**:
```bash
# List available models
docker-compose exec ollama ollama list

# Re-run export
./scripts/export_to_ollama.sh exp-001

# Check experiment directory exists
ls experiments/exp-001/
```

### Issue: Benchmark fails

**Cause**: Base model not pulled or Ollama not ready

**Solution**:
```bash
# Pull base model
docker-compose exec ollama ollama pull qwen2.5:0.5b

# Wait for Ollama to be ready
curl http://localhost:11434/api/tags

# Run benchmark again
python benchmark/run.py exp-001
```

---

## Next Steps

### 1. Create Your Own Dataset

Create `datasets/my-data.json`:

```json
[
  {
    "instruction": "Your question or task here",
    "output": "Expected model response here"
  },
  {
    "instruction": "Another example",
    "output": "Another response"
  }
]
```

**Tips**:
- Start with 20-50 examples
- Use consistent formatting
- Cover diverse scenarios
- Include edge cases

### 2. Customize Benchmark Prompts

Edit `benchmark/prompts.py` to test your specific use case.

### 3. Experiment with Parameters

In `train.py`, try adjusting:
- `LORA_RANK`: 4 (faster) vs 16 (better quality)
- `BATCH_SIZE`: 2 (less memory) vs 8 (faster training)
- `LEARNING_RATE`: 1e-4 (conservative) vs 5e-4 (aggressive)
- `EPOCHS`: 1 (quick test) vs 10 (thorough training)

### 4. Learn the Architecture

Read `docs/ARCHITECTURE.md` to understand how everything fits together.

### 5. Deep Dive into Agents

Read individual agent teaching docs in `docs/agents/` to master each component.

---

## Cheat Sheet

```bash
# Start everything
docker-compose up -d
docker-compose exec ollama ollama pull qwen2.5:0.5b

# Run iteration
./iterate.sh <name> <dataset> [epochs]

# View results
open benchmark/results/report.html

# Check experiments
cat experiments/log.json

# Stop everything
docker-compose down
```

---

## Getting Help

1. **Check logs**:
   ```bash
   # Training logs
   cat experiments/<name>/logs/*.log

   # Ollama logs
   docker-compose logs ollama

   # Benchmark results
   cat benchmark/results/*.json
   ```

2. **Verify each step**:
   ```bash
   # After training
   ls experiments/<name>/lora/

   # After export
   docker-compose exec ollama ollama list | grep <name>

   # After benchmark
   ls benchmark/results/
   ```

3. **Read teaching materials**:
   - `docs/agents/` for component details
   - `docs/ARCHITECTURE.md` for system design

---

**You're ready!** Start experimenting with `./iterate.sh` and iterate quickly! 🚀
