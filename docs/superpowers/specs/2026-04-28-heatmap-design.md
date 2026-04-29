# ST% Heatmap Design Spec

**Date:** 2026-04-28
**Feature:** Country × Division sell-through heatmap on SKU Performance page

---

## Goal

Add a `go.Heatmap` chart to the bottom of the SKU Performance page showing average sell-through % for every Country × Division combination. Gives planners an instant visual read of where performance is strong or weak across markets and product categories.

---

## Placement

Bottom of `pages/3_SKU_Performance.py`, below the Top 10 / Bottom 10 bar charts.

---

## Data

Source: `filtered` DataFrame (already respects Division, Channel, and Flag page-level filters).

Aggregation:
```python
heatmap_df = (
    filtered.groupby(["country", "division"])["sell_through_pct"]
    .mean()
    .reset_index()
)
```

Then pivot to a 2D matrix (countries as rows, divisions as columns) for `go.Heatmap`.

---

## Chart Spec

- **Library:** `plotly.graph_objects` — add `import plotly.graph_objects as go` to the file
- **Type:** `go.Heatmap`
- **X-axis:** Divisions (4 values: Men's Sport, Women's Sport, Women's Comfort, Kids)
- **Y-axis:** Countries (up to 6, based on sidebar `selected_countries`)
- **Z values:** Average sell-through % (0–1 scale)
- **Colorscale:** `[[0, "#E31837"], [0.5, "#FFFFFF"], [1, "#16A34A"]]` — red → white → green
- **zmin / zmax:** 0 and 1 (fixed, so colors are consistent across filter changes)
- **Cell text annotations:** formatted as `"XX%"` (e.g. `"72%"`) shown inside each cell
- **Hover tooltip:** country, division, exact ST% value
- **Title:** `"Sell-Through % by Country × Division"`
- **Layout:** `width="stretch"`, consistent with existing charts

---

## Files Changed

| File | Change |
|---|---|
| `pages/3_SKU_Performance.py` | Add `import plotly.graph_objects as go`; add heatmap section at bottom |

No other files change. No new tests needed (chart rendering is not unit-testable; existing data pipeline tests cover the underlying data).
