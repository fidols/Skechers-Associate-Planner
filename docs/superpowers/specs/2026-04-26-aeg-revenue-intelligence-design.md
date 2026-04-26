# AEG Presents Revenue Intelligence — Design Spec

## Overview

**Goal:** A 3-page Streamlit dashboard that loads simulated live event data, runs a linear regression to identify revenue drivers, and surfaces over/underperforming events via residual analysis — structured to mirror how AEG Presents' Strategy Group would analyze business performance across festivals, venues, and touring.

**Target role:** AEG Presents Data Analyst (Strategy Group)

**Key requirements addressed:**
- SQL: standalone `data/queries.sql` + pandas with inline `# SQL equivalent:` comments in Python
- Python: pandas, scikit-learn, Plotly, Streamlit
- Statistical modeling: linear regression with coefficient interpretation and residual analysis
- Financial analysis: revenue modeling, sell-through rates
- Cross-department storytelling: genre, venue type, and event-level breakdowns
- Non-technical presentation: plain-English captions on all model outputs

---

## Branding

- Background: white (`#FFFFFF`)
- Primary text/accent: AEG navy blue (`#003DA5`)
- `.streamlit/config.toml`: `primaryColor = "#003DA5"`, `backgroundColor = "#FFFFFF"`, `textColor = "#1A1A1A"`

---

## Repo Structure

```
aeg-revenue-intelligence/
├── app.py                      # Overview: KPI cards + revenue by genre/venue type
├── pages/
│   ├── 1_Revenue_Drivers.py    # Regression coefficients, R², feature importance chart
│   └── 2_Performance_Score.py  # Residual analysis: flagged over/underperformers
├── data/
│   ├── simulate.py             # Seeded event data generator
│   └── queries.sql             # Standalone SQL: 3 core aggregation queries
├── utils/
│   ├── model.py                # Feature engineering + sklearn LinearRegression
│   └── metrics.py              # KPI helpers (overview aggregations)
├── tests/
│   ├── test_simulate.py        # Data shape, column types, value ranges
│   └── test_model.py           # Model output shape, R² sanity, residual calculation
├── .streamlit/
│   └── config.toml             # AEG brand theme
└── README.md                   # Project summary, page-to-role mapping, how to run
```

---

## Data Model

Simulated via `data/simulate.py`, seeded at 42. ~2,000 rows, each row = one event.

| Column | Type | Description |
|---|---|---|
| `event_id` | str | Unique identifier |
| `event_name` | str | Artist + tour name |
| `venue_type` | str | Arena / Theater / Festival / Club |
| `venue_capacity` | int | 500 – 80,000 |
| `genre` | str | Pop / Rock / Hip-Hop / EDM / Country / Other |
| `day_of_week` | int | 0–6 (Mon=0, Sun=6) |
| `months_in_advance` | int | How far out tickets went on sale (1–12) |
| `avg_ticket_price` | float | $25 – $350 |
| `sell_through_pct` | float | 0.30 – 1.00 |
| `tickets_sold` | int | `venue_capacity × sell_through_pct` |
| `revenue` | float | `tickets_sold × avg_ticket_price` (regression target) |
| `year` | int | 2022–2024 |

---

## SQL Layer (`data/queries.sql`)

Three queries, written as if running against a `events` table in a relational DB:

1. **Revenue by genre** — `SELECT genre, SUM(revenue), AVG(sell_through_pct) FROM events GROUP BY genre ORDER BY SUM(revenue) DESC`
2. **Sell-through by venue type** — `SELECT venue_type, AVG(sell_through_pct), COUNT(*) FROM events GROUP BY venue_type`
3. **Top 20 events by revenue** — `SELECT event_name, venue_type, genre, revenue FROM events ORDER BY revenue DESC LIMIT 20`

In Python (`utils/metrics.py`), pandas replicates each query with a `# SQL equivalent: ...` comment above the aggregation.

---

## Statistical Model (`utils/model.py`)

**Type:** `sklearn.linear_model.LinearRegression`

**Target:** `revenue`

**Features:**
- `venue_capacity` — normalized
- `avg_ticket_price` — normalized
- `months_in_advance` — continuous
- `is_weekend` — binary (day_of_week in {5, 6})
- `genre` — one-hot encoded (drop_first=True)
- `venue_type` — one-hot encoded (drop_first=True)

**Outputs:**
1. `r_squared` — float, proportion of variance explained
2. `coefficients` — Series, feature name → coefficient value
3. `residuals` — Series, `actual_revenue − predicted_revenue` per event
4. `flag` — "Overperformer" (residual > +1 std), "Underperformer" (residual < −1 std), "On Track"

**Design note:** No train/test split. This is a descriptive/explanatory model for business insight, not a production ML deployment. Fitting on the full dataset is appropriate and expected in a business analytics context.

---

## Dashboard Pages

### `app.py` — Overview

- **Sidebar filters:** Genre (multiselect), Venue Type (multiselect), Year (selectbox)
- **KPI cards (4):** Total Revenue, Total Events, Avg Revenue per Event, Avg Sell-Through %
- **Chart 1:** Grouped bar — Revenue vs. Avg Ticket Price by genre
- **Chart 2:** Bar — Total Revenue by venue type

### `pages/1_Revenue_Drivers.py`

- **Stakeholders:** Chief Strategy Officer, Strategy Directors
- **Decisions:** Where to invest booking budget, which genres/venue types drive margin
- **KPI card:** R² displayed as "Model explains X% of revenue variance"
- **Chart:** Horizontal bar — feature coefficients sorted by absolute magnitude, colored positive (navy) / negative (red)
- **Caption:** Plain-English summary of top 3 drivers (e.g., "Venue capacity has the strongest positive effect on revenue, followed by ticket price. EDM events outperform similarly-sized Pop events by ~$X on average.")

### `pages/2_Performance_Score.py`

- **Stakeholders:** Strategy Directors, Venue/Touring team leads
- **Decisions:** Identify which events outperformed predictions (chase model), flag underperformers for investigation
- **Page filters:** Genre, Venue Type, Flag (Overperformer / Underperformer / On Track)
- **Table:** event_name, venue_type, genre, actual revenue, predicted revenue, residual $, flag badge (🟢/🔴/⚪)
- **Scatter plot:** Actual vs. predicted revenue; diagonal reference line ("perfect forecast"); points colored by flag

---

## Cross-Page Data Flow

Same pattern as Skechers app:
- `app.py` loads data via `@st.cache_data`, stores in `st.session_state`
- All pages read from session state, guard with `st.warning + st.stop()` if missing
- Sidebar filters on `app.py` are shared; page-level filters are local

---

## Testing

**`tests/test_simulate.py`:**
- DataFrame has expected columns
- No nulls in key columns
- `revenue == tickets_sold × avg_ticket_price` (within float tolerance)
- `tickets_sold <= venue_capacity` always
- `sell_through_pct` in [0.3, 1.0]

**`tests/test_model.py`:**
- `run_model()` returns dict with keys: `r_squared`, `coefficients`, `residuals`, `flag`
- R² is between 0 and 1
- `len(residuals) == len(input_df)`
- Flag values are a subset of {"Overperformer", "Underperformer", "On Track"}
- Residuals sum to approximately 0 (OLS property)
