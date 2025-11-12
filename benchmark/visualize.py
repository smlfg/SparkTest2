#!/usr/bin/env python3
"""
================================================================================
DGX Spark Fast Fine-tuning System
Agent 4: Visualization - HTML Report Generator
================================================================================

WHAT: Generate interactive HTML report showing base vs fine-tuned comparison
WHY:  Human-readable format for quick iteration feedback
HOW:  Read deltas.json, render HTML with:
      - Side-by-side response comparison
      - Color-coded assessment indicators
      - Metrics dashboard
      - Category breakdown

USAGE: python benchmark/visualize.py

INPUT:  benchmark/results/deltas.json

OUTPUT: benchmark/results/report.html

TIME: ~instant

================================================================================
LEARNING OBJECTIVES:
- Why visualization matters (humans need quick insights)
- How to present ML results to non-technical users
- Trade-offs: Interactive dashboards vs static HTML
================================================================================
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# ===== CONFIGURATION =====
RESULTS_DIR = Path("benchmark/results")
DELTAS_FILE = RESULTS_DIR / "deltas.json"
OUTPUT_FILE = RESULTS_DIR / "report.html"


# ===== HTML TEMPLATE =====
# Using inline CSS for portability (no external dependencies)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fine-tuning Delta Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .stat-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .stat-card .label {{
            color: #666;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
        }}

        .stat-card.improved .number {{ color: #10b981; }}
        .stat-card.regressed .number {{ color: #ef4444; }}
        .stat-card.changed .number {{ color: #f59e0b; }}
        .stat-card.unchanged .number {{ color: #6b7280; }}

        .prompt-section {{
            margin-bottom: 30px;
        }}

        .prompt-card {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
            margin-bottom: 20px;
        }}

        .prompt-header {{
            padding: 20px;
            border-bottom: 2px solid #f0f0f0;
        }}

        .prompt-id {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }}

        .prompt-text {{
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 10px;
        }}

        .assessment-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .badge-improved {{
            background: #d1fae5;
            color: #065f46;
        }}

        .badge-regressed {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .badge-changed {{
            background: #fef3c7;
            color: #92400e;
        }}

        .badge-unchanged {{
            background: #f3f4f6;
            color: #374151;
        }}

        .metrics-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            padding: 15px 20px;
            background: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
        }}

        .metric {{
            text-align: center;
        }}

        .metric-label {{
            font-size: 0.8em;
            color: #6b7280;
            margin-bottom: 3px;
        }}

        .metric-value {{
            font-size: 1.1em;
            font-weight: 600;
        }}

        .responses-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
        }}

        .response-box {{
            padding: 20px;
            border-right: 1px solid #e5e7eb;
        }}

        .response-box:last-child {{
            border-right: none;
        }}

        .response-label {{
            font-size: 0.9em;
            font-weight: 600;
            color: #6b7280;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .response-text {{
            white-space: pre-wrap;
            line-height: 1.8;
            color: #1f2937;
        }}

        @media (max-width: 768px) {{
            .responses-container {{
                grid-template-columns: 1fr;
            }}

            .response-box {{
                border-right: none;
                border-bottom: 1px solid #e5e7eb;
            }}

            .response-box:last-child {{
                border-bottom: none;
            }}
        }}

        .category-filter {{
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .category-filter button {{
            margin-right: 10px;
            margin-bottom: 10px;
            padding: 8px 16px;
            border: 2px solid #e5e7eb;
            background: white;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .category-filter button:hover {{
            border-color: #667eea;
            background: #f0f4ff;
        }}

        .category-filter button.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}

        footer {{
            text-align: center;
            padding: 30px;
            color: #6b7280;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Fine-tuning Delta Report</h1>
            <p>Comparing base model vs fine-tuned model performance</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Generated: {timestamp}</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card improved">
                <div class="number">{improved_count}</div>
                <div class="label">Improved</div>
            </div>
            <div class="stat-card regressed">
                <div class="number">{regressed_count}</div>
                <div class="label">Regressed</div>
            </div>
            <div class="stat-card changed">
                <div class="number">{changed_count}</div>
                <div class="label">Changed</div>
            </div>
            <div class="stat-card unchanged">
                <div class="number">{unchanged_count}</div>
                <div class="label">Unchanged</div>
            </div>
        </div>

        <div class="category-filter">
            <button class="active" onclick="filterCategory('all')">All ({total_prompts})</button>
            {category_buttons}
        </div>

        <div class="prompt-section">
            {prompt_cards}
        </div>

        <footer>
            <p>DGX Spark Fast Fine-tuning System</p>
            <p>Built for rapid iteration and experimentation</p>
        </footer>
    </div>

    <script>
        function filterCategory(category) {{
            // Update button states
            document.querySelectorAll('.category-filter button').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');

            // Show/hide cards
            document.querySelectorAll('.prompt-card').forEach(card => {{
                if (category === 'all' || card.dataset.category === category) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>
"""

PROMPT_CARD_TEMPLATE = """
<div class="prompt-card" data-category="{category}">
    <div class="prompt-header">
        <div class="prompt-id">{prompt_id} • {category}</div>
        <div class="prompt-text">{prompt}</div>
        <span class="assessment-badge badge-{assessment_class}">{assessment}</span>
    </div>
    <div class="metrics-row">
        <div class="metric">
            <div class="metric-label">Keyword Match</div>
            <div class="metric-value">{keyword_base} → {keyword_finetuned}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Length</div>
            <div class="metric-value">{length_base} → {length_finetuned}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Similarity</div>
            <div class="metric-value">{similarity:.2f}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Improvement</div>
            <div class="metric-value">{improvement:+.0%}</div>
        </div>
    </div>
    <div class="responses-container">
        <div class="response-box">
            <div class="response-label">Base Model</div>
            <div class="response-text">{base_response}</div>
        </div>
        <div class="response-box">
            <div class="response-label">Fine-tuned Model</div>
            <div class="response-text">{finetuned_response}</div>
        </div>
    </div>
</div>
"""


# ===== HELPER FUNCTIONS =====

def load_deltas():
    """Load delta results from JSON."""
    if not DELTAS_FILE.exists():
        print(f"❌ Error: Deltas file not found: {DELTAS_FILE}")
        print("   Run: python benchmark/delta.py")
        sys.exit(1)

    with open(DELTAS_FILE) as f:
        return json.load(f)


def get_assessment_class(assessment: str) -> str:
    """Map assessment to CSS class."""
    if "improved" in assessment:
        return "improved"
    elif "regressed" in assessment:
        return "regressed"
    elif "unchanged" in assessment:
        return "unchanged"
    else:
        return "changed"


def generate_report(deltas):
    """Generate HTML report from deltas."""
    print(f"\n📊 Generating HTML report...")

    # Calculate summary stats
    total = len(deltas)
    assessments = [d["overall_assessment"] for d in deltas]
    improved = assessments.count("improved")
    regressed = assessments.count("regressed")
    unchanged = assessments.count("unchanged")
    changed = total - improved - regressed - unchanged

    # Get unique categories
    categories = sorted(set(d["category"] for d in deltas))
    category_counts = {cat: sum(1 for d in deltas if d["category"] == cat) for cat in categories}

    # Generate category buttons
    category_buttons = "".join([
        f'<button onclick="filterCategory(\'{cat}\')">{cat.replace("_", " ").title()} ({category_counts[cat]})</button>'
        for cat in categories
    ])

    # Generate prompt cards
    prompt_cards = []
    for delta in deltas:
        card = PROMPT_CARD_TEMPLATE.format(
            prompt_id=delta["prompt_id"],
            category=delta["category"],
            prompt=delta["prompt"],
            assessment=delta["overall_assessment"].replace("_", " ").title(),
            assessment_class=get_assessment_class(delta["overall_assessment"]),
            keyword_base=delta["keywords"]["base"]["match_count"],
            keyword_finetuned=delta["keywords"]["finetuned"]["match_count"],
            length_base=delta["length"]["base_length"],
            length_finetuned=delta["length"]["finetuned_length"],
            similarity=delta["similarity"]["similarity"],
            improvement=delta["keywords"]["improvement"],
            base_response=delta["base_response"],
            finetuned_response=delta["finetuned_response"],
        )
        prompt_cards.append(card)

    # Render full HTML
    html = HTML_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        improved_count=improved,
        regressed_count=regressed,
        changed_count=changed,
        unchanged_count=unchanged,
        total_prompts=total,
        category_buttons=category_buttons,
        prompt_cards="\n".join(prompt_cards),
    )

    return html


def save_report(html: str):
    """Save HTML report to file."""
    with open(OUTPUT_FILE, 'w') as f:
        f.write(html)

    print(f"   ✅ Saved to: {OUTPUT_FILE}")


# ===== MAIN =====

def main():
    """Main entry point."""
    print("=" * 80)
    print("🎨 Visualization Generator")
    print("=" * 80)

    # Load deltas
    deltas = load_deltas()
    print(f"   Loaded {len(deltas)} delta results")

    # Generate HTML
    html = generate_report(deltas)

    # Save
    save_report(html)

    # Summary
    print("\n" + "=" * 80)
    print("✅ Report Generated!")
    print("=" * 80)
    print(f"\nOpen in browser:")
    print(f"  {OUTPUT_FILE.absolute()}")
    print(f"\nOr use:")
    print(f"  open {OUTPUT_FILE}  (macOS)")
    print(f"  xdg-open {OUTPUT_FILE}  (Linux)")
    print(f"  start {OUTPUT_FILE}  (Windows)")
    print("=" * 80)


if __name__ == "__main__":
    main()
