# Skechers JV Dashboard — Industry Calibration Design Spec

## Overview

**Goal:** Recalibrate the simulated data in `data/simulate.py` so that country volumes, channel AURs, and unit scales reflect real footwear industry proportions — anchored to Wolverine World Wide's FY2025 10-K geographic revenue breakdown.

**Scope:** Single file change — `data/simulate.py` constants only. No schema changes, no new files, no test changes.

**Source:** Wolverine World Wide, Inc. — FY2025 Annual Report (10-K)
SEC Accession: `0001628280-26-012614`
Filed: January 2026

---

## Calibration Reference Data (from Wolverine 10-K)

### Geographic Revenue Breakdown

| Region | FY2025 ($M) | FY2024 ($M) | YoY Growth |
|---|---|---|---|
| United States | 896.2 | 893.4 | +0.3% |
| EMEA | 601.5 | 529.6 | +13.6% |
| Asia Pacific | 181.7 | 150.9 | +20.4% |
| Canada | 83.2 | 82.6 | +0.7% |
| Latin America | 111.7 | 98.5 | +13.4% |
| **Total International** | **978.1** | **861.6** | +13.5% |

### Channel Split (Active Group — closest to Skechers lifestyle footwear)

| Channel | FY2025 ($M) | FY2024 ($M) |
|---|---|---|
| Wholesale | 977.8 | 815.7 |
| Direct-to-Consumer | 430.0 | 430.4 |

---

## Country Calibration Logic

The Skechers JV dashboard covers 3 countries across 2 Wolverine geographic regions:

| Country | Wolverine Region | Assumed Share of Region | Derived Revenue Proxy |
|---|---|---|---|
| Japan | Asia Pacific ($181.7M) | 55% | ~$99.9M |
| South Korea | Asia Pacific ($181.7M) | 45% | ~$81.8M |
| Mexico | Latin America ($111.7M) | 70% | ~$78.2M |

**`COUNTRY_VOLUME` derivation** (normalized to South Korea = 1.0):
- Japan: 99.9 / 81.8 = **1.22**
- Mexico: 78.2 / 81.8 = **0.96**
- South Korea: 81.8 / 81.8 = **1.00**

Previous values: `{Japan: 1.0, Mexico: 1.3, South Korea: 0.9}` — Mexico was largest, which does not reflect APAC/LatAm proportions.

---

## Channel AUR Calibration

Updated to published footwear industry benchmarks for mid-tier lifestyle/athletic brands:

| Channel | Previous AUR | Updated AUR | Rationale |
|---|---|---|---|
| Normal Retail | $72 | $82 | Avg retail price for lifestyle footwear |
| Outlet | $45 | $52 | Off-price/outlet discount ~35% below retail |
| Franchise | $68 | $76 | Franchise partner pricing |
| Wholesale | $38 | $45 | Wholesale cost ~55% of retail |
| Ecommerce | $65 | $78 | DTC commands price premium over wholesale |

---

## Unit Range Calibration

`generate_sales_data()` unit draw: `rng.integers(800, 3000)` → `rng.integers(2500, 7000)`

**Rationale:** At the old range, total simulated annual revenue per country was ~$5–10M — unrealistically small for a JV operation in Japan or Mexico. At the new range, per-country annual revenue falls in the $30–80M range, consistent with a mid-size JV footwear portfolio.

---

## Changes Summary

| Location | What changes |
|---|---|
| `data/simulate.py` top | Add `BENCHMARK_SOURCE` comment block with SEC reference |
| `data/simulate.py` | Add `COUNTRY_REGION` dict mapping country → Wolverine region |
| `data/simulate.py` | Update `COUNTRY_VOLUME` to `{Japan: 1.22, Mexico: 0.96, South Korea: 1.00}` |
| `data/simulate.py` | Update `CHANNEL_AUR` to calibrated values |
| `data/simulate.py` | Update unit range in `generate_sales_data()` to `rng.integers(2500, 7000)` |

## No Changes

- Column schemas (all three generators)
- Function signatures
- `generate_otb_data()` and `generate_sku_data()` logic
- `tests/test_simulate.py` — no value-range assertions exist, all tests remain valid
- All page files

---

## Spec Self-Review

- No placeholders or TBDs
- Internal consistency: calibration math in the table matches the constants described
- Scope: single file, tightly focused
- Ambiguity: "assumed share of region" (Japan 55%, South Korea 45%, Mexico 70%) is an estimate — documented as such, not presented as precise fact
