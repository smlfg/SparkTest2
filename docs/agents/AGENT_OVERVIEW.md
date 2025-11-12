# Agent Teaching Guides

Each agent in the system has a specific responsibility and uses particular technologies. These guides explain not just *how* each agent works, but *why* it's designed that way.

## Available Guides

### Core Pipeline
- **Agent 1: Training** - Fast fine-tuning with Unsloth and LoRA
- **Agent 2: Benchmark** - Systematic model evaluation
- **Agent 3: Delta Analysis** - Quantifying improvements
- **Agent 4: Visualization** - Making results scannable
- **Agent 5: Infrastructure** - Model export and deployment
- **Agent 6: Orchestration** - Tying it all together

## Learning Path

### Beginner (Just want to use it)
1. Read main README.md
2. Follow QUICKSTART.md
3. Run a few iterations
4. You're done! 🎉

### Intermediate (Want to customize)
1. Read ARCHITECTURE.md
2. Customize benchmark prompts (Agent 2)
3. Modify training hyperparameters (Agent 1)
4. Add domain-specific metrics (Agent 3)

### Advanced (Want to understand deeply)
1. Read all agent guides
2. Study the code with inline comments
3. Modify agents for your use case
4. Contribute improvements back

## Key Concepts

### Fine-tuning
- **What**: Adapting a pre-trained model to your specific task
- **Why**: Base models are general, fine-tuning makes them specialized
- **How**: Show the model examples of desired behavior

### LoRA (Low-Rank Adaptation)
- **What**: Efficient fine-tuning method that adds small adapter layers
- **Why**: Full fine-tuning is slow and memory-intensive
- **How**: Updates only ~1% of parameters, gets 99% of the quality

### Quantization
- **What**: Representing model weights with fewer bits (e.g., 4-bit instead of 16-bit)
- **Why**: Saves memory (4x less), enables training on smaller hardware
- **How**: Groups of weights share scaling factors

### Delta Analysis
- **What**: Comparing base model output to fine-tuned output
- **Why**: Systematic evaluation, not subjective "looks better"
- **How**: Automated metrics + manual review

### Iteration Velocity
- **What**: How fast you can complete one train-test cycle
- **Why**: Faster iteration = more learning = better results
- **How**: Small model, efficient training, automated pipeline

## Common Questions

### Q: Why Qwen2.5-0.5B and not GPT-4?

**A**: We prioritize iteration speed over absolute quality. A 500M parameter model you can train in 3 minutes beats a 1.7T parameter model that takes 3 hours. Run 20 iterations with the small model in the time it takes to run 1 with the large model.

### Q: Why only 10 benchmark prompts?

**A**: Balance of coverage vs. speed. 10 prompts cover major categories (reasoning, knowledge, instruction-following) while keeping benchmark under 1 minute. You can add more for your domain.

### Q: Can I use this for production?

**A**: No, this is for rapid experimentation. For production:
- Use larger model (Qwen2.5-7B or bigger)
- More training data (1000+ examples)
- Proper evaluation (100+ test cases)
- Safety testing (red teaming, bias evaluation)
- Different deployment (not Ollama)

### Q: Why not use [popular framework]?

We chose technologies based on:
1. **Speed**: Unsloth is 2x faster than alternatives
2. **Simplicity**: Fewer dependencies, easier to understand
3. **Portability**: Works on DGX and consumer hardware
4. **Learning**: Clear code, teaching comments

Popular frameworks optimize for production, we optimize for learning.

### Q: How do I know if my fine-tuning worked?

Look for:
1. **Improved prompts** > **Regressed prompts** (net positive)
2. Improvements align with training data (model learned)
3. Regressions are explainable (e.g., topics not in training)
4. Consistent style across responses

If 30-50% of prompts improve and <20% regress, you're doing well!

## Best Practices

### Training Data
- **Quality over quantity**: 20 great examples > 100 mediocre ones
- **Diversity**: Cover different types of questions/tasks
- **Consistency**: Maintain same style/format across examples
- **Relevance**: Focus on what you want the model to do

### Hyperparameters
- **Start with defaults**: They're tuned for this use case
- **Change one thing at a time**: Isolate what works
- **Track everything**: Use experiment log to compare

### Iteration Strategy
- **Start small**: 10-15 examples, 3 epochs
- **Iterate fast**: Don't perfect each iteration
- **Follow the data**: Let benchmark results guide you
- **Compare regularly**: Look at experiment log trends

### Debugging
- **Check metadata**: `experiments/exp-001/metadata.json`
- **Review logs**: Training loss, timing, parameters
- **Spot check**: Manually review interesting responses
- **Compare iterations**: What changed between exp-001 and exp-002?

## Contributing

Want to improve the system?

### Easy contributions
- Add domain-specific prompts
- Write better documentation
- Share example datasets
- Report bugs

### Medium contributions
- Improve metrics (Agent 3)
- Better visualizations (Agent 4)
- Optimization speedups
- Additional examples

### Advanced contributions
- Multi-GPU support
- Hyperparameter search
- Advanced evaluation metrics
- Web dashboard

See main README.md for contribution guidelines.

## Resources

### Learning Materials
- [Unsloth Documentation](https://github.com/unslothai/unsloth)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [Qwen2.5 Model Card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
- [Ollama Documentation](https://ollama.ai/docs)

### Related Projects
- Axolotl (alternative training framework)
- LLaMA-Factory (GUI for fine-tuning)
- FastChat (chatbot arena)
- OpenLLM (model deployment)

## Next Steps

Pick an agent guide based on what you want to learn:
- **Want to modify training?** → Agent 1
- **Want custom evaluation?** → Agents 2-4
- **Want to deploy elsewhere?** → Agent 5
- **Want to automate more?** → Agent 6

Each guide includes:
- Detailed explanation of code
- Design rationale
- Common modifications
- Troubleshooting tips

Happy learning! 🚀
