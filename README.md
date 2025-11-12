# 🚀 DGX Spark Fast Fine-tuning Iteration Lab

**Goal**: Complete one fine-tuning iteration (train → test → analyze) in **5 minutes or less**.

## What This Does

This system helps you rapidly experiment with fine-tuning small language models:
- Train a model in 3-5 minutes (Qwen2.5-0.5B with Unsloth)
- Automatically benchmark against base model
- Get visual delta analysis
- Iterate 10+ times in 2 hours

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama (for inference)
docker compose up -d

# 3. Run a complete iteration
./iterate.sh exp-001 datasets/example-chatbot.json

# 4. View results
open benchmark/results/report.html
```

## System Architecture

```
[Training] → [Export] → [Benchmark] → [Analysis] → [Visualization] → [Tracking]
  Agent 1      Agent 5     Agent 2       Agent 3       Agent 4         Agent 6
  3-5 min      30 sec      1 min         instant       instant         instant
```

## Components

### Agent 1: Fast Training (`train.py`)
- Uses Unsloth for 2x speedup
- Trains Qwen2.5-0.5B with LoRA
- Outputs to `experiments/{name}/lora/`

### Agent 2: Benchmark Suite (`benchmark/run.py`)
- Runs 10 standard prompts
- Tests both base and fine-tuned models
- Outputs JSON results

### Agent 3: Delta Calculator (`benchmark/delta.py`)
- Compares base vs fine-tuned responses
- Calculates metrics: length, similarity, keywords
- Flags improvements/regressions

### Agent 4: Visualization (`benchmark/visualize.py`)
- Generates HTML report
- Side-by-side comparison
- Color-coded deltas

### Agent 5: Infrastructure (`scripts/export_to_ollama.sh`)
- Merges LoRA weights
- Converts to GGUF format
- Imports to Ollama

### Agent 6: Orchestration (`iterate.sh`)
- Runs full pipeline
- Tracks experiments
- Compares iterations

## File Structure

```
dgx-fast-iteration/
├── train.py                    # Agent 1: Training
├── iterate.sh                  # Agent 6: Full iteration
├── docker-compose.yml          # Ollama container
├── requirements.txt            # Python dependencies
│
├── datasets/                   # Training data
│   ├── example-chatbot.json
│   └── example-classifier.json
│
├── benchmark/                  # Testing & analysis
│   ├── prompts.py             # Test prompts
│   ├── run.py                 # Benchmark runner
│   ├── delta.py               # Comparison logic
│   ├── visualize.py           # HTML generator
│   └── results/               # Output files
│
├── experiments/                # Training outputs
│   ├── exp-001/
│   │   ├── lora/             # Trained model
│   │   └── metadata.json     # Training info
│   └── log.json              # Experiment history
│
├── scripts/
│   └── export_to_ollama.sh   # Model export pipeline
│
└── docs/                      # Learning materials
    ├── ARCHITECTURE.md
    ├── QUICKSTART.md
    └── agents/               # Per-agent guides
```

## Hardware Requirements

- **Tested on**: NVIDIA DGX Spark (Blackwell GB10)
- **Minimum**: 16GB RAM, 8GB VRAM (or CPU inference)
- **Recommended**: 32GB+ RAM, 16GB+ VRAM

## Tech Stack

- **Model**: Qwen2.5-0.5B-Instruct (500M params)
- **Training**: Unsloth, TRL, LoRA (rank 8), 4-bit quantization
- **Inference**: Ollama (CPU or GPU)
- **Format**: GGUF for portability

## Usage Examples

### Basic Iteration
```bash
./iterate.sh exp-001 datasets/example-chatbot.json
```

### Custom Training Parameters
```bash
python train.py \
  --dataset datasets/example-chatbot.json \
  --output experiments/exp-002 \
  --epochs 5 \
  --lr 3e-4
```

### Benchmark Only
```bash
python benchmark/run.py \
  --base qwen2.5:0.5b \
  --finetuned exp-001 \
  --output benchmark/results/
```

### Compare Experiments
```bash
python benchmark/visualize.py \
  --experiments exp-001 exp-002 exp-003 \
  --output benchmark/results/comparison.html
```

## Learning Resources

Each agent includes teaching materials:
- **Why** we made certain design choices
- **How** the code works (inline comments)
- **When** to modify parameters

See `docs/agents/` for detailed guides.

## Success Criteria

✅ Full iteration completes in <10 minutes
✅ HTML report shows clear deltas
✅ Can run 10 iterations in 2 hours
✅ Code is readable and well-commented

## Philosophy

**Speed over perfection**: This is for rapid experimentation, not production.
**Learn by doing**: Code teaches concepts, not just implements features.
**Scientific method**: Systematic comparison, reproducible results.

## Troubleshooting

### Training is slow
- Check GPU is detected: `nvidia-smi`
- Ensure Unsloth is installed correctly
- Try smaller batch size

### Ollama errors
- Verify container is running: `docker compose ps`
- Check model list: `docker compose exec ollama ollama list`
- Restart: `docker compose restart`

### Out of memory
- Reduce batch size in `train.py`
- Use CPU inference: Set `OLLAMA_USE_CPU=1`

## Contributing

This is a learning project. Feel free to:
- Add new benchmark prompts
- Improve visualization
- Optimize training speed
- Enhance documentation

## License

MIT License - Use for learning and experimentation.

---

**Built with**: Python, PyTorch, Unsloth, Ollama, Docker
**Optimized for**: DGX Spark, but works on consumer hardware
