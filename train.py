#!/usr/bin/env python3
"""
================================================================================
DGX Spark Fast Fine-tuning System
Agent 1: Fast Training Pipeline
================================================================================

WHAT: Fine-tune Qwen2.5-0.5B with LoRA using Unsloth for maximum speed
WHY:  Need to complete training in 3-5 minutes for rapid iteration
HOW:  1. Load model with Unsloth (2x faster than HuggingFace)
      2. Configure LoRA adapters (low rank = fast training)
      3. Train with SFTTrainer (supervised fine-tuning)
      4. Save LoRA weights only (small file size)

USAGE: python train.py <experiment_name> <dataset_path> [--epochs N]

EXAMPLE: python train.py exp-001 datasets/example-chatbot.json --epochs 3

TIME: 3-5 minutes for 500M model with 100 samples

================================================================================
LEARNING OBJECTIVES:
- Understand LoRA: Why we fine-tune adapters, not full weights
- See Unsloth in action: Memory optimization & Flash Attention
- Track metrics: How to monitor training progress
- Experiment tracking: Why we save metadata
================================================================================
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import torch
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import FastLanguageModel

# ===== CONFIGURATION =====
# These are optimized for speed on DGX Spark (128GB UMA, Blackwell GB10)

# Model settings
BASE_MODEL = "unsloth/Qwen2.5-0.5B-Instruct"  # Unsloth's optimized version
MAX_SEQ_LENGTH = 2048  # Longer sequences = more memory, slower training

# LoRA settings
# WHY LORA? Full fine-tuning = update all 500M parameters = slow & memory-hungry
# LoRA = update small "adapter" matrices = 100x smaller, 2x faster
LORA_RANK = 8  # r=8 is sweet spot (higher = more capacity, slower training)
LORA_ALPHA = 16  # Usually 2x rank
LORA_DROPOUT = 0.05  # Regularization
LORA_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"]  # Which layers to adapt

# Training settings (optimized for speed)
DEFAULT_EPOCHS = 3  # More epochs = better fit, but slower
BATCH_SIZE = 4  # Adjust based on GPU memory (higher = faster, more memory)
LEARNING_RATE = 2e-4  # Standard for LoRA
WARMUP_STEPS = 10  # Gradual learning rate increase
WEIGHT_DECAY = 0.01  # Regularization
GRADIENT_ACCUMULATION_STEPS = 1  # Simulate larger batch size

# Optimization flags (Unsloth magic)
USE_GRADIENT_CHECKPOINTING = True  # Trade compute for memory
FP16 = False  # Use BF16 instead (better for training)
BF16 = True  # Brain float 16 - faster on modern GPUs


# ===== HELPER FUNCTIONS =====

def load_and_validate_dataset(dataset_path):
    """
    Load training dataset and validate format.

    Expected format: JSON/JSONL with 'instruction' and 'output' fields
    Or HuggingFace dataset format with 'text' field

    WHY VALIDATE? Better to fail fast with clear error than mysterious training crash
    """
    print(f"📂 Loading dataset from: {dataset_path}")

    if not os.path.exists(dataset_path):
        print(f"❌ Error: Dataset not found at {dataset_path}")
        sys.exit(1)

    # Load dataset with exception handling for malformed JSON
    if dataset_path.endswith('.json') or dataset_path.endswith('.jsonl'):
        try:
            dataset = load_dataset('json', data_files=dataset_path, split='train')
        except Exception as e:
            print(f"❌ Error: Failed to load dataset. Is the JSON valid?")
            print(f"   Details: {str(e)}")
            sys.exit(1)
    else:
        print(f"❌ Error: Unsupported dataset format. Use .json or .jsonl")
        sys.exit(1)

    # Validate format
    if len(dataset) == 0:
        print(f"❌ Error: Dataset is empty!")
        sys.exit(1)

    print(f"   ✅ Loaded {len(dataset)} samples")

    # Check for required fields - STRICT validation
    first_sample = dataset[0]
    if 'instruction' in first_sample and 'output' in first_sample:
        print(f"   ✅ Format: instruction + output")
    elif 'text' in first_sample:
        print(f"   ✅ Format: text (pre-formatted)")
    else:
        print(f"   ❌ Error: Unknown format. Expected 'instruction'+'output' or 'text'")
        print(f"   First sample keys: {list(first_sample.keys())}")
        print(f"   Please fix your dataset format.")
        sys.exit(1)

    return dataset


def format_prompt(sample):
    """
    Convert dataset sample to Qwen2.5 chat format.

    WHY? Models are trained on specific prompt formats. Using the right format
    is CRITICAL for good performance. Qwen2.5 uses ChatML format.

    TEMPLATE:
        <|im_start|>system
        {system_message}<|im_end|>
        <|im_start|>user
        {instruction}<|im_end|>
        <|im_start|>assistant
        {output}<|im_end|>
    """
    # Handle different dataset formats
    if 'instruction' in sample and 'output' in sample:
        instruction = sample['instruction']
        output = sample['output']
        system = sample.get('system', 'You are a helpful AI assistant.')

        # Qwen2.5 ChatML format
        formatted = f"""<|im_start|>system
{system}<|im_end|>
<|im_start|>user
{instruction}<|im_end|>
<|im_start|>assistant
{output}<|im_end|>"""

    elif 'text' in sample:
        # Already formatted
        formatted = sample['text']
    else:
        # This should never happen due to validation, but defensive programming!
        print(f"⚠️  Warning: Unexpected sample format during formatting: {list(sample.keys())}")
        # Create a basic fallback format
        formatted = f"""<|im_start|>system
You are a helpful AI assistant.<|im_end|>
<|im_start|>user
{str(sample)}<|im_end|>
<|im_start|>assistant
Unable to format properly.<|im_end|>"""

    return {"text": formatted}


def train_model(experiment_name, dataset_path, epochs=DEFAULT_EPOCHS):
    """
    Main training function.

    FLOW:
        1. Setup experiment directory
        2. Load model with Unsloth optimizations
        3. Prepare dataset
        4. Configure training
        5. Train!
        6. Save LoRA weights
        7. Save metadata
    """
    print("=" * 80)
    print(f"🚀 Starting Fast Fine-tuning: {experiment_name}")
    print("=" * 80)

    start_time = time.time()

    # ===== STEP 0: PRE-FLIGHT CHECKS =====
    # Check GPU availability
    if not torch.cuda.is_available():
        print("⚠️  WARNING: No GPU detected! Training will be VERY slow.")
        print("   Continue anyway? (yes/no)")
        response = input().strip().lower()
        if response != 'yes':
            print("Aborted.")
            sys.exit(1)
    else:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"✅ GPU detected: {gpu_name} ({gpu_memory:.1f} GB)")

    # Validate epochs
    if epochs <= 0:
        print(f"❌ Error: Epochs must be > 0 (got {epochs})")
        sys.exit(1)
    if epochs > 20:
        print(f"⚠️  Warning: {epochs} epochs is very high. Risk of overfitting!")
        print("   Continue anyway? (yes/no)")
        response = input().strip().lower()
        if response != 'yes':
            print("Aborted.")
            sys.exit(1)

    # ===== STEP 1: SETUP =====
    experiment_dir = Path(f"experiments/{experiment_name}")
    lora_dir = experiment_dir / "lora"
    checkpoints_dir = experiment_dir / "checkpoints"
    logs_dir = experiment_dir / "logs"

    # Create ALL necessary directories upfront (defensive!)
    experiment_dir.mkdir(parents=True, exist_ok=True)
    lora_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📁 Experiment directory: {experiment_dir}")
    print(f"   ✅ Created directories: lora/, checkpoints/, logs/")

    # ===== STEP 2: LOAD MODEL =====
    # WHY UNSLOTH? It uses Flash Attention 2, memory optimizations, and custom kernels
    # to achieve 2x speedup over vanilla transformers
    print(f"\n🤖 Loading model: {BASE_MODEL}")
    print(f"   Using Unsloth optimizations...")

    try:
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=BASE_MODEL,
            max_seq_length=MAX_SEQ_LENGTH,
            dtype=None,  # Auto-detect best dtype (BF16 on modern GPUs)
            load_in_4bit=True,  # 4-bit quantization = 4x less memory (CRITICAL!)
        )
        print(f"   ✅ Model loaded!")
    except Exception as e:
        print(f"❌ Error: Failed to load model '{BASE_MODEL}'")
        print(f"   Details: {str(e)}")
        print(f"\n   Possible causes:")
        print(f"   - Network issue (model download failed)")
        print(f"   - Unsloth not installed correctly")
        print(f"   - GPU not compatible")
        print(f"   - Out of memory")
        sys.exit(1)

    # ===== STEP 3: CONFIGURE LORA =====
    # WHY THESE PARAMETERS?
    # - rank=8: Balance between model capacity and speed (higher = better fit, slower)
    # - alpha=16: Scales LoRA contribution (usually 2x rank)
    # - target_modules: Which layers to adapt (attention + MLP for Qwen)
    print(f"\n🔧 Configuring LoRA adapters...")
    print(f"   Rank: {LORA_RANK}, Alpha: {LORA_ALPHA}")

    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES,
        bias="none",  # Don't adapt bias terms
        use_gradient_checkpointing=USE_GRADIENT_CHECKPOINTING,
        random_state=42,  # Reproducibility
    )

    # Print trainable parameters
    # LoRA typically trains <1% of total parameters!
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"   ✅ LoRA configured!")
    print(f"   Trainable parameters: {trainable_params:,} / {total_params:,} "
          f"({100 * trainable_params / total_params:.2f}%)")

    # ===== STEP 4: PREPARE DATASET =====
    print(f"\n📊 Preparing dataset...")
    dataset = load_and_validate_dataset(dataset_path)

    # Format prompts for Qwen2.5
    dataset = dataset.map(format_prompt, remove_columns=dataset.column_names)

    # ===== STEP 5: CONFIGURE TRAINING =====
    print(f"\n⚙️  Configuring training...")
    print(f"   Epochs: {epochs}")
    print(f"   Batch size: {BATCH_SIZE}")
    print(f"   Learning rate: {LEARNING_RATE}")

    training_args = TrainingArguments(
        # Output (use our pre-created directories)
        output_dir=str(checkpoints_dir),

        # Training duration
        num_train_epochs=epochs,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,

        # Optimization
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        warmup_steps=WARMUP_STEPS,

        # Performance
        fp16=FP16,
        bf16=BF16,
        optim="adamw_8bit",  # 8-bit Adam = less memory

        # Logging (use pre-created logs directory)
        logging_steps=10,
        logging_dir=str(logs_dir),
        report_to="none",  # No wandb/tensorboard for speed

        # Saving
        save_strategy="epoch",  # Save at end of each epoch
        save_total_limit=1,  # Only keep latest checkpoint

        # Other
        seed=42,
        dataloader_num_workers=4,  # Parallel data loading
    )

    # ===== STEP 6: CREATE TRAINER =====
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",  # Which field contains the formatted prompts
        max_seq_length=MAX_SEQ_LENGTH,
        args=training_args,
        packing=False,  # Don't pack multiple samples (simpler, slightly slower)
    )

    # ===== STEP 7: TRAIN! =====
    print(f"\n🎯 Starting training...")
    print(f"   Watch for progress bars below")
    # Safer time estimation (avoid division by zero)
    est_min = max(1, len(dataset) * epochs // (BATCH_SIZE * 60))
    est_max = max(2, len(dataset) * epochs // (BATCH_SIZE * 30))
    print(f"   Expected time: {est_min}-{est_max} minutes")
    print("-" * 80)

    try:
        train_result = trainer.train()
        print("-" * 80)
        print(f"   ✅ Training complete!")
    except Exception as e:
        print("-" * 80)
        print(f"❌ Error: Training failed!")
        print(f"   Details: {str(e)}")
        print(f"\n   Common causes:")
        print(f"   - Out of GPU memory (try reducing BATCH_SIZE)")
        print(f"   - Dataset format issues")
        print(f"   - CUDA error (driver issue)")
        sys.exit(1)

    # ===== STEP 8: SAVE LORA WEIGHTS =====
    print(f"\n💾 Saving LoRA weights to: {lora_dir}")
    model.save_pretrained(str(lora_dir))
    tokenizer.save_pretrained(str(lora_dir))
    print(f"   ✅ Saved!")

    # ===== STEP 9: SAVE METADATA =====
    # WHY? Track experiment details for comparison and debugging
    end_time = time.time()
    training_time = end_time - start_time

    metadata = {
        "experiment_name": experiment_name,
        "timestamp": datetime.now().isoformat(),
        "training_time_seconds": training_time,
        "training_time_minutes": training_time / 60,

        # Model config
        "base_model": BASE_MODEL,
        "max_seq_length": MAX_SEQ_LENGTH,

        # LoRA config
        "lora_rank": LORA_RANK,
        "lora_alpha": LORA_ALPHA,
        "lora_dropout": LORA_DROPOUT,
        "trainable_params": trainable_params,
        "total_params": total_params,
        "trainable_percentage": 100 * trainable_params / total_params,

        # Training config
        "epochs": epochs,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "dataset_path": dataset_path,
        "dataset_size": len(dataset),

        # Results
        "final_loss": float(train_result.training_loss),
        "training_samples": train_result.global_step * BATCH_SIZE,
    }

    metadata_path = experiment_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n📋 Metadata saved to: {metadata_path}")

    # ===== SUMMARY =====
    print("\n" + "=" * 80)
    print("✅ Training Complete!")
    print("=" * 80)
    print(f"Experiment: {experiment_name}")
    print(f"Time: {training_time / 60:.1f} minutes")
    print(f"Final loss: {train_result.training_loss:.4f}")
    print(f"LoRA weights: {lora_dir}")
    print(f"\nNext steps:")
    print(f"  1. Export to Ollama: ./scripts/export_to_ollama.sh {experiment_name}")
    print(f"  2. Run benchmark: python benchmark/run.py {experiment_name}")
    print(f"  3. View results: open benchmark/results/report.html")
    print("=" * 80)

    return experiment_dir


# ===== MAIN =====
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fast fine-tuning with Unsloth + Qwen2.5-0.5B",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick test with 3 epochs
  python train.py exp-001 datasets/example-chatbot.json

  # Longer training with 5 epochs
  python train.py exp-002 datasets/example-chatbot.json --epochs 5

  # Custom dataset
  python train.py exp-003 my_data.json --epochs 3

Tips:
  - Start with 3 epochs, increase if model underfits
  - Smaller datasets need fewer epochs (risk overfitting)
  - Monitor loss: should decrease steadily
  - If OOM (out of memory), reduce BATCH_SIZE in script
        """
    )

    parser.add_argument(
        "experiment_name",
        help="Unique name for this experiment (e.g., exp-001, chatbot-v2)"
    )
    parser.add_argument(
        "dataset_path",
        help="Path to training dataset (JSON/JSONL format)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=DEFAULT_EPOCHS,
        help=f"Number of training epochs (default: {DEFAULT_EPOCHS})"
    )

    args = parser.parse_args()

    # Validate experiment name doesn't already exist
    experiment_dir = Path(f"experiments/{args.experiment_name}")
    if experiment_dir.exists():
        print(f"⚠️  Warning: Experiment '{args.experiment_name}' already exists!")
        response = input("Overwrite? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Aborted.")
            sys.exit(1)

    # Train!
    train_model(args.experiment_name, args.dataset_path, args.epochs)
