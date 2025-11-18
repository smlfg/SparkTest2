#!/usr/bin/env python3
"""
HTML Report Generator

WHAT THIS DOES:
1. Reads the `deltas.json` file created by Agent 3.
2. Generates a static HTML file (`report.html`).
3. This HTML file provides a visual, human-readable summary
   of the fine-tuning iteration.

WHY A STATIC HTML FILE?
- Portable: You can send `report.html` to anyone.
- Simple: No web server needed (just open in browser).
- Zero Dependencies: Self-contained (CSS is inline).
- Git-friendly: You can commit the reports to track history.
"""

import json
import html  # ROBUSTNESS: For HTML escaping to prevent XSS
from pathlib import Path
from datetime import datetime

# Input/Output Paths
RESULTS_DIR = Path("benchmark/results")
DELTA_PATH = RESULTS_DIR / "deltas.json"
REPORT_PATH = RESULTS_DIR / "report.html"

# TEACHING: Why inline CSS?
# We embed CSS inside the HTML file using <style> tags.
# This makes the HTML file "self-contained".
# We don't need to ship a separate .css file, which simplifies things.
HTML_TEMPLATE_HEADER = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fine-Tuning Delta Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f7f6;
        }
        .container {
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
        h1, h2 {
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        .summary {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-box {
            padding: 20px;
            border-radius: 8px;
            font-size: 1.5em;
            font-weight: 500;
            text-align: center;
            flex-grow: 1;
        }
        .summary-improved { background-color: #e6f7ec; color: #2d6b46; }
        .summary-regressed { background-color: #fdecea; color: #a5303a; }
        .summary-neutral { background-color: #f0f4f8; color: #5a6e82; }

        .prompt-card {
            background-color: #fdfdfd;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 25px;
            overflow: hidden; /* Contains floats */
        }
        .prompt-header {
            padding: 15px 20px;
            border-bottom: 1px solid #e0e0e0;
            background-color: #f9f9f9;
        }
        .prompt-header h3 {
            margin: 0;
            font-size: 1.4em;
            color: #111;
        }
        /* TEACHING: This is the color-coding based on Agent 3's assessment */
        .assessment-improved { border-left: 5px solid #28a745; }
        .assessment-regressed { border-left: 5px solid #dc3545; }
        .assessment-neutral { border-left: 5px solid #6c757d; }
        .assessment-changed { border-left: 5px solid #ffc107; }

        .prompt-text {
            font-family: monospace;
            background: #eee;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }
        .comparison-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1px;
            background-color: #e0e0e0;
        }
        .response-box {
            padding: 20px;
            background-color: #ffffff;
        }
        .response-box h4 {
            margin-top: 0;
            color: #555;
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
        }
        .response-text {
            font-family: "Menlo", "Consolas", monospace;
            white-space: pre-wrap; /* TEACHING: Preserves newlines and spaces */
            word-wrap: break-word;
            font-size: 0.9em;
            line-height: 1.6;
            background-color: #fafafa;
            padding: 10px;
            border-radius: 4px;
            min-height: 100px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1px;
            background-color: #e0e0e0;
            border-top: 1px solid #e0e0e0;
        }
        .metric-box {
            padding: 15px;
            background: #ffffff;
            text-align: center;
        }
        .metric-box-label {
            font-size: 0.8em;
            color: #666;
            text-transform: uppercase;
        }
        .metric-box-value {
            font-size: 1.4em;
            font-weight: 500;
            color: #222;
        }
        footer {
            text-align: center;
            margin-top: 20px;
            font-size: 0.9em;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
"""

HTML_TEMPLATE_FOOTER = """
    </div>
</body>
</html>
"""

def escape_html(text: str) -> str:
    """
    ROBUSTNESS: HTML Escaping

    This prevents XSS (Cross-Site Scripting) attacks.
    If a prompt or response contains HTML/JavaScript, it will be
    displayed as text, not executed as code.

    Example:
      Input:  "<script>alert('XSS')</script>"
      Output: "&lt;script&gt;alert('XSS')&lt;/script&gt;"

    The browser displays: <script>alert('XSS')</script> (as text)
    Instead of executing the JavaScript.
    """
    if not text:
        return ""
    return html.escape(str(text), quote=True)

def get_assessment_class(assessment_text: str) -> str:
    """
    TEACHING: Mapping Logic to UI
    This function translates Agent 3's logic ("✅ IMPROVED")
    into a CSS class name ("assessment-improved")
    that our <style> block understands.
    """
    if "✅" in assessment_text: return "assessment-improved"
    if "❌" in assessment_text: return "assessment-regressed"
    if "⚪" in assessment_text: return "assessment-neutral"
    return "assessment-changed" # Default for ⚠️, 🔄, etc.

def create_prompt_card_html(delta: dict) -> str:
    """
    TEACHING: Python String Formatting (f-strings)
    This function uses Python's f-strings to build an HTML block.
    We inject data from the `delta` dictionary directly into the HTML.
    This is a simple form of "template engine".

    ROBUSTNESS: All user data is escaped with escape_html() to prevent XSS.
    """
    assessment_class = get_assessment_class(delta.get('assessment', ''))
    metrics = delta.get('metrics', {})

    # Format metrics for display with fallbacks
    sim_val = f"{metrics.get('similarity', 0) * 100:.1f}%"
    len_delta_pct = metrics.get('length_delta_pct', 0)
    len_val = f"{len_delta_pct:+.1f}%" # + prefix for positive nums
    kw_val = f"{metrics.get('keywords_base', 0)} → {metrics.get('keywords_ft', 0)}"

    # ROBUSTNESS: Escape all user-provided content
    safe_prompt_id = escape_html(delta.get('prompt_id', 'unknown'))
    safe_category = escape_html(delta.get('category', 'unknown'))
    safe_assessment = escape_html(delta.get('assessment', ''))
    safe_prompt = escape_html(delta.get('prompt', ''))
    safe_base_response = escape_html(delta.get('base_response', ''))
    safe_ft_response = escape_html(delta.get('finetuned_response', ''))

    return f"""
    <div class="prompt-card {assessment_class}">
        <div class="prompt-header">
            <h3>{safe_prompt_id} <span style="font-weight: 400; color: #555;">({safe_category})</span></h3>
            <div style="font-size: 1.2em; font-weight: 500;">{safe_assessment}</div>
            <div class="prompt-text">{safe_prompt}</div>
        </div>

        <div class="comparison-grid">
            <div class="response-box">
                <h4>Base Response</h4>
                <div class="response-text">{safe_base_response}</div>
            </div>
            <div class="response-box">
                <h4>Finetuned Response</h4>
                <div class="response-text">{safe_ft_response}</div>
            </div>
        </div>

        <div class="metrics-grid">
            <div class="metric-box">
                <div class="metric-box-label">Similarity</div>
                <div class="metric-box-value">{sim_val}</div>
            </div>
            <div class="metric-box">
                <div class="metric-box-label">Length Delta</div>
                <div class="metric-box-value">{len_val}</div>
            </div>
            <div class="metric-box">
                <div class="metric-box-label">Keywords</div>
                <div class="metric-box-value">{kw_val}</div>
            </div>
        </div>
    </div>
    """

def create_summary_html(stats: dict) -> str:
    """Builds the top-level summary boxes."""
    return f"""
    <div class="summary">
        <div class="summary-box summary-improved">
            {stats['improved']} Improved ✅
        </div>
        <div class="summary-box summary-regressed">
            {stats['regressed']} Regressed ❌
        </div>
        <div class="summary-box summary-neutral">
            {stats['neutral']} Neutral/Other
        </div>
    </div>
    """

def create_empty_data_message() -> str:
    """
    ROBUSTNESS: Message shown when there's no data.
    This ensures we ALWAYS generate a report, even with no data.
    """
    return """
    <div style="text-align: center; padding: 60px 20px; background: #f9f9f9; border-radius: 8px; margin: 40px 0;">
        <h2 style="color: #666; font-size: 2em; margin-bottom: 20px;">📊 No Data Available</h2>
        <p style="color: #888; font-size: 1.2em; line-height: 1.6;">
            No benchmark results were found to compare.<br>
            This could mean:
        </p>
        <ul style="text-align: left; max-width: 500px; margin: 20px auto; color: #666; font-size: 1.1em; line-height: 1.8;">
            <li>Agent 2 (benchmark runner) hasn't run yet</li>
            <li>Agent 3 (delta calculator) found no matching prompts</li>
            <li>The benchmark failed or was interrupted</li>
        </ul>
        <p style="color: #888; font-size: 1.1em; margin-top: 30px;">
            Run the full iteration pipeline to generate data:<br>
            <code style="background: #333; color: #0f0; padding: 8px 16px; border-radius: 4px; font-size: 0.9em;">./iterate.sh exp-001 datasets/example.json</code>
        </p>
    </div>
    """

def main():
    print("\n" + "="*70)
    print("  AGENT 4: HTML VISUALIZER (Creating Web Report)")
    print("="*70)
    print()
    print("📚 WHAT THIS DOES:")
    print("   Transforms the delta analysis (JSON) into a beautiful")
    print("   HTML report that you can open in your web browser.")
    print()
    print("🎨 REPORT FEATURES:")
    print("   • Color-coded cards (green=improved, red=regressed)")
    print("   • Side-by-side response comparison")
    print("   • Summary dashboard with statistics")
    print("   • Self-contained (no external dependencies)")
    print()
    print("-" * 70)

    # ROBUSTNESS: We ALWAYS create a report, even if data is missing
    deltas = []
    error_message = None

    # 1. Try to load input
    print("\n🔍 STEP 1: Loading delta analysis...")
    print("   Reading: benchmark/results/deltas.json")

    if not DELTA_PATH.exists():
        print(f"   ⚠️  File not found")
        print("   Will create report with 'No Data' message...")
        error_message = "deltas.json not found"
    else:
        # 2. Try to load JSON
        try:
            with open(DELTA_PATH, "r", encoding="utf-8") as f:
                deltas = json.load(f)

            print(f"   ✓ Loaded {len(deltas)} delta entries")

            # Validate it's a list
            if not isinstance(deltas, list):
                print(f"   ⚠️  Invalid format (expected list, got {type(deltas).__name__})")
                print("   Will create report with 'No Data' message...")
                deltas = []
                error_message = "deltas.json has invalid format"

        except json.JSONDecodeError as e:
            print(f"   ⚠️  JSON parse error: {e}")
            print("   Will create report with 'No Data' message...")
            deltas = []
            error_message = f"JSON decode error: {e}"
        except Exception as e:
            print(f"   ⚠️  Unexpected error: {e}")
            print("   Will create report with 'No Data' message...")
            deltas = []
            error_message = f"Error: {e}"

    # 3. Build HTML content
    print("\n🎨 STEP 2: Building HTML report...")
    print()
    print("   💡 HOW HTML GENERATION WORKS:")
    print("   We use Python f-strings to inject data into HTML templates.")
    print("   All user data is HTML-escaped to prevent XSS attacks.")
    print()
    print("   Process:")
    print("   1. Build HTML as list of strings (fast)")
    print("   2. Join all parts at the end (efficient)")
    print("   3. Write to file")
    print()

    # TEACHING: We build the HTML as a list of strings
    # and then .join() them at the end.
    # This is much faster than `html += "new_line"` over and over.
    html_parts = []

    # Add header
    html_parts.append(HTML_TEMPLATE_HEADER)

    # Add title and timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_parts.append(f"<h1>Fine-Tuning Delta Report</h1>")
    html_parts.append(f"<p>Generated: {timestamp}</p>")

    # ROBUSTNESS: Handle empty data gracefully
    if not deltas:
        print("   Creating 'No Data' message...")
        html_parts.append(create_empty_data_message())
        if error_message:
            html_parts.append(f"<p style='color: #999; text-align: center; font-size: 0.9em;'>Error details: {escape_html(error_message)}</p>")
    else:
        # Calculate summary stats
        stats = {"improved": 0, "regressed": 0, "neutral": 0}
        for d in deltas:
            assessment = d.get("assessment", "")
            if "✅" in assessment: stats["improved"] += 1
            elif "❌" in assessment: stats["regressed"] += 1
            else: stats["neutral"] += 1

        print(f"   Creating summary: {stats['improved']} improved, {stats['regressed']} regressed, {stats['neutral']} other")

        # Add summary
        html_parts.append(create_summary_html(stats))

        html_parts.append("<h2>Prompt-by-Prompt Analysis</h2>")

        # Add each prompt card
        print(f"   Generating {len(deltas)} prompt cards...")
        cards_created = 0
        for delta in deltas:
            try:
                html_parts.append(create_prompt_card_html(delta))
                cards_created += 1
            except Exception as e:
                # ROBUSTNESS: If one card fails, don't crash the entire report
                print(f"   ⚠️  Error creating card for {delta.get('prompt_id', 'unknown')}: {e}")
                html_parts.append(f"<p style='color: red;'>Error rendering prompt card: {escape_html(str(e))}</p>")

        print(f"   ✓ Created {cards_created} cards successfully")

    # Add footer
    html_parts.append(f"<footer>Report generated by Agent 4.</footer>")
    html_parts.append(HTML_TEMPLATE_FOOTER)

    # 4. Write to file (ensure directory exists)
    print("\n💾 STEP 3: Saving HTML report...")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    final_html = "\n".join(html_parts)
    file_size = len(final_html)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"   ✓ Saved: benchmark/results/report.html ({file_size:,} bytes)")
    print()
    print("="*70)
    print("  ✅ HTML REPORT GENERATED")
    print()
    print("  📖 To view the report:")
    if not deltas:
        print("     Report shows 'No Data' message (run Agent 2 & 3 first)")
    else:
        print("     open benchmark/results/report.html     # macOS")
        print("     xdg-open benchmark/results/report.html  # Linux")
        print("     start benchmark/results/report.html     # Windows")
    print("="*70)
    print()

if __name__ == "__main__":
    main()
