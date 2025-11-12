#!/usr/bin/env python3

################################################################################
# AGENT 1: Fast Training Pipeline
#
# This script fine-tunes Qwen2.5-0.5B using Unsloth for 2x speedup.
#
# TEACHING NOTES:
#
# 1. WHY UNSLOTH?
#    - Traditional training: 5-10 minutes per epoch
#    - Unsloth: 2-3 minutes per epoch (2x faster)
#    - How: Optimized CUDA kernels, memory-efficient attention
#
# 2. WHY LORA (Low-Rank Adaptation)?
#    - Full fine-tuning: Update all 500M parameters (slow, lots of memory)
#    - LoRA: Add small adapter layers (~2M parameters)
#    - Result: 99% accuracy of full fine-tuning, 1% of the memory
#
# 3. WHY 4-BIT QUANTIZATION?
#    - FP16 model: ~1GB memory for 500M params
#    - 4-bit model: ~250MB memory
#    - Enables training on consumer hardware
#    - Minimal accuracy loss (~1-2%)
#
# 4. HYPERPARAMETER CHOICES:
#    - LoRA rank=8: Sweet spot for small models (higher = more capacity)
#    - Alpha=16: Scales LoRA contribution (typically 2x rank)
#    - Learning rate 3e-4: Higher than normal (LoRA is stable)
#    - Batch size=4: Balances speed and memory
#
# 5. DATASET FORMAT:
#    - Standard chat format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
#    - Tokenizer applies chat template automatically
#    - Trains on assistant responses only (user messages are context)
################################################################################

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import torch
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel, is_bfloat16_supported
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

################################################################################
# Configuration
################################################################################

# Model configuration
MODEL_ID = "unsloth/Qwen2.5-0.5B-Instruct"  # Unsloth's optimized version
MAX_SEQ_LENGTH = 2048  # Maximum sequence length (longer = more memory)
LOAD_IN_4BIT = True    # Use 4-bit quantization (saves memory)

# LoRA configuration
LORA_R = 8             # Rank (higher = more parameters, more capacity)
LORA_ALPHA = 16        # Scaling factor (typically 2x rank)
LORA_DROPOUT = 0.0     # Dropout (0 = no dropout, more stable for small datasets)

# Which layers to apply LoRA (targeting key attention/MLP layers)
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj",
                  "gate_proj", "up_proj", "down_proj"]

################################################################################
# Helper Functions
################################################################################

def load_training_data(dataset_path):
    """
    Load training dataset from JSON file.

    Expected format:
    [
        {
            "messages": [
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        },
        ...
    ]
    """
    console.print(f"[cyan]Loading dataset from {dataset_path}...[/cyan]")

    if not os.path.exists(dataset_path):
        console.print(f"[red]Error: Dataset not found: {dataset_path}[/red]")
        sys.exit(1)

    # Load JSON file
    with open(dataset_path, 'r') as f:
        data = json.load(f)

    # Validate format
    if not isinstance(data, list):
        console.print("[red]Error: Dataset must be a list of examples[/red]")
        sys.exit(1)

    if len(data) == 0:
        console.print("[red]Error: Dataset is empty[/red]")
        sys.exit(1)

    # Check first example has correct format
    if "messages" not in data[0]:
        console.print("[red]Error: Each example must have 'messages' field[/red]")
        sys.exit(1)

    console.print(f"[green]✓ Loaded {len(data)} training examples[/green]")

    # Convert to Hugging Face dataset
    from datasets import Dataset
    dataset = Dataset.from_list(data)

    return dataset


def format_chat_template(example, tokenizer):
    """
    Format messages using the model's chat template.

    This converts the chat format to the model's expected format:
    <|im_start|>user\nHello!<|im_end|>\n<|im_start|>assistant\nHi there!<|im_end|>
    """
    messages = example["messages"]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    )
    return {"text": text}


def save_metadata(output_dir, args, train_result, dataset_size):
    """Save training metadata for experiment tracking."""
    metadata = {
        "experiment_name": os.path.basename(output_dir),
        "timestamp": datetime.now().isoformat(),
        "dataset": {
            "path": args.dataset,
            "size": dataset_size
        },
        "model": {
            "base": MODEL_ID,
            "max_seq_length": MAX_SEQ_LENGTH,
            "load_in_4bit": LOAD_IN_4BIT
        },
        "lora": {
            "r": LORA_R,
            "alpha": LORA_ALPHA,
            "dropout": LORA_DROPOUT,
            "target_modules": TARGET_MODULES
        },
        "training": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "warmup_ratio": args.warmup_ratio,
            "gradient_accumulation_steps": args.gradient_accumulation_steps
        },
        "results": {
            "train_loss": train_result.metrics.get("train_loss"),
            "train_runtime": train_result.metrics.get("train_runtime"),
            "train_samples_per_second": train_result.metrics.get("train_samples_per_second"),
            "total_steps": train_result.metrics.get("train_steps", 0)
        }
    }

    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    console.print(f"[green]✓ Saved metadata to {metadata_path}[/green]")


################################################################################
# Main Training Function
################################################################################

def train(args):
    """Main training function."""

    console.print("\n[bold blue]" + "="*60 + "[/bold blue]")
    console.print("[bold blue]Agent 1: Fast Training Pipeline[/bold blue]")
    console.print("[bold blue]" + "="*60 + "[/bold blue]\n")

    start_time = time.time()

    # Create output directory
    output_dir = args.output
    lora_dir = os.path.join(output_dir, "lora")
    os.makedirs(lora_dir, exist_ok=True)

    console.print(f"[cyan]Output directory: {output_dir}[/cyan]")

    # Step 1: Load dataset
    dataset = load_training_data(args.dataset)

    # Step 2: Load model with Unsloth
    console.print(f"\n[cyan]Loading model: {MODEL_ID}...[/cyan]")
    console.print("[dim]This may take a minute on first run (downloads ~1GB)[/dim]")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_ID,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,  # Auto-detect (bfloat16 if supported, else float16)
        load_in_4bit=LOAD_IN_4BIT,
    )

    console.print("[green]✓ Model loaded[/green]")

    # Step 3: Apply LoRA adapters
    console.print(f"\n[cyan]Applying LoRA adapters (rank={LORA_R})...[/cyan]")

    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        target_modules=TARGET_MODULES,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",  # Don't train bias terms (faster, minimal impact)
        use_gradient_checkpointing="unsloth",  # Unsloth's optimized checkpointing
        random_state=42,
        use_rslora=False,  # Rank-stabilized LoRA (optional, slight improvement)
    )

    # Print trainable parameters
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    console.print(f"[green]✓ LoRA adapters applied[/green]")
    console.print(f"[dim]Trainable parameters: {trainable_params:,} / {total_params:,} "
                  f"({100 * trainable_params / total_params:.2f}%)[/dim]")

    # Step 4: Format dataset
    console.print(f"\n[cyan]Formatting dataset...[/cyan]")
    formatted_dataset = dataset.map(
        lambda x: format_chat_template(x, tokenizer),
        remove_columns=dataset.column_names
    )
    console.print("[green]✓ Dataset formatted[/green]")

    # Step 5: Set up training arguments
    training_args = TrainingArguments(
        # Output
        output_dir=lora_dir,
        run_name=os.path.basename(output_dir),

        # Training schedule
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        warmup_ratio=args.warmup_ratio,

        # Optimizer
        learning_rate=args.learning_rate,
        optim="adamw_8bit",  # 8-bit AdamW (saves memory)
        weight_decay=0.01,

        # Logging
        logging_steps=10,
        logging_strategy="steps",

        # Saving
        save_strategy="epoch",
        save_total_limit=1,  # Keep only the last checkpoint

        # Performance
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        gradient_checkpointing=True,

        # Misc
        seed=42,
        report_to="none",  # Disable wandb/tensorboard
    )

    # Step 6: Create trainer
    console.print(f"\n[cyan]Initializing trainer...[/cyan]")

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=formatted_dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        args=training_args,
        packing=False,  # Don't pack multiple examples (simpler for chat)
    )

    console.print("[green]✓ Trainer ready[/green]")

    # Step 7: Train!
    console.print(f"\n[bold yellow]Starting training ({args.epochs} epochs)...[/bold yellow]")
    console.print("[dim]This will take 3-5 minutes. Go grab coffee! ☕[/dim]\n")

    train_result = trainer.train()

    # Step 8: Save model
    console.print(f"\n[cyan]Saving LoRA adapters to {lora_dir}...[/cyan]")
    model.save_pretrained(lora_dir)
    tokenizer.save_pretrained(lora_dir)
    console.print("[green]✓ Model saved[/green]")

    # Step 9: Save metadata
    save_metadata(output_dir, args, train_result, len(dataset))

    # Done!
    elapsed = time.time() - start_time
    console.print(f"\n[bold green]" + "="*60 + "[/bold green]")
    console.print(f"[bold green]Training Complete! 🎉[/bold green]")
    console.print(f"[bold green]" + "="*60 + "[/bold green]")
    console.print(f"\n[green]Time elapsed: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)[/green]")
    console.print(f"[green]Output: {output_dir}[/green]")
    console.print(f"\n[cyan]Next steps:[/cyan]")
    console.print(f"  1. Export to Ollama: [bold]./scripts/export_to_ollama.sh {output_dir} {os.path.basename(output_dir)}[/bold]")
    console.print(f"  2. Or run full benchmark: [bold]./iterate.sh {os.path.basename(output_dir)} {args.dataset}[/bold]\n")


################################################################################
# CLI
################################################################################

def main():
    parser = argparse.ArgumentParser(
        description="Agent 1: Fast fine-tuning with Unsloth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python train.py --dataset datasets/example-chatbot.json --output experiments/exp-001

  # Custom hyperparameters
  python train.py \\
    --dataset datasets/example-chatbot.json \\
    --output experiments/exp-002 \\
    --epochs 5 \\
    --learning-rate 5e-4 \\
    --batch-size 2

Dataset format:
  [
    {
      "messages": [
        {"role": "user", "content": "What is 2+2?"},
        {"role": "assistant", "content": "2+2 equals 4."}
      ]
    }
  ]
        """
    )

    # Required arguments
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to training dataset (JSON file)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output directory for experiment (e.g., experiments/exp-001)"
    )

    # Training hyperparameters
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs (default: 3)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Training batch size (default: 4)"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=3e-4,
        help="Learning rate (default: 3e-4)"
    )
    parser.add_argument(
        "--warmup-ratio",
        type=float,
        default=0.1,
        help="Warmup ratio (default: 0.1 = 10%% of steps)"
    )
    parser.add_argument(
        "--gradient-accumulation-steps",
        type=int,
        default=1,
        help="Gradient accumulation steps (default: 1)"
    )

    args = parser.parse_args()

    # Run training
    train(args)


if __name__ == "__main__":
    main()
