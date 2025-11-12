# Agent 5 Teaching Guide: The Bridge to Production

## 🎯 What You Built

You built the **Deployment Pipeline** - the critical infrastructure that transforms trained models into queryable APIs. In the real world, training a model is only 50% of the work. **Serving it** (making it usable) is the other 50%.

### Your Role in the System

```
┌─────────────────────────────────────────────────────────┐
│  Agent 1: Training                                      │
│  Output: experiments/exp-001/lora/                      │
│          (LoRA adapter files - useless alone)           │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Agent 5: Infrastructure & Export (YOU!)                │
│                                                         │
│  [1] Docker Infrastructure                              │
│      • Ollama server (inference engine)                 │
│      • GPU-enabled container                            │
│      • Persistent model storage                         │
│                                                         │
│  [2] Export Pipeline                                    │
│      • Load LoRA adapters                               │
│      • Merge with base model                            │
│      • Convert to GGUF format                           │
│      • Create Modelfile                                 │
│      • Register in Ollama                               │
│                                                         │
│  Output: Live API endpoint                              │
│          http://localhost:11434/api/generate            │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Agent 2: Benchmarking                                  │
│  Uses: curl/requests to query the model                │
└─────────────────────────────────────────────────────────┘
```

**Without your work**: The trained model sits on disk as useless adapter files.
**With your work**: The model is live, queryable, and ready for testing in seconds.

---

## 🧠 Core Concepts Explained

### 1. What is LoRA?

**LoRA** = Low-Rank Adaptation (a fine-tuning technique)

Imagine you have a 500M parameter model (Qwen2.5-0.5B). Traditional fine-tuning updates all 500M parameters, which:
- Takes lots of time
- Requires lots of VRAM
- Produces a full copy of the model (1GB+ storage)

**LoRA's Clever Trick**:
Instead of updating the full weight matrix W, we learn two small matrices A and B such that:
```
W_new = W_original + A × B
```

Where:
- W_original: 4096 × 4096 matrix (16M parameters)
- A: 4096 × 8 matrix (32K parameters)
- B: 8 × 4096 matrix (32K parameters)
- Total LoRA params: 64K vs. 16M original ✅

**Result**: We only train 64K parameters instead of 16M (250x smaller!)

**The Catch**: LoRA adapters are just deltas. You need to merge them with the base model to use them.

---

### 2. The Modelfile (LLM's Dockerfile)

Just like a `Dockerfile` defines a container, a `Modelfile` defines an LLM for Ollama.

**Example Modelfile**:
```dockerfile
FROM /experiments/exp-001/gguf/model.gguf

TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ .Response }}<|im_end|>
"""

PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
PARAMETER temperature 0.7
```

**Breaking it down**:

#### `FROM` - The Model Weights
Points to the GGUF file (the actual neural network weights).

#### `TEMPLATE` - The Chat Format (CRITICAL!)
This tells Ollama how the model expects conversations to be formatted.

**Why is this critical?**
- Models are trained on specific formats (ChatML, Llama2, Alpaca, etc.)
- If you use the wrong format, the model gets confused
- It's like speaking English to someone who only understands Spanish

**Qwen uses ChatML**:
```
<|im_start|>system
You are a helpful assistant<|im_end|>
<|im_start|>user
What is 2+2?<|im_end|>
<|im_start|>assistant
4<|im_end|>
```

If you mess up the template, symptoms:
- Model outputs `<|im_start|>` in responses (leaking special tokens)
- Doesn't stop generating (continues with fake user messages)
- Nonsense responses

#### `PARAMETER stop` - When to Stop
Without stop tokens, the model might generate:
```
assistant: 4<|im_end|>
<|im_start|>user
Thanks! What about 3+3?<|im_end|>
<|im_start|>assistant
6<|im_end|>
...continues forever...
```

Stop tokens tell Ollama: "When you see this, STOP generating."

---

### 3. GGUF Format (GPT-Generated Unified Format)

**GGUF** is the binary format used by llama.cpp (which Ollama uses under the hood).

**Why convert to GGUF?**

| Feature | PyTorch `.pth` | HuggingFace `.safetensors` | GGUF |
|---------|----------------|----------------------------|------|
| **Loading Speed** | Slow (deserialize) | Medium | ⚡ Instant (mmap) |
| **Quantization** | No | No | ✅ Yes (q4, q8, etc.) |
| **Portability** | Python-only | Python-only | ✅ C++ (runs anywhere) |
| **Size (0.5B)** | ~1GB | ~1GB | ~250MB (q4_k_m) |

**GGUF's Magic: Memory-mapped Files (mmap)**

Normal file reading:
```
1. Read file from disk
2. Copy to RAM
3. Deserialize to model object
4. Use model

Total time: 10-30 seconds for 1GB
```

GGUF with mmap:
```
1. mmap the file (OS maps disk directly to memory addresses)
2. Access model weights as if they're in RAM
3. Use model immediately

Total time: <1 second
```

**Quantization in GGUF**

Quantization = Reducing precision to save space/speed

| Method | Bits | Size (0.5B) | Quality | Speed |
|--------|------|-------------|---------|-------|
| **f16** | 16-bit | ~1 GB | 100% | Baseline |
| **q8_0** | 8-bit | ~500 MB | 99% | 1.5x faster |
| **q4_k_m** | 4-bit | ~250 MB | 97% | 2x faster |
| **q2_k** | 2-bit | ~125 MB | 90% | 3x faster |

**For 0.5B models**: q4_k_m is the sweet spot (minimal quality loss, 4x smaller).

---

### 4. Docker Volumes (Data Persistence)

Docker containers are **ephemeral** (they forget everything when restarted). Volumes solve this.

**Two types of volumes**:

#### Named Volume (`ollama-data`)
```yaml
volumes:
  - ollama-data:/root/.ollama
```

- Docker creates and manages this volume
- Stored in `/var/lib/docker/volumes/`
- Survives container restarts
- Used for: Ollama's internal data (downloaded models, registry)

**To inspect**:
```bash
docker volume inspect dgx-fast-iteration_ollama-data
```

#### Bind Mount (`./experiments`)
```yaml
volumes:
  - ./experiments:/experiments
```

- Maps a **host folder** to a **container path**
- Changes on host are instantly visible in container (and vice versa)
- Used for: Sharing data between host scripts and containerized services

**How it works**:

```
Host Machine                          Docker Container
────────────────                      ────────────────
/home/user/SparkTest2/experiments  ←→  /experiments
    ├── exp-001/
    │   ├── gguf/
    │   │   └── model.gguf           (same file!)
```

When `export_to_ollama.py` (host) writes a GGUF file:
```python
model.save_pretrained_gguf("experiments/exp-001/gguf", ...)
```

Ollama (container) sees it at:
```
/experiments/exp-001/gguf/model.gguf
```

No copying needed! They share the same disk space.

---

### 5. GPU Passthrough in Docker

**The Problem**: GPUs are hardware devices. Docker containers are isolated virtual environments. How does the container access the GPU?

**The Solution**: GPU passthrough via NVIDIA Container Toolkit

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

**What this does**:
1. Docker talks to the NVIDIA driver on the host
2. The driver "loans" the GPU to the container
3. Inside the container, CUDA code can use the GPU normally

**To verify**:
```bash
docker exec ollama nvidia-smi
```

You should see your GPU (GB10 on DGX Spark).

**Speed comparison (0.5B model inference)**:
- CPU: ~10-20 tokens/second
- GPU: ~100-300 tokens/second (10-30x faster!)

---

## 🧪 Experiments to Deepen Understanding

### Experiment 1: Wrong Chat Template

**Goal**: Understand why chat templates matter.

**Steps**:
1. Edit `scripts/export_to_ollama.py`
2. In the Modelfile, change the TEMPLATE to:
   ```
   TEMPLATE """{{ .System }} {{ .Prompt }} {{ .Response }}"""
   ```
3. Export a model: `python scripts/export_to_ollama.py exp-broken`
4. Test it: `docker exec ollama ollama run exp-broken "What is 2+2?"`

**Expected Result**:
- Model may output special tokens like `<|im_end|>`
- May not stop generating (continues with fake conversation)
- May give nonsensical responses

**Why?**
The model was trained to expect `<|im_start|>user\n...<|im_end|>`, but you're giving it raw text. It's like giving someone a scrambled message.

**Lesson**: Chat templates MUST match the format used during training.

---

### Experiment 2: Quantization Comparison

**Goal**: See the trade-off between quality, size, and speed.

**Steps**:
1. Export the same experiment with different quantization:
   ```bash
   python scripts/export_to_ollama.py exp-001 --quantization f16
   python scripts/export_to_ollama.py exp-001-q8 --quantization q8_0
   python scripts/export_to_ollama.py exp-001-q4 --quantization q4_k_m
   ```

2. Compare file sizes:
   ```bash
   ls -lh experiments/*/gguf/*.gguf
   ```

3. Test quality (ask the same question to all three):
   ```bash
   docker exec ollama ollama run exp-001 "Explain quantum computing in simple terms"
   docker exec ollama ollama run exp-001-q8 "Explain quantum computing in simple terms"
   docker exec ollama ollama run exp-001-q4 "Explain quantum computing in simple terms"
   ```

4. Time the responses

**Expected Results**:
- f16: Largest file (~1GB), slowest, best quality
- q8_0: Medium file (~500MB), medium speed, near-identical quality
- q4_k_m: Smallest file (~250MB), fastest, 95-98% of quality

**Lesson**: For sub-1B models, q4_k_m is almost always the right choice. Quality loss is negligible, but you gain 4x storage savings and 2x speed.

---

### Experiment 3: No Docker Volumes

**Goal**: Understand why volumes are necessary.

**Steps**:
1. Stop Ollama: `docker-compose down`
2. Edit `docker-compose.yml`, remove the `ollama-data` volume line
3. Start Ollama: `docker-compose up -d`
4. Pull the base model: `docker exec ollama ollama pull qwen2.5:0.5b`
5. Stop and restart: `docker-compose down && docker-compose up -d`
6. Check models: `docker exec ollama ollama list`

**Expected Result**:
The model you pulled is GONE. You'd have to re-download it (wasting time and bandwidth).

**Lesson**: Without volumes, containers forget everything. Volumes provide persistence.

---

## 🔧 Integration Points

### What Agent 5 Expects from Agent 1

**Input**: `experiments/{name}/lora/`

**Required files**:
```
experiments/exp-001/lora/
├── adapter_config.json      # LoRA configuration
├── adapter_model.safetensors # Trained weights
├── tokenizer_config.json    # Tokenizer setup
└── special_tokens_map.json  # Special tokens
```

**What happens if these are missing?**
- Script will fail at the "Load LoRA" step
- Error: `FileNotFoundError: adapter_config.json`

**Agent 1's responsibility**: Ensure these files are saved correctly during training.

---

### What Agent 2 Expects from Agent 5

**Output**: A registered Ollama model

**How to verify**:
```bash
# List all models
docker exec ollama ollama list

# Should show:
# NAME            SIZE    MODIFIED
# exp-001         250MB   2 minutes ago
```

**API endpoint**: `http://localhost:11434/api/generate`

**Example request** (what Agent 2 will do):
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "exp-001",
  "prompt": "What is 2+2?",
  "stream": false
}'
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

**Agent 2's responsibility**: Send properly formatted requests, parse responses.

---

## ✅ Success Criteria

Your implementation is complete when:

- [ ] `docker-compose up -d` starts Ollama successfully
- [ ] `docker ps` shows the `ollama` container running
- [ ] `curl http://localhost:11434/api/tags` returns JSON
- [ ] `python scripts/export_to_ollama.py exp-test` runs without errors (after Agent 1 trains a model)
- [ ] `docker exec ollama ollama list` shows the exported model
- [ ] The GGUF file exists: `ls experiments/exp-test/gguf/*.gguf`
- [ ] The model responds: `docker exec ollama ollama run exp-test "Hello"`
- [ ] GPU is accessible: `docker exec ollama nvidia-smi` shows GPU

---

## 🐛 Common Issues & Solutions

### Issue 1: "Error: NVIDIA driver not found"

**Symptom**: Docker can't access GPU

**Diagnosis**:
```bash
nvidia-smi  # Should work on host
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi  # Fails
```

**Solution**:
```bash
# Install nvidia-docker2
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Restart Docker
sudo systemctl restart docker

# Test again
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

---

### Issue 2: "Port 11434 already in use"

**Symptom**: `docker-compose up` fails with port conflict

**Diagnosis**:
```bash
sudo lsof -i :11434
# Shows another process using port 11434
```

**Solution A** (stop the other process):
```bash
docker stop ollama  # If it's another Ollama instance
```

**Solution B** (change port):
Edit `docker-compose.yml`:
```yaml
ports:
  - "12345:11434"  # Use a different host port
```
Then update scripts to use `http://localhost:12345`

---

### Issue 3: "Model not found in Ollama"

**Symptom**: `ollama list` doesn't show your model

**Diagnosis**:
```bash
# Check if GGUF file exists
ls -lh experiments/exp-001/gguf/

# Check if Modelfile exists
cat experiments/exp-001/Modelfile

# Check Ollama logs
docker logs ollama
```

**Common causes**:
1. Path mismatch: Modelfile points to wrong path
2. GGUF file is corrupted: Re-run export
3. Ollama crashed during import: Check logs

**Solution**:
```bash
# Manually create the model
docker exec ollama ollama create exp-001 -f /experiments/exp-001/Modelfile
```

---

### Issue 4: "GGUF conversion fails with CUDA out of memory"

**Symptom**: Export script crashes during `save_pretrained_gguf`

**Diagnosis**:
```bash
# Check GPU memory
nvidia-smi

# Should show available VRAM
```

**Solution A** (free up VRAM):
```bash
# Stop other processes using GPU
docker stop ollama  # Temporarily
```

**Solution B** (use CPU for conversion):
Edit `scripts/export_to_ollama.py`:
```python
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=lora_path,
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=False,  # Change to False
    device_map="cpu"      # Add this line
)
```

---

## 📚 Further Learning

### Recommended Reading

1. **GGUF Format Specification**
   - https://github.com/ggerganov/ggml/blob/master/docs/gguf.md
   - Deep dive into the binary format

2. **Ollama Modelfile Reference**
   - https://github.com/ollama/ollama/blob/main/docs/modelfile.md
   - All available parameters and options

3. **LoRA Paper** (academic but worth skimming)
   - "LoRA: Low-Rank Adaptation of Large Language Models"
   - https://arxiv.org/abs/2106.09685

4. **Docker Volumes Documentation**
   - https://docs.docker.com/storage/volumes/
   - Master data persistence

### Hands-on Challenges

1. **Add a new quantization option**: Implement q2_k (2-bit) export. Compare quality vs. q4_k_m.

2. **Create a model comparison script**: Export the same experiment with f16, q8, q4. Benchmark inference speed for all three.

3. **Build a model registry UI**: Write a simple Python script that lists all exported models with their metadata (size, quantization, export date).

4. **Implement automatic base model downloading**: Modify the export script to check if the base model is in Ollama, and auto-download if missing.

---

## 🎓 What You Learned

By completing Agent 5, you now understand:

✅ **LoRA fundamentals**: Adapter weights vs. full models
✅ **GGUF format**: Why it's fast, how quantization works
✅ **Docker deployment**: Containers, volumes, GPU passthrough
✅ **Chat templates**: Why they're critical for LLM inference
✅ **Model serving**: Transforming trained weights into APIs
✅ **System integration**: How to bridge Python training code with C++ inference engines

**Real-world applications**:
- Deploy custom LLMs in production
- Build model registries for ML teams
- Optimize inference cost (quantization)
- Debug model serving issues
- Set up local LLM development environments

---

## 🚀 Next Steps

Your infrastructure is ready. Next:
- **Agent 6** will use your export pipeline in the orchestration script (`iterate.sh`)
- **Agent 2** will query your Ollama API for benchmarking
- **All agents** depend on your Docker setup working reliably

**Pro tip**: Keep the Ollama container running during development. Starting/stopping adds overhead. Just run `docker-compose up -d` once at the start of your session.

---

**You've built the bridge from training to production. Models are useless without inference. Inference is impossible without your work. Well done! 🎉**
