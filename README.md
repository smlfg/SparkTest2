# 🚀 DGX Spark Fast Fine-tuning System

**Complete one fine-tuning iteration in under 10 minutes.**

A rapid experimentation system for fine-tuning small language models with instant feedback loops. Built for the NVIDIA DGX Spark platform, optimized for speed and iteration velocity.

---

## 🎯 Project Vision

Traditional fine-tuning is slow:
- ⏱️ Train for 30+ minutes
- 🤷 Manually test models
- 📊 No systematic comparison
- 🐌 Can't iterate quickly

**Our solution**: Ultra-fast pipeline with automated delta analysis.

### What You Get

- **3-5 minute training** using Unsloth + Qwen2.5-0.5B
- **Automated benchmarking** with 10 standard test prompts
- **Delta analysis** showing exactly what changed
- **HTML reports** for instant feedback
- **One-command iteration**: `./iterate.sh exp-001 dataset.json`

---

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama (for inference)
docker-compose up -d

# 3. Pull base model
docker-compose exec ollama ollama pull qwen2.5:0.5b

# 4. Run your first iteration!
./iterate.sh exp-001 datasets/example-chatbot.json

# 5. View results
open benchmark/results/report.html
```

**Total time**: ~5-10 minutes from start to finish.

---

## 📁 Project Structure

```
dgx-fast-iteration/
├── train.py                     # Agent 1: Fast training
├── iterate.sh                   # Agent 6: One-command workflow
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Ollama container
│
├── datasets/
│   ├── example-chatbot.json    # Sample: chatbot training
│   └── example-classifier.json # Sample: classification training
│
├── benchmark/
│   ├── prompts.py              # Agent 2: 10 test prompts
│   ├── run.py                  # Agent 2: Benchmark runner
│   ├── delta.py                # Agent 3: Comparison metrics
│   ├── visualize.py            # Agent 4: HTML generator
│   └── results/
│       ├── base.json
│       ├── finetuned.json
│       ├── deltas.json
│       └── report.html
│
├── experiments/
│   ├── exp-001/
│   │   ├── lora/              # Trained LoRA adapters
│   │   └── metadata.json      # Config & stats
│   └── log.json               # Experiment history
│
├── scripts/
│   └── export_to_ollama.sh    # Agent 5: Model export
│
└── docs/
    ├── QUICKSTART.md           # Getting started guide
    ├── ARCHITECTURE.md         # System design
    └── agents/
        └── agent*_teaching.md  # Teaching materials
```

---

## 🔄 The Iteration Loop

```
┌─────────────────────────────────────────────────┐
│  ONE COMMAND: ./iterate.sh exp-001 data.json   │
├─────────────────────────────────────────────────┤
│                                                 │
│  [1] Train (3-5 min)                           │
│      ├─ Load Qwen2.5-0.5B                     │
│      ├─ Apply LoRA (rank=8)                   │
│      └─ Train with Unsloth                    │
│           ↓                                    │
│  [2] Export (30 sec)                           │
│      ├─ Merge LoRA + base                     │
│      ├─ Convert to GGUF                       │
│      └─ Import to Ollama                      │
│           ↓                                    │
│  [3] Benchmark (1 min)                         │
│      ├─ Test base model                       │
│      └─ Test fine-tuned model                 │
│           ↓                                    │
│  [4] Analyze (instant)                         │
│      ├─ Calculate deltas                      │
│      └─ Assess improvements                   │
│           ↓                                    │
│  [5] Visualize (instant)                       │
│      └─ Generate HTML report                  │
│                                                 │
│  TOTAL: 5-10 minutes                           │
└─────────────────────────────────────────────────┘
```

---

## 🧠 System Components

### Agent 1: Fast Training Pipeline
- **Tool**: Unsloth (2x faster than HuggingFace)
- **Model**: Qwen2.5-0.5B (500M params)
- **Method**: LoRA fine-tuning (rank 8)
- **Time**: 3-5 minutes
- **Output**: `experiments/{name}/lora/`

### Agent 2: Benchmark Suite
- **Prompts**: 10 diverse test cases
- **Models**: Base + fine-tuned
- **Tool**: Ollama API
- **Time**: ~1 minute
- **Output**: `benchmark/results/{base,finetuned}.json`

### Agent 3: Delta Calculator
- **Metrics**: Length, keywords, similarity, correctness
- **Method**: TF-IDF + cosine similarity
- **Assessment**: Improved/Regressed/Changed/Unchanged
- **Time**: Instant
- **Output**: `benchmark/results/deltas.json`

### Agent 4: Visualization
- **Format**: Interactive HTML report
- **Features**: Side-by-side comparison, metrics dashboard
- **Time**: Instant
- **Output**: `benchmark/results/report.html`

### Agent 5: Infrastructure
- **Docker**: Ollama container with GPU support
- **Export**: LoRA → GGUF → Ollama pipeline
- **Storage**: Persistent model registry

### Agent 6: Orchestration
- **Script**: `iterate.sh`
- **Function**: Chain all agents seamlessly
- **Logging**: Track all experiments
- **Output**: `experiments/log.json`

---

## 💡 Use Cases

### 1. Domain Adaptation
Fine-tune on domain-specific data (medical, legal, technical) and measure improvement.

### 2. Instruction Following
Train on custom instruction formats and verify adherence.

### 3. Language Transfer
Adapt multilingual models to specific languages.

### 4. Style Control
Fine-tune for specific writing styles or tones.

### 5. Rapid Prototyping
Test 10+ dataset variations in an afternoon.

---

## 📊 Dataset Format

Use the **Alpaca format** (JSON):

```json
[
  {
    "instruction": "What is machine learning?",
    "output": "Machine learning is a branch of AI..."
  },
  {
    "instruction": "Explain neural networks.",
    "output": "Neural networks are..."
  }
]
```

**Tips**:
- 20-100 samples: Good for quick experiments
- 100-500 samples: Better quality, still fast
- 500+ samples: Longer training, higher quality

---

## 🔧 Advanced Usage

### Custom Training Parameters

```bash
# More epochs (better fit, slower)
python train.py exp-002 dataset.json --epochs 5

# Larger LoRA rank (more capacity, slower)
python train.py exp-003 dataset.json --lora-r 16

# Custom batch size (adjust for memory)
# Edit BATCH_SIZE in train.py
```

### Manual Pipeline Steps

```bash
# 1. Train only
python train.py exp-001 dataset.json

# 2. Export only
./scripts/export_to_ollama.sh exp-001

# 3. Benchmark only
python benchmark/run.py exp-001

# 4. Analyze only
python benchmark/delta.py

# 5. Visualize only
python benchmark/visualize.py
```

### Compare Multiple Experiments

```bash
# View experiment log
cat experiments/log.json

# Compare across iterations
python -c "
import json
with open('experiments/log.json') as f:
    log = json.load(f)
    for exp in log:
        print(f\"{exp['experiment_name']}: {exp['results']['improved']} improved\")
"
```

---

## 🎓 Learning Resources

- **[QUICKSTART.md](docs/QUICKSTART.md)**: Step-by-step beginner guide
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System design deep dive
- **[Agent Teaching Docs](docs/agents/)**: Learn each component in depth

---

## 🐛 Troubleshooting

### Training Issues

**OOM (Out of Memory)**:
- Reduce `BATCH_SIZE` in `train.py`
- Reduce `MAX_SEQ_LENGTH` in `train.py`

**Slow training**:
- Check GPU is being used: `nvidia-smi`
- Verify Unsloth is installed correctly

### Inference Issues

**Ollama not responding**:
```bash
docker-compose logs ollama
docker-compose restart ollama
```

**Model not found**:
```bash
docker-compose exec ollama ollama list
```

### Benchmark Issues

**Benchmark fails**:
- Ensure base model is pulled: `ollama pull qwen2.5:0.5b`
- Check Ollama is running: `curl http://localhost:11434/api/tags`

---

## 📈 Performance Benchmarks

**Hardware**: NVIDIA DGX Spark (Blackwell GB10, 128GB UMA)

| Component | Time | Notes |
|-----------|------|-------|
| Training (100 samples, 3 epochs) | 3-5 min | Varies by sample length |
| Export | 30 sec | One-time per experiment |
| Benchmark (10 prompts × 2 models) | 1 min | Depends on response length |
| Delta + Viz | < 5 sec | Instant |
| **Total** | **5-10 min** | **Full iteration** |

**Comparison**:
- Traditional (Llama-3-8B, HF Transformers): 30-60 min
- Our system (Qwen2.5-0.5B, Unsloth): 5-10 min
- **Speedup**: 3-6x faster ⚡

---

## 🤝 Contributing

This is a teaching project. Improvements welcome:
- Better benchmark prompts
- Additional metrics
- Performance optimizations
- Documentation improvements

---

## 📝 Citation

```bibtex
@software{dgx_fast_finetuning,
  title={DGX Spark Fast Fine-tuning System},
  year={2024},
  description={Rapid iteration framework for small LLM fine-tuning},
  platform={NVIDIA DGX Spark}
}
```

---

## 🎯 Success Metrics

The system is successful when:
- ✅ Complete iteration in < 10 minutes
- ✅ Clear delta visualization
- ✅ 10+ iterations in 2 hours possible
- ✅ Learning objectives met (see teaching docs)

---

## 📧 Support

Issues? Questions? Improvements?
- Check `docs/` for detailed guides
- Review teaching materials in `docs/agents/`
- Open an issue or discussion

---

**Built for rapid experimentation. Optimized for learning.**

*Start iterating in 10 minutes. Achieve 10 experiments in 2 hours.*
