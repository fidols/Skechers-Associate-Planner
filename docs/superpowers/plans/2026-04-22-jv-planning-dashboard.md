# Skechers JV Planning Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-page Streamlit dashboard simulating the Skechers Associate Planner workflow across 3 JV markets, 5 channels, and 4 divisions.

**Architecture:** All data is generated in-memory at startup via seeded NumPy functions in `data/simulate.py`. Shared KPI logic lives in `utils/metrics.py`. Each planning view is an isolated Streamlit page that reads from `st.session_state` populated by `app.py`.

**Tech Stack:** Python 3.11+, Streamlit, Pandas, Plotly, NumPy, pytest

---

## File Map

| File | Responsibility |
|---|---|
| `app.py` | Entry point, sidebar filters, loads all data into session state, Overview page |
| `data/simulate.py` | Three seeded data generators: sales, OTB, SKU |
| `utils/metrics.py` | `overview_kpis()` and `months_of_supply()` — shared calculations |
| `pages/1_quarterly_recap.py` | Channel/division recap page |
| `pages/2_otb_tracker.py` | Monthly inventory flow + OTB page |
| `pages/3_sku_performance.py` | Style-level sell-through + opportunity/risk flags |
| `tests/test_simulate.py` | Unit tests for all three data generators |
| `tests/test_metrics.py` | Unit tests for KPI helpers |
| `pytest.ini` | Adds project root to Python path |
| `requirements.txt` | Pinned dependencies |
| `README.md` | Setup instructions + page-to-role mapping |

---

## Task 1: Scaffold Project Structure

**Files:**
- Create: `data/__init__.py`
- Create: `utils/__init__.py`
- Create: `pages/.gitkeep`
- Create: `tests/__init__.py`
- Create: `pytest.ini`
- Create: `requirements.txt`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p data utils pages tests
touch data/__init__.py utils/__init__.py tests/__init__.py
```

- [ ] **Step 2: Create `pytest.ini`**

```ini
[pytest]
pythonpath = .
```

- [ ] **Step 3: Create `requirements.txt`**

```
streamlit>=1.32.0
pandas>=2.0.0
numpy>=1.26.0
plotly>=5.20.0
pytest>=8.0.0
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 5: Commit**

```bash
git add pytest.ini requirements.txt data/__init__.py utils/__init__.py tests/__init__.py
git commit -m "feat: scaffold project structure"
```

---

## Task 2: Data Simulation (`data/simulate.py`)

**Files:**
- Create: `data/simulate.py`
- Create: `tests/test_simulate.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_simulate.py`:

```python
import pandas as pd
import pytest
from data.simulate import (
    generate_sales_data, generate_otb_data, generate_sku_data,
    COUNTRIES, CHANNELS, DIVISIONS, QUARTERS,
)


def test_sales_data_columns():
    df = generate_sales_data()
    expected = {
        "country", "channel", "division", "quarter",
        "sales_units", "sales_dollars", "target_units", "target_dollars",
        "AUR", "discount_pct",
    }
    assert expected.issubset(set(df.columns))


def test_sales_data_no_nulls():
    df = generate_sales_data()
    assert df.isnull().sum().sum() == 0


def test_sales_data_countries():
    df = generate_sales_data()
    assert set(df["country"].unique()) == set(COUNTRIES)


def test_sales_data_positive_values():
    df = generate_sales_data()
    assert (df["sales_units"] > 0).all()
    assert (df["sales_dollars"] > 0).all()
    assert (df["AUR"] > 0).all()


def test_sales_data_discount_range():
    df = generate_sales_data()
    assert (df["discount_pct"] >= 0).all()
    assert (df["discount_pct"] <= 1).all()


def test_otb_data_columns():
    df = generate_otb_data()
    expected = {
        "month", "country", "channel", "beg_inventory", "receipts", "sales",
        "end_inventory", "otb_budget", "committed_units", "open_to_buy",
    }
    assert expected.issubset(set(df.columns))


def test_otb_end_inventory_derived():
    df = generate_otb_data()
    computed = df["beg_inventory"] + df["receipts"] - df["sales"]
    pd.testing.assert_series_equal(computed, df["end_inventory"], check_names=False)


def test_otb_open_to_buy_derived():
    df = generate_otb_data()
    computed = df["otb_budget"] - df["committed_units"]
    pd.testing.assert_series_equal(computed, df["open_to_buy"], check_names=False)


def test_sku_data_columns():
    df = generate_sku_data()
    expected = {
        "style_id", "style_name", "division", "country", "channel",
        "units_sold", "units_on_hand", "avg_weekly_sales",
        "weeks_of_supply", "sell_through_pct", "flag",
    }
    assert expected.issubset(set(df.columns))


def test_sku_sell_through_range():
    df = generate_sku_data()
    assert (df["sell_through_pct"] >= 0).all()
    assert (df["sell_through_pct"] <= 1).all()


def test_sku_flag_values():
    df = generate_sku_data()
    assert set(df["flag"].unique()).issubset({"Opportunity", "Risk", "On Track"})


def test_sku_flag_logic_risk():
    df = generate_sku_data()
    risk = df[df["flag"] == "Risk"]
    assert ((risk["sell_through_pct"] < 0.40) | (risk["weeks_of_supply"] > 12)).all()


def test_sku_flag_logic_opportunity():
    df = generate_sku_data()
    opp = df[df["flag"] == "Opportunity"]
    assert ((opp["sell_through_pct"] > 0.75) & (opp["weeks_of_supply"] < 4)).all()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_simulate.py -v
```

Expected: `ModuleNotFoundError: No module named 'data.simulate'`

- [ ] **Step 3: Implement `data/simulate.py`**

```python
import numpy as np
import pandas as pd

SEED = 42

COUNTRIES = ["Japan", "Mexico", "South Korea"]
CHANNELS = ["Normal Retail", "Outlet", "Franchise", "Wholesale", "Ecommerce"]
DIVISIONS = ["Men's Sport", "Women's Sport", "Women's Comfort", "Kids"]
QUARTERS = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025"]

CHANNEL_AUR = {
    "Normal Retail": 72,
    "Outlet": 45,
    "Franchise": 68,
    "Wholesale": 38,
    "Ecommerce": 65,
}

COUNTRY_VOLUME = {
    "Japan": 1.0,
    "Mexico": 1.3,
    "South Korea": 0.9,
}

STYLE_NAMES = [
    "Arch Fit Comfy", "D'Lites Retro", "Go Walk 7", "Relaxed Fit Summits",
    "Max Cushioning Premier", "Skech-Air Element", "Equalizer 5", "Flex Advantage 4",
    "Go Run Consistent", "Summits Air Dazzle", "Bobs B-Cool", "Uno Stand On Air",
    "Glide Step Sport", "Dynamight 2", "Squad SR", "Gratis", "Work: Sure Track",
    "Arch Fit AD", "Slip-Ins Summits", "Foamies Creston Ultra",
]


def generate_sales_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows = []
    for country in COUNTRIES:
        for channel in CHANNELS:
            for division in DIVISIONS:
                for quarter in QUARTERS:
                    base_units = int(rng.integers(800, 3000) * COUNTRY_VOLUME[country])
                    target_units = int(base_units * rng.uniform(0.9, 1.15))
                    aur = CHANNEL_AUR[channel] * rng.uniform(0.9, 1.1)
                    if channel == "Outlet":
                        discount_pct = rng.uniform(0.25, 0.40)
                    else:
                        discount_pct = rng.uniform(0.03, 0.18)
                    sales_dollars = round(base_units * aur, 2)
                    target_dollars = round(target_units * aur, 2)
                    rows.append({
                        "country": country,
                        "channel": channel,
                        "division": division,
                        "quarter": quarter,
                        "sales_units": base_units,
                        "sales_dollars": sales_dollars,
                        "target_units": target_units,
                        "target_dollars": target_dollars,
                        "AUR": round(aur, 2),
                        "discount_pct": round(float(discount_pct), 3),
                    })
    return pd.DataFrame(rows)


def generate_otb_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 1)
    months = pd.date_range("2024-01-01", "2025-03-01", freq="MS")
    rows = []
    for country in COUNTRIES:
        for channel in CHANNELS:
            beg_inv = int(rng.integers(5000, 15000) * COUNTRY_VOLUME[country])
            for month in months:
                receipts = int(rng.integers(1000, 5000) * COUNTRY_VOLUME[country])
                max_sales = max(beg_inv + receipts - 50, 1)
                sales = int(min(rng.integers(800, 4500) * COUNTRY_VOLUME[country], max_sales))
                end_inv = beg_inv + receipts - sales
                otb_budget = int(rng.integers(2000, 6000) * COUNTRY_VOLUME[country])
                committed = int(otb_budget * rng.uniform(0.5, 0.95))
                rows.append({
                    "month": month,
                    "country": country,
                    "channel": channel,
                    "beg_inventory": beg_inv,
                    "receipts": receipts,
                    "sales": sales,
                    "end_inventory": end_inv,
                    "otb_budget": otb_budget,
                    "committed_units": committed,
                    "open_to_buy": otb_budget - committed,
                })
                beg_inv = end_inv
    return pd.DataFrame(rows)


def generate_sku_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 2)
    style_pool = [
        (f"SK-{1000 + i}", STYLE_NAMES[i % len(STYLE_NAMES)], DIVISIONS[i % len(DIVISIONS)])
        for i in range(40)
    ]
    rows = []
    for style_id, style_name, division in style_pool:
        for country in COUNTRIES:
            for channel in CHANNELS:
                units_sold = int(rng.integers(50, 600))
                units_on_hand = int(rng.integers(20, 400))
                avg_weekly = round(float(rng.uniform(5, 50)), 1)
                weeks_of_supply = round(units_on_hand / avg_weekly, 1)
                sell_through = round(units_sold / (units_sold + units_on_hand), 3)
                if sell_through < 0.40 or weeks_of_supply > 12:
                    flag = "Risk"
                elif sell_through > 0.75 and weeks_of_supply < 4:
                    flag = "Opportunity"
                else:
                    flag = "On Track"
                rows.append({
                    "style_id": style_id,
                    "style_name": style_name,
                    "division": division,
                    "country": country,
                    "channel": channel,
                    "units_sold": units_sold,
                    "units_on_hand": units_on_hand,
                    "avg_weekly_sales": avg_weekly,
                    "weeks_of_supply": weeks_of_supply,
                    "sell_through_pct": sell_through,
                    "flag": flag,
                })
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_simulate.py -v
```

Expected: All 14 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add data/simulate.py tests/test_simulate.py
git commit -m "feat: add seeded data simulation for sales, OTB, and SKU datasets"
```

---

## Task 3: Metrics Utilities (`utils/metrics.py`)

**Files:**
- Create: `utils/metrics.py`
- Create: `tests/test_metrics.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_metrics.py`:

```python
import pandas as pd
import pytest
from utils.metrics import overview_kpis, months_of_supply


def make_sales_df():
    return pd.DataFrame({
        "sales_dollars": [100.0, 200.0],
        "target_dollars": [150.0, 180.0],
    })


def make_otb_df():
    return pd.DataFrame({
        "country": ["Japan", "Japan"],
        "channel": ["Normal Retail", "Outlet"],
        "open_to_buy": [1000, 2000],
        "sales": [500, 400],
        "end_inventory": [3000, 2000],
        "beg_inventory": [4000, 3000],
        "receipts": [500, 400],
        "otb_budget": [1500, 2500],
        "committed_units": [500, 500],
        "month": pd.to_datetime(["2024-01-01", "2024-01-01"]),
    })


def make_sku_df():
    return pd.DataFrame({
        "units_sold": [80, 20],
        "units_on_hand": [20, 80],
        "flag": ["Opportunity", "Risk"],
    })


def test_overview_kpis_total_sales():
    kpis = overview_kpis(make_sales_df(), make_otb_df(), make_sku_df())
    assert kpis["total_sales_dollars"] == 300.0


def test_overview_kpis_sell_through():
    kpis = overview_kpis(make_sales_df(), make_otb_df(), make_sku_df())
    # (80 + 20) / (80 + 20 + 20 + 80) = 100 / 200 = 0.5
    assert kpis["sell_through_pct"] == 0.5


def test_overview_kpis_avg_otb():
    kpis = overview_kpis(make_sales_df(), make_otb_df(), make_sku_df())
    # mean([1000, 2000]) = 1500
    assert kpis["avg_otb_remaining"] == 1500.0


def test_overview_kpis_risk_count():
    kpis = overview_kpis(make_sales_df(), make_otb_df(), make_sku_df())
    assert kpis["risk_sku_count"] == 1


def test_months_of_supply_columns():
    mos = months_of_supply(make_otb_df())
    assert "months_of_supply" in mos.columns
    assert "country" in mos.columns
    assert "channel" in mos.columns


def test_months_of_supply_positive():
    mos = months_of_supply(make_otb_df())
    assert (mos["months_of_supply"] >= 0).all()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_metrics.py -v
```

Expected: `ModuleNotFoundError: No module named 'utils.metrics'`

- [ ] **Step 3: Implement `utils/metrics.py`**

```python
import pandas as pd


def overview_kpis(
    sales_df: pd.DataFrame,
    otb_df: pd.DataFrame,
    sku_df: pd.DataFrame,
) -> dict:
    """
    Returns top-level KPIs for the Overview page.

    Keys:
        total_sales_dollars: float
        sell_through_pct: float (0–1)
        avg_otb_remaining: float (units)
        risk_sku_count: int
    """
    total_sales = sales_df["sales_dollars"].sum()
    total_sold = sku_df["units_sold"].sum()
    total_available = total_sold + sku_df["units_on_hand"].sum()
    sell_through = total_sold / total_available if total_available > 0 else 0.0
    avg_otb = otb_df["open_to_buy"].mean()
    risk_count = int((sku_df["flag"] == "Risk").sum())
    return {
        "total_sales_dollars": round(float(total_sales), 2),
        "sell_through_pct": round(float(sell_through), 3),
        "avg_otb_remaining": round(float(avg_otb), 0),
        "risk_sku_count": risk_count,
    }


def months_of_supply(otb_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns avg monthly sales, avg end inventory, and months of supply
    per country/channel combination.
    """
    agg = (
        otb_df.groupby(["country", "channel"])
        .agg(
            avg_monthly_sales=("sales", "mean"),
            avg_end_inventory=("end_inventory", "mean"),
        )
        .reset_index()
    )
    agg["months_of_supply"] = (
        agg["avg_end_inventory"] / agg["avg_monthly_sales"]
    ).round(1)
    return agg
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -v
```

Expected: All 20 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/metrics.py tests/test_metrics.py
git commit -m "feat: add overview_kpis and months_of_supply metric helpers"
```

---

## Task 4: Overview Page (`app.py`)

**Files:**
- Create: `app.py`

- [ ] **Step 1: Create `app.py`**

```python
import streamlit as st
import plotly.express as px

from data.simulate import generate_sales_data, generate_otb_data, generate_sku_data
from utils.metrics import overview_kpis

st.set_page_config(
    page_title="Skechers JV Planning Dashboard",
    page_icon="👟",
    layout="wide",
)


@st.cache_data
def load_data():
    return generate_sales_data(), generate_otb_data(), generate_sku_data()


sales_df, otb_df, sku_df = load_data()

# Persist datasets so all pages can access them without re-generating
st.session_state["sales_df"] = sales_df
st.session_state["otb_df"] = otb_df
st.session_state["sku_df"] = sku_df

# --- Sidebar filters (shared across all pages) ---
st.sidebar.title("Filters")
quarters = sales_df["quarter"].unique().tolist()
selected_quarter = st.sidebar.selectbox("Quarter", quarters, index=len(quarters) - 1)

countries = sorted(sales_df["country"].unique().tolist())
selected_countries = st.sidebar.multiselect("Countries", countries, default=countries)

st.session_state["selected_quarter"] = selected_quarter
st.session_state["selected_countries"] = selected_countries

# --- Filter datasets for this view ---
filtered_sales = sales_df[
    (sales_df["quarter"] == selected_quarter)
    & (sales_df["country"].isin(selected_countries))
]
filtered_otb = otb_df[otb_df["country"].isin(selected_countries)]
filtered_sku = sku_df[sku_df["country"].isin(selected_countries)]

# --- Page header ---
st.title("Skechers International JV Planning Dashboard")
st.caption(
    "**Stakeholders:** Senior Merchandisers · JV Regional Leads · Planning Manager  \n"
    "**Decisions:** Market health pulse · Sell-through check · OTB capacity · Risk SKU triage"
)
st.divider()

# --- KPI cards ---
kpis = overview_kpis(filtered_sales, filtered_otb, filtered_sku)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sales", f"${kpis['total_sales_dollars']:,.0f}")
col2.metric("Sell-Through", f"{kpis['sell_through_pct'] * 100:.1f}%")
col3.metric("Avg OTB Remaining", f"{kpis['avg_otb_remaining']:,.0f} units")
col4.metric("Risk SKUs", f"{kpis['risk_sku_count']:,}")

# --- Sales vs Target by country ---
country_summary = (
    filtered_sales.groupby("country")
    .agg(sales_dollars=("sales_dollars", "sum"), target_dollars=("target_dollars", "sum"))
    .reset_index()
)
fig = px.bar(
    country_summary.melt(
        id_vars="country",
        value_vars=["sales_dollars", "target_dollars"],
        var_name="Metric",
        value_name="USD",
    ),
    x="country",
    y="USD",
    color="Metric",
    barmode="group",
    title=f"Sales vs. Target by Country — {selected_quarter}",
    labels={"USD": "Revenue (USD)", "country": "Country"},
    color_discrete_map={"sales_dollars": "#1f77b4", "target_dollars": "#aec7e8"},
)
st.plotly_chart(fig, use_container_width=True)
```

- [ ] **Step 2: Smoke test — run the app**

```bash
streamlit run app.py
```

Expected: App opens at `http://localhost:8501`. Overview page shows 4 KPI cards and a grouped bar chart. Sidebar filters update the chart.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add overview page with KPI cards and sales vs target chart"
```

---

## Task 5: Quarterly Recap Page (`pages/1_quarterly_recap.py`)

**Files:**
- Create: `pages/1_quarterly_recap.py`

- [ ] **Step 1: Create `pages/1_quarterly_recap.py`**

```python
import streamlit as st
import plotly.express as px

st.title("Quarterly Recap")
st.caption(
    "**Stakeholders:** JV Country Partners · Merchandisers · Planning Manager  \n"
    "**Decisions:** Channel gap analysis · Division mix review · Buy budget direction · JV partner narrative"
)
st.divider()

sales_df = st.session_state.get("sales_df")
selected_quarter = st.session_state.get("selected_quarter")
selected_countries = st.session_state.get("selected_countries")

if sales_df is None:
    st.warning("Please navigate to the Overview page first to load data.")
    st.stop()

filtered = sales_df[
    (sales_df["quarter"] == selected_quarter)
    & (sales_df["country"].isin(selected_countries))
]

# --- Grouped bar: Sales vs Target by channel ---
channel_summary = (
    filtered.groupby("channel")
    .agg(sales_dollars=("sales_dollars", "sum"), target_dollars=("target_dollars", "sum"))
    .reset_index()
)
fig1 = px.bar(
    channel_summary.melt(
        id_vars="channel",
        value_vars=["sales_dollars", "target_dollars"],
        var_name="Metric",
        value_name="USD",
    ),
    x="channel",
    y="USD",
    color="Metric",
    barmode="group",
    title=f"Sales vs. Target by Channel — {selected_quarter}",
    labels={"USD": "Revenue (USD)", "channel": "Channel"},
    color_discrete_map={"sales_dollars": "#2ca02c", "target_dollars": "#98df8a"},
)
st.plotly_chart(fig1, use_container_width=True)

# --- Stacked bar: Sales by division over all quarters ---
all_filtered = sales_df[sales_df["country"].isin(selected_countries)]
division_trend = (
    all_filtered.groupby(["quarter", "division"])["sales_dollars"]
    .sum()
    .reset_index()
)
fig2 = px.bar(
    division_trend,
    x="quarter",
    y="sales_dollars",
    color="division",
    barmode="stack",
    title="Sales by Division Over Time",
    labels={"sales_dollars": "Revenue (USD)", "quarter": "Quarter"},
)
st.plotly_chart(fig2, use_container_width=True)

# --- Summary table with color-coded variance ---
table = (
    filtered.groupby(["country", "channel"])
    .agg(sales_dollars=("sales_dollars", "sum"), target_dollars=("target_dollars", "sum"))
    .reset_index()
)
table["variance_dollars"] = (table["sales_dollars"] - table["target_dollars"]).round(2)
table["variance_pct"] = ((table["variance_dollars"] / table["target_dollars"]) * 100).round(1)

st.subheader("Country × Channel Summary")


def color_variance(val):
    if isinstance(val, (int, float)):
        return "color: green" if val >= 0 else "color: red"
    return ""


st.dataframe(
    table.style.map(color_variance, subset=["variance_dollars", "variance_pct"]),
    use_container_width=True,
)
```

- [ ] **Step 2: Smoke test**

With the app running, click "1 quarterly recap" in the sidebar.

Expected: Page loads with grouped bar chart, stacked trend chart, and color-coded summary table. Changing the Quarter filter updates all three views.

- [ ] **Step 3: Commit**

```bash
git add pages/1_quarterly_recap.py
git commit -m "feat: add quarterly recap page with channel/division charts and variance table"
```

---

## Task 6: OTB Tracker Page (`pages/2_otb_tracker.py`)

**Files:**
- Create: `pages/2_otb_tracker.py`

- [ ] **Step 1: Create `pages/2_otb_tracker.py`**

```python
import streamlit as st
import plotly.express as px

from utils.metrics import months_of_supply

st.title("OTB Tracker")
st.caption(
    "**Stakeholders:** JV Country Partners · Merchandisers · IT/Systems  \n"
    "**Decisions:** Chase fast sellers · Hold/pull back receipts · Markdown excess inventory · Commitment alignment"
)
st.divider()

otb_df = st.session_state.get("otb_df")
selected_countries = st.session_state.get("selected_countries")

if otb_df is None:
    st.warning("Please navigate to the Overview page first to load data.")
    st.stop()

filtered = otb_df[otb_df["country"].isin(selected_countries)]

# --- Country selector for inventory flow line chart ---
country = st.selectbox("View inventory flow for:", sorted(selected_countries))

country_monthly = (
    filtered[filtered["country"] == country]
    .groupby("month")
    .agg(
        beg_inventory=("beg_inventory", "sum"),
        receipts=("receipts", "sum"),
        sales=("sales", "sum"),
        end_inventory=("end_inventory", "sum"),
    )
    .reset_index()
)
fig1 = px.line(
    country_monthly.melt(
        id_vars="month",
        value_vars=["beg_inventory", "receipts", "sales", "end_inventory"],
        var_name="Metric",
        value_name="Units",
    ),
    x="month",
    y="Units",
    color="Metric",
    title=f"Monthly Inventory Flow — {country}",
    labels={"month": "Month"},
)
st.plotly_chart(fig1, use_container_width=True)

# --- OTB Budget vs Committed vs Open-to-Buy by country ---
otb_summary = (
    filtered.groupby("country")
    .agg(
        otb_budget=("otb_budget", "sum"),
        committed_units=("committed_units", "sum"),
        open_to_buy=("open_to_buy", "sum"),
    )
    .reset_index()
)
fig2 = px.bar(
    otb_summary.melt(
        id_vars="country",
        value_vars=["otb_budget", "committed_units", "open_to_buy"],
        var_name="Category",
        value_name="Units",
    ),
    x="country",
    y="Units",
    color="Category",
    barmode="group",
    title="OTB Budget vs. Committed vs. Open-to-Buy by Country",
    color_discrete_map={
        "otb_budget": "#1f77b4",
        "committed_units": "#ff7f0e",
        "open_to_buy": "#2ca02c",
    },
)
st.plotly_chart(fig2, use_container_width=True)

# --- Months of Supply callout ---
st.subheader("Months of Supply by Channel")
st.caption("Flagged red if > 4 months — signals excess inventory risk")

mos = months_of_supply(filtered)


def highlight_mos(val):
    if isinstance(val, float) and val > 4:
        return "background-color: #ffcccc"
    return ""


st.dataframe(
    mos[["country", "channel", "avg_monthly_sales", "months_of_supply"]]
    .rename(columns={
        "avg_monthly_sales": "Avg Monthly Sales (units)",
        "months_of_supply": "Months of Supply",
    })
    .style.map(highlight_mos, subset=["Months of Supply"]),
    use_container_width=True,
)
```

- [ ] **Step 2: Smoke test**

Click "2 otb tracker" in the sidebar.

Expected: Line chart shows inventory flow for the selected country. Bar chart shows OTB breakdown by country. Months of Supply table highlights rows > 4 in red. Country selector updates the line chart.

- [ ] **Step 3: Commit**

```bash
git add pages/2_otb_tracker.py
git commit -m "feat: add OTB tracker page with inventory flow, buy budget, and months of supply"
```

---

## Task 7: SKU Performance Page (`pages/3_sku_performance.py`)

**Files:**
- Create: `pages/3_sku_performance.py`

- [ ] **Step 1: Create `pages/3_sku_performance.py`**

```python
import streamlit as st
import plotly.express as px

st.title("SKU Performance")
st.caption(
    "**Stakeholders:** Merchandisers · JV Country Partners · Associate Planner  \n"
    "**Decisions:** Chase reorders · Markdown/exit stalling styles · Identify assortment gaps · Next season buy"
)
st.divider()

sku_df = st.session_state.get("sku_df")
selected_countries = st.session_state.get("selected_countries")

if sku_df is None:
    st.warning("Please navigate to the Overview page first to load data.")
    st.stop()

filtered = sku_df[sku_df["country"].isin(selected_countries)].copy()

# --- Page-level filters ---
col1, col2, col3 = st.columns(3)
division_opts = ["All"] + sorted(filtered["division"].unique().tolist())
channel_opts = ["All"] + sorted(filtered["channel"].unique().tolist())
flag_opts = ["All", "Opportunity", "Risk", "On Track"]

division_filter = col1.selectbox("Division", division_opts)
channel_filter = col2.selectbox("Channel", channel_opts)
flag_filter = col3.selectbox("Flag", flag_opts)

if division_filter != "All":
    filtered = filtered[filtered["division"] == division_filter]
if channel_filter != "All":
    filtered = filtered[filtered["channel"] == channel_filter]
if flag_filter != "All":
    filtered = filtered[filtered["flag"] == flag_filter]

# --- Flag display with emoji badges ---
FLAG_ICONS = {"Opportunity": "🟢", "Risk": "🔴", "On Track": "⚪"}
filtered["Flag"] = filtered["flag"].map(FLAG_ICONS) + " " + filtered["flag"]

# --- Sortable SKU detail table ---
st.subheader("SKU Detail")
st.dataframe(
    filtered[
        [
            "style_id", "style_name", "division", "channel", "country",
            "units_sold", "units_on_hand", "sell_through_pct", "weeks_of_supply", "Flag",
        ]
    ]
    .rename(columns={
        "style_id": "Style ID",
        "style_name": "Style Name",
        "sell_through_pct": "ST%",
        "weeks_of_supply": "WOS",
    })
    .sort_values("ST%", ascending=False),
    use_container_width=True,
)

# --- Top 10 / Bottom 10 by sell-through ---
style_summary = (
    filtered.groupby(["style_id", "style_name"])["sell_through_pct"]
    .mean()
    .reset_index()
)
top10 = style_summary.nlargest(10, "sell_through_pct").sort_values("sell_through_pct")
bottom10 = style_summary.nsmallest(10, "sell_through_pct").sort_values(
    "sell_through_pct", ascending=False
)

col_a, col_b = st.columns(2)
with col_a:
    fig1 = px.bar(
        top10,
        x="sell_through_pct",
        y="style_name",
        orientation="h",
        title="Top 10 Styles by Sell-Through %",
        labels={"sell_through_pct": "ST%", "style_name": "Style"},
        color_discrete_sequence=["#2ca02c"],
    )
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    fig2 = px.bar(
        bottom10,
        x="sell_through_pct",
        y="style_name",
        orientation="h",
        title="Bottom 10 Styles by Sell-Through %",
        labels={"sell_through_pct": "ST%", "style_name": "Style"},
        color_discrete_sequence=["#d62728"],
    )
    st.plotly_chart(fig2, use_container_width=True)
```

- [ ] **Step 2: Smoke test**

Click "3 sku performance" in the sidebar.

Expected: Sortable table loads with flag badges. Top/bottom 10 charts appear side by side. Division, Channel, and Flag filters narrow the table and update the charts.

- [ ] **Step 3: Commit**

```bash
git add pages/3_sku_performance.py
git commit -m "feat: add SKU performance page with sell-through table and top/bottom charts"
```

---

## Task 8: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

```markdown
# Skechers International JV Planning Dashboard

A portfolio project demonstrating core Associate Planner capabilities for the Skechers International Joint Venture role.

Built with Python + Streamlit using simulated but realistic data across **3 JV markets** (Japan, Mexico, South Korea), **5 business channels**, and **4 product divisions**.

---

## What This Demonstrates

| Page | Job Description Responsibility |
|---|---|
| **Overview** | "Analyzing country's historical sales and inventory" — cross-market pulse check for leadership |
| **Quarterly Recap** | "Provides constructive analysis of monthly/quarterly recaps at the business channel level by country" |
| **OTB Tracker** | "Maintains in-season data via monthly OTB by reviewing sales, inventory and identifying opportunities and risks" |
| **SKU Performance** | "Identify/react to in-season misses/opportunities at the gender/category/division/style/SKU level" |

---

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd skechers-jv-planner

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

App opens at `http://localhost:8501`.

---

## Run Tests

```bash
pytest tests/ -v
```

---

## Data Note

All data is simulated using seeded NumPy random generators — no real Skechers data is used. Values (AUR, unit volumes, inventory levels) are calibrated to reflect realistic international footwear planning ranges.
```

- [ ] **Step 2: Run the full test suite one final time**

```bash
pytest tests/ -v
```

Expected: All 20 tests PASS.

- [ ] **Step 3: Final smoke test — full app walkthrough**

```bash
streamlit run app.py
```

Verify:
- Overview loads with 4 KPI cards and bar chart
- Quarterly Recap shows channel bars, division trend, and variance table
- OTB Tracker shows inventory flow line, OTB bar chart, and months of supply table (red highlights > 4)
- SKU Performance shows table with flag badges, top/bottom 10 horizontal bars
- Changing Quarter or Country filters on the sidebar updates all pages correctly

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "feat: add README with setup instructions and page-to-role mapping"
```

---

## Self-Review

**Spec coverage check:**
- Overview KPIs + Sales vs Target chart ✅ (app.py)
- Quarterly Recap: channel bars + division trend + variance table ✅ (pages/1)
- OTB: inventory flow + OTB budget/committed/open + months of supply ✅ (pages/2)
- SKU Performance: sortable table + top/bottom 10 + filters ✅ (pages/3)
- Sidebar filters: Quarter + Country multiselect ✅ (app.py)
- Flag logic: Risk (<40% ST or >12 WOS), Opportunity (>75% ST and <4 WOS) ✅ (simulate.py)
- README connecting pages to role ✅ (Task 8)
- All data fields from spec ✅ (simulate.py)

**No placeholders found.**

**Type consistency:** `overview_kpis()` and `months_of_supply()` signatures are consistent between `utils/metrics.py` definition and usage in `app.py` and `pages/2_otb_tracker.py`. `st.session_state` keys (`sales_df`, `otb_df`, `sku_df`, `selected_quarter`, `selected_countries`) are set in `app.py` and read identically in all three pages.
