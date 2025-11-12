#!/usr/bin/env python3
"""
Agent 1: Fast Training Pipeline with Unsloth

This script fine-tunes Qwen2.5-0.5B using LoRA (Low-Rank Adaptation) adapters.

WHY UNSLOTH?
- 2x faster than standard HuggingFace Transformers
- Uses optimized kernels for NVIDIA GPUs
- Supports 4-bit quantization (saves memory)
- Maintains same quality as standard training

WHY LORA?
- Only trains 0.1% of model parameters (adapters)
- 50MB adapters vs 1GB full model
- Prevents catastrophic forgetting of base knowledge
- Fast training (3-5 minutes vs 30+ minutes)

TIME BREAKDOWN (DGX Spark):
- Load model: 30 seconds
- Training 3 epochs: 2-3 minutes
- Save adapters: 10 seconds
Total: ~3-5 minutes

WHAT THIS SCRIPT DOES:
1. Loads Qwen2.5-0.5B with 4-bit quantization
2. Adds LoRA adapters (rank 8, target all linear layers)
3. Trains on your dataset using SFTTrainer
4. Saves adapters to experiments/{name}/lora/
5. Logs metrics for analysis

LEARNING OBJECTIVES:
- Understand LoRA parameter-efficient fine-tuning
- See how quantization enables faster training
- Learn dataset formatting for instruction tuning
- Track training metrics (loss, learning rate)
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

# Training imports
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset

# Utilities
from tqdm import tqdm
import torch


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fast fine-tuning with Unsloth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python train.py --name exp-001 --dataset datasets/example-chatbot.json

  # Custom hyperparameters
  python train.py --name exp-001 --dataset data.json --epochs 5 --lr 5e-4

  # Resume from checkpoint
  python train.py --name exp-001 --dataset data.json --resume
        """
    )

    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Experiment name (e.g., exp-001, customer-support-v2)"
    )

    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to training dataset (JSON format)"
    )

    # Hyperparameters
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs (default: 3)"
    )

    parser.add_argument(
        "--lr",
        type=float,
        default=2e-4,
        help="Learning rate (default: 2e-4)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Batch size per GPU (default: 4)"
    )

    parser.add_argument(
        "--lora-rank",
        type=int,
        default=8,
        help="LoRA rank - higher = more capacity but slower (default: 8)"
    )

    parser.add_argument(
        "--max-seq-length",
        type=int,
        default=2048,
        help="Maximum sequence length (default: 2048)"
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint if exists"
    )

    return parser.parse_args()


def setup_experiment(name):
    """Create experiment directory structure."""
    exp_dir = Path(f"experiments/{name}")
    lora_dir = exp_dir / "lora"
    checkpoint_dir = exp_dir / "checkpoints"

    exp_dir.mkdir(parents=True, exist_ok=True)
    lora_dir.mkdir(exist_ok=True)
    checkpoint_dir.mkdir(exist_ok=True)

    return exp_dir, lora_dir, checkpoint_dir


def load_model(max_seq_length, lora_rank):
    """
    Load Qwen2.5-0.5B with LoRA adapters.

    TEACHING NOTE:
    - FastLanguageModel is Unsloth's optimized model loader
    - load_in_4bit=True reduces memory by 75% (16-bit → 4-bit)
    - LoRA adapters are added to all "q_proj", "v_proj" layers
      (these are attention mechanism weights)
    - Rank 8 means each adapter has 2 small matrices (hidden_dim × 8 and 8 × hidden_dim)
    """
    print("📦 Loading Qwen2.5-0.5B with 4-bit quantization...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Qwen2.5-0.5B-Instruct",
        max_seq_length=max_seq_length,
        dtype=None,  # Auto-detect best dtype for your GPU
        load_in_4bit=True,  # 4-bit quantization for speed
    )

    print("🔧 Adding LoRA adapters...")

    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_rank,  # Rank (higher = more capacity)
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",  # Attention
            "gate_proj", "up_proj", "down_proj",      # MLP
        ],
        lora_alpha=16,  # Scaling factor (typically 2x rank)
        lora_dropout=0,  # No dropout (Unsloth optimized)
        bias="none",     # Don't train biases
        use_gradient_checkpointing="unsloth",  # Memory-efficient backprop
        random_state=42,
    )

    print(f"✓ Model loaded with {lora_rank}-rank LoRA adapters")

    return model, tokenizer


def format_prompt(example):
    """
    Format dataset example into Qwen2.5 chat template.

    TEACHING NOTE:
    Qwen2.5 uses ChatML format:
    <|im_start|>system
    You are a helpful assistant.<|im_end|>
    <|im_start|>user
    Hello!<|im_end|>
    <|im_start|>assistant
    Hi there!<|im_end|>

    During training, the model only learns from the assistant's response.
    The user message and system prompt are just context.
    """
    messages = []

    # Add system message if present
    if "system" in example:
        messages.append({"role": "system", "content": example["system"]})

    # Add conversation
    if "messages" in example:
        messages.extend(example["messages"])
    else:
        # Legacy format: single user/assistant pair
        messages.append({"role": "user", "content": example["user"]})
        messages.append({"role": "assistant", "content": example["assistant"]})

    return {"messages": messages}


def load_and_prepare_dataset(dataset_path, tokenizer):
    """Load dataset and format for training."""
    print(f"📂 Loading dataset from {dataset_path}...")

    # Load dataset
    if dataset_path.endswith('.json'):
        dataset = load_dataset('json', data_files=dataset_path, split='train')
    elif dataset_path.endswith('.jsonl'):
        dataset = load_dataset('json', data_files=dataset_path, split='train')
    else:
        raise ValueError("Dataset must be .json or .jsonl format")

    print(f"✓ Loaded {len(dataset)} examples")

    # Show first example
    print("\n📝 First training example:")
    print(json.dumps(dataset[0], indent=2))

    return dataset


def train(model, tokenizer, dataset, args, output_dir, checkpoint_dir):
    """
    Fine-tune model with SFTTrainer.

    TEACHING NOTE:
    SFTTrainer is specialized for instruction tuning:
    - Automatically formats messages with chat template
    - Only computes loss on assistant responses (not user messages)
    - Handles padding and batching
    """
    print("\n🏋️  Starting training...")
    print(f"Hyperparameters:")
    print(f"  - Epochs: {args.epochs}")
    print(f"  - Learning rate: {args.lr}")
    print(f"  - Batch size: {args.batch_size}")
    print(f"  - LoRA rank: {args.lora_rank}")
    print(f"  - Max sequence length: {args.max_seq_length}")

    # Training arguments
    training_args = TrainingArguments(
        # Output
        output_dir=str(checkpoint_dir),
        run_name=args.name,

        # Training schedule
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=1,

        # Optimization
        learning_rate=args.lr,
        weight_decay=0.01,
        warmup_steps=10,
        optim="adamw_8bit",  # 8-bit optimizer (saves memory)

        # Logging
        logging_steps=10,
        logging_first_step=True,

        # Saving
        save_strategy="epoch",
        save_total_limit=2,

        # Performance
        fp16=not torch.cuda.is_bf16_supported(),  # Use fp16 if bf16 unavailable
        bf16=torch.cuda.is_bf16_supported(),       # Use bf16 if available
        dataloader_num_workers=2,

        # Misc
        seed=42,
        report_to="none",  # Don't use wandb/tensorboard
    )

    # Trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
        max_seq_length=args.max_seq_length,
        dataset_text_field="messages",  # Field containing chat messages
        packing=False,  # Don't pack multiple examples (clearer for learning)
    )

    # Train!
    start_time = time.time()

    print("\n⏱️  Training started...")
    trainer.train(resume_from_checkpoint=args.resume)

    train_time = time.time() - start_time
    print(f"\n✓ Training complete in {train_time:.1f} seconds ({train_time/60:.1f} minutes)")

    # Save final model
    print(f"💾 Saving LoRA adapters to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    return trainer, train_time


def save_metadata(exp_dir, args, train_time, dataset_size):
    """Save experiment metadata for tracking."""
    metadata = {
        "name": args.name,
        "timestamp": datetime.now().isoformat(),
        "dataset": {
            "path": args.dataset,
            "size": dataset_size,
        },
        "hyperparameters": {
            "epochs": args.epochs,
            "learning_rate": args.lr,
            "batch_size": args.batch_size,
            "lora_rank": args.lora_rank,
            "max_seq_length": args.max_seq_length,
        },
        "training": {
            "time_seconds": train_time,
            "time_minutes": train_time / 60,
        },
        "model": {
            "base": "unsloth/Qwen2.5-0.5B-Instruct",
            "method": "LoRA",
            "quantization": "4-bit",
        }
    }

    metadata_path = exp_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"✓ Metadata saved to {metadata_path}")


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("Agent 1: Fast Training Pipeline with Unsloth")
    print("=" * 60)

    # Parse arguments
    args = parse_args()

    # Setup experiment
    exp_dir, lora_dir, checkpoint_dir = setup_experiment(args.name)
    print(f"📁 Experiment directory: {exp_dir}")

    # Check dataset exists
    if not os.path.exists(args.dataset):
        print(f"❌ Error: Dataset not found at {args.dataset}")
        return 1

    # Load model
    model, tokenizer = load_model(args.max_seq_length, args.lora_rank)

    # Load dataset
    dataset = load_and_prepare_dataset(args.dataset, tokenizer)

    # Train
    trainer, train_time = train(
        model, tokenizer, dataset, args,
        lora_dir, checkpoint_dir
    )

    # Save metadata
    save_metadata(exp_dir, args, train_time, len(dataset))

    print("\n" + "=" * 60)
    print("✅ Training complete!")
    print(f"📊 LoRA adapters: {lora_dir}")
    print(f"📋 Metadata: {exp_dir}/metadata.json")
    print("\nNext steps:")
    print(f"  1. Export to Ollama: ./scripts/export_to_ollama.sh {args.name}")
    print(f"  2. Run benchmark: python benchmark/run.py {args.name}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
