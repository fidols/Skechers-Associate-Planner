import math

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

if sales_df is None or selected_quarter is None or selected_countries is None:
    st.warning("Please navigate to the Overview page first to load data and make selections.")
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
channel_summary["Actual Sales"] = channel_summary["sales_dollars"]
channel_summary["Target"] = channel_summary["target_dollars"]

fig1 = px.bar(
    channel_summary.melt(
        id_vars="channel",
        value_vars=["Actual Sales", "Target"],
        var_name="Metric",
        value_name="USD",
    ),
    x="channel",
    y="USD",
    color="Metric",
    barmode="group",
    title=f"Sales vs. Target by Channel — {selected_quarter}",
    labels={"USD": "Revenue (USD)", "channel": "Channel", "Metric": ""},
    color_discrete_map={"Actual Sales": "#1A1A1A", "Target": "#A7A9AC"},
)
fig1.update_yaxes(tickprefix="$", tickformat="~s")
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
    labels={"sales_dollars": "Revenue (USD)", "quarter": "Quarter", "division": "Division"},
    color_discrete_sequence=["#1A1A1A", "#E31837", "#6D6E71", "#A7A9AC"],
)
fig2.update_yaxes(tickprefix="$", tickformat="~s")
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
    if isinstance(val, (int, float)) and not math.isnan(val):
        return "color: #1A1A1A" if val >= 0 else "color: #E31837"
    return ""


table = table.rename(columns={
    "country": "Country",
    "channel": "Channel",
    "sales_dollars": "Sales ($)",
    "target_dollars": "Target ($)",
    "variance_dollars": "Variance ($)",
    "variance_pct": "Variance %",
})

st.dataframe(
    table.style
    .format({
        "Sales ($)": "${:,.0f}",
        "Target ($)": "${:,.0f}",
        "Variance ($)": "${:+,.0f}",
        "Variance %": "{:+.1f}%",
    })
    .map(color_variance, subset=["Variance ($)", "Variance %"]),
    use_container_width=True,
    hide_index=True,
)
