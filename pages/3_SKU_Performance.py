import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

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

filtered = filtered.copy()

if filtered.empty:
    st.info("No SKUs match the selected filters. Adjust Division, Channel, or Flag.")
    st.stop()

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
        "division": "Division",
        "channel": "Channel",
        "country": "Country",
        "units_sold": "Units Sold",
        "units_on_hand": "Units On Hand",
        "sell_through_pct": "ST%",
        "weeks_of_supply": "WOS",
    })
    .sort_values("ST%", ascending=False),
    width="stretch",
    hide_index=True,
)
st.download_button(
    "Download SKU Detail CSV",
    data=filtered[
        ["style_id", "style_name", "division", "channel", "country",
         "units_sold", "units_on_hand", "sell_through_pct", "weeks_of_supply", "flag"]
    ].to_csv(index=False),
    file_name="sku_detail.csv",
    mime="text/csv",
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
avg_st = style_summary["sell_through_pct"].mean()

col_a, col_b = st.columns(2)
with col_a:
    fig1 = px.bar(
        top10,
        x="sell_through_pct",
        y="style_name",
        orientation="h",
        title="Top 10 Styles by Sell-Through %",
        labels={"sell_through_pct": "ST%", "style_name": "Style"},
        color_discrete_sequence=["#1A1A1A"],
    )
    fig1.update_xaxes(tickformat=".0%")
    fig1.add_vline(x=avg_st, line_dash="dash", line_color="#6D6E71",
                   annotation_text="Avg", annotation_position="top right")
    st.plotly_chart(fig1, width="stretch")

with col_b:
    fig2 = px.bar(
        bottom10,
        x="sell_through_pct",
        y="style_name",
        orientation="h",
        title="Bottom 10 Styles by Sell-Through %",
        labels={"sell_through_pct": "ST%", "style_name": "Style"},
        color_discrete_sequence=["#E31837"],
    )
    fig2.update_xaxes(tickformat=".0%")
    fig2.add_vline(x=avg_st, line_dash="dash", line_color="#6D6E71",
                   annotation_text="Avg", annotation_position="top right")
    st.plotly_chart(fig2, width="stretch")

# --- ST% Heatmap: Country × Division ---
st.subheader("Sell-Through % by Country \u00d7 Division")

heatmap_df = (
    filtered.groupby(["country", "division"])["sell_through_pct"]
    .mean()
    .reset_index()
)
pivot = heatmap_df.pivot(index="country", columns="division", values="sell_through_pct")

division_order = ["Men's Sport", "Women's Sport", "Women's Comfort", "Kids"]
pivot = pivot.reindex(columns=[d for d in division_order if d in pivot.columns])

text_values = [
    [f"{v:.0%}" if v is not None and v == v else "" for v in row]
    for row in pivot.values.tolist()
]

fig_heat = go.Figure(
    go.Heatmap(
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        z=pivot.values.tolist(),
        text=text_values,
        texttemplate="%{text}",
        colorscale=[[0, "#E31837"], [0.575, "#FFFFFF"], [1, "#16A34A"]],
        zmin=0,
        zmax=1,
        hovertemplate="Country: %{y}<br>Division: %{x}<br>ST%%: %{text}<extra></extra>",
    )
)
fig_heat.update_layout(
    xaxis_title="Division",
    yaxis_title="Country",
    height=max(250, len(pivot) * 60),
)
st.plotly_chart(fig_heat, width="stretch")
