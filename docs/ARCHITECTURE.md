# System Architecture

## Overview

The DGX Fast Fine-tuning Iteration Lab is designed as a modular pipeline where each agent has a specific responsibility. This document explains how the components integrate and why the system is designed this way.

## Design Philosophy

### 1. **Speed First**
Every component is optimized for fast iteration. We use:
- Small models (500M params)
- LoRA adapters (0.1% of params trained)
- 4-bit quantization
- Unsloth (2x speedup)
- Local inference with Ollama

**Goal**: Complete one iteration in <10 minutes

### 2. **Modular Components**
Each agent can be run independently or as part of the full pipeline:
- Test individual components during development
- Debug specific stages without re-running everything
- Customize workflow for different use cases

### 3. **Systematic Evaluation**
Always compare against baseline:
- Prevents "feels better" bias
- Quantifies improvements
- Tracks regressions
- Enables data-driven iteration decisions

### 4. **Learning-Oriented**
Code includes extensive teaching comments:
- Explains "why" not just "what"
- References concepts (LoRA, quantization, etc.)
- Includes learning objectives
- Helps users understand, not just use

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                       │
│                    (Agent 6: iterate.sh)                     │
│  - Coordinates all agents                                    │
│  - Tracks timing and metrics                                 │
│  - Maintains experiment log                                  │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Agent 1       │  │   Agent 5       │  │   Agent 2       │
│   Training      │─▶│   Export        │─▶│   Benchmark     │
│                 │  │                 │  │                 │
│ - Unsloth       │  │ - LoRA merge    │  │ - Base model    │
│ - LoRA          │  │ - GGUF convert  │  │ - Fine-tuned    │
│ - 4-bit quant   │  │ - Ollama import │  │ - 10 prompts    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                                                    │
                              ┌─────────────────────┘
                              ▼
                     ┌─────────────────┐
                     │   Agent 3       │
                     │   Delta         │
                     │                 │
                     │ - Compare       │
                     │ - Metrics       │
                     │ - Assess        │
                     └─────────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   Agent 4       │
                     │   Visualize     │
                     │                 │
                     │ - HTML report   │
                     │ - Interactive   │
                     │ - Shareable     │
                     └─────────────────┘
```

---

## Data Flow

### 1. Training Data → Agent 1

**Input**: JSON dataset with chat format
```json
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**Output**: LoRA adapters
- Location: `experiments/{name}/lora/`
- Size: ~50MB (vs 1GB full model)
- Format: SafeTensors + config

**Why LoRA?**
- Fast training (3-5 min vs 30+ min)
- Memory efficient
- Prevents catastrophic forgetting

### 2. LoRA Adapters → Agent 5

**Input**: LoRA adapters from Agent 1

**Process**:
1. Merge adapters with base model → Full model
2. Convert to GGUF → Quantized format
3. Create Modelfile → Ollama config
4. Import to Ollama → Ready for inference

**Output**: Ollama model `{experiment-name}`

**Why GGUF?**
- Optimized for CPU/GPU inference
- Smaller size (quantized)
- Fast loading in Ollama

### 3. Ollama Models → Agent 2

**Input**: Two models
- Base: `qwen2.5:0.5b`
- Fine-tuned: `{experiment-name}`

**Process**:
- Run 10 standard prompts through both models
- Collect responses + metadata (tokens, time)

**Output**: JSON files
- `benchmark/results/base.json`
- `benchmark/results/finetuned.json`

**Why 10 prompts?**
- Fast enough for iteration (<2 min)
- Diverse enough to catch regressions
- Standardized for comparison

### 4. Benchmark Results → Agent 3

**Input**: Base + fine-tuned responses

**Process**:
- Calculate length deltas
- Measure similarity (cosine, sequence)
- Assess change (IMPROVED/REGRESSED/CHANGED/UNCHANGED)

**Output**: `benchmark/results/deltas.json`

**Metrics explained**:
- **Length delta**: Response verbosity change
- **Cosine similarity**: Semantic similarity (0-1)
- **Sequence ratio**: Character-level similarity (0-1)
- **Assessment**: Heuristic judgment

### 5. Deltas → Agent 4

**Input**: Delta analysis JSON

**Process**:
- Render HTML template with Jinja2
- Generate summary dashboard
- Create side-by-side comparisons
- Add interactive filters

**Output**: `benchmark/results/report.html`

**Why HTML?**
- Single file, easy to share
- Works offline
- Interactive (filter by assessment)
- Archives well

### 6. All Outputs → Agent 6

**Input**: Metadata from all stages

**Process**:
- Log experiment with:
  - Timing breakdown
  - Assessment counts
  - Improvement rate
  - File locations

**Output**: `experiments/log.json`

**Why track?**
- Compare across iterations
- Identify best experiments
- Track progress over time

---

## Integration Points

### Environment Variables
None required! System uses:
- Default Ollama port: 11434
- Local Docker socket
- Filesystem paths (relative)

### Dependencies Between Agents

**Hard dependencies** (must run in order):
1. Agent 1 → Agent 5 (needs LoRA to export)
2. Agent 5 → Agent 2 (needs Ollama model)
3. Agent 2 → Agent 3 (needs both responses)
4. Agent 3 → Agent 4 (needs deltas)

**Soft dependencies** (can be skipped):
- Agent 6 can run without previous stages (if files exist)
- Agent 2 can skip base model (use existing results)
- Agent 4 can re-run without Agent 3 (use cached deltas)

---

## Error Handling

### Agent 1 (Training)
- **Dataset not found**: Clear error, suggest location
- **Out of memory**: Reduce batch size or sequence length
- **CUDA errors**: Fall back to CPU (slower but works)

### Agent 5 (Export)
- **Ollama not running**: Check Docker, provide start command
- **Conversion fails**: Log detailed error, suggest llama.cpp check
- **Import fails**: Verify Modelfile format, check disk space

### Agent 2 (Benchmark)
- **Ollama API timeout**: Increase timeout, check model loaded
- **Model not found**: List available models, suggest export
- **Partial results**: Save what succeeded, warn about missing

### Agent 3 (Delta)
- **Results mismatch**: Warn about missing IDs, continue with matches
- **Empty results**: Clear error, suggest re-running benchmark

### Agent 4 (Visualize)
- **Template error**: Log Jinja2 error, suggest format check
- **Missing data**: Generate partial report with warnings

### Agent 6 (Orchestrate)
- **Stage failure**: Stop pipeline, report last successful stage
- **Timeout**: Configurable per-stage timeouts
- **Disk space**: Check before training (large files)

---

## Performance Characteristics

### Time Breakdown (Target)

| Stage | Time | % of Total |
|-------|------|------------|
| Training (Agent 1) | 3-5 min | 60% |
| Export (Agent 5) | 30-60 sec | 10% |
| Benchmark (Agent 2) | 1-2 min | 25% |
| Delta (Agent 3) | <5 sec | <1% |
| Visualize (Agent 4) | <5 sec | <1% |
| Log (Agent 6) | <5 sec | <1% |
| **TOTAL** | **<10 min** | **100%** |

### Resource Usage

**Training (Agent 1)**:
- GPU Memory: 8-12 GB
- CPU Memory: 16 GB
- Disk: 200 MB (LoRA adapters)

**Export (Agent 5)**:
- CPU Memory: 8 GB
- Disk: 1.5 GB (merged + GGUF)

**Benchmark (Agent 2)**:
- GPU Memory: 4 GB (if GPU) or CPU only
- Network: Local (Ollama)

**Other Agents**: Minimal (<1 GB memory, negligible disk)

---

## Customization Points

### Change Base Model
Edit `iterate.sh`:
```bash
BASE_MODEL="qwen2.5:1.5b"  # Or any compatible model
```

Update `train.py`:
```python
model_name="unsloth/Qwen2.5-1.5B-Instruct"
```

### Change Hyperparameters
Edit `iterate.sh` or pass to `train.py`:
```bash
python3 train.py \
    --epochs 5 \
    --lr 5e-4 \
    --lora-rank 16
```

### Customize Benchmark Prompts
Edit `benchmark/prompts.py`:
```python
BENCHMARK_PROMPTS = [
    # Your domain-specific prompts
]
```

### Modify Assessment Logic
Edit `benchmark/delta.py`:
```python
def assess_change(self, ...):
    # Custom heuristics or LLM-based assessment
```

### Change HTML Styling
Edit `benchmark/visualize.py`:
```python
HTML_TEMPLATE = """
    <!-- Custom CSS and layout -->
"""
```

---

## Extension Ideas

### Multi-Model Comparison
Compare multiple fine-tuned models:
```bash
./iterate.sh exp-001 data1.json
./iterate.sh exp-002 data2.json
python benchmark/compare_experiments.py exp-001 exp-002
```

### Automated Hyperparameter Search
Grid search over learning rates:
```bash
for lr in 1e-4 2e-4 5e-4; do
    ./iterate.sh exp-lr-${lr} data.json --lr ${lr}
done
```

### LLM-Based Assessment
Replace heuristics in Agent 3 with LLM judge:
```python
def assess_with_llm(base_resp, ft_resp, expected):
    prompt = f"Which response is better?..."
    return llm.generate(prompt)
```

### Continuous Monitoring
Watch for new datasets and auto-run:
```bash
inotifywait -m datasets/ -e create |
while read path action file; do
    ./iterate.sh auto-${timestamp} ${path}${file}
done
```

---

## Best Practices

### 1. Version Control
- Git track: code, configs, prompts
- Git ignore: models, checkpoints, results (large files)
- Tag successful experiments

### 2. Experiment Naming
Use descriptive names:
- `customer-support-v1` (good)
- `exp-001` (okay for testing)
- `test` (bad - unclear)

### 3. Dataset Quality
- Start small (10-20 examples)
- Ensure format consistency
- Balance training data
- Iterate based on delta analysis

### 4. Baseline Comparison
- Always run base model comparison
- Don't skip delta analysis
- Track improvement rate over time

### 5. Documentation
- Note why you made dataset changes
- Document unexpected results
- Save reports for each iteration

---

## Troubleshooting

### Training is too slow
1. Reduce `--max-seq-length` (2048 → 1024)
2. Reduce `--batch-size` (4 → 2)
3. Check GPU utilization with `nvidia-smi`
4. Verify Unsloth installed correctly

### No improvements in benchmarks
1. Check if training data matches test prompts
2. Increase epochs (3 → 5)
3. Try higher learning rate (2e-4 → 5e-4)
4. Review training loss (should decrease)

### Ollama out of memory
1. Use CPU inference (slower but works)
2. Reduce model size (0.5B → smaller)
3. Close other applications
4. Increase Docker memory limit

### Export fails
1. Check disk space (need 2-3 GB)
2. Verify llama.cpp installed
3. Try manual merge and conversion
4. Check Modelfile format

---

## Security Considerations

### Model Safety
- Models inherit biases from training data
- Test for harmful outputs before deployment
- Don't train on sensitive data without precautions

### Docker Security
- Ollama runs with default permissions
- Models stored in Docker volume (not directly accessible)
- Consider running Docker rootless for production

### Data Privacy
- Training data stored locally (not sent to cloud)
- Results contain model outputs (review before sharing)
- Experiment log may contain dataset paths (be careful)

---

## Future Improvements

### Planned Features
- [ ] Web UI for experiment tracking
- [ ] Automatic dataset augmentation
- [ ] Multi-GPU training support
- [ ] Experiment comparison dashboard
- [ ] LLM-based response assessment
- [ ] Integration with HuggingFace Hub

### Community Contributions
We welcome:
- New benchmark prompt sets (domain-specific)
- Alternative visualization templates
- Performance optimizations
- Documentation improvements
- Bug fixes and error handling

---

## References

**Concepts**:
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [Unsloth Documentation](https://github.com/unslothai/unsloth)
- [GGUF Format](https://github.com/ggerganov/llama.cpp/blob/master/gguf-py/README.md)
- [Ollama Documentation](https://github.com/ollama/ollama)

**Tools**:
- [Qwen2.5 Models](https://huggingface.co/Qwen)
- [TRL Library](https://github.com/huggingface/trl)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)

---

**Questions?** Check QUICKSTART.md or open an issue!
