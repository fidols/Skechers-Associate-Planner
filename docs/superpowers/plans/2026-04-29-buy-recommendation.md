# Buy Recommendation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Buy Recommendation page (`pages/5_Buy_Recommendation.py`) that uses current WOS and avg weekly sales velocity to recommend next-season buy quantities at the division × channel level.

**Architecture:** Pure calculation logic extracted to `utils/buy_recommendation.py` (testable), consumed by a new Streamlit page. The engine aggregates `sku_df` by division × channel for selected countries, computes current WOS, and derives recommended buy units and an action flag (Chase / On Plan / Reduce) relative to a user-adjustable target WOS. No changes to existing pages or data simulation.

**Tech Stack:** Python, pandas, Streamlit, pytest

---

## File Map

| File | Change |
|---|---|
| `utils/buy_recommendation.py` | Create — pure recommendation engine function |
| `tests/test_buy_recommendation.py` | Create — unit tests for engine |
| `pages/5_Buy_Recommendation.py` | Create — Streamlit page |

---

## Task 1: Recommendation engine (TDD)

**Files:**
- Create: `utils/buy_recommendation.py`
- Create: `tests/test_buy_recommendation.py`

`sku_df` columns available: `style_id`, `style_name`, `division`, `country`, `channel`, `units_sold`, `units_on_hand`, `avg_weekly_sales`, `weeks_of_supply`, `sell_through_pct`, `flag`.

The engine aggregates by `division × channel` for `selected_countries`, sums `units_on_hand` and `avg_weekly_sales`, then derives `current_wos`, `recommended_buy`, and `action`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_buy_recommendation.py`:

```python
import pandas as pd
import pytest
from utils.buy_recommendation import compute_buy_recommendations


def _make_sku_df(units_on_hand, avg_weekly_sales, country="China", division="Men's Sport", channel="Normal Retail"):
    return pd.DataFrame([{
        "country": country,
        "division": division,
        "channel": channel,
        "units_on_hand": units_on_hand,
        "avg_weekly_sales": avg_weekly_sales,
    }])


def test_chase_flag_when_wos_below_75pct_of_target():
    # current_wos = 100 / 20 = 5.0, target = 8, threshold = 6.0 → Chase
    df = _make_sku_df(units_on_hand=100, avg_weekly_sales=20)
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    assert result.iloc[0]["action"] == "Chase"


def test_reduce_flag_when_wos_above_125pct_of_target():
    # current_wos = 200 / 15 ≈ 13.3, target = 8, threshold = 10.0 → Reduce
    df = _make_sku_df(units_on_hand=200, avg_weekly_sales=15)
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    assert result.iloc[0]["action"] == "Reduce"


def test_on_plan_flag_within_range():
    # current_wos = 70 / 10 = 7.0, target = 8, range [6.0, 10.0] → On Plan
    df = _make_sku_df(units_on_hand=70, avg_weekly_sales=10)
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    assert result.iloc[0]["action"] == "On Plan"


def test_recommended_buy_correct_units():
    # current_wos = 50 / 20 = 2.5, target = 8 → buy = (8 - 2.5) * 20 = 110
    df = _make_sku_df(units_on_hand=50, avg_weekly_sales=20)
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    assert result.iloc[0]["recommended_buy"] == 110


def test_recommended_buy_is_zero_when_wos_at_or_above_target():
    # current_wos = 200 / 20 = 10.0 >= 8 → buy = 0
    df = _make_sku_df(units_on_hand=200, avg_weekly_sales=20)
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    assert result.iloc[0]["recommended_buy"] == 0


def test_filters_by_selected_countries():
    df = pd.DataFrame([
        {"country": "China",    "division": "Kids", "channel": "Outlet", "units_on_hand": 100, "avg_weekly_sales": 10},
        {"country": "Mexico",   "division": "Kids", "channel": "Outlet", "units_on_hand": 200, "avg_weekly_sales": 10},
    ])
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    # Only China row: units_on_hand=100, wos=10 → Reduce
    assert len(result) == 1
    assert result.iloc[0]["action"] == "Reduce"


def test_aggregates_multiple_skus_in_same_division_channel():
    df = pd.DataFrame([
        {"country": "China", "division": "Kids", "channel": "Outlet", "units_on_hand": 30, "avg_weekly_sales": 5},
        {"country": "China", "division": "Kids", "channel": "Outlet", "units_on_hand": 20, "avg_weekly_sales": 5},
    ])
    # Combined: units_on_hand=50, avg_weekly_sales=10, wos=5.0, target=8
    # buy = (8 - 5) * 10 = 30
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    assert len(result) == 1
    assert result.iloc[0]["recommended_buy"] == 30
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && python -m pytest tests/test_buy_recommendation.py -v
```

Expected: 7 FAILED with `ModuleNotFoundError: No module named 'utils.buy_recommendation'`

- [ ] **Step 3: Implement the engine**

Create `utils/buy_recommendation.py`:

```python
import pandas as pd


def compute_buy_recommendations(
    sku_df: pd.DataFrame,
    selected_countries: list,
    target_wos: float,
) -> pd.DataFrame:
    """Aggregate sku_df by division × channel and recommend buy quantities.

    Returns a DataFrame with columns:
        division, channel, units_on_hand, avg_weekly_sales,
        current_wos, recommended_buy, action
    """
    filtered = sku_df[sku_df["country"].isin(selected_countries)]
    agg = (
        filtered
        .groupby(["division", "channel"])
        .agg(
            units_on_hand=("units_on_hand", "sum"),
            avg_weekly_sales=("avg_weekly_sales", "sum"),
        )
        .reset_index()
    )
    agg["current_wos"] = agg["units_on_hand"] / agg["avg_weekly_sales"]
    agg["recommended_buy"] = (
        ((target_wos - agg["current_wos"]) * agg["avg_weekly_sales"])
        .clip(lower=0)
        .round()
        .astype(int)
    )
    agg["action"] = agg["current_wos"].apply(
        lambda wos: (
            "Chase" if wos < target_wos * 0.75
            else "Reduce" if wos > target_wos * 1.25
            else "On Plan"
        )
    )
    return agg
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && python -m pytest tests/test_buy_recommendation.py -v
```

Expected: **7 PASSED**

- [ ] **Step 5: Run full test suite**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && python -m pytest tests/ -v
```

Expected: **30 PASSED** (23 existing + 7 new)

- [ ] **Step 6: Commit**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && git add utils/buy_recommendation.py tests/test_buy_recommendation.py && git commit -m "feat: add buy recommendation engine with tests"
```

---

## Task 2: Page scaffold and inputs

**Files:**
- Create: `pages/5_Buy_Recommendation.py`

- [ ] **Step 1: Create the page**

Create `pages/5_Buy_Recommendation.py` with this exact content:

```python
import streamlit as st
from utils.buy_recommendation import compute_buy_recommendations

st.title("Buy Recommendation")
st.caption(
    "**Stakeholders:** Associate Planner · Merchandisers · JV Country Partners  \n"
    "**Decisions:** Next season buy quantities · Chase reorders · Inventory reduction targets"
)
st.divider()

sku_df = st.session_state.get("sku_df")
selected_countries = st.session_state.get("selected_countries")

if sku_df is None or not selected_countries:
    st.warning("Please navigate to the Overview page first to load data and make selections.")
    st.stop()

# --- Inputs ---
target_wos = st.slider(
    "Target Weeks of Supply",
    min_value=4,
    max_value=16,
    value=8,
    step=1,
    format="%d wks",
)

col1, col2 = st.columns(2)
division_opts = ["All"] + sorted(sku_df["division"].unique().tolist())
channel_opts = ["All"] + sorted(sku_df["channel"].unique().tolist())
division_filter = col1.selectbox("Division", division_opts)
channel_filter = col2.selectbox("Channel", channel_opts)

# --- Compute recommendations ---
recs = compute_buy_recommendations(sku_df, selected_countries, target_wos)

# Apply page-level filters for display
if division_filter != "All":
    recs = recs[recs["division"] == division_filter]
if channel_filter != "All":
    recs = recs[recs["channel"] == channel_filter]

if recs.empty:
    st.info("No data matches the selected filters.")
    st.stop()
```

- [ ] **Step 2: Run full test suite**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && python -m pytest tests/ -v
```

Expected: **30 PASSED**

- [ ] **Step 3: Commit**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && git add pages/5_Buy_Recommendation.py && git commit -m "feat: add Buy Recommendation page scaffold and inputs"
```

---

## Task 3: Outputs (metric cards, table, CSV)

**Files:**
- Modify: `pages/5_Buy_Recommendation.py`

Append after the `st.stop()` at the end of Task 2's file.

- [ ] **Step 1: Append outputs**

```python
# --- Metric cards ---
st.divider()
total_buy = int(recs["recommended_buy"].sum())
n_chase = int((recs["action"] == "Chase").sum())
n_reduce = int((recs["action"] == "Reduce").sum())

c1, c2, c3 = st.columns(3)
c1.metric("Total Rec. Buy Units", f"{total_buy:,}")
c2.metric("Chase", f"{n_chase}")
c3.metric("Reduce", f"{n_reduce}")

# --- Recommendation table ---
st.subheader("Recommendation by Division × Channel")

ACTION_COLORS = {"Chase": "color: #16A34A", "Reduce": "color: #E31837", "On Plan": ""}


def _color_action(val):
    return ACTION_COLORS.get(val, "")


display = recs.rename(columns={
    "division": "Division",
    "channel": "Channel",
    "current_wos": "Current WOS",
    "recommended_buy": "Rec. Buy Units",
    "action": "Action",
}).drop(columns=["units_on_hand", "avg_weekly_sales"])

display.insert(2, "Target WOS", target_wos)

st.dataframe(
    display.style
    .format({
        "Current WOS": "{:.1f}",
        "Target WOS": "{:.0f}",
        "Rec. Buy Units": "{:,}",
    })
    .map(_color_action, subset=["Action"]),
    hide_index=True,
    width="stretch",
)
st.download_button(
    "Download Recommendations CSV",
    data=display.to_csv(index=False),
    file_name="buy_recommendations.csv",
    mime="text/csv",
)
```

- [ ] **Step 2: Run full test suite**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && python -m pytest tests/ -v
```

Expected: **30 PASSED**

- [ ] **Step 3: Smoke-test the page**

```bash
streamlit run /Users/mr.fidols/github/Skechers-Associate-Planner/app.py --server.port 8502
```

Navigate to Overview first, then "5 Buy Recommendation". Confirm:

- Target WOS slider renders, default 8 wks
- Changing slider updates metric cards and table instantly
- Division and Channel filters narrow the table
- Chase rows show green action text, Reduce rows show red
- "Current WOS" column shows 1 decimal, "Rec. Buy Units" shows comma-formatted integer
- Rec. Buy Units = 0 for rows where Current WOS ≥ Target WOS
- CSV download contains: Division, Channel, Current WOS, Target WOS, Rec. Buy Units, Action

- [ ] **Step 4: Commit and push**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && git add pages/5_Buy_Recommendation.py && git commit -m "feat: add Buy Recommendation outputs — metric cards, table, CSV" && git push origin main
```

Expected: `main -> main` confirmed.
