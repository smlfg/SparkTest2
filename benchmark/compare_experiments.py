#!/usr/bin/env python3
"""
Experiment Comparison Tool

Compare multiple experiments to identify the best configuration.

Usage:
    python benchmark/compare_experiments.py

This will analyze experiments/log.json and show:
- Best experiment by improvement rate
- Training time comparison
- Success rate trends
"""

import json
from pathlib import Path
from datetime import datetime


def load_experiment_log():
    """Load experiment log."""
    log_path = Path("experiments/log.json")

    if not log_path.exists():
        print("❌ No experiments found. Run an iteration first!")
        return []

    with open(log_path, 'r') as f:
        return json.load(f)


def print_summary(experiments):
    """Print experiment summary table."""
    print("\n📊 Experiment Summary")
    print("=" * 100)

    if not experiments:
        print("No experiments yet.")
        return

    # Header
    print(f"{'Name':<30} {'Improvement':>12} {'Train Time':>12} {'Total Time':>12} {'Timestamp':<20}")
    print("-" * 100)

    # Sort by improvement rate
    experiments_sorted = sorted(
        experiments,
        key=lambda x: x["results"]["improvement_rate"],
        reverse=True
    )

    # Print rows
    for exp in experiments_sorted:
        name = exp["experiment_name"]
        improvement = exp["results"]["improvement_rate"]
        train_time = exp["timing"]["train_seconds"]
        total_time = exp["timing"]["total_minutes"]
        timestamp = exp["timestamp"].split("T")[0]  # Date only

        print(f"{name:<30} {improvement:>11.1f}% {train_time:>11.0f}s {total_time:>11.1f}m {timestamp:<20}")

    print("=" * 100)


def print_best_experiment(experiments):
    """Print details of best experiment."""
    if not experiments:
        return

    best = max(experiments, key=lambda x: x["results"]["improvement_rate"])

    print("\n🏆 Best Experiment")
    print("=" * 60)
    print(f"Name: {best['experiment_name']}")
    print(f"Improvement Rate: {best['results']['improvement_rate']}%")
    print(f"Improved: {best['results']['improved']} / {best['results']['total_prompts']}")
    print(f"Regressed: {best['results']['regressed']}")
    print(f"Training Time: {best['timing']['train_seconds']}s ({best['timing']['train_seconds']/60:.1f}m)")
    print(f"Total Time: {best['timing']['total_minutes']:.1f}m")
    print(f"Dataset: {best['dataset']}")
    print("=" * 60)


def print_statistics(experiments):
    """Print aggregate statistics."""
    if not experiments:
        return

    improvements = [e["results"]["improvement_rate"] for e in experiments]
    train_times = [e["timing"]["train_seconds"] for e in experiments]
    total_times = [e["timing"]["total_minutes"] for e in experiments]

    print("\n📈 Aggregate Statistics")
    print("=" * 60)
    print(f"Total experiments: {len(experiments)}")
    print(f"\nImprovement Rate:")
    print(f"  Average: {sum(improvements)/len(improvements):.1f}%")
    print(f"  Best: {max(improvements):.1f}%")
    print(f"  Worst: {min(improvements):.1f}%")
    print(f"\nTraining Time:")
    print(f"  Average: {sum(train_times)/len(train_times):.0f}s ({sum(train_times)/len(train_times)/60:.1f}m)")
    print(f"  Fastest: {min(train_times):.0f}s")
    print(f"  Slowest: {max(train_times):.0f}s")
    print(f"\nTotal Iteration Time:")
    print(f"  Average: {sum(total_times)/len(total_times):.1f}m")
    print(f"  Fastest: {min(total_times):.1f}m")
    print(f"  Slowest: {max(total_times):.1f}m")
    print("=" * 60)


def print_trends(experiments):
    """Print trends over time."""
    if len(experiments) < 3:
        return

    # Sort by timestamp
    experiments_sorted = sorted(experiments, key=lambda x: x["timestamp"])

    print("\n📉 Trends (Chronological)")
    print("=" * 60)

    improvements = [e["results"]["improvement_rate"] for e in experiments_sorted]

    # Calculate trend
    if improvements[-1] > improvements[0]:
        trend = "📈 IMPROVING"
        change = improvements[-1] - improvements[0]
        print(f"Trend: {trend} (+{change:.1f}% overall)")
    elif improvements[-1] < improvements[0]:
        trend = "📉 DECLINING"
        change = improvements[0] - improvements[-1]
        print(f"Trend: {trend} (-{change:.1f}% overall)")
    else:
        trend = "➡️  STABLE"
        print(f"Trend: {trend}")

    # Last 3 experiments
    print(f"\nLast 3 experiments:")
    for exp in experiments_sorted[-3:]:
        print(f"  {exp['experiment_name']}: {exp['results']['improvement_rate']:.1f}%")

    print("=" * 60)


def export_csv(experiments):
    """Export experiments to CSV for further analysis."""
    if not experiments:
        return

    output_path = Path("experiments/experiments.csv")

    with open(output_path, 'w') as f:
        # Header
        f.write("name,timestamp,dataset,improvement_rate,improved,regressed,changed,unchanged,")
        f.write("train_seconds,total_minutes\n")

        # Rows
        for exp in experiments:
            f.write(f"{exp['experiment_name']},")
            f.write(f"{exp['timestamp']},")
            f.write(f"{exp['dataset']},")
            f.write(f"{exp['results']['improvement_rate']},")
            f.write(f"{exp['results']['improved']},")
            f.write(f"{exp['results']['regressed']},")
            f.write(f"{exp['results']['changed']},")
            f.write(f"{exp['results']['unchanged']},")
            f.write(f"{exp['timing']['train_seconds']},")
            f.write(f"{exp['timing']['total_minutes']}\n")

    print(f"\n💾 Exported to {output_path}")


def main():
    """Main comparison script."""
    print("=" * 60)
    print("Experiment Comparison Tool")
    print("=" * 60)

    # Load experiments
    experiments = load_experiment_log()

    if not experiments:
        print("\n❌ No experiments found.")
        print("Run your first iteration:")
        print("  ./iterate.sh exp-001 datasets/example-chatbot.json")
        return

    # Print summaries
    print_summary(experiments)
    print_best_experiment(experiments)
    print_statistics(experiments)
    print_trends(experiments)

    # Export CSV
    export_csv(experiments)

    print("\n" + "=" * 60)
    print("✅ Comparison complete!")
    print("\nNext steps:")
    print("  - Review best experiment settings")
    print("  - Iterate on successful configurations")
    print("  - Analyze trends to guide future experiments")
    print("=" * 60)


if __name__ == "__main__":
    main()
