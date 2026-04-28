# =============================================================================
# BENCHMARK SOURCE
# Calibration constants below are anchored to:
#   Wolverine World Wide, Inc. — FY2025 Annual Report (10-K)
#   SEC Accession: 0001628280-26-012614  |  Filed: January 2026
#
# Geographic revenue used for COUNTRY_VOLUME proportions:
#   Asia Pacific:   $181.7M (+20.4% YoY)  — proxy for Japan + South Korea
#   Latin America:  $111.7M (+13.4% YoY)  — proxy for Mexico
#
# Channel AURs reflect published benchmarks for mid-tier lifestyle/athletic
# footwear brands operating in JV wholesale + DTC markets.
# =============================================================================

import numpy as np
import pandas as pd

SEED = 42

COUNTRIES = ["Japan", "Mexico", "South Korea"]
CHANNELS = ["Normal Retail", "Outlet", "Franchise", "Wholesale", "Ecommerce"]
DIVISIONS = ["Men's Sport", "Women's Sport", "Women's Comfort", "Kids"]
QUARTERS = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025"]

# Maps each JV country to its Wolverine geographic segment
COUNTRY_REGION = {
    "Japan":       "Asia Pacific",
    "South Korea": "Asia Pacific",
    "Mexico":      "Latin America",
}

# Relative revenue weight per country, normalized to South Korea = 1.0
# Derived from Wolverine APAC ($181.7M): Japan ~55%, South Korea ~45%
# Derived from Wolverine LatAm ($111.7M): Mexico ~70%
# Japan:       $99.9M / $81.8M = 1.22
# Mexico:      $78.2M / $81.8M = 0.96
# South Korea: $81.8M / $81.8M = 1.00
COUNTRY_VOLUME = {
    "Japan":       1.22,
    "Mexico":      0.96,
    "South Korea": 1.00,
}

# Average Unit Retail by channel — calibrated to footwear industry benchmarks
CHANNEL_AUR = {
    "Normal Retail": 82,
    "Outlet":        52,
    "Franchise":     76,
    "Wholesale":     45,
    "Ecommerce":     78,
}

STYLE_NAMES = [
    "Arch Fit Comfy", "D'Lites Retro", "Go Walk 7", "Relaxed Fit Summits",
    "Max Cushioning Premier", "Skech-Air Element", "Equalizer 5", "Flex Advantage 4",
    "Go Run Consistent", "Summits Air Dazzle", "Bobs B-Cool", "Uno Stand On Air",
    "Glide Step Sport", "Dynamight 2", "Squad SR", "Gratis", "Work: Sure Track",
    "Arch Fit AD", "Slip-Ins Summits", "Foamies Creston Ultra",
]


def generate_sales_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows = []
    for country in COUNTRIES:
        for channel in CHANNELS:
            for division in DIVISIONS:
                for quarter in QUARTERS:
                    base_units = int(rng.integers(2500, 7000) * COUNTRY_VOLUME[country])
                    target_units = int(base_units * rng.uniform(0.9, 1.15))
                    aur = CHANNEL_AUR[channel] * rng.uniform(0.9, 1.1)
                    sales_dollars = round(base_units * aur, 2)
                    target_dollars = round(target_units * aur, 2)
                    rows.append({
                        "country":        country,
                        "channel":        channel,
                        "division":       division,
                        "quarter":        quarter,
                        "sales_units":    base_units,
                        "sales_dollars":  sales_dollars,
                        "target_units":   target_units,
                        "target_dollars": target_dollars,
                        "AUR":            round(aur, 2),
                    })
    return pd.DataFrame(rows)


def generate_otb_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 1)
    months = pd.date_range("2024-01-01", "2025-03-01", freq="MS")
    rows = []
    for country in COUNTRIES:
        for channel in CHANNELS:
            beg_inv = int(rng.integers(5000, 15000) * COUNTRY_VOLUME[country])
            for month in months:
                receipts = int(rng.integers(1000, 5000) * COUNTRY_VOLUME[country])
                max_sales = max(beg_inv + receipts - 50, 1)
                sales = int(min(rng.integers(800, 4500) * COUNTRY_VOLUME[country], max_sales))
                end_inv = beg_inv + receipts - sales
                otb_budget = int(rng.integers(2000, 6000) * COUNTRY_VOLUME[country])
                committed = int(otb_budget * rng.uniform(0.5, 0.95))
                rows.append({
                    "month":           month,
                    "country":         country,
                    "channel":         channel,
                    "beg_inventory":   beg_inv,
                    "receipts":        receipts,
                    "sales":           sales,
                    "end_inventory":   end_inv,
                    "otb_budget":      otb_budget,
                    "committed_units": committed,
                    "open_to_buy":     otb_budget - committed,
                })
                beg_inv = end_inv
    return pd.DataFrame(rows)


def generate_sku_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 2)
    style_pool = [
        (f"SK-{1000 + i}", STYLE_NAMES[i % len(STYLE_NAMES)], DIVISIONS[i % len(DIVISIONS)])
        for i in range(40)
    ]
    rows = []
    for style_id, style_name, division in style_pool:
        for country in COUNTRIES:
            for channel in CHANNELS:
                units_sold = int(rng.integers(50, 600))
                units_on_hand = int(rng.integers(20, 400))
                avg_weekly = round(float(rng.uniform(5, 50)), 1)
                weeks_of_supply = round(units_on_hand / avg_weekly, 1)
                sell_through = round(units_sold / (units_sold + units_on_hand), 3)
                if sell_through < 0.40 or weeks_of_supply > 12:
                    flag = "Risk"
                elif sell_through > 0.75 and weeks_of_supply < 4:
                    flag = "Opportunity"
                else:
                    flag = "On Track"
                rows.append({
                    "style_id":         style_id,
                    "style_name":       style_name,
                    "division":         division,
                    "country":          country,
                    "channel":          channel,
                    "units_sold":       units_sold,
                    "units_on_hand":    units_on_hand,
                    "avg_weekly_sales": avg_weekly,
                    "weeks_of_supply":  weeks_of_supply,
                    "sell_through_pct": sell_through,
                    "flag":             flag,
                })
    return pd.DataFrame(rows)
