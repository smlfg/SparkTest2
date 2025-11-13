# 🚀 DGX Fast Fine-tuning Iteration Lab

**Complete one fine-tuning iteration (train → test → analyze) in 5 minutes or less.**

A rapid experimentation system for fine-tuning small language models with instant feedback loops. Built for the NVIDIA DGX Spark (GB10 GPU, 128GB UMA).

```
Traditional Fine-tuning:  30+ min train, manual testing, subjective results
Our System:              3 min train, automated benchmarks, objective deltas
```

---

## 📋 Quick Start (5 Minutes)

### Prerequisites

Before you start, ensure you have:
- ✅ **NVIDIA DGX Spark** (or compatible GPU system)
- ✅ **Docker & Docker Compose** installed
- ✅ **Python 3.8+** installed
- ✅ **Git** installed
- ✅ **NVIDIA drivers** working (`nvidia-smi` shows GPU)

---

### Step 1: Clone Repository

```bash
git clone https://github.com/smlfg/SparkTest2.git
cd SparkTest2
```

---

### Step 2: Set Up Python Environment

**Why virtual environment?** Keeps dependencies isolated from system Python.

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Verify installation**:
```bash
python -c "import requests; print('✅ Python dependencies OK')"
```

---

### Step 3: Verify GPU Access

```bash
nvidia-smi
```

**Expected output**:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.x   |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  GB10            On   | 00000000:01:00.0 Off |                  N/A |
|  0%   45C    P0    50W / 300W |      0MiB / 131072MiB|      0%      Default |
+-------------------------------+----------------------+----------------------+
```

If you see `NVIDIA-SMI has failed`, fix drivers first:
```bash
# Check driver
lsmod | grep nvidia

# Reinstall if needed (Ubuntu/Debian)
sudo apt-get install nvidia-driver-535
```

---

### Step 4: Start Ollama (Inference Engine)

**What is Ollama?** Local LLM inference server (like running your own ChatGPT).

```bash
# Start Ollama container
docker-compose up -d

# Verify it's running
docker-compose ps
```

**Expected output**:
```
NAME      COMMAND                  SERVICE   STATUS    PORTS
ollama    "/bin/ollama serve"      ollama    Up        0.0.0.0:11434->11434/tcp
```

**Test Ollama API**:
```bash
curl http://localhost:11434/api/tags
```

Should return JSON with `{"models": [...]}`.

---

### Step 5: Pull Base Model (One-Time Setup)

**Why manually?** First pull is slow (500MB download). Do it once, reuse forever.

```bash
# Pull Qwen2.5-0.5B (500M parameters, optimized for speed)
docker exec ollama ollama pull qwen2.5:0.5b
```

**Expected output**:
```
pulling manifest
pulling 8e823e30d9b2... 100% ▕████████████████▏ 352 MB
pulling 462dfa0c23fa... 100% ▕████████████████▏  254 B
pulling bbf21006f38d... 100% ▕████████████████▏  120 B
pulling 56bb8bd477a5... 100% ▕████████████████▏   96 B
pulling 1cad41a8f581... 100% ▕████████████████▏  485 B
verifying sha256 digest
writing manifest
success
```

**Verify model is available**:
```bash
docker exec ollama ollama list
```

You should see:
```
NAME              ID              SIZE      MODIFIED
qwen2.5:0.5b     abc123def456    352 MB    10 seconds ago
```

---

## 🎯 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  ITERATION LOOP (5 minutes total)                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Agent 1] Fast Training          (3-5 min)                │
│      └─> experiments/exp-001/lora/                          │
│                                                             │
│  [Agent 5] Export to Ollama       (30 sec)                 │
│      └─> Ollama model "exp-001"                             │
│                                                             │
│  [Agent 2] Benchmark Suite        (1 min)   ← YOU ARE HERE │
│      └─> benchmark/results/base.json                        │
│          benchmark/results/finetuned.json                   │
│                                                             │
│  [Agent 3] Delta Calculator       (instant)                │
│      └─> benchmark/results/deltas.json                      │
│                                                             │
│  [Agent 4] HTML Visualization     (instant)                │
│      └─> benchmark/results/report.html                      │
│                                                             │
│  [Agent 6] Orchestration          (runs all)               │
│      └─> ./iterate.sh exp-001 datasets/example.json        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 Test the System

### Test 1: Verify Ollama Works

```bash
cd benchmark
python run.py --help
```

**Expected**:
```
✅ Loaded 10 benchmark prompts
usage: run.py [-h] [--base BASE] --finetuned FINETUNED [--ollama-url OLLAMA_URL]
```

### Test 2: Run Benchmark (Manual)

**Note**: This will fail until Agent 5 exports a fine-tuned model. For now, test with base model only:

```bash
# This tests the benchmark infrastructure
# (Will fail on --finetuned exp-001 because model doesn't exist yet)

# Expected error:
python run.py --finetuned exp-001

# Output:
# ❌ Fine-tuned model 'exp-001' not found in Ollama
#    Available models: qwen2.5:0.5b
#    Did Agent 5 export it? Run: ./scripts/export_to_ollama.sh
```

**This is correct!** Agent 5 (export pipeline) isn't built yet.

---

## 📁 Repository Structure

```
SparkTest2/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Ollama container (to be added by Agent 5)
│
├── benchmark/                   # ✅ Agent 2 (complete)
│   ├── prompts.py              # 10 standard test prompts
│   ├── run.py                  # Automated benchmark runner
│   ├── README.md               # Detailed benchmark docs
│   └── results/                # Generated benchmark results
│       └── .gitkeep
│
├── docs/
│   └── agents/
│       ├── agent2_teaching.md      # Learning guide for benchmarks
│       └── agent2_audit_report.md  # Robustness audit report
│
└── [TO BE BUILT]
    ├── train.py                 # Agent 1: Fast training
    ├── iterate.sh               # Agent 6: Full iteration script
    ├── datasets/                # Training datasets
    ├── experiments/             # Training outputs
    └── scripts/
        └── export_to_ollama.sh  # Agent 5: Export pipeline
```

---

## 🛠️ What's Currently Available

### ✅ Agent 2: Benchmark Suite (Production-Ready v2.0)

**Status**: Complete and hardened against production failures

**Features**:
- 10 standard test prompts (German language)
- Automated Ollama API integration
- Retry logic with exponential backoff (3 attempts)
- Progressive timeouts (60s → 120s → 180s) for cold starts
- Model warmup (eliminates first-query bias)
- Empty response detection and warnings
- Comprehensive error reporting

**Usage**:
```bash
cd benchmark
python run.py --finetuned exp-001
```

**Output**:
- `benchmark/results/base.json` (base model responses)
- `benchmark/results/finetuned.json` (fine-tuned model responses)

**Documentation**:
- [benchmark/README.md](benchmark/README.md) - Usage guide
- [docs/agents/agent2_teaching.md](docs/agents/agent2_teaching.md) - Learning guide
- [docs/agents/agent2_audit_report.md](docs/agents/agent2_audit_report.md) - Robustness audit

---

## 🚧 Coming Soon

### 🔜 Agent 1: Fast Training Pipeline
- Unsloth integration (2x speedup)
- Qwen2.5-0.5B setup
- LoRA fine-tuning (rank 8, 4-bit quantization)
- 3-5 minute training time

### 🔜 Agent 5: Infrastructure & Export
- `docker-compose.yml` (Ollama + GPU passthrough)
- LoRA → GGUF → Ollama export pipeline
- Model registry

### 🔜 Agent 3: Delta Calculator
- Response comparison logic
- Metrics: length, similarity, keywords, correctness
- Improvement/regression assessment

### 🔜 Agent 4: Visualization
- HTML report generator
- Side-by-side response comparison
- Color-coded delta indicators

### 🔜 Agent 6: Orchestration
- `iterate.sh` one-command workflow
- Experiment tracker
- Cross-iteration comparison

---

## 🐛 Troubleshooting

### Issue: `nvidia-smi` not found

**Cause**: NVIDIA drivers not installed or not in PATH

**Fix**:
```bash
# Check if drivers are installed
lsmod | grep nvidia

# Install drivers (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install nvidia-driver-535

# Reboot
sudo reboot
```

### Issue: `docker: command not found`

**Cause**: Docker not installed

**Fix**:
```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (avoid sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
```

### Issue: `Cannot connect to the Docker daemon`

**Cause**: Docker service not running

**Fix**:
```bash
# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Verify
docker ps
```

### Issue: `Ollama connection refused`

**Cause**: Ollama container not running

**Fix**:
```bash
# Check container status
docker-compose ps

# If not running, start it
docker-compose up -d

# Check logs
docker logs ollama

# Test API
curl http://localhost:11434/api/tags
```

### Issue: `Model 'qwen2.5:0.5b' not found`

**Cause**: Base model not pulled yet

**Fix**:
```bash
# Pull base model (one-time setup)
docker exec ollama ollama pull qwen2.5:0.5b

# Verify
docker exec ollama ollama list
```

### Issue: `Python module 'requests' not found`

**Cause**: Virtual environment not activated or dependencies not installed

**Fix**:
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify
python -c "import requests; print('OK')"
```

---

## 📚 Learning Resources

### Documentation
- [Master Overview](docs/MASTER_OVERVIEW.md) - System architecture (if exists)
- [Agent 2 Teaching Guide](docs/agents/agent2_teaching.md) - Learn benchmark concepts
- [Agent 2 Audit Report](docs/agents/agent2_audit_report.md) - Robustness analysis

### Key Concepts
- **LoRA Fine-tuning**: Efficient parameter updates (learn in Agent 1)
- **Systematic Evaluation**: Benchmark suite (learn in Agent 2)
- **Delta Analysis**: Improvement measurement (learn in Agent 3)
- **Rapid Iteration**: Complete loop in <10 minutes (learn in Agent 6)

---

## 🤝 Contributing

This is an educational project. Key principles:

1. **Teaching First**: Code should teach, not just work
2. **Speed Over Perfection**: Optimize for iteration velocity
3. **Simplicity**: CLI + static HTML, no complex dashboards
4. **Reproducibility**: Lock versions, document assumptions

---

## 📄 License

[Add your license here]

---

## 🆘 Getting Help

**Issue Tracker**: [https://github.com/smlfg/SparkTest2/issues](https://github.com/smlfg/SparkTest2/issues)

**Common Questions**:
1. "Benchmark fails with timeout" → See Agent 2 audit report (cold start handling)
2. "Model not found" → Did you run `ollama pull qwen2.5:0.5b`?
3. "GPU not detected" → Check `nvidia-smi` and Docker GPU passthrough

---

**Status**: 🟡 In Development (Agent 2 complete, Agents 1,3,4,5,6 coming soon)

**Last Updated**: 2025-11-13
