# 🚀 Quick Start Guide

Get up and running with the DGX Fast Fine-tuning System in 10 minutes.

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- NVIDIA GPU (recommended, but CPU works too)
- 16GB+ RAM

## Installation

### 1. Clone and Setup

```bash
cd dgx-fast-iteration
pip install -r requirements.txt
```

### 2. Start Ollama

```bash
docker compose up -d
```

Wait ~30 seconds for Ollama to start, then pull the base model:

```bash
docker compose exec ollama ollama pull qwen2.5:0.5b
```

This downloads the base model (~300MB, takes 1-2 minutes).

### 3. Verify Installation

```bash
# Check Ollama is running
docker compose ps

# Check base model is available
docker compose exec ollama ollama list

# Should show: qwen2.5:0.5b
```

## Your First Iteration

### Run the Example

```bash
./iterate.sh exp-001 datasets/example-chatbot.json
```

This will:
1. Train on 20 chatbot examples (~3-5 minutes)
2. Export to Ollama (~30 seconds)
3. Run 10 benchmark prompts (~1 minute)
4. Generate HTML report (instant)

**Total time: ~5-7 minutes**

### View Results

```bash
# Open the HTML report
open benchmark/results/report-exp-001.html
```

You'll see:
- Summary statistics (improved, regressed, changed, similar)
- Side-by-side comparison of responses
- Metrics for each prompt

## Understanding Your First Results

### What to Look For

1. **Improved prompts** (green badges)
   - These prompts show clear improvement
   - Check if the improvements match your training data

2. **Regressed prompts** (red badges)
   - These prompts got worse
   - Common on first iteration (model is overfitting to training data)
   - You may need more diverse training examples

3. **Changed prompts** (yellow badges)
   - Response is different but not clearly better/worse
   - Review manually to decide if it's an improvement

4. **Similar prompts** (gray badges)
   - Model didn't change much for these
   - May need more training or different examples

### Typical First Iteration

With the example dataset, you'll typically see:
- 2-3 improved (greetings, questions from training data)
- 1-2 regressed (topics not in training data)
- 3-4 changed (style changes)
- 2-3 similar (no significant change)

This is normal! The model is learning your style but may overfit.

## Next Steps

### Iteration 2: Improve Training Data

Based on your results, create a better dataset:

```bash
# Copy example as template
cp datasets/example-chatbot.json datasets/my-iteration-2.json

# Edit to add:
# 1. Examples for prompts that regressed
# 2. More diverse examples
# 3. Edge cases you discovered

# Run iteration 2
./iterate.sh exp-002 datasets/my-iteration-2.json
```

### Compare Experiments

```bash
# View experiment log
cat experiments/log.json | python3 -m json.tool

# Shows all iterations with metrics
```

### Customize Benchmark Prompts

Edit `benchmark/prompts.py` to add domain-specific prompts:

```python
CUSTOM_PROMPTS = [
    {
        "id": "my_prompt",
        "category": "custom",
        "prompt": "Your test prompt here",
        "expected_behavior": "What you expect",
        "why": "Why this prompt matters"
    }
]
```

## Common Issues

### Training is Slow

- **Check GPU**: Run `nvidia-smi` to verify GPU is detected
- **Reduce batch size**: Add `--batch-size 2` to train.py call in iterate.sh
- **Use smaller dataset**: Start with 10-15 examples

### Ollama Connection Error

```bash
# Check Ollama is running
docker compose ps

# If not running, start it
docker compose up -d

# Check logs
docker compose logs ollama
```

### Model Quality is Poor

- **More training data**: Aim for 30-50 examples minimum
- **More epochs**: Edit iterate.sh, add `--epochs 5` to train.py
- **Better examples**: Ensure training examples match desired behavior

### Out of Memory

```bash
# Edit train.py, reduce batch size
--batch-size 2

# Or use gradient accumulation
--batch-size 2 --gradient-accumulation-steps 2
```

## Tips for Success

### 1. Start Small
- Use 10-15 examples for first iteration
- Get quick feedback
- Iterate rapidly

### 2. Focus on Quality
- Each training example should be high-quality
- Consistent format and style
- Representative of desired behavior

### 3. Track Everything
- The system logs every iteration
- Compare across iterations to see progress
- Look for patterns in what works

### 4. Iterate Fast
- Goal: 10 iterations in 2 hours
- Don't overthink each iteration
- Let the data guide you

### 5. Use Benchmark Prompts Wisely
- Add prompts that matter to your use case
- Cover edge cases and failure modes
- Update prompts as you discover issues

## Next Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design deep dive
- [agents/](agents/) - Per-agent implementation guides
- [README.md](../README.md) - Full documentation

## Getting Help

- Check experiment logs: `experiments/log.json`
- Review training metadata: `experiments/exp-001/metadata.json`
- View HTML reports: `benchmark/results/report-*.html`

Happy iterating! 🚀
