# 🏗️ System Architecture

Deep dive into how the DGX Spark Fast Fine-tuning System works.

---

## Design Philosophy

### Core Principles

1. **Speed First**: Every decision optimized for iteration velocity
2. **Simplicity**: Minimal dependencies, clear data flow
3. **Observability**: Every step logs progress and outputs results
4. **Modularity**: Each agent can run independently
5. **Teachability**: Code explains "why" not just "what"

### The 5-Minute Target

Traditional fine-tuning takes 30+ minutes. Our system achieves 5-10 minutes through:

- **Small model** (500M vs 7B+ params): 14x fewer parameters
- **Unsloth optimizations**: 2x speedup via Flash Attention & custom kernels
- **LoRA training**: Train 0.1% of parameters vs full model
- **4-bit quantization**: 4x less memory, faster compute
- **Local inference**: No API latency, GPU-accelerated

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                         │
│                                                             │
│  Input: ./iterate.sh <name> <dataset> [epochs]             │
│                          ↓                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Agent 6: Orchestrator]                                    │
│  ├─ Validates inputs                                        │
│  ├─ Tracks timing                                           │
│  ├─ Chains agents 1→5→2→3→4                                │
│  └─ Logs to experiments/log.json                            │
│                          ↓                                  │
├─────────────────────────────────────────────────────────────┤
│                   TRAINING PHASE                            │
│                                                             │
│  [Agent 1: Fast Training]                                   │
│  ├─ Loads Qwen2.5-0.5B with Unsloth                        │
│  ├─ Applies LoRA adapters (r=8)                            │
│  ├─ Trains with SFTTrainer                                 │
│  └─ Saves to experiments/<name>/lora/                      │
│      Time: 3-5 minutes                                      │
│                          ↓                                  │
├─────────────────────────────────────────────────────────────┤
│                   EXPORT PHASE                              │
│                                                             │
│  [Agent 5: Infrastructure]                                  │
│  ├─ Merges LoRA with base model                            │
│  ├─ Converts to GGUF format                                │
│  ├─ Creates Ollama Modelfile                               │
│  └─ Imports to Ollama registry                             │
│      Time: ~30 seconds                                      │
│                          ↓                                  │
├─────────────────────────────────────────────────────────────┤
│                  EVALUATION PHASE                           │
│                                                             │
│  [Agent 2: Benchmark]                                       │
│  ├─ Loads 10 test prompts                                  │
│  ├─ Queries base model (qwen2.5:0.5b)                      │
│  ├─ Queries fine-tuned model                               │
│  └─ Saves benchmark/results/{base,finetuned}.json          │
│      Time: ~1 minute                                        │
│                          ↓                                  │
│  [Agent 3: Delta Calculator]                                │
│  ├─ Compares responses                                      │
│  ├─ Calculates metrics (length, keywords, similarity)      │
│  ├─ Assesses overall change                                │
│  └─ Saves benchmark/results/deltas.json                    │
│      Time: <1 second                                        │
│                          ↓                                  │
│  [Agent 4: Visualization]                                   │
│  ├─ Renders HTML template                                  │
│  ├─ Populates with delta data                              │
│  └─ Saves benchmark/results/report.html                    │
│      Time: <1 second                                        │
│                          ↓                                  │
├─────────────────────────────────────────────────────────────┤
│                    OUTPUT                                   │
│                                                             │
│  ✓ Trained model: experiments/<name>/                      │
│  ✓ Benchmark results: benchmark/results/                   │
│  ✓ HTML report: benchmark/results/report.html              │
│  ✓ Experiment log: experiments/log.json                    │
│                                                             │
│  Total Time: 5-10 minutes                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent Deep Dive

### Agent 1: Fast Training Pipeline

**File**: `train.py`

**Responsibilities**:
- Load base model with memory optimizations
- Configure LoRA adapters
- Execute training loop
- Save LoRA weights and metadata

**Key Technologies**:

```python
from unsloth import FastLanguageModel  # 2x speedup
from trl import SFTTrainer  # Supervised fine-tuning
from peft import LoraConfig  # Parameter-efficient fine-tuning
```

**Data Flow**:
```
Input: datasets/*.json (Alpaca format)
       ↓
[Load & Format] → Qwen2.5 chat template
       ↓
[Training] → 3-5 minutes
       ↓
Output: experiments/<name>/lora/
        ├─ adapter_model.bin (~10MB)
        ├─ adapter_config.json
        └─ tokenizer files
```

**Performance Optimizations**:
- **4-bit quantization**: 16GB → 4GB memory
- **Gradient checkpointing**: Trade compute for memory
- **Flash Attention 2**: 2x faster attention
- **8-bit AdamW**: 50% less optimizer memory

**Why LoRA?**
```
Full fine-tuning:
- Update all 500M parameters
- Requires 4-8GB per epoch
- Takes 30+ minutes

LoRA (rank=8):
- Update ~500K parameters (0.1%)
- Requires <1GB per epoch
- Takes 3-5 minutes
- 95%+ of full fine-tuning quality
```

---

### Agent 2: Benchmark Suite

**Files**: `benchmark/prompts.py`, `benchmark/run.py`

**Responsibilities**:
- Define standard test prompts
- Query both models via Ollama API
- Record responses and metrics
- Save structured results

**Test Coverage**:
```
10 prompts across 5 categories:
├─ Factual Knowledge (2)     # Knowledge retention
├─ Reasoning (2)              # Logical thinking
├─ Instruction Following (2)  # Task adherence
├─ Conversational (2)         # Natural interaction
└─ Domain-Specific (2)        # Target domain
```

**Data Flow**:
```
[10 prompts] → Ollama API (base model)
              ↓
         [Store responses]
              ↓
         Ollama API (fine-tuned model)
              ↓
         [Store responses]
              ↓
         benchmark/results/{base,finetuned}.json
```

**Result Format**:
```json
{
  "prompt_id": "factual-01",
  "category": "factual_knowledge",
  "prompt": "What is the capital of France?",
  "model": "qwen2.5:0.5b",
  "response": "The capital of France is Paris.",
  "time_ms": 847,
  "tokens": 12,
  "tokens_per_second": 14.2
}
```

---

### Agent 3: Delta Calculator

**File**: `benchmark/delta.py`

**Responsibilities**:
- Load benchmark results
- Calculate comparison metrics
- Assess improvement/regression
- Generate delta report

**Metrics**:

1. **Length Delta**
   ```python
   ratio = len(finetuned) / len(base)
   # < 0.8: shorter
   # 0.8-1.2: similar
   # > 1.2: longer
   ```

2. **Keyword Matching**
   ```python
   matches = [kw for kw in expected if kw in response.lower()]
   match_rate = len(matches) / len(expected)
   ```

3. **Semantic Similarity**
   ```python
   # TF-IDF + Cosine Similarity
   vectorizer = TfidfVectorizer()
   vectors = vectorizer.fit_transform([base, finetuned])
   similarity = cosine_similarity(vectors)[0][1]
   ```

4. **Overall Assessment**
   ```python
   def assess(keyword_delta, length_reasonable, similarity):
       if keyword_delta > 0.2 and length_reasonable:
           return "improved"
       elif keyword_delta < -0.2:
           return "regressed"
       elif similarity > 0.95:
           return "unchanged"
       else:
           return "changed"
   ```

**Why Multiple Metrics?**

No single metric captures everything:
- Length: Verbosity changes
- Keywords: Topical relevance
- Similarity: Overall shift
- Assessment: Holistic view

---

### Agent 4: Visualization

**File**: `benchmark/visualize.py`

**Responsibilities**:
- Load delta results
- Render HTML template
- Create interactive report
- Save to file

**Report Components**:

```html
┌─────────────────────────────────────┐
│  HEADER: Title + Timestamp          │
├─────────────────────────────────────┤
│  STATS DASHBOARD                    │
│  [6 Improved] [1 Regressed]         │
│  [2 Changed]  [1 Unchanged]         │
├─────────────────────────────────────┤
│  CATEGORY FILTER                    │
│  [All] [Factual] [Reasoning] ...    │
├─────────────────────────────────────┤
│  PROMPT CARDS (for each prompt)     │
│  ┌───────────────────────────────┐  │
│  │ Prompt: "What is ML?"         │  │
│  │ Badge: IMPROVED               │  │
│  ├───────────────────────────────┤  │
│  │ Metrics: Keywords 2→3         │  │
│  │          Length 45→67         │  │
│  │          Similarity 0.73      │  │
│  ├───────────────────────────────┤  │
│  │ Base Response | Fine-tuned    │  │
│  │ (side by side)                │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Design Choices**:
- **Static HTML**: No server needed, portable
- **Inline CSS**: No external dependencies
- **JavaScript filtering**: Interactive without backend
- **Color coding**: Quick visual assessment

---

### Agent 5: Infrastructure

**Files**: `docker-compose.yml`, `scripts/export_to_ollama.sh`

**Responsibilities**:
- Manage Ollama container
- Export pipeline (LoRA → GGUF → Ollama)
- Model registry management

**Docker Setup**:
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia  # GPU access
              count: 1
              capabilities: [gpu]
    ports:
      - "11434:11434"
    volumes:
      - ./ollama-models:/root/.ollama  # Persistent storage
```

**Export Pipeline**:
```bash
1. Merge LoRA + Base Model
   ├─ Load LoRA adapters
   ├─ Load base model
   └─ Merge weights

2. Convert to GGUF
   ├─ Serialize to GGUF format
   └─ Apply quantization (optional)

3. Create Modelfile
   ├─ Specify format
   ├─ Set parameters
   └─ Define template

4. Import to Ollama
   └─ ollama create <name> -f Modelfile
```

**Why Ollama?**
- **Fast**: Optimized inference engine
- **Simple**: REST API, no complex setup
- **Portable**: Works on CPU or GPU
- **Compatible**: GGUF format, standard models

---

### Agent 6: Orchestrator

**File**: `iterate.sh`

**Responsibilities**:
- Validate inputs
- Chain all agents
- Track timing
- Log experiments
- Handle errors gracefully

**Execution Flow**:
```bash
1. Validate
   ├─ Check experiment name
   ├─ Check dataset exists
   └─ Confirm with user

2. Train (Agent 1)
   └─ python train.py <name> <dataset> --epochs <n>

3. Export (Agent 5)
   └─ ./scripts/export_to_ollama.sh <name>

4. Benchmark (Agent 2)
   ├─ Check base model exists
   └─ python benchmark/run.py <name>

5. Analyze (Agent 3)
   └─ python benchmark/delta.py

6. Visualize (Agent 4)
   └─ python benchmark/visualize.py

7. Log
   └─ Append to experiments/log.json
```

**Error Handling**:
- `set -e`: Exit on first error
- Each step verified before proceeding
- Clear error messages
- Timing logged even on failure

---

## Data Formats

### Training Data (Alpaca Format)

```json
[
  {
    "instruction": "Question or task",
    "input": "Optional context",
    "output": "Expected response"
  }
]
```

**Transformed to Qwen2.5 Format**:
```
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
{instruction}
{input}<|im_end|>
<|im_start|>assistant
{output}<|im_end|>
```

### Benchmark Results

```json
{
  "prompt_id": "unique-id",
  "category": "category_name",
  "prompt": "prompt text",
  "model": "model name",
  "response": "model response",
  "time_ms": 847,
  "tokens": 42,
  "tokens_per_second": 49.5,
  "error": null
}
```

### Delta Results

```json
{
  "prompt_id": "unique-id",
  "base_response": "...",
  "finetuned_response": "...",
  "length": {
    "base_length": 45,
    "finetuned_length": 67,
    "delta": 22,
    "ratio": 1.49,
    "assessment": "longer"
  },
  "keywords": {
    "base": {"match_count": 2, "match_rate": 0.67},
    "finetuned": {"match_count": 3, "match_rate": 1.0},
    "improvement": 0.33
  },
  "similarity": {
    "similarity": 0.73,
    "assessment": "somewhat_similar"
  },
  "overall_assessment": "improved"
}
```

### Experiment Log

```json
{
  "experiment_name": "exp-001",
  "timestamp": "2024-01-15T14:30:00",
  "dataset": "datasets/example-chatbot.json",
  "epochs": 3,
  "timing": {
    "total_minutes": 6.2,
    "train_seconds": 245,
    "export_seconds": 28,
    "benchmark_seconds": 72,
    "delta_seconds": 1,
    "viz_seconds": 1
  },
  "results": {
    "improved": 6,
    "regressed": 1,
    "changed": 2,
    "unchanged": 1
  }
}
```

---

## Performance Characteristics

### Time Breakdown (100 samples, 3 epochs)

| Component | Time | % of Total |
|-----------|------|------------|
| Model loading | 20s | 5% |
| Training | 240s | 65% |
| LoRA merge | 15s | 4% |
| GGUF conversion | 10s | 3% |
| Ollama import | 5s | 1% |
| Benchmark (20 queries) | 60s | 16% |
| Delta calculation | 1s | <1% |
| Visualization | 1s | <1% |
| **Total** | **~6 min** | **100%** |

### Scalability

| Dataset Size | Training Time | Total Time |
|--------------|---------------|------------|
| 20 samples | 1-2 min | 3-4 min |
| 50 samples | 2-3 min | 4-5 min |
| 100 samples | 3-5 min | 5-7 min |
| 200 samples | 6-8 min | 8-10 min |
| 500 samples | 12-15 min | 14-17 min |

### Resource Usage

| Component | GPU VRAM | System RAM | Disk |
|-----------|----------|------------|------|
| Training | 3-4 GB | 8 GB | 10 MB |
| Export | 4-6 GB | 12 GB | 500 MB |
| Ollama (loaded) | 2 GB | 4 GB | 500 MB |
| **Peak** | **6 GB** | **16 GB** | **1 GB** |

---

## Extension Points

### Adding New Metrics (Agent 3)

```python
def calculate_custom_metric(base, finetuned):
    # Your logic here
    return {
        "metric_name": value,
        "interpretation": "good/bad/neutral"
    }

# Add to compare_results():
delta["custom"] = calculate_custom_metric(base, finetuned)
```

### Adding New Prompts (Agent 2)

```python
# In benchmark/prompts.py
BENCHMARK_PROMPTS.append({
    "id": "custom-01",
    "category": "custom_category",
    "prompt": "Your prompt here",
    "expected_keywords": ["keyword1", "keyword2"],
    "reasoning": "Why this prompt matters"
})
```

### Custom Training Config (Agent 1)

```python
# In train.py, modify:
LORA_RANK = 16  # More capacity
BATCH_SIZE = 8  # Faster training
LEARNING_RATE = 5e-4  # More aggressive
```

---

## Design Decisions & Trade-offs

### Why Qwen2.5-0.5B?

**Pros**:
- Ultra-fast training (3-5 min)
- Low memory footprint
- Multilingual support
- Recent model (2024)

**Cons**:
- Lower capability than 7B+ models
- Limited context (2048 tokens)

**Alternative**: Phi-3-mini (3.8B) for better quality but slower training (10-15 min)

### Why LoRA over Full Fine-tuning?

**Pros**:
- 100x fewer parameters to train
- 2-3x faster
- 10x less disk space
- Same quality for most tasks

**Cons**:
- Slightly lower ceiling for quality
- Can't fundamentally change model behavior

**Alternative**: Full fine-tuning for production deployments

### Why Ollama over HF Transformers?

**Pros**:
- 3x faster inference
- Simple API
- CPU + GPU support
- Easy model management

**Cons**:
- Requires GGUF conversion
- Less control over generation
- Separate process

**Alternative**: Use transformers for more control, but slower

### Why TF-IDF over Embeddings?

**Pros**:
- Instant (no model loading)
- Interpretable
- Good for comparing similar texts

**Cons**:
- Misses semantic meaning
- Sensitive to word choice

**Alternative**: sentence-transformers for semantic similarity (slower)

---

## Future Enhancements

### Short-term (Easy)

- [ ] More benchmark categories
- [ ] Configurable hyperparameters via CLI
- [ ] Comparison across multiple experiments
- [ ] Export report as PDF

### Medium-term (Moderate)

- [ ] Automatic hyperparameter tuning
- [ ] Multi-GPU training support
- [ ] Streaming visualization updates
- [ ] Integration with W&B/MLflow

### Long-term (Complex)

- [ ] Web dashboard for experiment management
- [ ] Distributed training across nodes
- [ ] Automatic dataset quality analysis
- [ ] Reinforcement learning from human feedback

---

## Conclusion

The system achieves 5-10 minute iterations through:
1. **Smart model selection** (500M params)
2. **Efficient training** (LoRA + Unsloth + 4-bit)
3. **Fast inference** (Ollama + GGUF)
4. **Automated pipeline** (iterate.sh)
5. **Minimal overhead** (simple formats, static HTML)

Every component optimized for speed while maintaining quality and teachability.
