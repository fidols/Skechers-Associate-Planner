import pandas as pd


def overview_kpis(
    sales_df: pd.DataFrame,
    otb_df: pd.DataFrame,
    sku_df: pd.DataFrame,
) -> dict:
    """
    Returns top-level KPIs for the Overview page.

    Keys:
        total_sales_dollars: float
        sell_through_pct: float (0–1)
        avg_otb_remaining: float (units)
        risk_sku_count: int
    """
    total_sales = sales_df["sales_dollars"].sum()
    total_sold = sku_df["units_sold"].sum()
    total_available = total_sold + sku_df["units_on_hand"].sum()
    sell_through = total_sold / total_available if total_available > 0 else 0.0
    avg_otb = otb_df["open_to_buy"].mean()
    risk_count = int((sku_df["flag"] == "Risk").sum())
    return {
        "total_sales_dollars": round(float(total_sales), 2),
        "sell_through_pct": round(float(sell_through), 3),
        "avg_otb_remaining": round(float(avg_otb), 0),
        "risk_sku_count": risk_count,
    }


def months_of_supply(otb_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns avg monthly sales, avg end inventory, and months of supply
    per country/channel combination.
    """
    agg = (
        otb_df.groupby(["country", "channel"])
        .agg(
            avg_monthly_sales=("sales", "mean"),
            avg_end_inventory=("end_inventory", "mean"),
        )
        .reset_index()
    )
    agg["months_of_supply"] = (
        agg["avg_end_inventory"] / agg["avg_monthly_sales"].replace(0, float("nan"))
    ).round(1)
    return agg
