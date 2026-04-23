# Skechers International JV Planning Dashboard — Design Spec
**Date:** 2026-04-22
**Author:** Fidel Vieira Araujo
**Purpose:** Portfolio project to demonstrate Associate Planner capabilities to Skechers hiring manager

---

## Overview

A multi-page Streamlit web application simulating the core planning workflow of the Skechers Associate Planner, International Joint Venture role. Built with simulated but realistic data across 3 JV markets, 5 business channels, and 4 product divisions.

**Live demo format:** Streamlit app running locally or deployed to Streamlit Community Cloud (shareable URL).

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.11+ | Core language |
| Streamlit | App framework |
| Pandas | Data wrangling |
| Plotly | Interactive charts |
| NumPy | Simulated data generation (seeded) |

No external database. All data generated in-memory at startup via `data/simulate.py` with a fixed random seed.

---

## File Structure

```
skechers-jv-planner/
├── app.py                        # Main entry point, sidebar nav, global filters
├── data/
│   └── simulate.py               # Generates all mock datasets (seeded)
├── pages/
│   ├── 1_quarterly_recap.py
│   ├── 2_otb_tracker.py
│   └── 3_sku_performance.py
├── utils/
│   └── metrics.py                # Shared KPI calculation helpers
└── requirements.txt
```

---

## Data Model

### Sales Data
Generated per (country × channel × division × quarter):

| Field | Type | Notes |
|---|---|---|
| `country` | str | Japan, Mexico, South Korea |
| `channel` | str | Normal Retail, Outlet, Franchise, Wholesale, Ecommerce |
| `division` | str | Men's Sport, Women's Sport, Women's Comfort, Kids |
| `quarter` | str | Q1–Q4 2024, Q1 2025 |
| `sales_units` | int | Actual units sold |
| `sales_dollars` | float | Actual revenue |
| `target_units` | int | Planned target |
| `target_dollars` | float | Planned revenue target |
| `AUR` | float | Average Unit Retail (sales_dollars / sales_units) |
| `discount_pct` | float | Average discount applied |

### Inventory / OTB Data
Generated per (country × channel × month):

| Field | Type | Notes |
|---|---|---|
| `month` | date | Jan 2024 – Mar 2025 |
| `country` | str | Same 3 markets |
| `channel` | str | Same 5 channels |
| `beg_inventory` | int | Beginning of month units |
| `receipts` | int | Units received |
| `sales` | int | Units sold |
| `end_inventory` | int | Derived: beg + receipts - sales |
| `otb_budget` | int | Planned buy budget (units) |
| `committed_units` | int | Already-ordered units |
| `open_to_buy` | int | Derived: otb_budget - committed_units |

### SKU Data
Generated per (style × country × channel):

| Field | Type | Notes |
|---|---|---|
| `style_id` | str | e.g., SK-1042 |
| `style_name` | str | Descriptive mock name |
| `division` | str | Same 4 divisions |
| `country` | str | Same 3 markets |
| `channel` | str | Same 5 channels |
| `units_sold` | int | Season to date |
| `units_on_hand` | int | Current inventory |
| `avg_weekly_sales` | float | Rolling 4-week average |
| `weeks_of_supply` | float | Derived: units_on_hand / avg_weekly_sales |
| `sell_through_pct` | float | units_sold / (units_sold + units_on_hand) |
| `flag` | str | "Opportunity", "Risk", or "On Track" |

**Flag logic:**
- `Risk`: sell_through < 40% OR weeks_of_supply > 12
- `Opportunity`: sell_through > 75% AND weeks_of_supply < 4
- `On Track`: everything else

---

## Pages

### app.py — Overview
**Purpose:** Landing page and global navigation — gives leadership a pulse on all JV markets at a glance before drilling in.

**Stakeholders:** Senior Merchandisers, JV Regional Leads, Planning Manager

**Decisions enabled:**
- Which markets are tracking below sales target this quarter and need attention?
- Is overall sell-through healthy enough to hold current inventory levels?
- How much open-to-buy capacity is left across the portfolio?
- Which markets have the most at-risk SKUs requiring immediate action?

- **Sidebar filters** (apply to all pages):
  - Quarter (single select)
  - Country (multiselect)
- **KPI cards (4):**
  - Total Sales $
  - Sell-Through %
  - OTB Remaining (avg across countries)
  - # Risk SKUs
- **Bar chart:** Sales vs. Target by country for selected quarter

---

### Page 1 — Quarterly Recap
**Purpose:** Pre-season and in-season performance review at the channel and division level — the primary artifact shared in monthly/quarterly business reviews with JV partners.

**Stakeholders:** JV Country Partners, Merchandisers, Planning Manager

**Decisions enabled:**
- Which channels are missing plan and by how much? Should targets be revised?
- Are specific divisions over- or under-performing relative to mix expectations?
- Where should next season's buy budget be shifted (up or down) by channel?
- What narrative should be communicated to JV partners in the next conference call?

- **Grouped bar chart:** Sales vs. Target by channel (filtered by country/quarter)
- **Stacked bar chart:** Sales by division over time (trend across all quarters)
- **Summary table:** Country × Channel with columns: Sales $, Target $, Variance $, Variance %, color-coded delta

---

### Page 2 — OTB Tracker
**Purpose:** Monthly in-season inventory health check — ensures JV markets are buying the right amount and not over- or under-committing against the plan.

**Stakeholders:** JV Country Partners, Merchandisers, IT/Systems (for reporting automation)

**Decisions enabled:**
- Does this market have budget remaining to chase a fast-selling style, or is OTB exhausted?
- Which channels are sitting on excess inventory (high months of supply) and need a markdown or hold on receipts?
- Are committed units aligned with the sales trajectory, or is the market over-committed?
- Should receipts be pulled forward or pushed back to optimize end-of-season inventory?

- **Line chart:** Monthly inventory flow — beg inventory, receipts, sales, end inventory (per country)
- **Bar chart:** OTB Budget vs. Committed vs. Open-to-Buy by country
- **Months of Supply callout:** Per channel, flagged red if > 4 months

---

### Page 3 — SKU Performance
**Purpose:** Style-level opportunity and risk identification — the tactical layer used to make assortment decisions within the season and inform future buys.

**Stakeholders:** Merchandisers, JV Country Partners, Associate Planner (self-directed analysis)

**Decisions enabled:**
- Which styles should be reordered or chased because they are selling through fast with low weeks of supply?
- Which styles are stalling and need a markdown, promotion, or exit strategy?
- Are there division-level patterns in the risk/opportunity flags that suggest an assortment gap?
- What styles should be dropped or added for the next seasonal assortment?

- **Sortable table:** All SKUs with sell-through %, weeks of supply, flag badges (color-coded: red/green/gray)
- **Bar chart:** Top 10 and Bottom 10 styles by sell-through %
- **Filters:** Division, Channel, Flag type (Opportunity / Risk / On Track)

---

## Success Criteria

1. Hiring manager can open a URL and immediately interact with the dashboard
2. Each page maps visibly to a responsibility listed in the job description
3. Simulated data looks realistic (plausible sales volumes, AUR ranges, inventory levels for international footwear)
4. App runs without errors across all filter combinations
5. README explains what each page demonstrates and connects it to the role

---

## Out of Scope

- Real Skechers data (all data is simulated)
- User authentication
- Database persistence
- Excel export
- Forecasting model (Advanced tier feature)
