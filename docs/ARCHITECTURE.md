# System Architecture

## Overview

The DGX Fast Fine-tuning System is designed around one core principle: **minimize iteration time to maximize learning**.

Traditional fine-tuning: 30+ minutes per iteration
Our system: 5-7 minutes per iteration

This 5-6x speedup enables true rapid experimentation.

## Design Philosophy

### 1. Speed Over Perfection

Every design decision prioritizes iteration velocity:
- Small model (Qwen2.5-0.5B) → fast training
- LoRA adapters → minimal parameters to train
- 4-bit quantization → fits in memory
- Unsloth → 2x training speedup
- Ollama → instant inference
- Static HTML reports → no server needed

### 2. Systematic Evaluation

Humans are bad at remembering "did that improve?"
Solution: Automated comparison with base model

Every iteration produces:
- Quantitative metrics (length, similarity, timing)
- Qualitative assessment (improved/regressed/changed)
- Visual report (easy to scan)
- Archived results (compare across iterations)

### 3. Fail Fast, Learn Fast

Make it trivially easy to try new ideas:
- One command: `./iterate.sh exp-001 dataset.json`
- Clear success/failure signals
- Low cost per iteration (5 minutes, not 30)
- Experiment tracking (know what you tried)

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     iterate.sh (Agent 6)                     │
│                    Orchestrates everything                   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Agent 1     │    │   Agent 5     │    │   Agent 2     │
│   Training    │───▶│   Export      │───▶│   Benchmark   │
│               │    │               │    │               │
│ train.py      │    │ export_to     │    │ run.py        │
│               │    │ _ollama.sh    │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
                                                   │
                                                   ▼
                                          ┌───────────────┐
                                          │   Agent 3     │
                                          │   Delta       │
                                          │   Analysis    │
                                          │ delta.py      │
                                          └───────────────┘
                                                   │
                                                   ▼
                                          ┌───────────────┐
                                          │   Agent 4     │
                                          │   Visualize   │
                                          │ visualize.py  │
                                          └───────────────┘
```

### Agent 1: Training (`train.py`)

**Purpose**: Fine-tune model as fast as possible

**Key Technologies**:
- Unsloth: Optimized training (2x faster than HuggingFace)
- LoRA: Only train 1% of parameters
- 4-bit quantization: Fit in limited memory
- Qwen2.5-0.5B: Small but capable model

**Inputs**:
- Training dataset (JSON)
- Hyperparameters (epochs, learning rate, etc.)

**Outputs**:
- LoRA adapter weights
- Training metadata (loss, timing, config)

**Time**: 3-5 minutes (for 20 examples, 3 epochs)

**Design Choices**:
- Why Qwen2.5-0.5B? Best quality/speed tradeoff at 500M params
- Why LoRA rank 8? Sufficient for most tasks, very fast
- Why 3 epochs? Sweet spot for small datasets (prevents overfit)
- Why 4-bit? 4x memory savings, minimal quality loss

### Agent 5: Export (`export_to_ollama.sh`)

**Purpose**: Convert trained model to inference-ready format

**Pipeline**:
1. Merge LoRA adapters with base model
2. (Optional) Convert to GGUF format
3. Import to Ollama model registry

**Why This Approach**:
- Merging: Simplifies inference (no adapter loading)
- Ollama: Consistent API for all models
- GGUF: Enables CPU inference (portable)

**Time**: 30 seconds

**Design Choices**:
- Why merge? Could use adapters directly, but merging is simpler
- Why Ollama? Could use HuggingFace transformers, but Ollama is faster
- Why GGUF? Makes model portable (can run on any device)

### Agent 2: Benchmark (`benchmark/run.py`)

**Purpose**: Test models systematically

**Process**:
1. Load standard prompts
2. Run each prompt on base model
3. Run each prompt on fine-tuned model
4. Save results as JSON

**Key Features**:
- Consistent parameters (same temperature, etc.)
- Timing metrics (is fine-tuned slower?)
- Extensible prompts (add domain-specific tests)

**Time**: ~1 minute (10 prompts × 2 models × ~3 seconds each)

**Design Choices**:
- Why 10 prompts? Balance coverage vs. speed
- Why JSON output? Easy to parse, archive, compare
- Why same prompts for all iterations? Tracks improvement over time

### Agent 3: Delta Analysis (`benchmark/delta.py`)

**Purpose**: Quantify differences between base and fine-tuned

**Metrics**:
- Length delta: Is response longer/shorter?
- Word overlap: How similar are responses?
- Correctness: Does it match expected behavior?
- Keywords: Does it use domain terms?

**Assessments**:
- **Improved**: Correctness increased
- **Regressed**: Correctness decreased
- **Changed**: Different but unclear if better
- **Similar**: Minimal change

**Time**: Instant (pure computation)

**Design Choices**:
- Why automated metrics? Humans are inconsistent
- Why simple metrics? Fast to compute, easy to understand
- Why four categories? Sufficient granularity for action

### Agent 4: Visualization (`benchmark/visualize.py`)

**Purpose**: Make results scannable

**Features**:
- Summary statistics (% improved, regressed)
- Side-by-side comparison
- Color coding (green = good, red = bad)
- Self-contained HTML (no server needed)

**Time**: Instant

**Design Choices**:
- Why HTML? Universal, archivable, shareable
- Why static? No server = no complexity
- Why color coding? Fastest way to scan results

### Agent 6: Orchestration (`iterate.sh`)

**Purpose**: One command to run everything

**Responsibilities**:
1. Prerequisites check (Ollama running, base model exists)
2. Sequential execution (train → export → benchmark → analyze → visualize)
3. Error handling (fail fast, clear messages)
4. Timing (track each step, total time)
5. Logging (record experiment for tracking)

**Time**: ~5-7 minutes total

**Design Choices**:
- Why bash? Simple, universal, no dependencies
- Why sequential? Each step depends on previous
- Why strict error handling? Fail fast, don't waste time

## Data Flow

### Training Dataset Format

```json
[
  {
    "messages": [
      {"role": "user", "content": "Question"},
      {"role": "assistant", "content": "Answer"}
    ]
  }
]
```

**Why This Format**:
- Standard chat format (works with any model)
- Flexible (supports multi-turn conversations)
- Simple (easy to create and edit)

### Benchmark Results Format

```json
{
  "model": "exp-001",
  "results": [
    {
      "prompt_id": "greeting",
      "prompt": "Hello!",
      "response": "Hi there!",
      "duration_ms": 234,
      "tokens": 12
    }
  ]
}
```

### Delta Results Format

```json
{
  "deltas": [
    {
      "prompt_id": "greeting",
      "assessment": "improved",
      "assessment_reason": "More natural response",
      "metrics": {
        "length_delta": "+5 chars",
        "word_overlap": 0.6,
        "base_correctness": "partial",
        "finetuned_correctness": "correct"
      }
    }
  ]
}
```

### Experiment Log Format

```json
[
  {
    "experiment_name": "exp-001",
    "timestamp": "2024-01-15T10:30:00",
    "dataset": "datasets/example-chatbot.json",
    "timing": {
      "train": 180,
      "export": 30,
      "benchmark": 60,
      "total": 270
    },
    "results": {
      "improved": 3,
      "regressed": 1,
      "changed": 4,
      "similar": 2
    }
  }
]
```

## Performance Characteristics

### Timing Breakdown (20 examples, 3 epochs)

| Step | Time | % of Total |
|------|------|------------|
| Training | 3-5 min | 60-70% |
| Export | 30s | 8% |
| Benchmark | 1 min | 15-20% |
| Analysis | <5s | <2% |
| Visualization | <5s | <2% |
| **Total** | **5-7 min** | **100%** |

### Optimization Opportunities

**Already Optimized**:
- ✅ Training: Unsloth (2x speedup)
- ✅ Inference: Ollama (optimized)
- ✅ Analysis: Pure computation (instant)

**Could Optimize Further**:
- Export: Could skip GGUF conversion (save ~10s)
- Benchmark: Could run prompts in parallel (save ~30s)
- Training: Could use even smaller model (but quality suffers)

**Bottom Line**: Current design is near-optimal for quality/speed tradeoff.

## Scalability

### Current Limits

| Dimension | Current | Max Tested | Bottleneck |
|-----------|---------|------------|------------|
| Dataset size | 20 examples | 100 examples | Training time |
| Prompts | 10 | 50 | Benchmark time |
| Model size | 0.5B | 1.5B | Memory |
| Concurrent experiments | 1 | 4 | GPU |

### Scaling Up

**More training data** (100+ examples):
- Add `--gradient-accumulation-steps 4` to reduce memory
- Consider 5-10 epochs instead of 3
- Training time scales linearly (~15 minutes for 100 examples)

**More prompts** (50+ benchmark tests):
- Benchmark time scales linearly (~5 minutes for 50 prompts)
- Consider sampling strategy (test subset each iteration)

**Larger model** (1.5B+ parameters):
- Qwen2.5-1.5B works with same code
- Training time ~10-15 minutes (2-3x slower)
- Better quality, but slower iteration

**Multiple GPUs**:
- Unsloth doesn't support multi-GPU well
- Better to run multiple experiments in parallel
- 4 GPUs → 4 concurrent iterations

## Security & Safety

### Model Safety

- Base model (Qwen2.5-0.5B) is pre-trained, not safety-tuned
- Fine-tuning can introduce biases from training data
- Always review training data for harmful content
- Test edge cases in benchmark prompts

### Data Privacy

- All data stays local (no cloud services)
- Ollama runs in Docker (isolated)
- Training data never leaves your machine
- Models are stored locally only

### Reproducibility

- Locked versions in requirements.txt
- Docker images pinned
- Random seeds set (training, LoRA init)
- Metadata saved for every experiment

## Future Extensions

### Possible Improvements

1. **Web Dashboard**: Real-time monitoring of training
2. **Hyperparameter Search**: Auto-tune learning rate, LoRA rank
3. **Multi-Model Comparison**: Test 3+ models in parallel
4. **Advanced Metrics**: Use embedding models for semantic similarity
5. **Automated Dataset Generation**: LLM-generated training examples
6. **Distributed Training**: Multi-GPU, multi-node
7. **Continuous Integration**: Auto-run on dataset changes

### Not Planned (Intentionally)

- **Production deployment**: This is for iteration, not production
- **Complex dashboards**: Static HTML is sufficient
- **Many dependencies**: Keep it simple and portable
- **Large models**: Defeats the purpose (speed)

## Summary

This system is optimized for one thing: **learning as fast as possible**.

Every design choice prioritizes:
1. Iteration velocity (5 minutes, not 30)
2. Systematic evaluation (automated comparison)
3. Simplicity (minimal dependencies, clear code)
4. Reproducibility (logged experiments, versioned)

The result: A system where you can run 10 iterations in 2 hours and truly understand your model's behavior.

**Next**: See `docs/agents/` for per-agent deep dives.
