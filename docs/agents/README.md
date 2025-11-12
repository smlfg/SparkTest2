# Agent Teaching Materials

This directory contains learning resources for each component of the fast fine-tuning system.

## Learning Philosophy

Each agent's code is **heavily documented with teaching comments** that explain:
- **What** the code does
- **Why** design decisions were made
- **How** components work together
- **When** to use different approaches

## Agent Overview

### Agent 1: Fast Training Pipeline
**File**: `train.py`
**Learn**: LoRA fine-tuning, Unsloth optimizations, memory management
**Key Concepts**:
- Why LoRA is 100x more efficient than full fine-tuning
- How 4-bit quantization saves memory
- What makes Unsloth 2x faster

**To Learn**: Read the extensive comments in `train.py`, especially:
- Model loading section (line ~130)
- LoRA configuration (line ~160)
- Training loop setup (line ~220)

### Agent 2: Benchmark Suite
**Files**: `benchmark/prompts.py`, `benchmark/run.py`
**Learn**: Systematic evaluation, API integration, test design
**Key Concepts**:
- Why we need diverse test categories
- How to structure benchmark prompts
- What metrics matter for evaluation

**To Learn**: Read the comments in:
- `benchmark/prompts.py` - Prompt design principles
- `benchmark/run.py` - Ollama API usage

### Agent 3: Delta Calculator
**File**: `benchmark/delta.py`
**Learn**: Comparison metrics, semantic similarity, assessment logic
**Key Concepts**:
- Different types of metrics (length, keywords, similarity)
- Why no single metric is sufficient
- How to assess improvement holistically

**To Learn**: Read the metric functions in `benchmark/delta.py`:
- `calculate_length_delta()` - Verbosity analysis
- `calculate_keyword_match()` - Topical relevance
- `calculate_similarity()` - Semantic comparison
- `assess_overall_change()` - Holistic assessment

### Agent 4: Visualization
**File**: `benchmark/visualize.py`
**Learn**: HTML report generation, data presentation, UI design
**Key Concepts**:
- Why static HTML vs web dashboards
- How to present ML results to non-technical users
- Trade-offs in visualization design

**To Learn**: Read:
- HTML template structure (line ~40)
- Report generation logic (line ~200)

### Agent 5: Infrastructure
**Files**: `docker-compose.yml`, `scripts/export_to_ollama.sh`
**Learn**: Docker containerization, model export pipelines, GGUF format
**Key Concepts**:
- Why Ollama for inference
- How LoRA → GGUF conversion works
- What model formats exist

**To Learn**: Read:
- `docker-compose.yml` - Container configuration
- `scripts/export_to_ollama.sh` - Export pipeline steps

### Agent 6: Orchestration
**File**: `iterate.sh`
**Learn**: Bash scripting, error handling, workflow automation
**Key Concepts**:
- How to chain multiple tools
- Why timing each step matters
- How to log experiments systematically

**To Learn**: Read `iterate.sh` from start to finish - it's well-commented and shows the complete workflow.

## Learning Path

### Beginner (Just Getting Started)

1. Read `README.md` - Understand the big picture
2. Follow `docs/QUICKSTART.md` - Run your first iteration
3. Read `iterate.sh` - See how everything connects
4. Read `benchmark/prompts.py` - Understand test design
5. Run a few experiments and observe results

**Time**: 2-3 hours

### Intermediate (Understanding the System)

1. Read `docs/ARCHITECTURE.md` - Deep dive into design
2. Read `train.py` fully - Understand LoRA and Unsloth
3. Read `benchmark/run.py` - Learn Ollama API usage
4. Read `benchmark/delta.py` - Study comparison metrics
5. Modify prompts and see how results change

**Time**: 1 day

### Advanced (Mastering and Extending)

1. Experiment with different hyperparameters
2. Add custom metrics to delta.py
3. Create custom benchmark categories
4. Try different base models
5. Optimize for your specific use case
6. Contribute improvements back

**Time**: Ongoing

## Key Learning Outcomes

After working with this system, you should understand:

### Machine Learning Concepts
- ✅ LoRA fine-tuning vs full fine-tuning
- ✅ Quantization (4-bit, 8-bit)
- ✅ Parameter-efficient training
- ✅ Model evaluation metrics
- ✅ Supervised fine-tuning

### Engineering Practices
- ✅ Experiment tracking and reproducibility
- ✅ Systematic evaluation
- ✅ Pipeline automation
- ✅ Docker containerization
- ✅ Error handling and logging

### Domain Knowledge
- ✅ LLM architectures (transformers)
- ✅ Model formats (GGUF, safetensors)
- ✅ Inference optimization
- ✅ Prompt engineering
- ✅ Benchmark design

### Practical Skills
- ✅ Setting up ML pipelines
- ✅ Using Ollama for inference
- ✅ Working with HuggingFace models
- ✅ Bash scripting for automation
- ✅ Rapid prototyping and iteration

## Teaching Resources by Topic

### LoRA Fine-tuning
- **Primary**: `train.py` lines 130-200
- **Also see**: ARCHITECTURE.md "Why LoRA?" section
- **Concept**: Parameter-efficient fine-tuning

### Unsloth Optimizations
- **Primary**: `train.py` model loading section
- **Also see**: ARCHITECTURE.md "Performance Optimizations"
- **Concept**: Flash Attention, gradient checkpointing

### Model Evaluation
- **Primary**: `benchmark/prompts.py`
- **Also see**: `benchmark/delta.py`
- **Concept**: Systematic testing and metrics

### Ollama & GGUF
- **Primary**: `scripts/export_to_ollama.sh`
- **Also see**: `docker-compose.yml`
- **Concept**: Optimized inference formats

### Experiment Tracking
- **Primary**: `iterate.sh` logging section
- **Also see**: Metadata in `train.py`
- **Concept**: Reproducible science

## Interactive Learning Exercises

### Exercise 1: Your First Fine-tune (30 minutes)
1. Create a custom dataset with 10 samples
2. Run `./iterate.sh my-experiment datasets/my-data.json`
3. Review the HTML report
4. Questions to answer:
   - Which prompts improved?
   - Why did some regress?
   - What would you change?

### Exercise 2: Parameter Exploration (1 hour)
1. Train with 1, 3, and 5 epochs
2. Compare results in `experiments/log.json`
3. Questions:
   - When does more training help?
   - When does it hurt (overfitting)?
   - What's the sweet spot?

### Exercise 3: Metric Analysis (45 minutes)
1. Review delta calculations in `benchmark/delta.py`
2. Add a new custom metric (e.g., word count, sentence count)
3. Regenerate the report
4. Questions:
   - Does your metric reveal new insights?
   - How does it correlate with existing metrics?

### Exercise 4: Benchmark Design (1 hour)
1. Study `benchmark/prompts.py`
2. Add 5 new prompts in a new category
3. Run benchmark with your prompts
4. Questions:
   - What aspects of model behavior do they test?
   - Are they diverse enough?
   - How would you improve them?

## Additional Resources

### External Documentation
- **Unsloth**: https://github.com/unslothai/unsloth
- **Ollama**: https://ollama.ai/
- **LoRA Paper**: https://arxiv.org/abs/2106.09685
- **Qwen2.5**: https://huggingface.co/Qwen

### Related Tutorials
- HuggingFace PEFT documentation
- TRL (Transformer Reinforcement Learning) docs
- Docker Compose basics
- Bash scripting guides

## Getting Help

1. **Start with code comments**: 90% of questions answered inline
2. **Check ARCHITECTURE.md**: Deep dives into design decisions
3. **Review QUICKSTART.md**: Common setup issues covered
4. **Experiment logs**: Check `experiments/log.json` for debugging
5. **Error messages**: Read them carefully - they're descriptive

## Contributing Your Learning

Found a better way to explain something? Create a PR with:
- Improved code comments
- Additional examples
- Clarifying diagrams
- FAQ entries

**Remember**: The best learning happens by doing. Run experiments, break things, fix them, and iterate!
