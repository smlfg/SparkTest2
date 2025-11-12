#!/usr/bin/env python3
"""
AGENT 6: Experiment Logger

WAS DIESES SKRIPT MACHT (TEACHING):
1. Lädt `metadata.json` (von Agent 1) – enthält Konfiguration (lr, rank) & Performance (Dauer).
2. Lädt `deltas.json` (von Agent 3) – enthält Analyseergebnisse.
3. Erstellt einen "Summary"-Eintrag.
4. Hängt diesen Eintrag an `experiments/log.json` an.

WARUM?
Dies ist unser "Laborbuch". Nach 10 Iterationen können wir
`log.json` öffnen und die beste Konfiguration finden, indem wir
`config` mit `summary.score` vergleichen.

TEACHING CONCEPTS:
- JSON persistence: Simple, human-readable experiment tracking
- Score calculation: Quantifying improvement for comparison
- Append-only log: Never lose experiment history
- Metadata capture: Everything needed to reproduce results
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

################################################################################
# Helper Functions
################################################################################

def load_json(path: Path) -> dict | list:
    """
    Lädt eine JSON-Datei sicher.

    TEACHING: Always validate file existence before reading.
    Failing fast with clear errors is better than cryptic crashes later.
    """
    if not path.exists():
        print(f"❌ Error: {path} not found!")
        print(f"   Make sure the previous step completed successfully.")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {path}")
        print(f"   {e}")
        sys.exit(1)


def summarize_deltas(deltas_data: dict) -> dict:
    """
    Zählt die Ergebnisse aus der Delta-Analyse zusammen.

    TEACHING: A "score" is a single metric to compare experiments.
    Here: (improvements - regressions) / total

    This allows sorting experiments by effectiveness:
    - Score +0.5 = 50% of prompts improved (great!)
    - Score -0.2 = 20% of prompts regressed (needs work)
    - Score  0.0 = Equal improvements and regressions (neutral)
    """
    deltas = deltas_data.get("deltas", [])

    stats = {
        "improved": 0,
        "regressed": 0,
        "changed": 0,
        "similar": 0,
        "total": len(deltas)
    }

    for delta in deltas:
        assessment = delta.get("assessment", "similar")
        if assessment in stats:
            stats[assessment] += 1

    # Calculate score
    # TEACHING: This is a simple heuristic. You could also use:
    # - Weighted score (improvement = +2, regression = -3)
    # - Average similarity improvement
    # - Task-specific metrics (accuracy for classifier, BLEU for translation)
    if stats["total"] > 0:
        stats["score"] = (stats["improved"] - stats["regressed"]) / stats["total"]
    else:
        stats["score"] = 0.0

    return stats


def create_log_entry(experiment_name: str, metadata: dict, deltas_data: dict,
                     report_path: str) -> dict:
    """
    Creates a structured log entry for this experiment.

    TEACHING: Good logging includes:
    1. What: Configuration (hyperparameters)
    2. How: Performance (timing, loss)
    3. Result: Summary (score, improved/regressed counts)
    4. When: Timestamp
    5. Where: Paths to artifacts
    """
    summary = summarize_deltas(deltas_data)

    return {
        "name": experiment_name,
        "timestamp": datetime.now().isoformat(),
        "dataset": metadata.get("dataset", {}).get("path", "unknown"),
        "config": {
            "model": metadata.get("model", {}).get("base", "unknown"),
            "lora": metadata.get("lora", {}),
            "training": metadata.get("training", {})
        },
        "performance": {
            "train_time_seconds": metadata.get("results", {}).get("train_runtime", 0),
            "train_loss": metadata.get("results", {}).get("train_loss", 0),
            "samples_per_second": metadata.get("results", {}).get("train_samples_per_second", 0)
        },
        "summary": summary,
        "artifacts": {
            "report": report_path,
            "model": f"experiments/{experiment_name}/lora",
            "metadata": f"experiments/{experiment_name}/metadata.json"
        }
    }


def append_to_log(log_path: Path, entry: dict):
    """
    Appends entry to log file, creating it if it doesn't exist.

    TEACHING: Append-only logs are safe:
    - Never lose data (no overwrites)
    - Easy to audit (see all history)
    - Simple to implement (read, append, write)
    """
    # Load existing log or create new
    if log_path.exists():
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️  Warning: Corrupted log file. Creating backup...")
            backup_path = log_path.with_suffix(".json.bak")
            log_path.rename(backup_path)
            log_data = []
    else:
        log_data = []

    # Append new entry
    log_data.append(entry)

    # Write back
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)


def print_summary(entry: dict):
    """Pretty-print the experiment summary."""
    print("\n" + "="*60)
    print("📊 EXPERIMENT SUMMARY")
    print("="*60)
    print(f"\nName:     {entry['name']}")
    print(f"Dataset:  {entry['dataset']}")
    print(f"Time:     {entry['timestamp']}")

    perf = entry['performance']
    print(f"\n⏱️  Performance:")
    print(f"   Training: {perf['train_time_seconds']:.1f}s")
    print(f"   Loss:     {perf['train_loss']:.4f}")
    print(f"   Speed:    {perf['samples_per_second']:.2f} samples/sec")

    summary = entry['summary']
    print(f"\n📈 Results:")
    print(f"   Score:      {summary['score']:+.2f}")
    print(f"   Improved:   {summary['improved']}/{summary['total']} ({summary['improved']/summary['total']*100:.0f}%)")
    print(f"   Regressed:  {summary['regressed']}/{summary['total']} ({summary['regressed']/summary['total']*100:.0f}%)")
    print(f"   Changed:    {summary['changed']}/{summary['total']}")
    print(f"   Similar:    {summary['similar']}/{summary['total']}")

    print(f"\n📁 Artifacts:")
    print(f"   Report: {entry['artifacts']['report']}")
    print(f"   Model:  {entry['artifacts']['model']}")

    print("\n" + "="*60)


def compare_with_previous(log_path: Path, current_entry: dict):
    """
    Compare current experiment with previous one.

    TEACHING: This shows iteration progress:
    - Is score improving over iterations?
    - Are we getting faster?
    - What changed in configuration?
    """
    if not log_path.exists():
        return

    with open(log_path, "r", encoding="utf-8") as f:
        log_data = json.load(f)

    if len(log_data) < 1:  # No previous experiments
        return

    prev = log_data[-1]  # Most recent previous experiment
    curr = current_entry

    print("\n" + "="*60)
    print("📊 COMPARISON WITH PREVIOUS EXPERIMENT")
    print("="*60)
    print(f"\nPrevious: {prev['name']} (score: {prev['summary']['score']:+.2f})")
    print(f"Current:  {curr['name']} (score: {curr['summary']['score']:+.2f})")

    score_delta = curr['summary']['score'] - prev['summary']['score']
    if score_delta > 0:
        print(f"\n✅ Score improved by {score_delta:+.2f}")
    elif score_delta < 0:
        print(f"\n⚠️  Score decreased by {score_delta:.2f}")
    else:
        print(f"\n➡️  Score unchanged")

    # Show what changed in config
    print("\n🔧 Configuration changes:")
    curr_lr = curr['config']['training'].get('learning_rate', 0)
    prev_lr = prev['config']['training'].get('learning_rate', 0)
    if curr_lr != prev_lr:
        print(f"   Learning rate: {prev_lr} → {curr_lr}")

    curr_epochs = curr['config']['training'].get('epochs', 0)
    prev_epochs = prev['config']['training'].get('epochs', 0)
    if curr_epochs != prev_epochs:
        print(f"   Epochs: {prev_epochs} → {curr_epochs}")

    curr_rank = curr['config']['lora'].get('r', 0)
    prev_rank = prev['config']['lora'].get('r', 0)
    if curr_rank != prev_rank:
        print(f"   LoRA rank: {prev_rank} → {curr_rank}")

    print("="*60)


################################################################################
# Main Function
################################################################################

def main():
    parser = argparse.ArgumentParser(
        description="Log experiment results to experiments/log.json",
        epilog="""
This script is called by iterate.sh as the final step.
It creates a permanent record of each experiment for comparison.

Example:
    python experiments/log_experiment.py exp-001
        """
    )

    parser.add_argument(
        "name",
        help="Experiment name (e.g., exp-001)"
    )
    parser.add_argument(
        "--report",
        default="benchmark/results/report.html",
        help="Path to HTML report (default: benchmark/results/report.html)"
    )

    args = parser.parse_args()

    print(f"\n📝 Logging experiment: {args.name}")

    # Define paths
    log_file_path = Path("experiments/log.json")
    meta_path = Path(f"experiments/{args.name}/metadata.json")
    delta_path = Path("benchmark/results/deltas.json")

    # Load data from previous agents
    print("   Loading metadata from Agent 1...")
    metadata = load_json(meta_path)

    print("   Loading deltas from Agent 3...")
    deltas_data = load_json(delta_path)

    # Create log entry
    print("   Creating summary...")
    entry = create_log_entry(args.name, metadata, deltas_data, args.report)

    # Compare with previous
    if log_file_path.exists():
        compare_with_previous(log_file_path, entry)

    # Append to log
    print(f"   Writing to {log_file_path}...")
    append_to_log(log_file_path, entry)

    # Print summary
    print_summary(entry)

    print(f"\n✅ Experiment logged successfully!")
    print(f"\n💡 Tip: View all experiments with:")
    print(f"   cat {log_file_path} | python3 -m json.tool")
    print(f"\n💡 Or find best experiment with:")
    print(f"   python3 -c \"import json; log=json.load(open('{log_file_path}')); best=max(log, key=lambda x: x['summary']['score']); print(f'Best: {{best[\\\"name\\\"]}} (score: {{best[\\\"summary\\\"][\\\"score\\\"]:.2f}})')\"")


if __name__ == "__main__":
    main()
