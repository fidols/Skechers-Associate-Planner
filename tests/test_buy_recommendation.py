import pandas as pd
import pytest
from utils.buy_recommendation import compute_buy_recommendations


def _make_sku_df(units_on_hand, avg_weekly_sales, country="China", division="Men's Sport", channel="Normal Retail"):
    return pd.DataFrame([{
        "country": country,
        "division": division,
        "channel": channel,
        "units_on_hand": units_on_hand,
        "avg_weekly_sales": avg_weekly_sales,
    }])


def test_chase_flag_when_wos_below_75pct_of_target():
    # current_wos = 100 / 20 = 5.0, target = 8, threshold = 6.0 → Chase
    df = _make_sku_df(units_on_hand=100, avg_weekly_sales=20)
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    assert result.iloc[0]["action"] == "Chase"


def test_reduce_flag_when_wos_above_125pct_of_target():
    # current_wos = 200 / 15 ≈ 13.3, target = 8, threshold = 10.0 → Reduce
    df = _make_sku_df(units_on_hand=200, avg_weekly_sales=15)
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    assert result.iloc[0]["action"] == "Reduce"


def test_on_plan_flag_within_range():
    # current_wos = 70 / 10 = 7.0, target = 8, range [6.0, 10.0] → On Plan
    df = _make_sku_df(units_on_hand=70, avg_weekly_sales=10)
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    assert result.iloc[0]["action"] == "On Plan"


def test_recommended_buy_correct_units():
    # current_wos = 50 / 20 = 2.5, target = 8 → buy = (8 - 2.5) * 20 = 110
    df = _make_sku_df(units_on_hand=50, avg_weekly_sales=20)
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    assert result.iloc[0]["recommended_buy"] == 110


def test_recommended_buy_is_zero_when_wos_at_or_above_target():
    # current_wos = 200 / 20 = 10.0 >= 8 → buy = 0
    df = _make_sku_df(units_on_hand=200, avg_weekly_sales=20)
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    assert result.iloc[0]["recommended_buy"] == 0


def test_filters_by_selected_countries():
    df = pd.DataFrame([
        {"country": "China",    "division": "Kids", "channel": "Outlet", "units_on_hand": 100, "avg_weekly_sales": 10},
        {"country": "Mexico",   "division": "Kids", "channel": "Outlet", "units_on_hand": 200, "avg_weekly_sales": 10},
    ])
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    # Only China row: units_on_hand=100, wos=10 → Reduce
    assert len(result) == 1
    assert result.iloc[0]["action"] == "Reduce"


def test_aggregates_multiple_skus_in_same_division_channel():
    df = pd.DataFrame([
        {"country": "China", "division": "Kids", "channel": "Outlet", "units_on_hand": 30, "avg_weekly_sales": 5},
        {"country": "China", "division": "Kids", "channel": "Outlet", "units_on_hand": 20, "avg_weekly_sales": 5},
    ])
    # Combined: units_on_hand=50, avg_weekly_sales=10, wos=5.0, target=8
    # buy = (8 - 5) * 10 = 30
    result = compute_buy_recommendations(df, ["China"], target_wos=8)
    assert len(result) == 1
    assert result.iloc[0]["recommended_buy"] == 30
