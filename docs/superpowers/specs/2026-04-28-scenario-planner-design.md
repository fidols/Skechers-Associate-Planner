# Scenario Planner Design Spec

**Date:** 2026-04-28
**Feature:** Interactive what-if scenario planner on a new dedicated page

---

## Goal

Add a new `4_Scenario_Planner.py` page that lets planners adjust sell-through % and receipt quantity assumptions per country and per division, then instantly see the revenue, units sold, end inventory, and ST% impact vs baseline.

---

## Placement

New page: `pages/4_Scenario_Planner.py`. Appears as "4 Scenario Planner" in the Streamlit sidebar.

---

## Data Sources

All from `st.session_state` — no simulation re-run, no new files:

| Key | Used for |
|---|---|
| `sku_df` | Baseline units_on_hand, units_sold, sell_through_pct by SKU |
| `sales_df` | Baseline revenue (sales_dollars) by country × division |
| `selected_countries` | Determines which countries appear as expanders |

If either `sku_df` or `selected_countries` is missing, show the standard "navigate to Overview first" warning and `st.stop()`.

---

## Inputs Panel

### Sliders

One `st.expander` per selected country (label = country name, collapsed by default).

Inside each expander: a 4-row layout, one row per division in order: Men's Sport, Women's Sport, Women's Comfort, Kids.

Each row contains two sliders side by side (`st.columns(2)`):
- **ST% Adjustment** — range −50 to +50, step 1, default 0, unit "%" — label e.g. "Men's Sport — ST% Adj"
- **Receipts Adjustment** — range −50 to +50, step 1, default 0, unit "%" — label e.g. "Men's Sport — Receipts Adj"

Slider keys must be unique: `f"{country}_{division}_st"` and `f"{country}_{division}_recv"`.

### Reset Button

A "Reset All" button above the expanders. Clicking it sets all slider values back to 0 using `st.session_state` key assignment and calls `st.rerun()`.

---

## Scenario Engine

### Step 1: Baseline aggregation

Aggregate `sku_df` (filtered to `selected_countries`) by country × division:

```python
baseline_sku = (
    sku_df[sku_df["country"].isin(selected_countries)]
    .groupby(["country", "division"])
    .agg(
        baseline_units_on_hand=("units_on_hand", "sum"),
        baseline_units_sold=("units_sold", "sum"),
        baseline_st_pct=("sell_through_pct", "mean"),
    )
    .reset_index()
)
```

Aggregate `sales_df` (filtered to `selected_countries`, all quarters) by country × division for revenue baseline:

```python
baseline_rev = (
    sales_df[sales_df["country"].isin(selected_countries)]
    .groupby(["country", "division"])
    .agg(baseline_revenue=("sales_dollars", "sum"))
    .reset_index()
)
```

Merge on country × division (left join from `baseline_sku`).

### Step 2: Apply adjustments

For each row, read slider values from `st.session_state`:

```python
st_adj = st.session_state.get(f"{row.country}_{row.division}_st", 0) / 100
recv_adj = st.session_state.get(f"{row.country}_{row.division}_recv", 0) / 100

scenario_receipts = row.baseline_units_on_hand * (1 + recv_adj)
scenario_st_pct = min(max(row.baseline_st_pct * (1 + st_adj), 0.0), 1.0)
scenario_units_sold = scenario_receipts * scenario_st_pct
scenario_revenue = row.baseline_revenue * (scenario_units_sold / row.baseline_units_sold) if row.baseline_units_sold > 0 else 0.0
scenario_end_inv = scenario_receipts * (1 - scenario_st_pct)
```

### Step 3: Deltas

```python
delta_revenue = scenario_revenue - baseline_revenue
delta_units_sold = scenario_units_sold - baseline_units_sold
delta_end_inv = scenario_end_inv - baseline_end_inv  # baseline_end_inv = units_on_hand * (1 - baseline_st_pct)
delta_st_pct = scenario_st_pct - baseline_st_pct
```

---

## Outputs

### Metric Cards

Four `st.metric` cards in a single row (`st.columns(4)`):

| Card | Value | Delta |
|---|---|---|
| Total Revenue | `$XM` (scenario total) | `+$XM vs baseline` |
| Units Sold | `X,XXX` (scenario total) | `+XXX vs baseline` |
| End Inventory | `X,XXX` (scenario total) | `+XXX vs baseline` |
| Avg ST% | `XX%` (scenario weighted avg) | `+X.X pp vs baseline` |

### Comparison Table

`st.dataframe` with one row per country × division. Columns:

| Column | Format |
|---|---|
| Country | text |
| Division | text |
| Baseline ST% | `XX%` |
| Scenario ST% | `XX%` |
| Δ ST% | `+X.X pp` — green if ≥ 0, red if < 0 |
| Baseline Revenue | `$X,XXX` |
| Scenario Revenue | `$X,XXX` |
| Δ Revenue | `+$X,XXX` — green if ≥ 0, red if < 0 |
| Baseline End Inv | `X,XXX` |
| Scenario End Inv | `X,XXX` |
| Δ End Inv | `+X,XXX` — green if ≥ 0, red if < 0 |

Color coding on Δ columns via `DataFrame.style.map`. End inventory delta: positive is red (more stuck inventory = bad), negative is green (less stuck = good). Revenue and ST% delta: positive is green, negative is red.

CSV download button below the table.

---

## Files Changed

| File | Change |
|---|---|
| `pages/4_Scenario_Planner.py` | Create new page |

No changes to simulate.py, utils/, or other pages. No new tests needed (pure UI arithmetic; underlying data pipeline is already tested).

---

## Success Criteria

- Expanders appear for each selected country (respects sidebar country selection)
- Moving a slider instantly updates metric cards and comparison table
- Reset All returns all values to baseline (zero deltas)
- ST% is clamped between 0% and 100% regardless of slider position
- Division/country combos with no SKU data show 0 or are excluded from table
- Page gracefully handles missing session_state (redirects to Overview)
