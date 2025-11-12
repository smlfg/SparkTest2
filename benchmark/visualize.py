#!/usr/bin/env python3
"""
Agent 4: HTML Visualization Generator

This script generates an interactive HTML report showing side-by-side
comparison of base vs fine-tuned model responses.

WHY HTML REPORTS?
- Easy to share (single file, no dependencies)
- Interactive (expand/collapse, filter by assessment)
- Visual (color-coded improvements/regressions)
- Archives well (keep reports for each iteration)

REPORT SECTIONS:
1. Summary dashboard (key metrics at a glance)
2. Assessment breakdown (pie chart)
3. Detailed comparisons (side-by-side for each prompt)

LEARNING OBJECTIVE:
Good visualizations make insights actionable. A clear report
helps you decide: "Should I iterate again or is this good enough?"
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from jinja2 import Template


# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fine-tuning Delta Report</title>
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
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        header {
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }

        h1 {
            color: #2c3e50;
            font-size: 32px;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #7f8c8d;
            font-size: 14px;
        }

        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .metric-value {
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }

        .metric-label {
            font-size: 14px;
            opacity: 0.9;
        }

        .assessment-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 40px;
        }

        .assessment-box {
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            font-weight: bold;
        }

        .improved {
            background: #d4edda;
            color: #155724;
            border: 2px solid #28a745;
        }

        .regressed {
            background: #f8d7da;
            color: #721c24;
            border: 2px solid #dc3545;
        }

        .changed {
            background: #fff3cd;
            color: #856404;
            border: 2px solid #ffc107;
        }

        .unchanged {
            background: #e2e3e5;
            color: #383d41;
            border: 2px solid #6c757d;
        }

        .comparison {
            margin-bottom: 30px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }

        .comparison-header {
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .prompt-id {
            font-weight: bold;
            color: #495057;
        }

        .category-badge {
            background: #6c757d;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
        }

        .assessment-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }

        .prompt-text {
            background: #e9ecef;
            padding: 15px 20px;
            font-style: italic;
            border-bottom: 1px solid #dee2e6;
        }

        .responses {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
        }

        .response-column {
            padding: 20px;
        }

        .response-column:first-child {
            border-right: 1px solid #dee2e6;
        }

        .response-title {
            font-weight: bold;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #dee2e6;
        }

        .base-title {
            color: #6c757d;
        }

        .finetuned-title {
            color: #007bff;
        }

        .response-text {
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.5;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
        }

        .metrics {
            font-size: 12px;
            color: #6c757d;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 10px;
        }

        .metric-item {
            background: #f8f9fa;
            padding: 8px;
            border-radius: 4px;
        }

        .metric-item strong {
            display: block;
            margin-bottom: 3px;
        }

        .filter-bar {
            background: #f8f9fa;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .filter-btn {
            padding: 8px 16px;
            border: 2px solid #dee2e6;
            background: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }

        .filter-btn:hover {
            background: #e9ecef;
        }

        .filter-btn.active {
            background: #007bff;
            color: white;
            border-color: #007bff;
        }

        footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
        }

        @media (max-width: 768px) {
            .responses {
                grid-template-columns: 1fr;
            }

            .response-column:first-child {
                border-right: none;
                border-bottom: 1px solid #dee2e6;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Fine-tuning Delta Report</h1>
            <div class="subtitle">
                Generated: {{ generation_time }}<br>
                Base model vs Fine-tuned model comparison
            </div>
        </header>

        <!-- Dashboard -->
        <div class="dashboard">
            <div class="metric-card">
                <div class="metric-label">Total Prompts</div>
                <div class="metric-value">{{ total_prompts }}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Improved</div>
                <div class="metric-value">{{ improved_count }}</div>
                <div class="metric-label">{{ improved_percent }}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Length Change</div>
                <div class="metric-value">{{ avg_length_delta }}</div>
                <div class="metric-label">characters</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Similarity</div>
                <div class="metric-value">{{ avg_similarity }}</div>
                <div class="metric-label">0.0 - 1.0</div>
            </div>
        </div>

        <!-- Assessment Summary -->
        <div class="assessment-summary">
            <div class="assessment-box improved">
                ✅ IMPROVED<br>
                <span style="font-size: 24px;">{{ improved_count }}</span>
            </div>
            <div class="assessment-box regressed">
                ❌ REGRESSED<br>
                <span style="font-size: 24px;">{{ regressed_count }}</span>
            </div>
            <div class="assessment-box changed">
                🔄 CHANGED<br>
                <span style="font-size: 24px;">{{ changed_count }}</span>
            </div>
            <div class="assessment-box unchanged">
                ⚪ UNCHANGED<br>
                <span style="font-size: 24px;">{{ unchanged_count }}</span>
            </div>
        </div>

        <!-- Filter Bar -->
        <div class="filter-bar">
            <button class="filter-btn active" onclick="filterByAssessment('all')">All</button>
            <button class="filter-btn" onclick="filterByAssessment('IMPROVED')">✅ Improved</button>
            <button class="filter-btn" onclick="filterByAssessment('REGRESSED')">❌ Regressed</button>
            <button class="filter-btn" onclick="filterByAssessment('CHANGED')">🔄 Changed</button>
            <button class="filter-btn" onclick="filterByAssessment('UNCHANGED')">⚪ Unchanged</button>
        </div>

        <!-- Comparisons -->
        <div id="comparisons">
            {% for delta in deltas %}
            <div class="comparison" data-assessment="{{ delta.assessment }}">
                <div class="comparison-header">
                    <div>
                        <span class="prompt-id">{{ delta.prompt_id }}</span>
                        <span class="category-badge">{{ delta.category }}</span>
                    </div>
                    <span class="assessment-badge {{ delta.assessment.lower() }}">
                        {{ delta.assessment }}
                    </span>
                </div>

                <div class="prompt-text">
                    <strong>Prompt:</strong> {{ delta.prompt }}
                    {% if delta.expected %}
                    <br><strong>Expected:</strong> {{ delta.expected }}
                    {% endif %}
                </div>

                <div class="responses">
                    <div class="response-column">
                        <div class="response-title base-title">Base Model Response</div>
                        <div class="response-text">{{ delta.base_response }}</div>
                        <div class="metrics">
                            <strong>Metrics:</strong>
                            <div class="metrics-grid">
                                <div class="metric-item">
                                    <strong>Length</strong>
                                    {{ delta.metrics.length.base_chars }} chars<br>
                                    {{ delta.metrics.length.base_words }} words
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="response-column">
                        <div class="response-title finetuned-title">Fine-tuned Model Response</div>
                        <div class="response-text">{{ delta.finetuned_response }}</div>
                        <div class="metrics">
                            <strong>Metrics:</strong>
                            <div class="metrics-grid">
                                <div class="metric-item">
                                    <strong>Length</strong>
                                    {{ delta.metrics.length.finetuned_chars }} chars<br>
                                    {{ delta.metrics.length.finetuned_words }} words<br>
                                    <span style="color: {% if delta.metrics.length.char_delta > 0 %}green{% else %}red{% endif %};">
                                        ({{ delta.metrics.length.char_delta|abs }} {{ 'more' if delta.metrics.length.char_delta > 0 else 'fewer' }})
                                    </span>
                                </div>
                                <div class="metric-item">
                                    <strong>Similarity</strong>
                                    Cosine: {{ delta.metrics.similarity.cosine_similarity }}<br>
                                    Sequence: {{ delta.metrics.similarity.sequence_ratio }}<br>
                                    {{ delta.metrics.similarity.interpretation }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <footer>
            Generated by Agent 4: HTML Visualization Generator<br>
            Part of DGX Fast Fine-tuning Iteration Lab
        </footer>
    </div>

    <script>
        function filterByAssessment(assessment) {
            const comparisons = document.querySelectorAll('.comparison');
            const buttons = document.querySelectorAll('.filter-btn');

            // Update active button
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            // Filter comparisons
            comparisons.forEach(comp => {
                if (assessment === 'all' || comp.dataset.assessment === assessment) {
                    comp.style.display = 'block';
                } else {
                    comp.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
"""


def load_deltas(deltas_path: Path):
    """Load delta results."""
    with open(deltas_path, 'r') as f:
        return json.load(f)


def calculate_summary_stats(deltas):
    """Calculate summary statistics for dashboard."""
    total = len(deltas)

    # Count assessments
    improved = sum(1 for d in deltas if d["assessment"] == "IMPROVED")
    regressed = sum(1 for d in deltas if d["assessment"] == "REGRESSED")
    changed = sum(1 for d in deltas if d["assessment"] == "CHANGED")
    unchanged = sum(1 for d in deltas if d["assessment"] == "UNCHANGED")

    # Average metrics
    avg_length_delta = sum(
        d["metrics"]["length"]["char_delta"] for d in deltas
    ) / total if total > 0 else 0

    avg_similarity = sum(
        d["metrics"]["similarity"]["cosine_similarity"] for d in deltas
    ) / total if total > 0 else 0

    return {
        "total_prompts": total,
        "improved_count": improved,
        "regressed_count": regressed,
        "changed_count": changed,
        "unchanged_count": unchanged,
        "improved_percent": round(improved / total * 100) if total > 0 else 0,
        "avg_length_delta": f"{avg_length_delta:+.0f}",
        "avg_similarity": f"{avg_similarity:.2f}",
    }


def generate_html(deltas, output_path: Path):
    """Generate HTML report from deltas."""
    # Calculate stats
    stats = calculate_summary_stats(deltas)

    # Render template
    template = Template(HTML_TEMPLATE)
    html = template.render(
        deltas=deltas,
        generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **stats
    )

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✓ HTML report saved to {output_path}")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate HTML visualization report"
    )

    parser.add_argument(
        "--deltas",
        type=str,
        default="benchmark/results/deltas.json",
        help="Path to deltas JSON"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="benchmark/results/report.html",
        help="Output HTML path"
    )

    return parser.parse_args()


def main():
    """Main visualization pipeline."""
    print("=" * 60)
    print("Agent 4: HTML Visualization Generator")
    print("=" * 60)

    # Parse arguments
    args = parse_args()

    # Check deltas exist
    deltas_path = Path(args.deltas)
    if not deltas_path.exists():
        print(f"❌ Error: Deltas not found at {deltas_path}")
        print("Run delta calculation first: python benchmark/delta.py")
        return 1

    # Load deltas
    print(f"\n📂 Loading deltas from {deltas_path}...")
    deltas = load_deltas(deltas_path)
    print(f"✓ Loaded {len(deltas)} deltas")

    # Generate HTML
    print(f"\n🎨 Generating HTML report...")
    output_path = Path(args.output)
    generate_html(deltas, output_path)

    print("\n" + "=" * 60)
    print("✅ Visualization complete!")
    print(f"\n📊 Open report: {output_path}")
    print("\nTip: Open in browser to view interactive report")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
