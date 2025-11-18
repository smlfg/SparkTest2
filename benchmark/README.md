# Agent 2: Benchmark Suite (HARDENED v2.0)

**The Quality Gatekeeper** - Systematic testing for fine-tuned models

## What This Does

Automatically tests your fine-tuned model against a base model using 10 standard prompts, providing objective data on improvements and regressions.

```
Manual Testing: 10-15 minutes, subjective, error-prone
Automated (This): 1-2 minutes, objective, reproducible
```

## 🛡️ Robustness Features (v2.0)

- **Retry Logic**: 3 attempts with exponential backoff (2s, 4s)
- **Progressive Timeouts**: 60s → 120s → 180s (handles cold starts)
- **Model Warmup**: Eliminates first-query slowness
- **Empty Response Detection**: Warns if model returns empty strings
- **Comprehensive Error Reporting**: Statistics and warnings
- **Connection Resilience**: Retries Ollama connection on failure

**Tested against**: Cold starts, network glitches, GPU throttling

## Quick Start

### 1. Prerequisites

- Ollama running (via Docker Compose from Agent 5)
- Base model available: `qwen2.5:0.5b`
- Fine-tuned model exported to Ollama: `exp-001`

### 2. Run Benchmark

```bash
cd benchmark
python run.py --finetuned exp-001
```

### 3. Check Results

```bash
ls -lh results/
# base.json       - Base model responses
# finetuned.json  - Fine-tuned model responses
```

## Usage Examples

### Basic Usage
```bash
python run.py --finetuned exp-001
```

### Custom Base Model
```bash
python run.py --base qwen2.5:1.5b --finetuned exp-001
```

### Remote Ollama Instance
```bash
python run.py --finetuned exp-001 --ollama-url http://192.168.1.100:11434
```

## File Structure

```
benchmark/
├── README.md           # This file
├── prompts.py          # 10 standard test prompts
├── run.py              # Benchmark runner (main script)
└── results/            # Generated output
    ├── base.json       # Base model responses
    └── finetuned.json  # Fine-tuned model responses
```

## The 10 Standard Prompts

Our benchmark suite covers 6 categories:

1. **Factual QA** (2 prompts)
   - Capital cities
   - Basic math

2. **Translation** (2 prompts)
   - English → German
   - German → English

3. **Instruction Following** (2 prompts)
   - List generation
   - Greeting creation

4. **Classification** (2 prompts)
   - Sentiment analysis (positive/negative)

5. **Code Generation** (1 prompt)
   - Simple Python function

6. **Explanation** (1 prompt)
   - Explain ML concepts

**Why 10?** Trade-off between coverage (enough diversity) and speed (runs in ~1 minute).

## Output Format

### base.json / finetuned.json

```json
[
  {
    "prompt_id": "factual_capital",
    "prompt": "Was ist die Hauptstadt von Deutschland?",
    "response": "Die Hauptstadt von Deutschland ist Berlin.",
    "metadata": {
      "category": "factual",
      "ground_truth": "Berlin",
      "keywords": null,
      "latency_seconds": 0.8,
      "response_length": 42
    }
  },
  ...
]
```

### Metadata Fields

- **category**: Prompt type (factual, translation, code, etc.)
- **ground_truth**: Expected answer (for exact matching)
- **keywords**: Acceptable terms (for flexible matching)
- **latency_seconds**: Inference time
- **response_length**: Response size in characters

## Integration with Other Agents

```
Agent 1: Trains model
    ↓
Agent 5: Exports to Ollama ("exp-001")
    ↓
┌─────────────────────────────────────┐
│  Agent 2: Benchmark (YOU ARE HERE)  │
│  Output: base.json, finetuned.json  │
└─────────────────────────────────────┘
    ↓
Agent 3: Calculate Delta
    ↓
Agent 4: Visualize
```

**What you need**: Ollama + base model + fine-tuned model
**What you provide**: JSON results for Agent 3 to analyze

## Customization

### Add a New Prompt

Edit `prompts.py`:

```python
BENCHMARK_PROMPTS = [
    # ... existing prompts ...
    {
        "id": "my_custom_test",
        "prompt": "Your test prompt here",
        "category": "custom",
        "ground_truth": "Expected answer",  # OR
        "keywords": ["keyword1", "keyword2"],
    },
]
```

### Change Temperature

Edit `run.py`:

```python
def query_ollama(model_name: str, prompt: str, max_tokens: int = 200):
    payload = {
        ...
        "options": {
            "temperature": 0.5,  # Change from 0.7 to 0.5
            ...
        }
    }
```

### Reduce Benchmark Time

```python
# Option 1: Fewer tokens
"num_predict": 100,  # Instead of 200

# Option 2: Subset of prompts (for development)
BENCHMARK_PROMPTS = BENCHMARK_PROMPTS[:5]  # First 5 only
```

## Robustness Testing

### How v2.0 Handles Real-World Failures

**Scenario 1: Cold Start (Ollama just restarted)**
```
Before (v1.0): ❌ Timeout after 30s → Benchmark fails
After (v2.0):  ⏱️  Timeout, retrying with 120s timeout → ✅ Success
```

**Scenario 2: Network Glitch**
```
Before: ❌ Connection error → Benchmark fails
After:  🔌 Connection error, retrying in 2s → ✅ Success
```

**Scenario 3: Empty Response**
```
Before: ✅ (0.8s, 0 chars) → User doesn't notice
After:  ⚠️  EMPTY (0.8s) → Clear warning + summary
```

**Test It Yourself**:
```bash
# Simulate cold start
docker-compose restart ollama && sleep 5
python run.py --finetuned exp-001  # Should succeed!
```

## Troubleshooting

### Error: "Model not found in Ollama"

```bash
# Check what models are available
curl http://localhost:11434/api/tags | jq '.models[].name'

# If your model is missing, re-run Agent 5 export
./scripts/export_to_ollama.sh experiments/exp-001/lora exp-001
```

### Error: "Error connecting to Ollama"

```bash
# Check if Ollama is running
docker-compose ps

# If not running, start it
docker-compose up -d

# Check logs
docker logs ollama
```

### Empty Responses

```json
{"response": "", ...}
```

**Causes**:
1. Model crashed (out of memory)
2. Timeout too short (increase from 30s)
3. Malformed prompt

**Debug**:
```bash
# Test manually
curl -X POST http://localhost:11434/api/generate \
  -d '{
    "model": "exp-001",
    "prompt": "Test",
    "stream": false
  }'
```

### Slow Performance (>5 minutes)

**Expected**: 1-2 minutes total

**Causes**:
- Model too large (not 0.5B)
- num_predict too high
- GPU throttling

**Solutions**:
- Use smaller model: `--base qwen2.5:0.5b`
- Reduce tokens: `"num_predict": 100`
- Check GPU: `nvidia-smi`

## Performance

**Typical Timing** (Qwen2.5-0.5B):
```
Phase 1 (Base model):       30-60 seconds
Wait:                       5 seconds
Phase 2 (Fine-tuned model): 30-60 seconds
─────────────────────────────────────────
Total:                      65-125 seconds (~1-2 minutes)
```

**Per-prompt latency**: 0.5-1.5 seconds
**Total prompts**: 20 (10 × 2 models)

## Command Line Options

```bash
python run.py --help
```

```
--base          Base model name (default: qwen2.5:0.5b)
--finetuned     Fine-tuned model name (required)
--ollama-url    Ollama API URL (default: http://localhost:11434)
```

## Next Steps

After running the benchmark:

1. **Check results**:
   ```bash
   cat results/base.json | jq '.[0]'
   cat results/finetuned.json | jq '.[0]'
   ```

2. **Run Agent 3** (Delta Calculator):
   ```bash
   python benchmark/delta.py
   ```

3. **View HTML Report** (Agent 4):
   ```bash
   open benchmark/results/report.html
   ```

## Learning Resources

- **Teaching Guide**: See `docs/agents/agent2_teaching.md`
- **Prompt Design**: See comments in `prompts.py`
- **API Integration**: See comments in `run.py`

## Success Criteria

✅ Runs in <2 minutes
✅ Outputs both JSON files
✅ 10 prompts in each file
✅ Non-empty responses
✅ Prompt validation works

## Architecture Principles

**Speed**: 1-2 minutes per iteration
**Simplicity**: Single Python script, no complex dependencies
**Teachability**: Extensive inline comments
**Reproducibility**: Same prompts every run

---

**Built with ❤️ as part of the DGX Fast Fine-tuning Iteration Lab**
