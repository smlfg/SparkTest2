# 🚀 DGX Spark Fast Fine-tuning Lab

> **Complete one fine-tuning iteration (train → test → analyze) in under 5 minutes**

A rapid experimentation system for fine-tuning small language models with instant feedback loops and automated delta analysis.

[![Built for DGX Spark](https://img.shields.io/badge/Built%20for-DGX%20Spark-76B900?style=flat-square&logo=nvidia&logoColor=white)](https://www.nvidia.com/en-us/data-center/dgx-spark/)
[![Qwen 2.5](https://img.shields.io/badge/Model-Qwen%202.5--0.5B-blue?style=flat-square)](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
[![Ollama](https://img.shields.io/badge/Inference-Ollama-black?style=flat-square)](https://ollama.ai/)

---

## 📋 Table of Contents

- [The Problem](#-the-problem)
- [Our Solution](#-our-solution)
- [System Architecture](#-system-architecture)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Agent Responsibilities](#-agent-responsibilities)
- [Learning Objectives](#-learning-objectives)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 The Problem

Traditional fine-tuning workflows are painfully slow:
- ⏰ Train for 30+ minutes
- 🐌 Manually test the model
- ❓ No systematic comparison to base model
- 🔁 Can't iterate quickly

**Result**: Slow experimentation, wasted time, missed insights.

---

## ✨ Our Solution

**Ultra-fast pipeline with automated delta analysis**:
- ⚡ Train in 3-5 minutes (Qwen2.5-0.5B + Unsloth)
- 🤖 Automated benchmarking (10 standard prompts)
- 📊 Delta analysis (what changed? improved? regressed?)
- 📈 Visual reports (HTML dashboard)
- 🔄 Complete iteration: **5 minutes or less**

**Goal**: Make fine-tuning feel like compiling code - fast feedback, quick iteration, constant improvement.

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  ITERATION LOOP (5 minutes total)                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [1] FAST TRAINING                                          │
│      • Model: Qwen2.5-0.5B (500M params)                   │
│      • Tool: Unsloth (2x speedup)                          │
│      • Method: LoRA (rank 8, 4-bit)                        │
│      • Time: 3-5 minutes                                    │
│           ↓                                                 │
│  [2] AUTO-EXPORT                                            │
│      • Merge LoRA → GGUF → Ollama                          │
│      • Time: 30 seconds                                     │
│           ↓                                                 │
│  [3] BENCHMARK                                              │
│      • Run 10 standard prompts                              │
│      • Base model vs. fine-tuned                           │
│      • Time: 1 minute                                       │
│           ↓                                                 │
│  [4] DELTA ANALYSIS                                         │
│      • Compare responses                                    │
│      • Metrics: length, similarity, keywords                │
│      • Time: instant                                        │
│           ↓                                                 │
│  [5] VISUALIZATION                                          │
│      • Generate HTML report                                 │
│      • Show improvements/regressions                        │
│      • Time: instant                                        │
│           ↓                                                 │
│  [6] ORCHESTRATION                                          │
│      • Log experiment                                       │
│      • Track history                                        │
│      • Compare across iterations                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- NVIDIA DGX Spark (or any GPU with 8GB+ VRAM)
- Docker + nvidia-docker2
- Python 3.10+
- CUDA 12.1+ (or 11.8+)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/dgx-fast-iteration.git
cd dgx-fast-iteration

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Start Ollama (inference engine)
docker-compose up -d

# 5. Verify GPU access
docker exec ollama nvidia-smi

# 6. Download base model
docker exec ollama ollama pull qwen2.5:0.5b
```

### Run Your First Iteration

```bash
# Full iteration (when implemented)
./iterate.sh exp-001 datasets/example-chatbot.json

# Or step-by-step:
python train.py --name exp-001 --dataset datasets/example-chatbot.json
python scripts/export_to_ollama.py exp-001
python benchmark/run.py exp-001
python benchmark/delta.py exp-001
python benchmark/visualize.py exp-001
```

**Result**: See `benchmark/results/report.html` for visual comparison!

---

## 📖 Usage

### Agent 5: Export Model to Ollama

After training a model with Agent 1, export it for inference:

```bash
# Basic usage (q4_k_m quantization)
python scripts/export_to_ollama.py exp-001

# Use 8-bit quantization (higher quality, larger file)
python scripts/export_to_ollama.py exp-001 --quantization q8_0

# Use full precision (largest, best quality)
python scripts/export_to_ollama.py exp-001 --quantization f16
```

**What it does**:
1. Loads LoRA adapters from `experiments/exp-001/lora/`
2. Merges with base model (Qwen2.5-0.5B)
3. Converts to GGUF format
4. Creates Modelfile (chat template + settings)
5. Registers model in Ollama as `exp-001`

**Verify export**:
```bash
# List models in Ollama
docker exec ollama ollama list

# Test the model
docker exec ollama ollama run exp-001 "Hello! Who are you?"

# Or via API
curl http://localhost:11434/api/generate -d '{
  "model": "exp-001",
  "prompt": "What is 2+2?",
  "stream": false
}'
```

---

## 📁 Project Structure

```
dgx-fast-iteration/
├── README.md                    # This file
├── docker-compose.yml           # Ollama container setup
├── requirements.txt             # Python dependencies
│
├── train.py                     # [TODO: Agent 1] Fast training
├── iterate.sh                   # [TODO: Agent 6] Full iteration
│
├── datasets/
│   ├── example-chatbot.json    # [TODO] Sample training data
│   └── example-classifier.json # [TODO] Sample training data
│
├── benchmark/
│   ├── prompts.py              # [TODO: Agent 2] Test prompts
│   ├── run.py                  # [TODO: Agent 2] Benchmark runner
│   ├── delta.py                # [TODO: Agent 3] Delta calculator
│   ├── visualize.py            # [TODO: Agent 4] HTML generator
│   └── results/                # Benchmark outputs
│       ├── base.json
│       ├── finetuned.json
│       ├── deltas.json
│       └── report.html
│
├── experiments/
│   ├── exp-001/
│   │   ├── lora/              # Trained LoRA adapters
│   │   ├── gguf/              # Exported GGUF model
│   │   ├── Modelfile          # Ollama model config
│   │   ├── metadata.json      # Training config
│   │   └── export_metadata.json # Export info
│   └── log.json               # [TODO: Agent 6] Experiment history
│
├── scripts/
│   └── export_to_ollama.py    # ✅ Agent 5: Export pipeline
│
└── docs/
    ├── ARCHITECTURE.md         # [TODO] System design
    ├── QUICKSTART.md          # [TODO] Getting started
    └── agents/
        └── agent5_teaching.md  # ✅ Agent 5: Teaching guide
```

**Legend**:
- ✅ Implemented
- [TODO] Not yet implemented

---

## 🤖 Agent Responsibilities

This project is built by 6 specialized agents:

| Agent | Role | Status | Key Deliverable |
|-------|------|--------|-----------------|
| **Agent 1** | Fast Training | 🔜 TODO | `train.py` (Unsloth + LoRA) |
| **Agent 2** | Benchmarking | 🔜 TODO | `benchmark/run.py` (API tester) |
| **Agent 3** | Delta Analysis | 🔜 TODO | `benchmark/delta.py` (Comparison) |
| **Agent 4** | Visualization | 🔜 TODO | `benchmark/visualize.py` (HTML report) |
| **Agent 5** | Infrastructure | ✅ **DONE** | `scripts/export_to_ollama.py` |
| **Agent 6** | Orchestration | 🔜 TODO | `iterate.sh` (Full pipeline) |

### Current Status: Agent 5 Complete

**Agent 5** has implemented:
- ✅ Docker Compose setup (Ollama + GPU)
- ✅ Export pipeline (LoRA → GGUF → Ollama)
- ✅ Comprehensive teaching documentation
- ✅ Error handling and validation
- ✅ Quantization options (q4_k_m, q8_0, f16)

**Next**: Other agents will build on this foundation.

---

## 🎓 Learning Objectives

By building and using this system, you will understand:

1. **LoRA Fine-tuning** (practical, not theoretical)
   - Why adapter weights are smaller
   - How to merge adapters with base models
   - Trade-offs in rank selection

2. **Model Evaluation** (systematic comparison)
   - How to benchmark consistently
   - What metrics matter
   - How to interpret deltas

3. **Experiment Tracking** (scientific method for ML)
   - Reproducible experiments
   - Version control for models
   - Comparing across iterations

4. **Rapid Iteration** (fail fast, learn fast)
   - Why speed matters in ML research
   - How to optimize the feedback loop
   - Tooling for velocity

5. **System Integration** (how components fit together)
   - Docker for reproducibility
   - API design for ML systems
   - Data flow between components

**Teaching approach**: Every script includes inline comments explaining the "why", not just the "what". See `docs/agents/` for deep dives.

---

## 🛠 Tech Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| **Hardware** | NVIDIA DGX Spark (GB10 GPU) | 128GB UMA, fast iteration |
| **Base Model** | Qwen2.5-0.5B-Instruct | Small, fast, good quality |
| **Training** | Unsloth | 2x speedup over HuggingFace |
| **Fine-tuning** | LoRA (rank 8, 4-bit) | Memory-efficient, fast |
| **Inference** | Ollama | Simple API, GGUF support |
| **Format** | GGUF (q4_k_m) | Fast loading, small size |
| **Orchestration** | Bash + Python | Simple, transparent |
| **Containers** | Docker Compose | Reproducible infrastructure |

---

## ❓ Troubleshooting

### Docker Issues

**Problem**: `Cannot connect to Docker daemon`
```bash
# Start Docker
sudo systemctl start docker

# Add user to docker group (no sudo needed)
sudo usermod -aG docker $USER
newgrp docker
```

**Problem**: `NVIDIA driver not found in container`
```bash
# Install nvidia-docker2
sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Test
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

**Problem**: `Port 11434 already in use`
```bash
# Find what's using the port
sudo lsof -i :11434

# Stop the conflicting service
docker stop ollama

# Or change port in docker-compose.yml
```

### Python Issues

**Problem**: `No module named 'unsloth'`
```bash
# Install from git
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
```

**Problem**: `CUDA out of memory`
```bash
# Check GPU usage
nvidia-smi

# Free VRAM by stopping Ollama during training
docker-compose down
```

**Problem**: `torch.cuda.is_available() returns False`
```bash
# Check CUDA installation
nvidia-smi
nvcc --version

# Reinstall PyTorch with correct CUDA version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Export Issues

**Problem**: `Model not found in Ollama after export`
```bash
# Check if GGUF exists
ls -lh experiments/*/gguf/

# Manually create model
docker exec ollama ollama create exp-001 -f /experiments/exp-001/Modelfile

# Check Ollama logs
docker logs ollama
```

**Problem**: `Wrong chat template (model outputs gibberish)`
- Check `experiments/{name}/Modelfile`
- Ensure TEMPLATE matches training format (ChatML for Qwen)
- See `docs/agents/agent5_teaching.md` → Experiment 1

---

## 📚 Documentation

- **Agent 5 Teaching Guide**: [`docs/agents/agent5_teaching.md`](docs/agents/agent5_teaching.md)
  - Deep dive: LoRA, GGUF, Docker, Modelfiles
  - Hands-on experiments
  - Troubleshooting guide

- **[TODO] Architecture Overview**: `docs/ARCHITECTURE.md`
- **[TODO] Quick Start Guide**: `docs/QUICKSTART.md`
- **[TODO] Agent Teaching Guides**: `docs/agents/agent{1-6}_teaching.md`

---

## 🤝 Contributing

This is a teaching project. Contributions that improve:
- ✅ Educational value (better explanations, more examples)
- ✅ Speed (faster training, more efficient pipelines)
- ✅ Reliability (better error handling, validation)

are welcome!

**Style guide**:
- Inline comments should explain "why", not "what"
- Teaching comments marked with `TEACHING:`
- Every script should be readable by a CS student

---

## 📜 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

- **Unsloth**: For 2x training speedup
- **Ollama**: For making local LLM inference simple
- **Qwen Team**: For the excellent 0.5B base model
- **NVIDIA**: For DGX Spark hardware

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/dgx-fast-iteration/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/dgx-fast-iteration/discussions)
- **Documentation**: [`docs/`](docs/)

---

**Built with ❤️ for rapid ML experimentation**

*Making fine-tuning as fast as compiling code* ⚡
