# 🚀 DGX Spark Fast Fine-tuning Iteration Lab

**Build → Benchmark → Analyze in 5 minutes**

## What is this?

A rapid experimentation system for fine-tuning small language models (Qwen2.5-0.5B) with instant feedback loops. Train a model, benchmark it against the base model, see what changed, and iterate again - all in under 10 minutes.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama (for inference)
docker-compose up -d

# 3. Pull base model
docker exec ollama ollama pull qwen2.5:0.5b

# 4. Run your first iteration
./iterate.sh exp-001 datasets/example-chatbot.json

# 5. View results
open benchmark/results/report.html
```

## System Architecture

```
[Training] → [Export] → [Benchmark] → [Delta Analysis] → [Report]
   3 min       30 sec      1 min          instant          instant
```

**Total time: ~5 minutes per iteration**

## What Each Component Does

### 🏋️ Agent 1: Fast Training (`train.py`)
- Uses Unsloth (2x faster than standard HuggingFace)
- Trains Qwen2.5-0.5B with LoRA adapters
- 4-bit quantization for speed
- Outputs: `experiments/{name}/lora/`

### 🚀 Agent 5: Infrastructure (`docker-compose.yml`, `scripts/export_to_ollama.sh`)
- Runs Ollama in Docker
- Converts LoRA → GGUF → Ollama model
- Makes models instantly testable

### 🧪 Agent 2: Benchmark Suite (`benchmark/run.py`)
- Runs 10 standard prompts
- Tests both base and fine-tuned models
- Outputs: `benchmark/results/{base,finetuned}.json`

### 📊 Agent 3: Delta Calculator (`benchmark/delta.py`)
- Compares responses
- Calculates metrics: length, similarity, keywords
- Assesses: improved/regressed/changed
- Outputs: `benchmark/results/deltas.json`

### 🎨 Agent 4: Visualization (`benchmark/visualize.py`)
- Generates HTML report
- Side-by-side comparison
- Color-coded improvements/regressions
- Outputs: `benchmark/results/report.html`

### 🎯 Agent 6: Orchestration (`iterate.sh`)
- One-command full iteration
- Tracks experiment history
- Cross-iteration comparison
- Outputs: `experiments/log.json`

## File Structure

```
dgx-fast-iteration/
├── train.py                    # Agent 1: Training
├── iterate.sh                  # Agent 6: Full workflow
├── docker-compose.yml          # Agent 5: Ollama
├── requirements.txt            # Dependencies
│
├── datasets/
│   ├── example-chatbot.json    # Sample: chatbot training
│   └── example-classifier.json # Sample: classification
│
├── benchmark/
│   ├── prompts.py              # 10 test prompts
│   ├── run.py                  # Benchmark runner
│   ├── delta.py                # Delta calculator
│   ├── visualize.py            # HTML generator
│   └── results/                # Output directory
│
├── experiments/
│   ├── exp-001/                # Each experiment tracked
│   │   ├── lora/               # Trained model
│   │   └── metadata.json       # Training config
│   └── log.json                # All experiments history
│
├── scripts/
│   └── export_to_ollama.sh     # LoRA → Ollama pipeline
│
└── docs/
    ├── ARCHITECTURE.md         # System design
    ├── QUICKSTART.md           # Getting started
    └── agents/                 # Teaching materials
```

## Hardware Requirements

**Designed for**: NVIDIA DGX Spark
- 128GB UMA
- Blackwell GB10 GPU

**Can also run on**:
- Any NVIDIA GPU with 16GB+ VRAM
- CPU-only (slower, ~15 min iterations)

## Learning Path

This system teaches you:
1. **LoRA Fine-tuning**: Practical implementation with Unsloth
2. **Model Evaluation**: Systematic before/after comparison
3. **Experiment Tracking**: Scientific method for ML
4. **Rapid Iteration**: Fast feedback loops
5. **System Integration**: Building end-to-end ML pipelines

Each component includes teaching comments explaining "why" not just "what".

## Example Workflow

```bash
# Iteration 1: Train on customer support data
./iterate.sh customer-support datasets/support-v1.json
# → View report.html: model is too formal

# Iteration 2: Add casual examples
./iterate.sh customer-support-casual datasets/support-v2.json
# → View report.html: better! But missing product knowledge

# Iteration 3: Add product FAQs
./iterate.sh customer-support-final datasets/support-v3.json
# → View report.html: perfect!

# Compare all iterations
python benchmark/compare_experiments.py
```

## Configuration

Edit `train.py` to adjust:
- Learning rate (default: 2e-4)
- Epochs (default: 3)
- LoRA rank (default: 8)
- Batch size (default: 4)

Edit `benchmark/prompts.py` to customize test prompts for your domain.

## Troubleshooting

**Training is slow**
- Check GPU is being used: `nvidia-smi`
- Verify Unsloth installed correctly
- Try smaller model: Qwen2.5-0.5B → Qwen2.5-0.25B

**Ollama export fails**
- Ensure Docker is running: `docker ps`
- Check Ollama logs: `docker logs ollama`
- Try manual export: `./scripts/export_to_ollama.sh exp-001`

**Benchmark shows no improvements**
- Check if training data matches test prompts
- Increase epochs (3 → 5)
- Try higher learning rate (2e-4 → 5e-4)

## Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System design and integration
- **[QUICKSTART.md](docs/QUICKSTART.md)**: Step-by-step setup
- **[agents/](docs/agents/)**: Deep dives on each component

## Contributing

This is an educational project. Feel free to:
- Add new benchmark prompts
- Experiment with different models
- Improve visualization
- Add new metrics to delta analysis

## License

MIT - Use for learning, research, or production

---

**Goal**: Make fine-tuning feel like compiling code - fast feedback, quick iteration, constant improvement.

Let's iterate! 🚀
