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
