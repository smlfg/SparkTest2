# Agent 4 Teaching Guide: Visualizing Data

## What You Built
You built a **Python-to-HTML** script. It's a "static site generator" in its simplest form. It takes structured data (JSON) and outputs a human-readable interface (HTML).

### The Core Concepts

#### 1. Why HTML?
The output of your benchmark is data. The best way for a human to consume data quickly is visually.
- **Console Output**: Hard to read, scrolls away, no color.
- **JSON**: Unreadable for non-programmers.
- **HTML**: Visual, color-coded, interactive, universally readable in any browser.

#### 2. Self-Contained HTML
We embedded our CSS (styles) directly into the HTML file using `<style>...</style>`.
- **Pro**: The report is a single file. You can email `report.html` to your professor, and it *just works*.
- **Con**: The file is larger. For a big web app, you'd use external `.css` files, but for a report, this is perfect.

#### 3. How the Script Works
It's a simple 3-step process:
1.  **Read Data**: `json.load(f)`
2.  **Transform**: Loop through the data, wrapping it in HTML tags using Python f-strings (`f"<h3>{delta['prompt_id']}</h3>"`).
3.  **Write File**: `f.write(final_html)`

This pattern (Read-Transform-Write) is fundamental in data processing.

#### 4. Key HTML/CSS Concepts You Used
-   **`display: grid`**: (in `.comparison-grid`) Creates the side-by-side columns. This is the modern, powerful way to do layouts.
-   **`white-space: pre-wrap`**: (in `.response-text`) This is **CRITICAL**. It tells the browser to respect newlines and spaces from the model's output. Without it, all responses would be a single, long line of text.
-   **`border-left: 5px solid ...`**: (in `.assessment-improved`) This is the color-coded bar that gives the user an instant "good/bad" signal before they even read the text.

### Experiments to Try

**Experiment 1: Break the CSS**
1.  In `visualize.py`, find the `.response-text` style.
2.  Comment out `white-space: pre-wrap;`.
3.  Re-run `python benchmark/visualize.py`.
4.  Open `report.html`.
**Result**: All model responses are collapsed into single lines. You'll immediately see why `pre-wrap` is so important.

**Experiment 2: Add a New Metric**
1.  Find the `metrics-grid` style. Change `grid-template-columns: repeat(3, 1fr);` to `repeat(4, 1fr);` (to make space for a 4th metric).
2.  In `create_prompt_card_html`, add a new `<div class="metric-box">` that displays the latency (which Agent 3 didn't use, but Agent 2 saved).
    ```python
    # (Inside create_prompt_card_html)
    latency_val = f"{delta['metadata']['latency_seconds']:.2f}s"

    # (Inside the HTML f-string for metrics-grid)
    <div class="metric-box">
        <div class="metric-box-label">Latency (FT)</div>
        <div class="metric-box-value">{latency_val}</div>
    </div>
    ```
3.  Re-run and check your report.
**Lesson**: You've learned how to modify the report layout and add new data.

---

## Integration Points

**Inputs:**
-   `benchmark/results/deltas.json` (From Agent 3)

**Outputs:**
-   `benchmark/results/report.html` (To Agent 6 / User)

**What Agent 6 expects:**
-   The `report.html` file to be generated successfully, so it can be logged and opened.

---

## The HTML Structure Explained

### 1. The Header Template
```html
<head>
    <style>
        /* All CSS lives here */
    </style>
</head>
```

This is where all the magic happens. By putting CSS in the `<head>`, we make the file self-contained. No external dependencies.

### 2. The Grid System
```css
.comparison-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
}
```

This creates two equal-width columns. The `1fr` means "1 fraction of available space". So `1fr 1fr` = 50% each.

**Why not use `width: 50%`?**
- Grid handles gaps automatically
- Grid is responsive
- Grid is more powerful for complex layouts

### 3. The Pre-Wrap Magic
```css
.response-text {
    white-space: pre-wrap;
}
```

**What this does:**
- `pre` = preserve whitespace (like `<pre>` tag)
- `wrap` = but still wrap long lines

**Why it matters:**
Without this, if a model outputs:
```
Line 1
Line 2
Line 3
```

The browser would show: `Line 1 Line 2 Line 3` (all one line!)

### 4. Color Coding Logic
```python
def get_assessment_class(assessment_text: str) -> str:
    if "✅" in assessment_text: return "assessment-improved"
    if "❌" in assessment_text: return "assessment-regressed"
    # ...
```

This maps Agent 3's emoji-based assessments to CSS classes. Then in HTML:
```html
<div class="prompt-card assessment-improved">
```

And the CSS rule:
```css
.assessment-improved { border-left: 5px solid #28a745; }
```

Creates the green bar. This is **conditional styling** - the appearance changes based on data.

---

## How Python Builds HTML

### Method 1: String Concatenation (DON'T DO THIS)
```python
html = ""
html += "<h1>Title</h1>"
html += "<p>Paragraph</p>"
# Slow and hard to read
```

### Method 2: List + Join (WHAT WE DID)
```python
html_parts = []
html_parts.append("<h1>Title</h1>")
html_parts.append("<p>Paragraph</p>")
html = "\n".join(html_parts)
# Fast and clean
```

**Why is list + join faster?**
- Strings in Python are immutable
- `html += "new"` creates a NEW string every time
- Appending to a list is O(1), joining is O(n)

### Method 3: Template Engines (For larger projects)
For bigger projects, you'd use:
- Jinja2 (Flask's template engine)
- Django templates
- Mako

But for our use case, f-strings are perfect!

---

## Understanding F-Strings

F-strings (formatted string literals) are Python 3.6+ magic:

```python
name = "Alice"
age = 30
html = f"<p>Hello, {name}! You are {age} years old.</p>"
# Result: <p>Hello, Alice! You are 30 years old.</p>
```

**In our code:**
```python
sim_val = f"{metrics['similarity'] * 100:.1f}%"
```

Let's break this down:
- `{...}` = placeholder
- `metrics['similarity']` = get the value
- `* 100` = convert 0.85 to 85
- `:.1f` = format as float with 1 decimal place
- `%` = add percent sign

So `0.8532` becomes `"85.3%"`.

**Another example:**
```python
len_val = f"{len_delta_pct:+.1f}%"
```

The `+` means "show the sign even for positive numbers":
- `15.2` becomes `"+15.2%"` (not just `"15.2%"`)
- `-5.3` becomes `"-5.3%"`

This is useful for deltas where you want to see if it increased or decreased.

---

## Data Flow Through the Script

```
deltas.json (from Agent 3)
      ↓
main() reads file
      ↓
Loop through deltas
      ↓
For each delta:
  - create_prompt_card_html(delta)
  - Returns HTML string
      ↓
Append to html_parts list
      ↓
Join all parts
      ↓
Write to report.html
```

**Key insight**: We're not doing anything fancy. We're just:
1. Reading JSON
2. Looping through it
3. Building strings with f-strings
4. Writing to a file

This is the essence of data transformation!

---

## CSS Layout Deep Dive

### The Container
```css
.container {
    max-width: 1200px;
    margin: 20px auto;
}
```

- `max-width: 1200px` = never wider than 1200px (readable on large screens)
- `margin: 20px auto` = 20px top/bottom, auto left/right (centers it)

### The Summary Boxes
```css
.summary {
    display: flex;
    gap: 20px;
}
.summary-box {
    flex-grow: 1;
}
```

- `display: flex` = arrange children horizontally
- `gap: 20px` = 20px space between boxes
- `flex-grow: 1` = each box takes equal space

**Visual:**
```
┌────────┐ gap ┌────────┐ gap ┌────────┐
│ Box 1  │ 20px│ Box 2  │ 20px│ Box 3  │
└────────┘     └────────┘     └────────┘
```

### The Prompt Cards
```css
.prompt-card {
    border-radius: 8px;
    overflow: hidden;
}
```

- `border-radius: 8px` = rounded corners
- `overflow: hidden` = clips content to rounded corners

**Why overflow: hidden?**
Without it, child elements (like the header) might have sharp corners that "stick out" beyond the rounded border.

---

## Common Pitfalls & Solutions

### Pitfall 1: HTML Escaping
**Problem**: What if a prompt contains `<script>alert('XSS')</script>`?

**Solution**: Python's `json.load()` doesn't execute code, but we should escape HTML:
```python
import html
safe_prompt = html.escape(delta['prompt'])
```

For this project, we trust our input (it's from our own benchmark), but in production, always escape user data!

### Pitfall 2: Unicode/Emoji
**Problem**: Emojis (✅❌) might break in HTML.

**Solution**: We use:
```python
with open(REPORT_PATH, "w", encoding="utf-8") as f:
```

The `encoding="utf-8"` ensures emojis are written correctly.

### Pitfall 3: Large Responses
**Problem**: What if a model response is 10,000 characters?

**Solution**: Add a max-height to `.response-text`:
```css
.response-text {
    max-height: 500px;
    overflow-y: auto; /* Adds scrollbar */
}
```

### Pitfall 4: Mobile Responsiveness
**Problem**: Report looks bad on phones.

**Solution**: Add a media query:
```css
@media (max-width: 768px) {
    .comparison-grid {
        grid-template-columns: 1fr; /* Stack vertically */
    }
}
```

---

## Performance Considerations

**How fast should this be?**
- For 10 prompts: < 0.1 seconds
- For 100 prompts: < 1 second
- For 1000 prompts: < 5 seconds

**Why is it fast?**
1. We use list + join (not string concatenation)
2. We only loop through the data once
3. We don't do any complex processing
4. File I/O is minimal (one read, one write)

**If it's slow:**
- Check if you're doing `html += "..."` instead of `html_parts.append(...)`
- Check if you're reading the file multiple times
- Profile with `python -m cProfile visualize.py`

---

## Testing Strategy

### Manual Test
1. Create a sample `deltas.json`:
```json
[
  {
    "prompt_id": "prompt_001",
    "category": "test",
    "prompt": "Hello",
    "base_response": "Hi there!",
    "finetuned_response": "Hello! How can I help?",
    "assessment": "✅ IMPROVED",
    "metrics": {
      "similarity": 0.6,
      "length_delta_pct": 25.5,
      "keywords_base": 2,
      "keywords_ft": 3
    }
  }
]
```

2. Run: `python benchmark/visualize.py`
3. Open `benchmark/results/report.html` in browser
4. Check: Does it look good? Are colors right?

### Automated Test
```python
def test_visualizer():
    # Create sample data
    sample_deltas = [...]
    with open("benchmark/results/deltas.json", "w") as f:
        json.dump(sample_deltas, f)

    # Run visualizer
    import benchmark.visualize as viz
    viz.main()

    # Check output exists
    assert Path("benchmark/results/report.html").exists()

    # Check HTML is valid
    html = Path("benchmark/results/report.html").read_text()
    assert "<html" in html
    assert "✅ IMPROVED" in html
```

---

## Extensions & Ideas

### Idea 1: Add Charts
Use a library like Chart.js (embedded via CDN):
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<canvas id="myChart"></canvas>
<script>
  new Chart(document.getElementById('myChart'), {
    type: 'bar',
    data: { labels: ['Improved', 'Regressed'], values: [7, 3] }
  });
</script>
```

### Idea 2: Add Search
```html
<input type="text" id="search" placeholder="Search prompts...">
<script>
  document.getElementById('search').addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    document.querySelectorAll('.prompt-card').forEach(card => {
      const text = card.textContent.toLowerCase();
      card.style.display = text.includes(query) ? 'block' : 'none';
    });
  });
</script>
```

### Idea 3: Comparison View
Show multiple experiments side-by-side:
```
┌─────────┬─────────┬─────────┐
│ Exp 001 │ Exp 002 │ Exp 003 │
├─────────┼─────────┼─────────┤
│ 7 ✅     │ 8 ✅     │ 6 ✅     │
│ 3 ❌     │ 2 ❌     │ 4 ❌     │
└─────────┴─────────┴─────────┘
```

### Idea 4: Export to PDF
Use a library like WeasyPrint:
```python
from weasyprint import HTML
HTML('report.html').write_pdf('report.pdf')
```

---

## Real-World Applications

This pattern (data → HTML report) is used everywhere:

1. **Test Runners**: JUnit, pytest-html
   - Input: Test results JSON
   - Output: HTML report

2. **CI/CD Dashboards**: Jenkins, GitHub Actions
   - Input: Build logs
   - Output: Status page

3. **Analytics Reports**: Google Analytics, Mixpanel
   - Input: Event data
   - Output: Visual dashboard

4. **ML Experiment Tracking**: Weights & Biases, MLflow
   - Input: Training metrics
   - Output: Experiment comparison

**You've learned a fundamental skill**: transforming machine data into human insights.

---

## SUCCESS CRITERIA
✅ `python benchmark/visualize.py` runs in < 1 second.
✅ `report.html` is valid HTML and opens in a browser.
✅ The summary stats (Improved/Regressed) are correct.
✅ All 10 prompts are displayed in "cards".
✅ "Base" and "Finetuned" responses are shown side-by-side.
✅ Cards are color-coded (green for ✅, red for ❌).
✅ Model output formatting (newlines) is preserved in the report.

---

## Troubleshooting

**Problem**: Report shows "❌ Input file not found"
- **Solution**: Run Agent 3 first to generate `deltas.json`

**Problem**: Responses show as one long line
- **Solution**: Check that `white-space: pre-wrap;` is in `.response-text` CSS

**Problem**: Colors are all wrong
- **Solution**: Check `get_assessment_class()` function - make sure it matches Agent 3's emoji format

**Problem**: HTML doesn't render in browser
- **Solution**: Check browser console for errors. Make sure all HTML tags are closed.

**Problem**: Unicode characters (✅❌) show as `?`
- **Solution**: Make sure `<meta charset="UTF-8">` is in the HTML head

---

## Next Steps

After completing Agent 4, you should:
1. Test with Agent 3's actual output
2. Review the HTML in a browser
3. Experiment with the CSS (change colors, fonts, layout)
4. Consider adding one of the extensions (search, charts)

Remember: This is a **teaching project**. The goal isn't just to generate a report, but to understand how data visualization works at a fundamental level.

---

END OF AGENT 4 TEACHING GUIDE
