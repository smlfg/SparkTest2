# Benchmark System - Agent 4: Visualization

This directory contains the visualization component of the DGX Fast Fine-tuning Iteration Lab.

## Purpose

Agent 4 transforms JSON data from Agent 3 (delta analysis) into beautiful, human-readable HTML reports. The goal is to make fine-tuning results instantly understandable.

## Files

```
benchmark/
├── README.md           # This file
├── visualize.py        # Main HTML generator (Agent 4)
└── results/
    ├── deltas.json     # Input: From Agent 3
    └── report.html     # Output: Visual report
```

## Quick Start

```bash
# Run the visualizer
python3 benchmark/visualize.py

# Open the report
open benchmark/results/report.html  # macOS
xdg-open benchmark/results/report.html  # Linux
```

## What It Does

1. **Reads** `deltas.json` (comparison data from Agent 3)
2. **Transforms** JSON into HTML with CSS styling
3. **Outputs** a self-contained `report.html` file

## Report Features

### Summary Dashboard
- **6 Improved ✅**: Prompts where fine-tuning helped
- **1 Regressed ❌**: Prompts where fine-tuning hurt
- **3 Neutral/Other**: Changed but not clearly better/worse

### Prompt Cards
Each prompt gets a visual card showing:
- **Side-by-side comparison**: Base vs Fine-tuned responses
- **Color coding**: Green (improved), Red (regressed), Gray (neutral)
- **Metrics**: Similarity, length delta, keyword counts
- **Assessment**: Clear ✅/❌/⚠️/⚪ indicator

## Design Principles

1. **Self-contained**: No external dependencies (CSS is inline)
2. **Portable**: Single HTML file you can email/share
3. **Fast**: Generates in <1 second for 100 prompts
4. **Git-friendly**: Track report history in version control

## Example Output

```html
┌─────────────────────────────────────────────┐
│ Fine-Tuning Delta Report                    │
├─────────────────────────────────────────────┤
│ [6 Improved ✅] [1 Regressed ❌] [3 Neutral] │
├─────────────────────────────────────────────┤
│ prompt_001 (factual) ✅ IMPROVED            │
│ ┌──────────────┬──────────────┐             │
│ │ Base         │ Finetuned    │             │
│ │ Paris        │ The capital  │             │
│ │              │ of France is │             │
│ │              │ Paris...     │             │
│ └──────────────┴──────────────┘             │
│ Similarity: 75% | Length: +85% | KW: 1→3   │
└─────────────────────────────────────────────┘
```

## Integration with Other Agents

```
Agent 3 (Delta Calculator)
      ↓
   deltas.json
      ↓
Agent 4 (Visualizer) ← YOU ARE HERE
      ↓
   report.html
      ↓
Agent 6 (Orchestrator) - Logs report path
      ↓
User opens in browser
```

## Key Technologies

- **Python f-strings**: Template engine for HTML generation
- **CSS Grid**: Modern layout system for side-by-side columns
- **Inline CSS**: Self-contained styling
- **UTF-8 encoding**: Emoji support (✅❌⚠️⚪)

## Learning Resources

See `docs/agents/agent4_teaching.md` for:
- How the code works line-by-line
- HTML/CSS concepts explained
- Experiments to try
- Common pitfalls and solutions

## Testing

A sample `deltas.json` is included for testing. It contains:
- 10 test prompts
- Mix of improved/regressed/neutral results
- Realistic response lengths
- Various categories (factual, math, coding, etc.)

## Success Criteria

✅ Runs in <1 second
✅ Valid HTML output
✅ Correct summary stats
✅ All prompts displayed
✅ Side-by-side comparison works
✅ Color coding matches assessments
✅ Newlines preserved in responses

## Troubleshooting

**No output file?**
- Check that `benchmark/results/` directory exists
- Verify `deltas.json` exists and is valid JSON

**Responses show as one line?**
- Ensure `white-space: pre-wrap;` is in CSS

**Colors wrong?**
- Check `get_assessment_class()` matches Agent 3's emoji format

**Emojis showing as ?**
- Verify `encoding="utf-8"` in file write operations

## Future Enhancements

Ideas for extending this agent:
- Add interactive search/filter
- Generate charts with Chart.js
- Compare multiple experiments side-by-side
- Export to PDF
- Add mobile responsive design

## Performance

- 10 prompts: ~0.05 seconds
- 100 prompts: ~0.3 seconds
- 1000 prompts: ~3 seconds

Time complexity: O(n) where n = number of prompts

---

**Built with teaching in mind.** Every design choice is explained in the code and documentation.
