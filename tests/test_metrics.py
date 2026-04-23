import pandas as pd
import pytest
from utils.metrics import overview_kpis, months_of_supply


def make_sales_df():
    return pd.DataFrame({
        "sales_dollars": [100.0, 200.0],
        "target_dollars": [150.0, 180.0],
    })


def make_otb_df():
    return pd.DataFrame({
        "country": ["Japan", "Japan"],
        "channel": ["Normal Retail", "Outlet"],
        "open_to_buy": [1000, 2000],
        "sales": [500, 400],
        "end_inventory": [3000, 2000],
        "beg_inventory": [4000, 3000],
        "receipts": [500, 400],
        "otb_budget": [1500, 2500],
        "committed_units": [500, 500],
        "month": pd.to_datetime(["2024-01-01", "2024-01-01"]),
    })


def make_sku_df():
    return pd.DataFrame({
        "units_sold": [80, 20],
        "units_on_hand": [20, 80],
        "flag": ["Opportunity", "Risk"],
    })


def test_overview_kpis_total_sales():
    kpis = overview_kpis(make_sales_df(), make_otb_df(), make_sku_df())
    assert kpis["total_sales_dollars"] == 300.0


def test_overview_kpis_sell_through():
    kpis = overview_kpis(make_sales_df(), make_otb_df(), make_sku_df())
    # (80 + 20) / (80 + 20 + 20 + 80) = 100 / 200 = 0.5
    assert kpis["sell_through_pct"] == 0.5


def test_overview_kpis_avg_otb():
    kpis = overview_kpis(make_sales_df(), make_otb_df(), make_sku_df())
    # mean([1000, 2000]) = 1500
    assert kpis["avg_otb_remaining"] == 1500.0


def test_overview_kpis_risk_count():
    kpis = overview_kpis(make_sales_df(), make_otb_df(), make_sku_df())
    assert kpis["risk_sku_count"] == 1


def test_months_of_supply_columns():
    mos = months_of_supply(make_otb_df())
    assert "months_of_supply" in mos.columns
    assert "country" in mos.columns
    assert "channel" in mos.columns


def test_months_of_supply_positive():
    mos = months_of_supply(make_otb_df())
    assert (mos["months_of_supply"] >= 0).all()


def test_months_of_supply_correctness():
    mos = months_of_supply(make_otb_df())
    japan_retail = mos[(mos["country"] == "Japan") & (mos["channel"] == "Normal Retail")]
    # avg_monthly_sales=500, avg_end_inventory=3000 → 3000/500 = 6.0
    assert japan_retail["months_of_supply"].iloc[0] == 6.0


def test_months_of_supply_zero_sales_returns_nan():
    df = pd.DataFrame({
        "country": ["Japan"],
        "channel": ["Normal Retail"],
        "sales": [0],
        "end_inventory": [1000],
    })
    mos = months_of_supply(df)
    import math
    assert math.isnan(mos["months_of_supply"].iloc[0])
