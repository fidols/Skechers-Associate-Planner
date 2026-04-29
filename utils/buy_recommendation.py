import pandas as pd


def compute_buy_recommendations(
    sku_df: pd.DataFrame,
    selected_countries: list,
    target_wos: float,
) -> pd.DataFrame:
    """Aggregate sku_df by division × channel and recommend buy quantities.

    Returns a DataFrame with columns:
        division, channel, units_on_hand, avg_weekly_sales,
        current_wos, recommended_buy, action
    """
    filtered = sku_df[sku_df["country"].isin(selected_countries)]
    agg = (
        filtered
        .groupby(["division", "channel"])
        .agg(
            units_on_hand=("units_on_hand", "sum"),
            avg_weekly_sales=("avg_weekly_sales", "sum"),
        )
        .reset_index()
    )
    agg["avg_weekly_sales"] = agg["avg_weekly_sales"].replace(0, float("nan"))
    agg["current_wos"] = agg["units_on_hand"] / agg["avg_weekly_sales"]
    agg["recommended_buy"] = (
        ((target_wos - agg["current_wos"]) * agg["avg_weekly_sales"])
        .fillna(0)
        .clip(lower=0)
        .round()
        .astype(int)
    )
    agg["action"] = agg["current_wos"].apply(
        lambda wos: (
            "No Data" if wos != wos  # NaN check
            else "Chase" if wos < target_wos * 0.75
            else "Reduce" if wos >= target_wos * 1.25
            else "On Plan"
        )
    )
    return agg
