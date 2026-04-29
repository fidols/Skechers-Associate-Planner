import streamlit as st
from utils.buy_recommendation import compute_buy_recommendations

st.title("Buy Recommendation")
st.caption(
    "**Stakeholders:** Associate Planner · Merchandisers · JV Country Partners  \n"
    "**Decisions:** Next season buy quantities · Chase reorders · Inventory reduction targets"
)
st.divider()

sku_df = st.session_state.get("sku_df")
selected_countries = st.session_state.get("selected_countries")

if sku_df is None or not selected_countries:
    st.warning("Please navigate to the Overview page first to load data and make selections.")
    st.stop()

# --- Inputs ---
target_wos = st.slider(
    "Target Weeks of Supply",
    min_value=4,
    max_value=16,
    value=8,
    step=1,
    format="%d wks",
)

col1, col2 = st.columns(2)
division_opts = ["All"] + sorted(sku_df["division"].unique().tolist())
channel_opts = ["All"] + sorted(sku_df["channel"].unique().tolist())
division_filter = col1.selectbox("Division", division_opts)
channel_filter = col2.selectbox("Channel", channel_opts)

# --- Compute recommendations ---
recs = compute_buy_recommendations(sku_df, selected_countries, target_wos)

# Apply page-level filters for display
if division_filter != "All":
    recs = recs[recs["division"] == division_filter]
if channel_filter != "All":
    recs = recs[recs["channel"] == channel_filter]

if recs.empty:
    st.info("No data matches the selected filters.")
    st.stop()
