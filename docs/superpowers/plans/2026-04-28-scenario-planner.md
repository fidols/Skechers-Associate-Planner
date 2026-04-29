# Scenario Planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new Scenario Planner page (`pages/4_Scenario_Planner.py`) that lets planners adjust ST% and receipt quantity assumptions per country and division, then instantly see the revenue, units sold, end inventory, and ST% impact vs baseline.

**Architecture:** Single new page reads `sku_df` and `sales_df` from `session_state`, aggregates them to a country × division baseline, applies percentage adjustments from `session_state`-backed sliders, and renders metric cards plus a color-coded comparison table. No new data files, no changes to existing pages or utilities.

**Tech Stack:** Python, Streamlit (`session_state`, `st.expander`, `st.slider`, `st.metric`, `st.dataframe`), pandas

---

## File Map

| File | Change |
|---|---|
| `pages/4_Scenario_Planner.py` | Create new page — all four tasks build this file incrementally |

---

## Task 1: Page scaffold and session guard

**Files:**
- Create: `pages/4_Scenario_Planner.py`

- [ ] **Step 1: Create the file with header and session guard**

Create `pages/4_Scenario_Planner.py` with this exact content:

```python
import pandas as pd
import streamlit as st

st.title("Scenario Planner")
st.caption(
    "**Stakeholders:** Associate Planner · Planning Manager · JV Country Partners  \n"
    "**Decisions:** What-if buy quantity adjustments · ST% sensitivity · Revenue impact forecasting"
)
st.divider()

sku_df = st.session_state.get("sku_df")
sales_df = st.session_state.get("sales_df")
selected_countries = st.session_state.get("selected_countries")

if sku_df is None or sales_df is None or not selected_countries:
    st.warning("Please navigate to the Overview page first to load data and make selections.")
    st.stop()
```

- [ ] **Step 2: Run existing tests to confirm no regressions**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && python -m pytest tests/ -v
```

Expected: **23 tests PASSED**, 0 failures.

- [ ] **Step 3: Commit**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && git add pages/4_Scenario_Planner.py && git commit -m "feat: scaffold Scenario Planner page with session guard"
```

---

## Task 2: Baseline aggregation

**Files:**
- Modify: `pages/4_Scenario_Planner.py`

Append the following block **after** the `st.stop()` line at the bottom of the file.

`sku_df` columns available: `style_id`, `style_name`, `division`, `country`, `channel`, `units_sold`, `units_on_hand`, `avg_weekly_sales`, `weeks_of_supply`, `sell_through_pct`, `flag`.

`sales_df` columns available: `country`, `channel`, `division`, `quarter`, `sales_units`, `sales_dollars`, `target_dollars`, `AUR`.

- [ ] **Step 1: Append baseline aggregation**

```python
DIVISIONS = ["Men's Sport", "Women's Sport", "Women's Comfort", "Kids"]

# --- Baseline: aggregate sku_df by country × division ---
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

# --- Baseline revenue from sales_df (all quarters, selected countries) ---
baseline_rev = (
    sales_df[sales_df["country"].isin(selected_countries)]
    .groupby(["country", "division"])
    .agg(baseline_revenue=("sales_dollars", "sum"))
    .reset_index()
)

baseline = baseline_sku.merge(baseline_rev, on=["country", "division"], how="left")
baseline["baseline_end_inv"] = (
    baseline["baseline_units_on_hand"] * (1 - baseline["baseline_st_pct"])
)
```

- [ ] **Step 2: Run existing tests to confirm no regressions**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && python -m pytest tests/ -v
```

Expected: **23 tests PASSED**, 0 failures.

- [ ] **Step 3: Commit**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && git add pages/4_Scenario_Planner.py && git commit -m "feat: add baseline aggregation to Scenario Planner"
```

---

## Task 3: Slider inputs panel

**Files:**
- Modify: `pages/4_Scenario_Planner.py`

Append after the baseline block. Slider keys use the prefix `sp_` to avoid collision with other pages' session state keys.

- [ ] **Step 1: Append the Reset button and slider expanders**

```python
# --- Reset button ---
if st.button("Reset All"):
    for country in selected_countries:
        for division in DIVISIONS:
            st.session_state[f"sp_{country}_{division}_st"] = 0
            st.session_state[f"sp_{country}_{division}_recv"] = 0
    st.rerun()

st.subheader("Adjust Assumptions")

# --- One expander per country, 4 division rows inside ---
for country in selected_countries:
    with st.expander(country, expanded=False):
        for division in DIVISIONS:
            col_a, col_b = st.columns(2)
            col_a.slider(
                f"{division} — ST% Adj",
                min_value=-50,
                max_value=50,
                value=0,
                step=1,
                format="%d%%",
                key=f"sp_{country}_{division}_st",
            )
            col_b.slider(
                f"{division} — Receipts Adj",
                min_value=-50,
                max_value=50,
                value=0,
                step=1,
                format="%d%%",
                key=f"sp_{country}_{division}_recv",
            )
```

- [ ] **Step 2: Run existing tests to confirm no regressions**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && python -m pytest tests/ -v
```

Expected: **23 tests PASSED**, 0 failures.

- [ ] **Step 3: Commit**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && git add pages/4_Scenario_Planner.py && git commit -m "feat: add slider inputs panel to Scenario Planner"
```

---

## Task 4: Scenario engine and outputs

**Files:**
- Modify: `pages/4_Scenario_Planner.py`

Append after the slider panel. The engine iterates the `baseline` DataFrame, reads current slider values from `session_state`, applies multipliers, and derives scenario metrics. Internal columns `_baseline_units_sold` and `_scenario_units_sold` are used for the Units Sold metric card and dropped before display.

- [ ] **Step 1: Append the scenario engine and outputs**

```python
# --- Scenario engine ---
rows = []
for _, row in baseline.iterrows():
    st_adj = st.session_state.get(f"sp_{row['country']}_{row['division']}_st", 0) / 100
    recv_adj = st.session_state.get(f"sp_{row['country']}_{row['division']}_recv", 0) / 100

    scenario_receipts = row["baseline_units_on_hand"] * (1 + recv_adj)
    scenario_st_pct = min(max(row["baseline_st_pct"] * (1 + st_adj), 0.0), 1.0)
    scenario_units_sold = scenario_receipts * scenario_st_pct
    if row["baseline_units_sold"] > 0:
        scenario_revenue = row["baseline_revenue"] * (
            scenario_units_sold / row["baseline_units_sold"]
        )
    else:
        scenario_revenue = 0.0
    scenario_end_inv = scenario_receipts * (1 - scenario_st_pct)

    rows.append({
        "Country": row["country"],
        "Division": row["division"],
        "Baseline ST%": row["baseline_st_pct"],
        "Scenario ST%": scenario_st_pct,
        "Δ ST%": scenario_st_pct - row["baseline_st_pct"],
        "Baseline Revenue": row["baseline_revenue"],
        "Scenario Revenue": scenario_revenue,
        "Δ Revenue": scenario_revenue - row["baseline_revenue"],
        "Baseline End Inv": row["baseline_end_inv"],
        "Scenario End Inv": scenario_end_inv,
        "Δ End Inv": scenario_end_inv - row["baseline_end_inv"],
        "_baseline_units_sold": row["baseline_units_sold"],
        "_scenario_units_sold": scenario_units_sold,
    })

scenario_df = pd.DataFrame(rows)

# --- Metric cards ---
st.divider()
st.subheader("Scenario vs Baseline")

total_rev_b = scenario_df["Baseline Revenue"].sum()
total_rev_s = scenario_df["Scenario Revenue"].sum()
delta_rev = total_rev_s - total_rev_b
rev_display = f"${total_rev_s/1e6:.1f}M" if total_rev_s >= 1e6 else f"${total_rev_s:,.0f}"
delta_rev_str = f"${delta_rev/1e6:+.1f}M" if abs(delta_rev) >= 1e6 else f"${delta_rev:+,.0f}"

total_units_b = scenario_df["_baseline_units_sold"].sum()
total_units_s = scenario_df["_scenario_units_sold"].sum()
delta_units = total_units_s - total_units_b

total_end_b = scenario_df["Baseline End Inv"].sum()
total_end_s = scenario_df["Scenario End Inv"].sum()
delta_end = total_end_s - total_end_b

avg_st_b = scenario_df["Baseline ST%"].mean()
avg_st_s = scenario_df["Scenario ST%"].mean()
delta_st = avg_st_s - avg_st_b

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", rev_display, delta=delta_rev_str)
c2.metric("Units Sold", f"{total_units_s:,.0f}", delta=f"{delta_units:+,.0f}")
c3.metric(
    "End Inventory",
    f"{total_end_s:,.0f}",
    delta=f"{delta_end:+,.0f}",
    delta_color="inverse",
)
c4.metric("Avg ST%", f"{avg_st_s:.1%}", delta=f"{delta_st:+.1%}")

# --- Comparison table ---
def _color_delta(val):
    if isinstance(val, (int, float)) and val == val:
        return "color: #16A34A" if val >= 0 else "color: #E31837"
    return ""


def _color_inv_delta(val):
    """More end inventory is bad (red), less end inventory is good (green)."""
    if isinstance(val, (int, float)) and val == val:
        return "color: #E31837" if val >= 0 else "color: #16A34A"
    return ""


display_df = scenario_df.drop(columns=["_baseline_units_sold", "_scenario_units_sold"])

st.dataframe(
    display_df.style
    .format({
        "Baseline ST%": "{:.1%}",
        "Scenario ST%": "{:.1%}",
        "Δ ST%": "{:+.1%}",
        "Baseline Revenue": "${:,.0f}",
        "Scenario Revenue": "${:,.0f}",
        "Δ Revenue": "${:+,.0f}",
        "Baseline End Inv": "{:,.0f}",
        "Scenario End Inv": "{:,.0f}",
        "Δ End Inv": "{:+,.0f}",
    })
    .map(_color_delta, subset=["Δ ST%", "Δ Revenue"])
    .map(_color_inv_delta, subset=["Δ End Inv"]),
    hide_index=True,
    width="stretch",
)
st.download_button(
    "Download Scenario CSV",
    data=display_df.to_csv(index=False),
    file_name="scenario_comparison.csv",
    mime="text/csv",
)
```

- [ ] **Step 2: Run existing tests to confirm no regressions**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && python -m pytest tests/ -v
```

Expected: **23 tests PASSED**, 0 failures.

- [ ] **Step 3: Smoke-test the page visually**

```bash
streamlit run /Users/mr.fidols/github/Skechers-Associate-Planner/app.py --server.port 8502
```

Navigate to Overview first (to populate session_state), then go to "4 Scenario Planner". Confirm:

- Page loads without the "navigate to Overview" warning
- One expander per selected country, collapsed by default
- Each expander shows 4 rows (Men's Sport / Women's Sport / Women's Comfort / Kids) × 2 sliders
- Sliders range −50% to +50%, default 0
- Moving a slider instantly updates metric cards and comparison table
- "Reset All" resets all sliders to 0 and all deltas return to zero
- Δ Revenue and Δ ST% columns: green when positive, red when negative
- Δ End Inv column: red when positive (more stuck inventory is bad), green when negative
- End Inventory metric card delta arrow: red when positive (uses `delta_color="inverse"`)
- CSV download contains 9 columns: Country, Division, Baseline ST%, Scenario ST%, Δ ST%, Baseline Revenue, Scenario Revenue, Δ Revenue, Baseline End Inv, Scenario End Inv, Δ End Inv

- [ ] **Step 4: Commit**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && git add pages/4_Scenario_Planner.py && git commit -m "feat: add scenario engine and outputs to Scenario Planner"
```

- [ ] **Step 5: Push**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && git push origin main
```

Expected: `main -> main` confirmed.
