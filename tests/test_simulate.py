import pandas as pd
import pytest
from data.simulate import (
    generate_sales_data, generate_otb_data, generate_sku_data,
    COUNTRIES, CHANNELS, DIVISIONS, QUARTERS,
)


def test_sales_data_columns():
    df = generate_sales_data()
    expected = {
        "country", "channel", "division", "quarter",
        "sales_units", "sales_dollars", "target_units", "target_dollars",
        "AUR", "discount_pct",
    }
    assert expected.issubset(set(df.columns))


def test_sales_data_no_nulls():
    df = generate_sales_data()
    assert df.isnull().sum().sum() == 0


def test_sales_data_countries():
    df = generate_sales_data()
    assert set(df["country"].unique()) == set(COUNTRIES)


def test_sales_data_positive_values():
    df = generate_sales_data()
    assert (df["sales_units"] > 0).all()
    assert (df["sales_dollars"] > 0).all()
    assert (df["AUR"] > 0).all()


def test_sales_data_discount_range():
    df = generate_sales_data()
    assert (df["discount_pct"] >= 0).all()
    assert (df["discount_pct"] <= 1).all()


def test_otb_data_columns():
    df = generate_otb_data()
    expected = {
        "month", "country", "channel", "beg_inventory", "receipts", "sales",
        "end_inventory", "otb_budget", "committed_units", "open_to_buy",
    }
    assert expected.issubset(set(df.columns))


def test_otb_end_inventory_derived():
    df = generate_otb_data()
    computed = df["beg_inventory"] + df["receipts"] - df["sales"]
    pd.testing.assert_series_equal(computed, df["end_inventory"], check_names=False)


def test_otb_open_to_buy_derived():
    df = generate_otb_data()
    computed = df["otb_budget"] - df["committed_units"]
    pd.testing.assert_series_equal(computed, df["open_to_buy"], check_names=False)


def test_sku_data_columns():
    df = generate_sku_data()
    expected = {
        "style_id", "style_name", "division", "country", "channel",
        "units_sold", "units_on_hand", "avg_weekly_sales",
        "weeks_of_supply", "sell_through_pct", "flag",
    }
    assert expected.issubset(set(df.columns))


def test_sku_sell_through_range():
    df = generate_sku_data()
    assert (df["sell_through_pct"] >= 0).all()
    assert (df["sell_through_pct"] <= 1).all()


def test_sku_flag_values():
    df = generate_sku_data()
    assert set(df["flag"].unique()).issubset({"Opportunity", "Risk", "On Track"})


def test_sku_flag_logic_risk():
    df = generate_sku_data()
    risk = df[df["flag"] == "Risk"]
    assert ((risk["sell_through_pct"] < 0.40) | (risk["weeks_of_supply"] > 12)).all()


def test_sku_flag_logic_opportunity():
    df = generate_sku_data()
    opp = df[df["flag"] == "Opportunity"]
    assert ((opp["sell_through_pct"] > 0.75) & (opp["weeks_of_supply"] < 4)).all()
