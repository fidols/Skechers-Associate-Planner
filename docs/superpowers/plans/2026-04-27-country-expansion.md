# Country Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the JV country set from 3 to 6 using real Skechers (SKX) 10-K data, replacing Japan (a subsidiary) with China, Malaysia, Singapore, and Thailand (all confirmed JV markets).

**Architecture:** Single-file change to `data/simulate.py` — update `COUNTRIES`, `COUNTRY_REGION`, `COUNTRY_VOLUME`, and `BENCHMARK_SOURCE`. The existing `test_country_volume_proportions` test (Wolverine-era) is replaced by two new SKX-anchored tests in `tests/test_simulate.py`. All 16 tests must pass after implementation.

**Tech Stack:** Python, NumPy, pandas, pytest

---

## File Map

| File | Change |
|---|---|
| `data/simulate.py` | Replace `BENCHMARK_SOURCE` comment, `COUNTRIES`, `COUNTRY_REGION`, `COUNTRY_VOLUME` |
| `tests/test_simulate.py` | Replace `test_country_volume_proportions` (lines 90–98) with `test_country_list`; append `test_country_volume_china_largest` |

---

## Task 1: Update tests (TDD — write failing tests first)

**Files:**
- Modify: `tests/test_simulate.py`

- [ ] **Step 1: Replace the Wolverine-era test with `test_country_list`**

Open `tests/test_simulate.py`. Find and replace the entire `test_country_volume_proportions` function (lines 90–98):

```python
# REMOVE this entire function:
def test_country_volume_proportions():
    """Japan should be the largest market, Mexico and South Korea close to equal."""
    from data.simulate import COUNTRY_VOLUME
    assert COUNTRY_VOLUME["Japan"] > COUNTRY_VOLUME["South Korea"]
    assert COUNTRY_VOLUME["Japan"] > COUNTRY_VOLUME["Mexico"]
    # Japan ~1.22, Mexico ~0.96, South Korea ~1.00 per Wolverine APAC/LatAm split
    assert 1.15 <= COUNTRY_VOLUME["Japan"] <= 1.30
    assert 0.85 <= COUNTRY_VOLUME["Mexico"] <= 1.05
    assert 0.90 <= COUNTRY_VOLUME["South Korea"] <= 1.10
```

Replace it with:

```python
def test_country_list():
    """Dashboard should reflect actual Skechers JV countries (SKX 10-K)."""
    from data.simulate import COUNTRIES
    assert "China" in COUNTRIES
    assert "Japan" not in COUNTRIES  # Japan is a wholly-owned subsidiary, not a JV
    assert len(COUNTRIES) == 6
```

- [ ] **Step 2: Append `test_country_volume_china_largest` at the bottom of `tests/test_simulate.py`**

Add this function after `test_channel_aur_values`:

```python
def test_country_volume_china_largest():
    """China is the largest JV market by revenue ($1.22B actual from SKX FY2024 10-K)."""
    from data.simulate import COUNTRY_VOLUME
    assert COUNTRY_VOLUME["China"] == max(COUNTRY_VOLUME.values())
    assert 3.8 <= COUNTRY_VOLUME["China"] <= 4.5
    assert COUNTRY_VOLUME["South Korea"] == 1.0  # baseline
    assert COUNTRY_VOLUME["Singapore"] < COUNTRY_VOLUME["Malaysia"]  # city-state < larger market
```

- [ ] **Step 3: Run the two new tests to confirm they fail**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && python -m pytest tests/test_simulate.py::test_country_list tests/test_simulate.py::test_country_volume_china_largest -v
```

Expected output:
```
FAILED tests/test_simulate.py::test_country_list - AssertionError
FAILED tests/test_simulate.py::test_country_volume_china_largest - KeyError: 'China'
```

`test_country_list` fails because `COUNTRIES` still contains `"Japan"` and has 3 items.
`test_country_volume_china_largest` fails because `COUNTRY_VOLUME` has no `"China"` key.

- [ ] **Step 4: Commit the failing tests**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && git add tests/test_simulate.py && git commit -m "test: replace Wolverine-era test with SKX-anchored country expansion tests (failing)"
```

---

## Task 2: Apply new constants to `data/simulate.py`

**Files:**
- Modify: `data/simulate.py`

- [ ] **Step 1: Replace the entire contents of `data/simulate.py` with the calibrated version**

```python
# =============================================================================
# BENCHMARK SOURCE
# Calibration constants below are anchored to:
#   Skechers U.S.A., Inc. — FY2024 Annual Report (10-K)
#   NYSE: SKX  |  SEC Accession: 0000950170-25-030016  |  Filed: February 2025
#
# JV countries and ownership stakes (directly from 10-K):
#   China, Malaysia, Singapore (50%) | Thailand (51%)
#   Mexico (60%) | South Korea (65%)
#   Note: Japan is a wholly-owned subsidiary — excluded from JV dashboard.
#
# FY2024 Revenue by region:
#   Americas (AMER): $4,367.9M | EMEA: $2,224.4M | APAC: $2,377.1M
#   China (separately disclosed): $1,218.2M
#
# COUNTRY_VOLUME is normalized to South Korea = 1.0 (~$300M estimated baseline).
# China volume is anchored to the actual disclosed figure ($1,218M / $300M = 4.10).
# All other volumes are estimated from regional pools — see spec for derivation:
#   docs/superpowers/specs/2026-04-27-country-expansion-design.md
# =============================================================================

import numpy as np
import pandas as pd

SEED = 42

COUNTRIES = ["China", "Malaysia", "Singapore", "Thailand", "Mexico", "South Korea"]
CHANNELS = ["Normal Retail", "Outlet", "Franchise", "Wholesale", "Ecommerce"]
DIVISIONS = ["Men's Sport", "Women's Sport", "Women's Comfort", "Kids"]
QUARTERS = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025"]

# Maps each JV country to its Skechers geographic segment (SKX 10-K terminology)
COUNTRY_REGION = {
    "China":       "Asia Pacific",
    "Malaysia":    "Asia Pacific",
    "Singapore":   "Asia Pacific",
    "Thailand":    "Asia Pacific",
    "South Korea": "Asia Pacific",
    "Mexico":      "Latin America",
}

# Relative revenue weight per country, normalized to South Korea = 1.0
# China:       $1,218M actual (SKX 10-K) ÷ $300M baseline = 4.10
# South Korea: baseline (~$300M estimated, 65% JV, largest non-China APAC JV)
# Mexico:      ~$290M estimated from AMER international pool ÷ $300M = 0.96
# Malaysia:    ~$144M estimated from APAC ex-China pool ÷ $300M = 0.48
# Thailand:    ~$126M estimated from APAC ex-China pool ÷ $300M = 0.42
# Singapore:   ~$90M estimated (city-state, smaller market) ÷ $300M = 0.30
COUNTRY_VOLUME = {
    "China":       4.10,
    "South Korea": 1.00,
    "Mexico":      0.96,
    "Malaysia":    0.48,
    "Thailand":    0.42,
    "Singapore":   0.30,
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
```

- [ ] **Step 2: Run the two new tests to confirm they now pass**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && python -m pytest tests/test_simulate.py::test_country_list tests/test_simulate.py::test_country_volume_china_largest -v
```

Expected output:
```
PASSED tests/test_simulate.py::test_country_list
PASSED tests/test_simulate.py::test_country_volume_china_largest
```

- [ ] **Step 3: Run the full test suite to confirm no regressions**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && python -m pytest tests/ -v
```

Expected: **15 tests PASSED** (14 existing tests, with `test_country_volume_proportions` replaced 1-for-1 by `test_country_list`, plus `test_country_volume_china_largest` added = 15 total). Zero failures.

If `test_sales_data_positive_values` fails, the COUNTRY_VOLUME values are producing zero units — re-check that all six entries in COUNTRY_VOLUME are > 0.

- [ ] **Step 4: Commit**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && git add data/simulate.py && git commit -m "feat: expand to 6 SKX JV countries, anchor to real 10-K data (China replaces Japan)"
```

- [ ] **Step 5: Push to remote**

```bash
cd /Users/mr.fidols/github/Skechers-Associate-Planner && git push origin main
```

Expected: `main -> main` confirmed.
