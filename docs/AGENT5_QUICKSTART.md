# Agent 5 Quick Start Guide

> **Export LoRA models to Ollama in 30 seconds**

This guide gets you up and running with Agent 5's infrastructure and export pipeline.

---

## ⚡ Quick Commands

```bash
# 1. Start Ollama
docker-compose up -d

# 2. Verify setup
python scripts/verify_setup.py

# 3. Export a model (after Agent 1 trains it)
python scripts/export_to_ollama.py exp-001

# 4. Test the exported model
docker exec ollama ollama run exp-001 "Hello!"
```

That's it! 🎉

---

## 📋 Step-by-Step Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install packages
pip install -r requirements.txt
```

**Verify**:
```bash
python -c "from unsloth import FastLanguageModel; print('✅ Unsloth OK')"
python -c "import torch; print('✅ CUDA:', torch.cuda.is_available())"
```

---

### 2. Start Ollama

```bash
# Start container
docker-compose up -d

# Verify it's running
docker ps | grep ollama

# Check API
curl http://localhost:11434/api/tags
```

**Expected output**: JSON with list of models (empty at first)

---

### 3. Pull Base Model

```bash
# Download Qwen2.5-0.5B for benchmarking
docker exec ollama ollama pull qwen2.5:0.5b
```

This takes ~1-2 minutes (downloads ~500MB).

---

### 4. Export Your First Model

**Prerequisites**: Agent 1 must have trained a model first.

The training produces: `experiments/exp-001/lora/`

**Export command**:
```bash
python scripts/export_to_ollama.py exp-001
```

**What happens**:
1. ✅ Loads LoRA adapters
2. ✅ Merges with base model
3. ✅ Converts to GGUF (q4_k_m quantization)
4. ✅ Creates Modelfile
5. ✅ Registers in Ollama

**Output**:
```
🚀 Starting Export: exp-001
   [1/3] Loading & Merging weights...
   ✅ Model loaded successfully
   [2/3] Converting to GGUF (q4_k_m)...
   ✅ GGUF created: model.gguf
   [3/3] Registering with Ollama...
   ✅ Model 'exp-001' created in Ollama!

✅ EXPORT COMPLETE!
   Model:        exp-001
   Size:         250.3 MB
   Ollama:       Registered as 'exp-001'
```

---

### 5. Test the Model

**Interactive test**:
```bash
docker exec -it ollama ollama run exp-001
```

Type prompts and press Enter. Type `/bye` to exit.

**Single prompt test**:
```bash
docker exec ollama ollama run exp-001 "What is machine learning?"
```

**API test** (what Agent 2 will use):
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "exp-001",
  "prompt": "Hello!",
  "stream": false
}'
```

---

## 🧰 Utility Scripts

### Verify Setup
```bash
python scripts/verify_setup.py
```

Checks:
- ✅ Python version
- ✅ Dependencies installed
- ✅ GPU available
- ✅ Docker running
- ✅ Ollama responding
- ✅ File structure

### Ollama Helper
```bash
# Start/stop
./scripts/ollama_helper.sh start
./scripts/ollama_helper.sh stop
./scripts/ollama_helper.sh restart

# Status
./scripts/ollama_helper.sh status
./scripts/ollama_helper.sh logs

# Model management
./scripts/ollama_helper.sh list
./scripts/ollama_helper.sh pull qwen2.5:0.5b
./scripts/ollama_helper.sh remove exp-001

# Testing
./scripts/ollama_helper.sh test exp-001 "What is 2+2?"
./scripts/ollama_helper.sh api-test exp-001

# GPU check
./scripts/ollama_helper.sh gpu

# Help
./scripts/ollama_helper.sh help
```

---

## 🔧 Troubleshooting

### "Ollama container not running"

```bash
# Check Docker
docker ps

# If not running, start it
docker-compose up -d

# Check logs if fails
docker-compose logs ollama
```

### "NVIDIA driver not found"

```bash
# Install nvidia-docker2
sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### "LoRA adapters not found"

**Error**: `❌ LoRA adapters not found at: experiments/exp-001/lora/`

**Solution**: Run Agent 1's training first:
```bash
python train.py --name exp-001 --dataset datasets/example-chatbot.json
```

### "Model not in Ollama after export"

```bash
# Check if GGUF exists
ls -lh experiments/exp-001/gguf/

# Check Modelfile
cat experiments/exp-001/Modelfile

# Manually create model
docker exec ollama ollama create exp-001 -f /experiments/exp-001/Modelfile

# Check Ollama logs
docker logs ollama
```

### "CUDA out of memory during export"

**Option A**: Free VRAM
```bash
docker-compose down  # Stop Ollama temporarily
python scripts/export_to_ollama.py exp-001
docker-compose up -d
```

**Option B**: Use CPU for export
Edit `scripts/export_to_ollama.py`:
```python
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=lora_path,
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=False,  # Change to False
    device_map="cpu"      # Add this
)
```

---

## 📊 Export Options

### Quantization Levels

```bash
# 4-bit (default, recommended)
python scripts/export_to_ollama.py exp-001 --quantization q4_k_m

# 8-bit (higher quality, 2x larger)
python scripts/export_to_ollama.py exp-001 --quantization q8_0

# Full precision (best quality, 4x larger)
python scripts/export_to_ollama.py exp-001 --quantization f16
```

**Comparison for 0.5B model**:
| Quantization | Size | Quality | Speed |
|--------------|------|---------|-------|
| q4_k_m       | ~250 MB | 97% | 2x faster |
| q8_0         | ~500 MB | 99% | 1.5x faster |
| f16          | ~1 GB | 100% | Baseline |

**Recommendation**: Use q4_k_m for all experiments. Switch to q8_0 only for final evaluation.

---

## 🔗 Integration Points

### Input from Agent 1

**Expected structure**:
```
experiments/exp-001/lora/
├── adapter_config.json      # LoRA configuration
├── adapter_model.safetensors # Trained weights (10-50MB)
├── tokenizer_config.json    # Tokenizer setup
└── special_tokens_map.json  # Special tokens
```

### Output for Agent 2

**Ollama model**: `exp-001`

**API endpoint**: `http://localhost:11434/api/generate`

**Example request**:
```json
{
  "model": "exp-001",
  "prompt": "What is 2+2?",
  "stream": false
}
```

**Example response**:
```json
{
  "model": "exp-001",
  "created_at": "2024-11-12T22:00:00Z",
  "response": "2+2 equals 4.",
  "done": true
}
```

---

## 📚 Learn More

- **Full Documentation**: [`docs/agents/agent5_teaching.md`](agents/agent5_teaching.md)
- **Docker Compose**: [`docker-compose.yml`](../docker-compose.yml)
- **Export Script**: [`scripts/export_to_ollama.py`](../scripts/export_to_ollama.py)
- **Main README**: [`README.md`](../README.md)

---

## ✅ Success Criteria

Your Agent 5 setup is complete when:

- [ ] `docker-compose up -d` starts Ollama
- [ ] `curl http://localhost:11434/api/tags` returns JSON
- [ ] `python scripts/verify_setup.py` shows all checks pass
- [ ] `python scripts/export_to_ollama.py exp-001` runs without errors
- [ ] `docker exec ollama ollama list` shows exported model
- [ ] `docker exec ollama ollama run exp-001 "Hello"` responds

---

**Need help?** See [`docs/agents/agent5_teaching.md`](agents/agent5_teaching.md) for deep dives and experiments.

**Ready for next step?** Once models are exported, Agent 2 will benchmark them!
