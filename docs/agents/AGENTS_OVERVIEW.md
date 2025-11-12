# Agents Overview - Deep Learning Guide

This document provides in-depth explanations of each agent's role, the concepts they implement, and how to customize them.

---

## Agent 1: Fast Training Pipeline

### What It Does
Trains Qwen2.5-0.5B with LoRA adapters using Unsloth for 2x speedup.

### Key Concepts

#### LoRA (Low-Rank Adaptation)
**What**: Instead of training all model parameters, LoRA adds small "adapter" matrices to specific layers.

**Why it works**:
- Most neural network weight matrices are "low-rank" (redundant)
- We can approximate updates with two small matrices: A (d × r) and B (r × d)
- Where r << d (rank 8 vs dimension 4096)

**Analogy**:
Think of the base model as a Swiss Army knife with 100 tools. Instead of replacing the whole knife, LoRA adds a few specialized attachments. You get new capabilities without changing the original tools.

**Math**:
```
Standard fine-tuning:  W' = W + ΔW        (update all weights)
LoRA fine-tuning:      W' = W + BA        (B and A are small)

Where:
- W: Original weight matrix (4096 × 4096)
- B: Down-projection (4096 × 8)
- A: Up-projection (8 × 4096)
- Parameters: 4096×4096 vs 2×4096×8
```

**Benefits**:
- 99.9% fewer parameters to train
- 10x faster training
- 20x less memory
- No catastrophic forgetting

#### 4-bit Quantization
**What**: Represent weights with 4 bits instead of 16 bits (or 32 bits).

**How**:
```
16-bit float: 65,536 possible values
4-bit int: 16 possible values

We store:
1. Quantized weights (4 bits each)
2. Scale factor (16 bits, shared across group)
3. Zero point (16 bits, shared across group)

Reconstruction: real_value = scale * (quantized - zero_point)
```

**Benefits**:
- 75% memory reduction (16-bit → 4-bit)
- Faster training (less data movement)
- Minimal quality loss (<1% typically)

**Trade-off**: Slight accuracy loss, but for fine-tuning this is negligible.

#### Unsloth Optimization
**What**: Hand-optimized CUDA kernels for common operations.

**Optimizations**:
1. **Fused kernels**: Combine multiple operations
   - Standard: ReLU → Dropout → LayerNorm (3 passes)
   - Unsloth: Single fused kernel (1 pass)

2. **Flash Attention**: O(N) memory instead of O(N²)
   - Standard attention stores entire NxN matrix
   - Flash Attention computes on-the-fly

3. **Gradient checkpointing**: Trade compute for memory
   - Don't store all activations
   - Recompute during backward pass

**Result**: 2x faster than standard PyTorch/HF.

### Customization Guide

#### Hyperparameters to Tune

**Learning Rate** (`--lr`):
- Default: 2e-4
- Too high: Training unstable, loss explodes
- Too low: Training too slow, underfitting
- Rule of thumb: Start at 2e-4, halve if unstable, double if too slow

**Epochs** (`--epochs`):
- Default: 3
- More epochs = more training, risk of overfitting
- Monitor: If validation loss increases, you're overfitting
- For small datasets (10-50 examples): 3-5 epochs
- For large datasets (1000+ examples): 1-2 epochs

**LoRA Rank** (`--lora-rank`):
- Default: 8
- Higher rank = more capacity, but slower and more memory
- Rank 4: Minimal changes, very fast
- Rank 8: Good balance (recommended)
- Rank 16: Large changes, slower
- Rank 32+: Usually overkill for small models

**Batch Size** (`--batch-size`):
- Default: 4
- Larger = faster training, more memory
- If OOM: Reduce to 2 or 1
- If GPU underutilized: Increase to 8 or 16
- Effective batch size: batch_size × gradient_accumulation_steps

#### Changing Base Model

Edit `train.py`:
```python
# Current (500M params, fast)
model_name="unsloth/Qwen2.5-0.5B-Instruct"

# Smaller (250M params, faster)
model_name="unsloth/Qwen2.5-0.25B"

# Larger (1.5B params, better quality)
model_name="unsloth/Qwen2.5-1.5B-Instruct"

# Different model family
model_name="unsloth/Llama-3.2-1B-Instruct"
```

**Trade-offs**:
- Smaller models: Faster, less capable
- Larger models: Slower, more capable
- Different families: Different strengths (Qwen = multilingual, Llama = English)

#### Advanced: Custom Training Loop

If you need more control:

```python
# In train.py, replace SFTTrainer with:

from transformers import Trainer

class CustomTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        # Custom loss calculation
        outputs = model(**inputs)
        loss = outputs.loss

        # Add custom regularization
        l2_reg = sum(p.pow(2).sum() for p in model.parameters())
        loss = loss + 0.01 * l2_reg

        return (loss, outputs) if return_outputs else loss
```

Use cases:
- Custom loss functions
- Multi-task learning
- Curriculum learning
- Knowledge distillation

---

## Agent 2: Benchmark Suite

### What It Does
Tests both base and fine-tuned models on 10 standard prompts via Ollama API.

### Key Concepts

#### Systematic Evaluation
**Why it matters**: Without systematic testing, you're guessing if fine-tuning worked.

**Principles**:
1. **Controlled**: Same prompts, same settings
2. **Comparative**: Base vs fine-tuned
3. **Diverse**: Cover different task types
4. **Repeatable**: Run multiple times for confidence

#### Test Prompt Design

**Good test prompts**:
- Specific to your domain
- Clear expected behavior
- Cover edge cases
- Diverse difficulty levels

**Example - Customer Support**:
```python
# Too general (bad)
"Help me"

# Specific (good)
"My order #12345 hasn't arrived. It was supposed to be delivered 3 days ago. What should I do?"

# Why good?
- Specific scenario (order not arrived)
- Includes details (order number, timeframe)
- Clear task (needs tracking/resolution)
- Tests knowledge (return policy, tracking process)
```

#### Ollama API Basics

**Architecture**:
```
Your code → HTTP POST → Ollama (localhost:11434) → Model inference → Response
```

**Request format**:
```json
{
  "model": "exp-001",
  "prompt": "Your prompt here",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "num_predict": 512
  }
}
```

**Temperature** (0.0 - 1.0):
- 0.0: Deterministic (same input = same output)
- 0.7: Balanced (recommended for benchmarks)
- 1.0: Creative (more random)

**Why 0.7 for benchmarks?**
- Consistent enough for comparison
- Not so deterministic that it masks model differences

### Customization Guide

#### Custom Prompt Sets

Edit `benchmark/prompts.py`:

```python
# Domain: Medical Q&A
BENCHMARK_PROMPTS = [
    {
        "id": "med_01",
        "category": "symptoms",
        "prompt": "What are the common symptoms of type 2 diabetes?",
        "expected": "Should mention: thirst, frequent urination, fatigue, blurred vision, with medical disclaimer"
    },
    {
        "id": "med_02",
        "category": "medication",
        "prompt": "How does metformin work?",
        "expected": "Should explain mechanism (reduces glucose production) in simple terms"
    },
    # Add 8 more...
]
```

**Prompt categories to include**:
- Core tasks (main use case)
- Edge cases (unusual but valid)
- Negatives (should refuse)
- Comparison (vs alternatives)
- Explanation (why/how questions)

#### Adding Evaluation Metrics

Currently tracks: response text, tokens, time.

To add custom metrics, edit `benchmark/run.py`:

```python
def run_benchmark(client, model_name, prompts):
    for prompt_info in prompts:
        result = client.generate(...)

        # Custom metrics
        full_result = {
            # ... existing fields ...

            # Custom additions
            "response_length": len(result["response"]),
            "word_count": len(result["response"].split()),
            "contains_disclaimer": "I am not a doctor" in result["response"],
            "politeness_score": calculate_politeness(result["response"]),
        }
```

#### Parallel Benchmarking

Speed up by testing prompts in parallel:

```python
from concurrent.futures import ThreadPoolExecutor

def run_benchmark_parallel(client, model_name, prompts, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(client.generate, model_name, p["prompt"])
            for p in prompts
        ]
        results = [f.result() for f in futures]
    return results
```

**Note**: Ollama handles concurrent requests, but don't overload it.

---

## Agent 3: Delta Calculator

### What It Does
Compares base vs fine-tuned responses using multiple metrics and assesses improvements.

### Key Concepts

#### Text Similarity Metrics

**1. Sequence Matcher (Edit Distance)**
```python
from difflib import SequenceMatcher
ratio = SequenceMatcher(None, text1, text2).ratio()
# 1.0 = identical, 0.0 = completely different
```

**How it works**:
- Finds longest common subsequence
- Calculates: 2 * matches / (len(text1) + len(text2))

**Good for**: Character-level changes, typos, minor edits

**Example**:
```
"The cat sat" vs "The cat stood"
Ratio: 0.85 (high similarity, only one word different)
```

**2. TF-IDF Cosine Similarity**
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

vectorizer = TfidfVectorizer()
tfidf = vectorizer.fit_transform([text1, text2])
similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
```

**How it works**:
1. **TF-IDF**: Term Frequency × Inverse Document Frequency
   - Weights important words higher
   - Rare words get higher scores than common words

2. **Cosine Similarity**: Angle between vectors
   - 1.0 = same direction (similar meaning)
   - 0.0 = perpendicular (unrelated)

**Good for**: Semantic similarity, same topic different words

**Example**:
```
"The feline was sleeping" vs "The cat was resting"
Cosine: 0.75 (different words, same meaning)
```

#### Assessment Heuristics

Current logic in `assess_change()`:

```python
if similarity > 0.95:
    return "UNCHANGED"  # Essentially same response

if "ERROR" in ft_resp:
    return "REGRESSED"  # Fine-tuning broke something

if ft_matches_expected > base_matches_expected:
    return "IMPROVED"   # Better alignment with expected

if similarity < 0.7:
    return "CHANGED"    # Significant but unclear change

return "CHANGED"
```

**Limitations**:
- Heuristic-based (not perfect)
- Can't judge nuanced quality
- Misses context-dependent improvements

### Customization Guide

#### Custom Assessment Logic

Replace heuristics with LLM judge:

```python
def assess_with_llm(self, base_resp, ft_resp, prompt, expected):
    """Use LLM to judge which response is better."""

    judge_prompt = f"""
Compare these two responses to the prompt: "{prompt}"

Response A (Base Model):
{base_resp}

Response B (Fine-tuned Model):
{ft_resp}

Expected behavior: {expected}

Which response is better? Reply with ONLY one of:
- IMPROVED (B is better)
- REGRESSED (A is better)
- CHANGED (Different but unclear)
- UNCHANGED (Essentially same)

Answer:"""

    # Call LLM API (OpenAI, Anthropic, etc.)
    result = llm_client.generate(judge_prompt)
    return result.strip()
```

**Benefits**:
- More nuanced judgments
- Understands context
- Catches subtle improvements

**Drawbacks**:
- Requires API calls (cost)
- Slower
- Less deterministic

#### Domain-Specific Metrics

Example: Code generation

```python
def calculate_code_metrics(response):
    """Metrics specific to code generation."""

    # Extract code block
    code = extract_code_block(response)

    return {
        "has_code_block": bool(code),
        "code_length": len(code),
        "syntax_valid": check_syntax(code),
        "has_comments": "#" in code or "//" in code,
        "follows_pep8": run_flake8(code),
        "passes_tests": run_tests(code),
    }
```

Example: Customer support

```python
def calculate_support_metrics(response):
    """Metrics specific to customer support."""

    return {
        "mentions_ticket": "ticket" in response.lower(),
        "provides_steps": len(find_numbered_lists(response)) > 0,
        "polite_greeting": response.startswith(("Hello", "Hi", "Thank")),
        "offers_further_help": "anything else" in response.lower(),
        "response_time_appropriate": len(response) > 50,  # Not too brief
    }
```

#### Statistical Significance

For more robust comparison:

```python
def run_benchmark_multiple_times(model, prompts, n=5):
    """Run benchmark N times and aggregate."""
    all_results = []

    for i in range(n):
        results = run_benchmark(model, prompts)
        all_results.append(results)

    # Calculate statistics
    return {
        "mean_improvement": np.mean([r["improvement"] for r in all_results]),
        "std_improvement": np.std([r["improvement"] for r in all_results]),
        "confidence_interval": calculate_ci(all_results),
    }
```

---

## Agent 4: HTML Visualization

### What It Does
Generates interactive HTML report with side-by-side comparisons and metrics dashboard.

### Key Concepts

#### Jinja2 Templating
**What**: Template engine for generating HTML from data.

```python
from jinja2 import Template

template = Template("""
<h1>{{ title }}</h1>
{% for item in items %}
    <p>{{ item }}</p>
{% endfor %}
""")

html = template.render(title="Results", items=["A", "B", "C"])
```

**Why use it?**
- Separates data from presentation
- Reusable templates
- Clean Python code (no string concatenation)

#### CSS Grid Layout
**What**: Modern CSS layout system.

```css
.dashboard {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
}
```

**Benefits**:
- Responsive (adapts to screen size)
- No manual calculations
- Clean semantic markup

### Customization Guide

#### Custom Styling

Edit `HTML_TEMPLATE` in `benchmark/visualize.py`:

```css
/* Dark mode */
body {
    background: #1a1a1a;
    color: #e0e0e0;
}

.comparison {
    background: #2a2a2a;
    border: 1px solid #3a3a3a;
}

/* Custom brand colors */
.improved {
    background: #your-green;
    border: 2px solid #your-dark-green;
}
```

#### Additional Visualizations

Add charts with Chart.js:

```html
<!-- In HTML_TEMPLATE -->
<canvas id="improvementChart"></canvas>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
const ctx = document.getElementById('improvementChart');
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: {{ categories | tojson }},
        datasets: [{
            label: 'Improvement Rate',
            data: {{ improvement_rates | tojson }}
        }]
    }
});
</script>
```

#### Export to PDF

Add PDF export with Python:

```python
from weasyprint import HTML

def generate_pdf(html_path, pdf_path):
    """Convert HTML report to PDF."""
    HTML(html_path).write_pdf(pdf_path)
```

---

## Agent 5: Infrastructure

### What It Does
- Runs Ollama in Docker
- Converts LoRA → GGUF → Ollama model

### Key Concepts

#### GGUF Format
**What**: Efficient model format for inference.

**Structure**:
```
[Header]
- Version
- Metadata (model name, params, etc.)

[Tensors]
- name: "model.layers.0.attention.weight"
- shape: [4096, 4096]
- type: Q8_0 (8-bit quantized)
- data: [binary blob]
```

**Why GGUF?**
- Single-file model (easy distribution)
- Mmap support (fast loading)
- Quantization built-in
- Cross-platform

#### Docker Volumes
**What**: Persistent storage for containers.

```yaml
volumes:
  - ollama_data:/root/.ollama  # Models persist here
```

**Why?**
- Survives container restarts
- Shared between containers
- Easy backups

### Customization Guide

#### Use Different Quantization

Edit `scripts/export_to_ollama.sh`:

```bash
# Current: Q8_0 (8-bit, good balance)
--outtype q8_0

# Options:
--outtype f16     # 16-bit float (best quality, largest)
--outtype q4_0    # 4-bit (fastest, smallest, lower quality)
--outtype q5_1    # 5-bit (good balance)
--outtype q8_0    # 8-bit (recommended)
```

**Trade-offs**:
| Format | Size | Speed | Quality |
|--------|------|-------|---------|
| f16    | 1GB  | Slow  | Best    |
| q8_0   | 550MB| Fast  | Excellent|
| q4_0   | 300MB| Fastest| Good   |

#### Alternative: llama.cpp Server

Instead of Ollama, use llama.cpp directly:

```bash
# Build llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make

# Start server
./server -m models/model.gguf -c 2048 --port 8080

# Update benchmark/run.py to use localhost:8080
```

**Pros**: More control, lower overhead
**Cons**: Less user-friendly

---

## Agent 6: Orchestration

### What It Does
Coordinates all agents, tracks timing, maintains experiment log.

### Key Concepts

#### Bash Error Handling
```bash
set -e  # Exit on any error
set -u  # Exit on undefined variable
set -o pipefail  # Exit if any command in pipe fails
```

**Why?** Ensures pipeline stops at first error, not continuing with bad data.

#### Experiment Tracking
**What**: JSON log of all experiments.

```json
{
  "experiment_name": "exp-001",
  "timestamp": "2024-01-15T10:30:00",
  "results": {
    "improvement_rate": 60.0,
    "total_prompts": 10,
    "improved": 6
  },
  "timing": {
    "total_minutes": 5.2
  }
}
```

**Why?** Compare experiments over time, find best configurations.

### Customization Guide

#### Custom Metrics in Log

Edit experiment logging section in `iterate.sh`:

```python
# Add custom metrics
entry = {
    # ... existing fields ...
    "custom_metrics": {
        "dataset_size": len(dataset),
        "avg_example_length": calculate_avg_length(dataset),
        "domain": detect_domain(dataset),
        "model_size": get_model_size("experiments/{name}/lora"),
    }
}
```

#### Notifications

Add Slack/email notifications:

```bash
# At end of iterate.sh

# Slack notification
curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"Experiment ${EXPERIMENT_NAME} complete! Improvement rate: ${IMPROVEMENT_RATE}%\"}" \
  $SLACK_WEBHOOK_URL

# Email notification
echo "Experiment complete. See report: benchmark/results/report.html" | \
  mail -s "Fine-tuning ${EXPERIMENT_NAME} complete" your@email.com
```

#### Parallel Experiments

Run multiple experiments concurrently:

```bash
# experiment_batch.sh
for dataset in datasets/*.json; do
    name=$(basename $dataset .json)
    ./iterate.sh "batch-${name}" "$dataset" &
done

wait  # Wait for all to complete
```

**Note**: Ensure enough GPU memory for parallel training!

---

## Common Patterns

### Pattern 1: A/B Testing
Compare two approaches:

```bash
# Approach A: High learning rate, fewer epochs
./iterate.sh test-A-high-lr datasets/data.json --lr 5e-4 --epochs 2

# Approach B: Low learning rate, more epochs
./iterate.sh test-B-low-lr datasets/data.json --lr 1e-4 --epochs 5

# Compare results
diff <(jq .results.improvement_rate experiments/log.json | grep test-A) \
     <(jq .results.improvement_rate experiments/log.json | grep test-B)
```

### Pattern 2: Curriculum Learning
Train progressively on harder examples:

```bash
# Stage 1: Easy examples
./iterate.sh curriculum-easy datasets/easy.json

# Stage 2: Medium (resume from previous)
./iterate.sh curriculum-medium datasets/medium.json --resume

# Stage 3: Hard
./iterate.sh curriculum-hard datasets/hard.json --resume
```

### Pattern 3: Incremental Improvement
Build on previous best:

```bash
# Iteration 1: Baseline
./iterate.sh v1 datasets/initial.json

# Analyze results, identify weaknesses
# Create v2 dataset addressing weaknesses

# Iteration 2: Improved
./iterate.sh v2 datasets/improved.json

# Repeat until satisfactory
```

---

## Advanced Topics

### Multi-GPU Training
Edit `train.py` to use multiple GPUs:

```python
training_args = TrainingArguments(
    # ... other args ...
    local_rank=int(os.environ.get("LOCAL_RANK", -1)),
    ddp_find_unused_parameters=False,
)

# Launch with:
# torchrun --nproc_per_node=2 train.py --name exp-001 --dataset data.json
```

### Model Merging
Combine multiple LoRA adapters:

```python
from peft import PeftModel

# Load base
base_model = AutoModelForCausalLM.from_pretrained("base")

# Load adapters
adapter1 = PeftModel.from_pretrained(base_model, "exp-001/lora")
adapter2 = PeftModel.from_pretrained(base_model, "exp-002/lora")

# Merge with weights
merged = merge_adapters([adapter1, adapter2], weights=[0.6, 0.4])
```

### Continuous Fine-tuning
Automatically fine-tune on new data:

```python
# watch_and_train.py
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DatasetHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith('.json'):
            name = f"auto-{timestamp}"
            os.system(f"./iterate.sh {name} {event.src_path}")

observer = Observer()
observer.schedule(DatasetHandler(), "datasets/", recursive=False)
observer.start()
```

---

## Further Reading

### Papers
- [LoRA: Low-Rank Adaptation](https://arxiv.org/abs/2106.09685)
- [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314)
- [Flash Attention](https://arxiv.org/abs/2205.14135)

### Tools Documentation
- [Unsloth GitHub](https://github.com/unslothai/unsloth)
- [Ollama Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [PEFT Library](https://huggingface.co/docs/peft)
- [TRL Documentation](https://huggingface.co/docs/trl)

### Tutorials
- [Fine-tuning LLMs (HuggingFace)](https://huggingface.co/docs/transformers/training)
- [Quantization Guide](https://huggingface.co/docs/optimum/concept_guides/quantization)
- [Docker for ML](https://docs.docker.com/samples/pytorch/)

---

**Questions?** Open an issue or contribute improvements!
