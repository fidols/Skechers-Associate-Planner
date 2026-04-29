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

# --- Metric cards ---
st.divider()
total_buy = int(recs["recommended_buy"].sum())
n_chase = int((recs["action"] == "Chase").sum())
n_reduce = int((recs["action"] == "Reduce").sum())

c1, c2, c3 = st.columns(3)
c1.metric("Total Rec. Buy Units", f"{total_buy:,}")
c2.metric("Chase", f"{n_chase}")
c3.metric("Reduce", f"{n_reduce}")

# --- Recommendation table ---
st.subheader("Recommendation by Division × Channel")

ACTION_COLORS = {"Chase": "color: #16A34A", "Reduce": "color: #E31837", "On Plan": ""}


def _color_action(val):
    return ACTION_COLORS.get(val, "")


display = recs.rename(columns={
    "division": "Division",
    "channel": "Channel",
    "current_wos": "Current WOS",
    "recommended_buy": "Rec. Buy Units",
    "action": "Action",
}).drop(columns=["units_on_hand", "avg_weekly_sales"])

display.insert(2, "Target WOS", target_wos)

st.dataframe(
    display.style
    .format({
        "Current WOS": "{:.1f}",
        "Target WOS": "{:.0f}",
        "Rec. Buy Units": "{:,}",
    })
    .map(_color_action, subset=["Action"]),
    hide_index=True,
    width="stretch",
)
st.download_button(
    "Download Recommendations CSV",
    data=display.to_csv(index=False),
    file_name="buy_recommendations.csv",
    mime="text/csv",
)
