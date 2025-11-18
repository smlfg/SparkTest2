#!/usr/bin/env python3
"""
Download and Convert Hugging Face Datasets

This script downloads datasets from Hugging Face and converts them
to the chat format needed for training.

Usage:
    python scripts/download_hf_dataset.py wikipedia --samples 1000
    python scripts/download_hf_dataset.py stackoverflow --samples 500
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from datasets import load_dataset
    from rich.console import Console
    from rich.progress import track
except ImportError:
    print("❌ Error: Missing dependencies")
    print("Install: pip install datasets rich")
    sys.exit(1)

console = Console()

################################################################################
# Dataset Configurations
################################################################################

DATASETS = {
    "wikipedia": {
        "hf_path": "legacy-datasets/wikipedia",
        "hf_config": "20220301.en",  # English Wikipedia
        "split": "train",
        "converter": "wikipedia_to_chat",
        "description": "Wikipedia articles (English)",
    },
    "stackoverflow": {
        "hf_path": "c17hawke/stackoverflow-dataset",
        "hf_config": None,
        "split": "train",
        "converter": "stackoverflow_to_chat",
        "description": "StackOverflow questions and answers",
    },
    "tiny-codes": {
        "hf_path": "nampdn-ai/tiny-codes",
        "hf_config": None,
        "split": "train",
        "converter": "tiny_codes_to_chat",
        "description": "Small code snippets with explanations",
    },
    "codeparrot": {
        "hf_path": "codeparrot/codeparrot-clean-train",
        "hf_config": None,
        "split": "train",
        "converter": "codeparrot_to_chat",
        "description": "Clean Python code examples",
    },
}

################################################################################
# Converters
################################################################################

def wikipedia_to_chat(example):
    """
    Convert Wikipedia article to chat format.

    Creates Q&A pairs from article:
    User: "Tell me about [title]"
    Assistant: [text excerpt]
    """
    title = example.get("title", "this topic")
    text = example.get("text", "")

    # Skip empty articles
    if not text or len(text) < 100:
        return None

    # Truncate to reasonable length (first ~500 chars)
    excerpt = text[:500].strip()
    if len(text) > 500:
        # Try to end at sentence boundary
        last_period = excerpt.rfind('.')
        if last_period > 200:
            excerpt = excerpt[:last_period + 1]
        else:
            excerpt += "..."

    return {
        "messages": [
            {
                "role": "user",
                "content": f"Tell me about {title}"
            },
            {
                "role": "assistant",
                "content": excerpt
            }
        ]
    }


def stackoverflow_to_chat(example):
    """
    Convert StackOverflow Q&A to chat format.

    User: [question]
    Assistant: [answer]
    """
    question = example.get("question", "")
    answer = example.get("answer", "")

    # Skip if missing either part
    if not question or not answer:
        return None

    # Truncate if too long
    if len(question) > 1000:
        question = question[:1000] + "..."
    if len(answer) > 1000:
        answer = answer[:1000] + "..."

    return {
        "messages": [
            {
                "role": "user",
                "content": question.strip()
            },
            {
                "role": "assistant",
                "content": answer.strip()
            }
        ]
    }


def tiny_codes_to_chat(example):
    """
    Convert tiny-codes to chat format.

    This dataset contains small code snippets with prompts/instructions.
    Handles multiple possible field names: prompt/instruction and response/output/code.

    User: [prompt/instruction]
    Assistant: [code/response]
    """
    # Try different field names for prompt
    prompt = example.get("prompt") or example.get("instruction") or example.get("question") or ""

    # Try different field names for code/response
    response = example.get("response") or example.get("output") or example.get("code") or example.get("answer") or ""

    # Skip if missing either part
    if not prompt or not response:
        return None

    # Skip if too short (likely invalid)
    if len(prompt) < 10 or len(response) < 10:
        return None

    # Truncate if too long
    if len(prompt) > 800:
        prompt = prompt[:800] + "..."
    if len(response) > 1500:
        # For code, try to keep it complete
        response = response[:1500] + "\n# ... (truncated)"

    return {
        "messages": [
            {
                "role": "user",
                "content": prompt.strip()
            },
            {
                "role": "assistant",
                "content": response.strip()
            }
        ]
    }


def codeparrot_to_chat(example):
    """
    Convert CodeParrot clean code to chat format.

    CodeParrot contains raw Python code. We create synthetic Q&A:
    User: "Write Python code for [inferred purpose]"
    Assistant: [code]

    For better training, we extract docstrings or first comments as hints.
    """
    code = example.get("content") or example.get("code") or ""

    # Skip empty or very short code
    if not code or len(code) < 50:
        return None

    # Skip if too long (only take first portion)
    if len(code) > 2000:
        code = code[:2000]
        # Try to cut at a complete function
        last_def = code.rfind("\ndef ")
        if last_def > 500:
            code = code[:last_def]
        code += "\n# ... (truncated)"

    # Extract first line comment or docstring as hint
    lines = code.split('\n')
    hint = "this task"

    # Look for docstring
    for i, line in enumerate(lines[:10]):
        if '"""' in line or "'''" in line:
            # Found docstring
            if i + 1 < len(lines):
                hint = lines[i + 1].strip('"""\'').strip()[:100]
            break
        elif line.strip().startswith('#'):
            # Found comment
            hint = line.strip('#').strip()[:100]
            break

    # Create synthetic prompt
    prompt = f"Write Python code for {hint}" if hint != "this task" else "Write Python code"

    return {
        "messages": [
            {
                "role": "user",
                "content": prompt
            },
            {
                "role": "assistant",
                "content": code.strip()
            }
        ]
    }


################################################################################
# Main Functions
################################################################################

def download_and_convert(dataset_name, num_samples=1000, output_dir="datasets"):
    """Download and convert a dataset."""

    if dataset_name not in DATASETS:
        console.print(f"[red]❌ Unknown dataset: {dataset_name}[/red]")
        console.print(f"[yellow]Available datasets: {', '.join(DATASETS.keys())}[/yellow]")
        return False

    config = DATASETS[dataset_name]

    console.print(f"\n[bold blue]📥 Downloading {dataset_name} from Hugging Face[/bold blue]")
    console.print(f"[dim]Description: {config['description']}[/dim]")
    console.print(f"[dim]HF Path: {config['hf_path']}[/dim]")
    console.print(f"[dim]Samples: {num_samples}[/dim]\n")

    # Load dataset
    try:
        console.print("[cyan]Loading dataset...[/cyan]")
        if config['hf_config']:
            dataset = load_dataset(
                config['hf_path'],
                config['hf_config'],
                split=config['split'],
                streaming=True  # Stream to avoid loading entire dataset
            )
        else:
            dataset = load_dataset(
                config['hf_path'],
                split=config['split'],
                streaming=True
            )
        console.print("[green]✓ Dataset loaded[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error loading dataset: {e}[/red]")
        return False

    # Get converter function
    converter_name = config['converter']
    converter = globals()[converter_name]

    # Convert samples
    console.print(f"\n[cyan]Converting {num_samples} samples...[/cyan]")

    converted = []
    skipped = 0

    for i, example in track(enumerate(dataset), total=num_samples, description="Converting"):
        if len(converted) >= num_samples:
            break

        try:
            chat_format = converter(example)
            if chat_format:
                converted.append(chat_format)
            else:
                skipped += 1
        except Exception as e:
            console.print(f"[yellow]⚠️  Skipped sample {i}: {e}[/yellow]")
            skipped += 1

    console.print(f"[green]✓ Converted {len(converted)} samples[/green]")
    if skipped > 0:
        console.print(f"[yellow]⚠️  Skipped {skipped} samples (empty or invalid)[/yellow]")

    # Save to file
    output_path = Path(output_dir) / f"{dataset_name}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[cyan]Saving to {output_path}...[/cyan]")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(converted, f, indent=2, ensure_ascii=False)

    # Get file size
    size_mb = output_path.stat().st_size / (1024 * 1024)

    console.print(f"[green]✓ Saved {len(converted)} examples[/green]")
    console.print(f"[green]  File: {output_path}[/green]")
    console.print(f"[green]  Size: {size_mb:.2f} MB[/green]")

    # Show preview
    console.print("\n[bold]Preview:[/bold]")
    if converted:
        first = converted[0]
        console.print(f"[cyan]User:[/cyan] {first['messages'][0]['content'][:100]}...")
        console.print(f"[green]Assistant:[/green] {first['messages'][1]['content'][:100]}...")

    console.print(f"\n[bold green]✅ Done! Dataset ready at: {output_path}[/bold green]")
    console.print(f"\n[cyan]Use it with:[/cyan]")
    console.print(f"  ./iterate.sh my-experiment")
    console.print(f"  -> Select '{dataset_name}.json' from the list\n")

    return True


def list_available_datasets():
    """List all available datasets."""
    console.print("\n[bold]Available Datasets:[/bold]\n")

    for name, config in DATASETS.items():
        console.print(f"  [green]• {name}[/green]")
        console.print(f"    {config['description']}")
        console.print(f"    HF: {config['hf_path']}")
        console.print()


################################################################################
# CLI
################################################################################

def main():
    parser = argparse.ArgumentParser(
        description="Download and convert Hugging Face datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download 1000 Wikipedia samples
  python scripts/download_hf_dataset.py wikipedia --samples 1000

  # Download 500 StackOverflow samples
  python scripts/download_hf_dataset.py stackoverflow --samples 500

  # List available datasets
  python scripts/download_hf_dataset.py --list

After downloading, the dataset will be available in the datasets/ folder
and will appear in the interactive selection menu when you run iterate.sh.
        """
    )

    parser.add_argument(
        "dataset",
        nargs="?",
        help="Dataset name (wikipedia, stackoverflow, etc.)"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=1000,
        help="Number of samples to download (default: 1000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="datasets",
        help="Output directory (default: datasets/)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available datasets"
    )

    args = parser.parse_args()

    if args.list:
        list_available_datasets()
        return

    if not args.dataset:
        console.print("[red]❌ Error: No dataset specified[/red]")
        console.print("[yellow]Use --list to see available datasets[/yellow]")
        parser.print_help()
        sys.exit(1)

    success = download_and_convert(
        args.dataset,
        num_samples=args.samples,
        output_dir=args.output
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
