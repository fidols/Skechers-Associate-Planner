# Skechers International JV Planning Dashboard

A portfolio project demonstrating core Associate Planner capabilities for the Skechers International Joint Venture role.

Built with Python + Streamlit using simulated but realistic data across **6 JV markets** (China, Malaysia, Singapore, Thailand, Mexico, South Korea), **5 business channels**, and **4 product divisions**. Volume calibrated to real SKX FY2024 10-K figures.

---

## What This Demonstrates

| Page | Job Description Responsibility |
|---|---|
| **Overview** | "Analyzing country's historical sales and inventory" — cross-market pulse check with QoQ delta and country snapshot |
| **Quarterly Recap** | "Provides constructive analysis of monthly/quarterly recaps at the business channel level by country" |
| **OTB Tracker** | "Maintains in-season data via monthly OTB by reviewing sales, inventory and identifying opportunities and risks" |
| **SKU Performance** | "Identify/react to in-season misses/opportunities at the gender/category/division/style/SKU level" — includes ST% heatmap by Country × Division |
| **Scenario Planner** | What-if analysis — adjust ST% (±30pp) and receipt quantity (±50%) per country and division to model revenue, units sold, and end inventory impact |

---

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd Skechers-Associate-Planner

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

App opens at `http://localhost:8501`.

---

## Run Tests

```bash
pytest tests/ -v
```

---

## Data Note

All data is simulated using seeded NumPy random generators — no real Skechers data is used. Country revenue volumes are calibrated to the SKX FY2024 10-K (SEC Accession: 0000950170-25-030016): China ($1.22B directly disclosed), other JV markets estimated from regional pools. AUR by channel reflects footwear industry benchmarks.
