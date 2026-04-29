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

if otb_df is None or not selected_countries:
    st.warning("Please navigate to the Overview page first to load data and make selections.")
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
country_monthly = country_monthly.rename(columns={
    "beg_inventory": "Beginning Inventory",
    "receipts": "Receipts",
    "sales": "Sales",
    "end_inventory": "End Inventory",
})

fig1 = px.line(
    country_monthly.melt(
        id_vars="month",
        value_vars=["Beginning Inventory", "Receipts", "Sales", "End Inventory"],
        var_name="Metric",
        value_name="Units",
    ),
    x="month",
    y="Units",
    color="Metric",
    title=f"Monthly Inventory Flow — {country}",
    labels={"month": "Month", "Metric": ""},
    color_discrete_map={
        "Beginning Inventory": "#1A1A1A",
        "Receipts": "#6D6E71",
        "Sales": "#16A34A",
        "End Inventory": "#E31837",
    },
)
st.plotly_chart(fig1, width="stretch")

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
otb_summary = otb_summary.rename(columns={
    "otb_budget": "OTB Budget",
    "committed_units": "Committed",
    "open_to_buy": "Open to Buy",
})

fig2 = px.bar(
    otb_summary.melt(
        id_vars="country",
        value_vars=["OTB Budget", "Committed", "Open to Buy"],
        var_name="Category",
        value_name="Units",
    ),
    x="country",
    y="Units",
    color="Category",
    barmode="group",
    title="OTB Budget vs. Committed vs. Open to Buy by Country",
    labels={"Category": "", "country": "Country"},
    color_discrete_map={
        "OTB Budget": "#E31837",
        "Committed": "#F59E0B",
        "Open to Buy": "#16A34A",
    },
)
st.plotly_chart(fig2, width="stretch")

# --- Months of Supply callout ---
st.subheader("Months of Supply by Channel")
st.caption("Flagged red if > 4 months — signals excess inventory risk")

mos = months_of_supply(filtered)


def highlight_mos(val):
    if isinstance(val, float) and not (val != val) and val > 4:
        return "background-color: #fde8ec; color: #E31837"
    return ""


st.dataframe(
    mos[["country", "channel", "avg_monthly_sales", "months_of_supply"]]
    .rename(columns={
        "country": "Country",
        "channel": "Channel",
        "avg_monthly_sales": "Avg Monthly Sales (units)",
        "months_of_supply": "Months of Supply",
    })
    .style
    .format({
        "Avg Monthly Sales (units)": "{:,.0f}",
        "Months of Supply": "{:.1f}",
    })
    .map(highlight_mos, subset=["Months of Supply"]),
    width="stretch",
    hide_index=True,
)
