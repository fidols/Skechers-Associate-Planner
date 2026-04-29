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

# Used by slider panel (Task 3) and scenario engine (Task 4)
DIVISIONS = ["Men's Sport", "Women's Sport", "Women's Comfort", "Kids"]

# --- Baseline: aggregate sku_df by country × division ---
baseline_sku = (
    sku_df[sku_df["country"].isin(selected_countries)]
    .groupby(["country", "division"])
    .agg(
        baseline_units_on_hand=("units_on_hand", "sum"),
        baseline_units_sold=("units_sold", "sum"),
    )
    .reset_index()
)
baseline_sku["baseline_st_pct"] = (
    baseline_sku["baseline_units_sold"]
    / (baseline_sku["baseline_units_sold"] + baseline_sku["baseline_units_on_hand"])
)

# --- Baseline revenue from sales_df (all quarters summed — consistent baseline for relative comparison) ---
baseline_rev = (
    sales_df[sales_df["country"].isin(selected_countries)]
    .groupby(["country", "division"])
    .agg(baseline_revenue=("sales_dollars", "sum"))
    .reset_index()
)

baseline = baseline_sku.merge(baseline_rev, on=["country", "division"], how="left")
# Proxy: fraction of current on-hand stock that hasn't sold through yet
baseline["baseline_end_inv"] = (
    baseline["baseline_units_on_hand"] * (1 - baseline["baseline_st_pct"])
)

# --- Reset button ---
if st.button("Reset All"):
    for country in selected_countries:
        for division in DIVISIONS:
            st.session_state[f"sp_{country}_{division}_st"] = 0
            st.session_state[f"sp_{country}_{division}_recv"] = 0
    st.rerun()

st.subheader("Adjust Assumptions")

# Initialize missing slider keys to 0 (handles country re-selection edge case)
for country in selected_countries:
    for division in DIVISIONS:
        for suffix in ("_st", "_recv"):
            key = f"sp_{country}_{division}{suffix}"
            if key not in st.session_state:
                st.session_state[key] = 0

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
