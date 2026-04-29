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
# Ending inventory baseline: units currently on hand
baseline["baseline_end_inv"] = baseline["baseline_units_on_hand"].copy()

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

# --- Scenario engine ---
rows = []
for _, row in baseline.iterrows():
    st_adj = st.session_state.get(f"sp_{row['country']}_{row['division']}_st", 0) / 100
    recv_adj = st.session_state.get(f"sp_{row['country']}_{row['division']}_recv", 0) / 100

    scenario_receipts = (row["baseline_units_on_hand"] + row["baseline_units_sold"]) * (1 + recv_adj)
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

total_b_units = scenario_df["_baseline_units_sold"].sum()
total_s_units = scenario_df["_scenario_units_sold"].sum()
avg_st_b = (
    (scenario_df["Baseline ST%"] * scenario_df["_baseline_units_sold"]).sum() / total_b_units
    if total_b_units > 0 else 0.0
)
avg_st_s = (
    (scenario_df["Scenario ST%"] * scenario_df["_scenario_units_sold"]).sum() / total_s_units
    if total_s_units > 0 else 0.0
)
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
