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
quarters = sorted(
    sales_df["quarter"].unique().tolist(),
    key=lambda q: (int(q.split()[1]), int(q.split()[0][1])),
)
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

# QoQ delta for Total Sales
prev_idx = quarters.index(selected_quarter) - 1
sales_delta_str = None
if prev_idx >= 0:
    prev_quarter = quarters[prev_idx]
    prev_sales = sales_df[
        (sales_df["quarter"] == prev_quarter)
        & (sales_df["country"].isin(selected_countries))
    ]
    prev_kpis = overview_kpis(prev_sales, filtered_otb, filtered_sku)
    sales_delta = kpis["total_sales_dollars"] - prev_kpis["total_sales_dollars"]
    if abs(sales_delta) >= 1e6:
        sales_delta_str = f"${sales_delta/1e6:+.1f}M vs {prev_quarter}"
    else:
        sales_delta_str = f"${sales_delta:+,.0f} vs {prev_quarter}"

col1, col2, col3, col4 = st.columns(4)
total_sales = kpis["total_sales_dollars"]
sales_display = f"${total_sales/1e6:.1f}M" if total_sales >= 1e6 else f"${total_sales:,.0f}"
col1.metric("Total Sales", sales_display, delta=sales_delta_str)
col2.metric("Sell-Through", f"{kpis['sell_through_pct'] * 100:.1f}%")
col3.metric("Avg OTB Remaining (units)", f"{kpis['avg_otb_remaining']:,.0f}")
col4.metric("Risk SKUs", f"{kpis['risk_sku_count']:,}")

# --- Sales vs Target by country ---
country_summary = (
    filtered_sales.groupby("country")
    .agg(sales_dollars=("sales_dollars", "sum"), target_dollars=("target_dollars", "sum"))
    .reset_index()
)
country_summary["Actual Sales"] = country_summary["sales_dollars"]
country_summary["Target"] = country_summary["target_dollars"]

fig = px.bar(
    country_summary.melt(
        id_vars="country",
        value_vars=["Actual Sales", "Target"],
        var_name="Metric",
        value_name="USD",
    ),
    x="country",
    y="USD",
    color="Metric",
    barmode="group",
    title=f"Sales vs. Target by Country — {selected_quarter}",
    labels={"USD": "Revenue (USD)", "country": "Country", "Metric": ""},
    color_discrete_map={"Actual Sales": "#2563EB", "Target": "#16A34A"},
)
fig.update_yaxes(tickprefix="$", tickformat="~s")
st.plotly_chart(fig, width="stretch")

# --- Country snapshot ---
st.subheader("Country Snapshot")

sales_snap = (
    filtered_sales.groupby("country")
    .agg(sales_dollars=("sales_dollars", "sum"), target_dollars=("target_dollars", "sum"))
    .reset_index()
)
sku_snap = (
    filtered_sku.groupby("country")
    .agg(
        units_sold=("units_sold", "sum"),
        units_on_hand=("units_on_hand", "sum"),
        risk_skus=("flag", lambda x: (x == "Risk").sum()),
    )
    .reset_index()
)
sku_snap["sell_through_pct"] = sku_snap["units_sold"] / (
    sku_snap["units_sold"] + sku_snap["units_on_hand"]
)
otb_snap = (
    filtered_otb.groupby("country")
    .agg(otb_budget=("otb_budget", "sum"), committed_units=("committed_units", "sum"))
    .reset_index()
)
otb_snap["otb_util_pct"] = otb_snap["committed_units"] / otb_snap["otb_budget"]

snap = sales_snap.merge(
    sku_snap[["country", "sell_through_pct", "risk_skus"]], on="country", how="left"
).merge(otb_snap[["country", "otb_util_pct"]], on="country", how="left")
snap["vs_target"] = (snap["sales_dollars"] - snap["target_dollars"]) / snap["target_dollars"]

snap = snap.rename(columns={
    "country": "Country",
    "sales_dollars": "Sales ($)",
    "vs_target": "vs Target",
    "sell_through_pct": "ST%",
    "risk_skus": "Risk SKUs",
    "otb_util_pct": "OTB Util%",
})


def _color_vs_target(val):
    if isinstance(val, float) and val == val:
        return "color: #16A34A" if val >= 0 else "color: #E31837"
    return ""


st.dataframe(
    snap[["Country", "Sales ($)", "vs Target", "ST%", "Risk SKUs", "OTB Util%"]]
    .style
    .format({
        "Sales ($)": "${:,.0f}",
        "vs Target": "{:+.1%}",
        "ST%": "{:.1%}",
        "Risk SKUs": "{:,.0f}",
        "OTB Util%": "{:.1%}",
    })
    .map(_color_vs_target, subset=["vs Target"]),
    hide_index=True,
    width="stretch",
)
