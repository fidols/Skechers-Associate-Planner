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

if sku_df is None or not selected_countries:
    st.warning("Please navigate to the Overview page first to load data and make selections.")
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
