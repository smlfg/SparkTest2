# Quick Start Guide

Get your first fine-tuning iteration running in 15 minutes!

## Prerequisites

### Hardware
- **Recommended**: NVIDIA GPU with 16GB+ VRAM (DGX Spark, A100, etc.)
- **Minimum**: 16GB RAM, can run on CPU (slower)

### Software
- Linux (Ubuntu 20.04+ recommended)
- Python 3.10+
- Docker & Docker Compose
- NVIDIA drivers + CUDA (if using GPU)
- Git

---

## Step 1: Clone and Setup (5 minutes)

### 1.1 Clone Repository
```bash
cd ~
git clone <your-repo-url> dgx-fast-iteration
cd dgx-fast-iteration
```

### 1.2 Install Python Dependencies
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Note**: Unsloth installation may take 5-10 minutes.

### 1.3 Verify GPU (if available)
```bash
nvidia-smi
```

You should see your GPU listed. If not, check NVIDIA driver installation.

### 1.4 Start Ollama
```bash
# Start Ollama container
docker-compose up -d

# Check it's running
docker ps | grep ollama

# Pull base model (this may take a few minutes)
docker exec ollama ollama pull qwen2.5:0.5b
```

**Expected output**:
```
pulling manifest
pulling 8a4e0... 100%
pulling 1234... 100%
success
```

---

## Step 2: Run Your First Iteration (10 minutes)

### 2.1 Check Example Dataset
```bash
# View the example dataset
cat datasets/example-chatbot.json
```

You should see 10 chat examples in JSON format.

### 2.2 Run Full Iteration
```bash
./iterate.sh exp-001 datasets/example-chatbot.json
```

**What happens**:
1. ⏱️ **Training** (3-5 min): Trains Qwen2.5-0.5B with LoRA
2. 🚀 **Export** (30 sec): Converts to Ollama model
3. 🧪 **Benchmark** (1 min): Tests 10 prompts on both models
4. 📊 **Delta** (<5 sec): Calculates improvements
5. 🎨 **Report** (<5 sec): Generates HTML report
6. 📝 **Log** (<5 sec): Records experiment

### 2.3 View Results
```bash
# Open HTML report (on desktop)
xdg-open benchmark/results/report.html

# Or on server, view in terminal
python3 -m http.server 8000 &
# Then open browser to: http://your-server:8000/benchmark/results/report.html
```

**What to look for**:
- ✅ How many prompts improved?
- ❌ Any regressions?
- 📈 Average similarity score
- 🎯 Specific prompt improvements

---

## Step 3: Test Your Fine-Tuned Model

### 3.1 Interactive Testing
```bash
docker exec -it ollama ollama run exp-001
```

Now you can chat with your fine-tuned model!

```
>>> Hello! How are you?
[Model response]

>>> Can you explain machine learning?
[Model response]

>>> /bye  # Exit
```

### 3.2 Single Prompt Test
```bash
docker exec ollama ollama run exp-001 "What's the capital of France?"
```

### 3.3 Compare with Base Model
```bash
# Base model
docker exec ollama ollama run qwen2.5:0.5b "Your prompt"

# Fine-tuned model
docker exec ollama ollama run exp-001 "Your prompt"
```

---

## Step 4: Run Second Iteration

### 4.1 Analyze First Iteration
Look at your HTML report:
- Which prompts didn't improve?
- What patterns do you see?
- What training examples might help?

### 4.2 Create Improved Dataset
```bash
cp datasets/example-chatbot.json datasets/my-improved-data.json
# Edit my-improved-data.json with your improvements
```

### 4.3 Run Second Iteration
```bash
./iterate.sh exp-002 datasets/my-improved-data.json
```

### 4.4 Compare Experiments
```bash
# View experiment log
cat experiments/log.json | python3 -m json.tool
```

Compare:
- Improvement rates
- Training times
- Which experiment performed better

---

## Common Workflows

### Workflow 1: Quick Test
Test if system works with minimal data:
```bash
# Use first 3 examples only
head -n 15 datasets/example-chatbot.json > datasets/quick-test.json
./iterate.sh quick-test datasets/quick-test.json
```

### Workflow 2: Hyperparameter Tuning
Try different learning rates:
```bash
./iterate.sh exp-lr-1e4 datasets/example-chatbot.json --lr 1e-4
./iterate.sh exp-lr-2e4 datasets/example-chatbot.json --lr 2e-4
./iterate.sh exp-lr-5e4 datasets/example-chatbot.json --lr 5e-4
```

Compare reports to find best learning rate.

### Workflow 3: Domain Adaptation
Fine-tune for your specific use case:

1. **Create domain dataset**:
```bash
# Example: Customer support
cat > datasets/customer-support.json <<EOF
[
  {
    "messages": [
      {"role": "system", "content": "You are a helpful customer support agent."},
      {"role": "user", "content": "How do I reset my password?"},
      {"role": "assistant", "content": "I'd be happy to help! Here's how to reset your password:\n1. Go to the login page\n2. Click 'Forgot Password'\n3. Enter your email\n4. Check your email for reset link\n5. Follow instructions in email\n\nIf you don't receive the email within 5 minutes, please check your spam folder or contact us directly."}
    ]
  }
  // Add 10-20 more examples...
]
EOF
```

2. **Customize benchmark prompts**:
Edit `benchmark/prompts.py` to include domain-specific tests.

3. **Run iteration**:
```bash
./iterate.sh customer-support-v1 datasets/customer-support.json
```

4. **Iterate based on results**:
Look at which prompts didn't improve, add more training examples for those areas.

---

## Troubleshooting

### Issue: "Dataset not found"
**Solution**:
```bash
# Check file exists
ls -lh datasets/

# Check file format (should be valid JSON)
python3 -c "import json; json.load(open('datasets/example-chatbot.json'))"
```

### Issue: "Ollama is not running"
**Solution**:
```bash
# Start Ollama
docker-compose up -d

# Wait a few seconds
sleep 5

# Verify
docker ps | grep ollama
```

### Issue: Training is very slow
**Solutions**:

1. **Check GPU is being used**:
```bash
# During training, run:
watch nvidia-smi

# Look for Python process using GPU memory
```

2. **Reduce batch size**:
```bash
# Edit iterate.sh, change:
--batch-size 2  # Instead of 4
```

3. **Reduce sequence length**:
```bash
# Edit iterate.sh, change:
--max-seq-length 1024  # Instead of 2048
```

### Issue: "CUDA out of memory"
**Solutions**:

1. **Enable gradient checkpointing** (already on by default)

2. **Reduce batch size**:
```bash
python3 train.py \
    --name test \
    --dataset datasets/example-chatbot.json \
    --batch-size 1
```

3. **Use smaller model**:
```bash
# Edit train.py, change model to:
model_name="unsloth/Qwen2.5-0.25B"  # Even smaller
```

### Issue: Export to Ollama fails
**Solution**:
```bash
# Check disk space
df -h

# Need at least 3 GB free

# Manual export:
./scripts/export_to_ollama.sh exp-001
```

### Issue: Benchmark shows no improvements
**Possible causes**:

1. **Training data doesn't match test prompts**
   - Solution: Edit `benchmark/prompts.py` to match your domain

2. **Not enough training**
   - Solution: Increase epochs or learning rate

3. **Model already knows this**
   - Solution: Test with more specific/novel knowledge

4. **Overfitting**
   - Solution: Add more diverse examples

---

## Best Practices

### Dataset Creation
✅ **Do**:
- Start with 10-20 high-quality examples
- Cover diverse aspects of your task
- Use consistent formatting
- Include edge cases

❌ **Don't**:
- Use thousands of examples initially (iterate!)
- Include contradictory examples
- Make examples too similar
- Skip system message (sets behavior)

### Iteration Strategy
1. **First iteration**: Establish baseline
   - Use small dataset (10-20 examples)
   - Default hyperparameters
   - Focus on getting pipeline working

2. **Second iteration**: Target weaknesses
   - Analyze first report
   - Add examples for regressed prompts
   - Keep what worked

3. **Third+ iterations**: Refine
   - Tune hyperparameters if needed
   - Expand to more examples
   - Test edge cases

### Experiment Naming
Use descriptive names that indicate:
- Purpose: `customer-support-v1`
- Iteration: `chatbot-improved-v3`
- Experiment: `tune-lr-5e4`

Avoid:
- Generic: `test`, `exp-1`
- Ambiguous: `final`, `last-one`

### Tracking Progress
```bash
# Keep notes in experiments directory
echo "Focused on improving technical explanations" > experiments/exp-002/notes.txt

# Tag successful experiments in git
git tag -a exp-customer-support-v3 -m "Best customer support model so far"

# Review experiment log regularly
cat experiments/log.json | jq '.[] | {name: .experiment_name, improvement: .results.improvement_rate}'
```

---

## Next Steps

### Learn More
1. **Architecture**: Read `docs/ARCHITECTURE.md` for system design
2. **Agent Details**: Check `docs/agents/` for deep dives
3. **Advanced Usage**: Experiment with different models and techniques

### Customize
1. **Your Domain**: Create custom datasets and prompts
2. **Hyperparameters**: Tune for your hardware and use case
3. **Visualization**: Modify HTML report styling
4. **Assessment**: Customize delta calculation logic

### Share
1. **Export models**: Share trained LoRA adapters
2. **Reports**: Share HTML reports with team
3. **Datasets**: Contribute example datasets for common domains
4. **Improvements**: Submit PRs with enhancements

---

## Quick Reference

### Essential Commands

```bash
# Start system
docker-compose up -d
source venv/bin/activate

# Run iteration
./iterate.sh <name> <dataset>

# Test model
docker exec -it ollama ollama run <name>

# View experiments
cat experiments/log.json | python3 -m json.tool

# Stop system
docker-compose down
deactivate
```

### File Locations

```
datasets/               # Training data
experiments/           # Trained models and logs
  ├── {name}/
  │   ├── lora/       # LoRA adapters
  │   └── metadata.json
  └── log.json        # All experiments
benchmark/
  ├── prompts.py      # Test prompts (customize here!)
  └── results/
      ├── base.json
      ├── finetuned.json
      ├── deltas.json
      └── report.html # Main output!
```

### Useful Scripts

```bash
# Individual agents (for debugging)
python3 train.py --name test --dataset data.json
./scripts/export_to_ollama.sh test
python3 benchmark/run.py test
python3 benchmark/delta.py
python3 benchmark/visualize.py

# Quick checks
docker exec ollama ollama list  # List models
docker logs ollama              # Ollama logs
nvidia-smi                      # GPU status
```

---

## Success Checklist

After completing this guide, you should be able to:

- [ ] Run full iteration in <10 minutes
- [ ] View HTML report showing improvements
- [ ] Test fine-tuned model interactively
- [ ] Create custom training datasets
- [ ] Run multiple iterations and compare
- [ ] Understand which prompts improved/regressed
- [ ] Customize benchmark prompts for your domain

If you can do all of the above, you're ready to start serious experimentation!

---

## Getting Help

**Something not working?**
1. Check troubleshooting section above
2. Review `docs/ARCHITECTURE.md` for system details
3. Look at agent teaching docs in `docs/agents/`
4. Open an issue on GitHub with:
   - What you tried
   - Error messages
   - System info (`python --version`, `nvidia-smi`)

**Want to learn more?**
- Each Python file has extensive teaching comments
- Read the agent-specific guides in `docs/agents/`
- Experiment! The system is designed for safe iteration

---

Happy iterating! 🚀
