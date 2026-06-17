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
selected_divisions = st.session_state.get("selected_divisions", [])

if sales_df is None or selected_quarter is None or selected_countries is None:
    st.warning("Please navigate to the Overview page first to load data and make selections.")
    st.stop()

filtered = sales_df[
    (sales_df["quarter"] == selected_quarter)
    & (sales_df["country"].isin(selected_countries))
    & (sales_df["division"].isin(selected_divisions) if selected_divisions else True)
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
    color_discrete_map={"Actual Sales": "#2563EB", "Target": "#16A34A"},
)
fig1.update_yaxes(tickprefix="$", tickformat="~s")
st.plotly_chart(fig1, width="stretch")

# --- Stacked bar: Sales by division over all quarters ---
all_filtered = sales_df[
    sales_df["country"].isin(selected_countries)
    & (sales_df["division"].isin(selected_divisions) if selected_divisions else True)
]
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
    color_discrete_map={
        "Kids":             "#2563EB",
        "Men's Sport":      "#E31837",
        "Women's Comfort":  "#F59E0B",
        "Women's Sport":    "#7C3AED",
    },
)
fig2.update_yaxes(tickprefix="$", tickformat="~s")
st.plotly_chart(fig2, width="stretch")

# --- AUR by Channel ---
aur_by_channel = (
    filtered.groupby("channel")["AUR"]
    .mean()
    .round(2)
    .reset_index()
    .sort_values("AUR", ascending=False)
)
fig3 = px.bar(
    aur_by_channel,
    x="channel",
    y="AUR",
    title=f"Average Unit Retail (AUR) by Channel — {selected_quarter}",
    labels={"channel": "Channel", "AUR": "Avg Unit Retail (USD)"},
    text="AUR",
    color_discrete_sequence=["#2563EB"],
)
fig3.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
fig3.update_yaxes(tickprefix="$")
fig3.update_layout(margin=dict(t=50, b=40))
st.plotly_chart(fig3, width="stretch")

# --- Summary table with color-coded variance ---
table = (
    filtered.groupby(["country", "channel"])
    .agg(
        sales_dollars=("sales_dollars", "sum"),
        target_dollars=("target_dollars", "sum"),
        avg_aur=("AUR", "mean"),
    )
    .reset_index()
)
table["variance_dollars"] = (table["sales_dollars"] - table["target_dollars"]).round(2)
table["variance_pct"] = ((table["variance_dollars"] / table["target_dollars"]) * 100).round(1)
table["avg_aur"] = table["avg_aur"].round(2)

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
    "avg_aur": "Avg AUR ($)",
})

st.dataframe(
    table.style
    .format({
        "Sales ($)": "${:,.0f}",
        "Target ($)": "${:,.0f}",
        "Variance ($)": "${:+,.0f}",
        "Variance %": "{:+.1f}%",
        "Avg AUR ($)": "${:.2f}",
    })
    .map(color_variance, subset=["Variance ($)", "Variance %"]),
    width="stretch",
    hide_index=True,
)
st.download_button(
    "Download Summary CSV",
    data=table.to_csv(index=False),
    file_name=f"quarterly_recap_{selected_quarter.replace(' ', '_')}.csv",
    mime="text/csv",
)
