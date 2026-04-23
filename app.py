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
quarters = sorted(sales_df["quarter"].unique().tolist())
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
