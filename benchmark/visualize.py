#!/usr/bin/env python3

"""
AGENT 4: Visualization

This script generates an HTML report from delta analysis results.

TEACHING NOTES:

1. WHY HTML REPORTS?
   - Easy to share (single file, open in browser)
   - Rich formatting (colors, tables, side-by-side comparison)
   - No dependencies (just open the file)
   - Can be archived for experiment tracking

2. WHAT TO SHOW:
   - Side-by-side comparison (base vs fine-tuned)
   - Color coding (green = improved, red = regressed)
   - Metrics (length, similarity, correctness)
   - Summary statistics (% improved, % regressed)

3. DESIGN PRINCIPLES:
   - Scannable: Quick visual overview
   - Detailed: Can drill into specific prompts
   - Actionable: Shows what to fix next
   - Archivable: Self-contained for future reference

4. USING THE REPORT:
   - Look at regressed prompts first (quick wins)
   - Check if improvements match your goals
   - Identify patterns (e.g., all math prompts regressed)
   - Use to guide next iteration
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List

from rich.console import Console

console = Console()

################################################################################
# HTML Template
################################################################################

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fine-tuning Benchmark Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }

        header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }

        header .meta {
            opacity: 0.9;
            font-size: 0.9em;
        }

        .summary {
            padding: 30px;
            background: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }

        .stat-card h3 {
            font-size: 0.85em;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }

        .stat-card.improved { border-left-color: #10b981; }
        .stat-card.regressed { border-left-color: #ef4444; }
        .stat-card.changed { border-left-color: #f59e0b; }
        .stat-card.similar { border-left-color: #6b7280; }

        .stat-card.improved .value { color: #10b981; }
        .stat-card.regressed .value { color: #ef4444; }
        .stat-card.changed .value { color: #f59e0b; }
        .stat-card.similar .value { color: #6b7280; }

        .results {
            padding: 30px;
        }

        .result-item {
            margin-bottom: 30px;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            overflow: hidden;
        }

        .result-header {
            padding: 15px 20px;
            background: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .result-header h3 {
            font-size: 1.1em;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge.improved { background: #d1fae5; color: #065f46; }
        .badge.regressed { background: #fee2e2; color: #991b1b; }
        .badge.changed { background: #fef3c7; color: #92400e; }
        .badge.similar { background: #e5e7eb; color: #374151; }

        .prompt {
            padding: 15px 20px;
            background: #fffbeb;
            border-bottom: 1px solid #e5e7eb;
            font-style: italic;
        }

        .responses {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
        }

        .response {
            padding: 20px;
        }

        .response.base {
            border-right: 1px solid #e5e7eb;
        }

        .response h4 {
            font-size: 0.85em;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }

        .response-text {
            background: #f9fafb;
            padding: 15px;
            border-radius: 4px;
            white-space: pre-wrap;
            font-family: 'SF Mono', Monaco, 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.5;
        }

        .metrics {
            padding: 15px 20px;
            background: #f9fafb;
            border-top: 1px solid #e5e7eb;
            font-size: 0.85em;
            color: #6b7280;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }

        .metric {
            display: flex;
            flex-direction: column;
        }

        .metric-label {
            font-weight: 600;
        }

        .metric-value {
            color: #111827;
        }

        .assessment-reason {
            margin-top: 10px;
            padding: 10px;
            background: white;
            border-left: 3px solid #667eea;
            border-radius: 4px;
        }

        footer {
            padding: 20px;
            text-align: center;
            color: #6b7280;
            font-size: 0.85em;
            border-top: 1px solid #e5e7eb;
        }

        @media (max-width: 768px) {
            .responses {
                grid-template-columns: 1fr;
            }

            .response.base {
                border-right: none;
                border-bottom: 1px solid #e5e7eb;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Fine-tuning Benchmark Report</h1>
            <div class="meta">
                <div><strong>Base Model:</strong> {{ base_model }}</div>
                <div><strong>Fine-tuned Model:</strong> {{ finetuned_model }}</div>
                <div><strong>Domain:</strong> {{ domain }}</div>
                <div><strong>Generated:</strong> {{ timestamp }}</div>
            </div>
        </header>

        <div class="summary">
            <h2>Summary</h2>
            <div class="stats">
                <div class="stat-card improved">
                    <h3>Improved</h3>
                    <div class="value">{{ summary.improved }}</div>
                    <div>{{ summary.improved_pct }}%</div>
                </div>
                <div class="stat-card regressed">
                    <h3>Regressed</h3>
                    <div class="value">{{ summary.regressed }}</div>
                    <div>{{ summary.regressed_pct }}%</div>
                </div>
                <div class="stat-card changed">
                    <h3>Changed</h3>
                    <div class="value">{{ summary.changed }}</div>
                    <div>{{ summary.changed_pct }}%</div>
                </div>
                <div class="stat-card similar">
                    <h3>Similar</h3>
                    <div class="value">{{ summary.similar }}</div>
                    <div>{{ summary.similar_pct }}%</div>
                </div>
            </div>
        </div>

        <div class="results">
            <h2>Detailed Results</h2>
            {{ results_html }}
        </div>

        <footer>
            Generated by Agent 4: Visualization | DGX Fast Fine-tuning System
        </footer>
    </div>
</body>
</html>
"""

RESULT_ITEM_TEMPLATE = """
<div class="result-item">
    <div class="result-header">
        <h3>{{ prompt_id }}</h3>
        <span class="badge {{ assessment }}">{{ assessment }}</span>
    </div>

    <div class="prompt">
        <strong>Prompt:</strong> {{ prompt }}
    </div>

    <div class="responses">
        <div class="response base">
            <h4>Base Model</h4>
            <div class="response-text">{{ base_response }}</div>
        </div>
        <div class="response finetuned">
            <h4>Fine-tuned Model</h4>
            <div class="response-text">{{ finetuned_response }}</div>
        </div>
    </div>

    <div class="metrics">
        <div class="assessment-reason">
            <strong>Assessment:</strong> {{ assessment_reason }}
        </div>
        <div class="metrics-grid">
            <div class="metric">
                <span class="metric-label">Length Delta:</span>
                <span class="metric-value">{{ length_delta }}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Word Overlap:</span>
                <span class="metric-value">{{ word_overlap }}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Base Correctness:</span>
                <span class="metric-value">{{ base_correctness }}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Fine-tuned Correctness:</span>
                <span class="metric-value">{{ finetuned_correctness }}</span>
            </div>
        </div>
    </div>
</div>
"""

################################################################################
# Helper Functions
################################################################################

def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def render_template(template: str, **kwargs) -> str:
    """Simple template rendering (replace {{ var }} with values)."""
    result = template
    for key, value in kwargs.items():
        result = result.replace(f"{{{{ {key} }}}}", str(value))
    return result


def calculate_summary(deltas: List[Dict]) -> Dict:
    """Calculate summary statistics."""
    total = len(deltas)
    improved = sum(1 for d in deltas if d["assessment"] == "improved")
    regressed = sum(1 for d in deltas if d["assessment"] == "regressed")
    changed = sum(1 for d in deltas if d["assessment"] == "changed")
    similar = sum(1 for d in deltas if d["assessment"] == "similar")

    return {
        "improved": improved,
        "improved_pct": round(improved / total * 100, 1) if total > 0 else 0,
        "regressed": regressed,
        "regressed_pct": round(regressed / total * 100, 1) if total > 0 else 0,
        "changed": changed,
        "changed_pct": round(changed / total * 100, 1) if total > 0 else 0,
        "similar": similar,
        "similar_pct": round(similar / total * 100, 1) if total > 0 else 0,
    }


def generate_result_html(delta: Dict) -> str:
    """Generate HTML for a single result."""
    return render_template(
        RESULT_ITEM_TEMPLATE,
        prompt_id=escape_html(delta["prompt_id"]),
        assessment=delta["assessment"],
        prompt=escape_html(delta["prompt"]),
        base_response=escape_html(delta["base_response"]),
        finetuned_response=escape_html(delta["finetuned_response"]),
        assessment_reason=escape_html(delta["assessment_reason"]),
        length_delta=f"{delta['metrics']['length']['length_delta']:+d} chars ({delta['metrics']['length']['length_delta_pct']:+.1f}%)",
        word_overlap=f"{delta['metrics']['word_overlap']:.1%}",
        base_correctness=escape_html(delta["correctness"]["base"]["assessment"]),
        finetuned_correctness=escape_html(delta["correctness"]["finetuned"]["assessment"])
    )


################################################################################
# Main Function
################################################################################

def main():
    parser = argparse.ArgumentParser(
        description="Agent 4: Generate HTML report from delta analysis"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="benchmark/results/",
        help="Directory containing deltas.json (default: benchmark/results/)"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Output HTML file path (default: <output>/report.html)"
    )

    args = parser.parse_args()

    # Load deltas
    deltas_path = os.path.join(args.output, "deltas.json")
    if not os.path.exists(deltas_path):
        console.print(f"[red]Error: Deltas file not found: {deltas_path}[/red]")
        console.print("[yellow]Run delta.py first to generate deltas[/yellow]")
        sys.exit(1)

    with open(deltas_path) as f:
        data = json.load(f)

    console.print("\n[bold blue]" + "="*60 + "[/bold blue]")
    console.print("[bold blue]Agent 4: Visualization[/bold blue]")
    console.print("[bold blue]" + "="*60 + "[/bold blue]\n")

    # Generate HTML
    deltas = data["deltas"]
    summary = calculate_summary(deltas)

    # Generate results HTML
    results_html_parts = []
    for delta in deltas:
        results_html_parts.append(generate_result_html(delta))
    results_html = "\n".join(results_html_parts)

    # Render full page
    html = render_template(
        HTML_TEMPLATE,
        base_model=escape_html(data["base_model"]),
        finetuned_model=escape_html(data["finetuned_model"]),
        domain=escape_html(data.get("domain", "unknown")),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        summary=summary,
        results_html=results_html
    )

    # Save HTML
    output_file = args.output_file or os.path.join(args.output, "report.html")
    with open(output_file, 'w') as f:
        f.write(html)

    console.print(f"[green]✓ Generated HTML report[/green]")
    console.print(f"[green]Saved to {output_file}[/green]\n")

    # Show summary
    console.print("[bold]Summary:[/bold]")
    console.print(f"  [green]Improved:[/green] {summary['improved']} ({summary['improved_pct']}%)")
    console.print(f"  [red]Regressed:[/red] {summary['regressed']} ({summary['regressed_pct']}%)")
    console.print(f"  [yellow]Changed:[/yellow] {summary['changed']} ({summary['changed_pct']}%)")
    console.print(f"  [dim]Similar:[/dim] {summary['similar']} ({summary['similar_pct']}%)")

    console.print(f"\n[cyan]Open report:[/cyan] [bold]open {output_file}[/bold]")


if __name__ == "__main__":
    main()
