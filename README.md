# Skechers International JV Planning Dashboard

A portfolio project demonstrating core Associate Planner capabilities for the Skechers International Joint Venture role.

Built with Python + Streamlit using simulated but realistic data across **3 JV markets** (Japan, Mexico, South Korea), **5 business channels**, and **4 product divisions**.

---

## What This Demonstrates

| Page | Job Description Responsibility |
|---|---|
| **Overview** | "Analyzing country's historical sales and inventory" — cross-market pulse check for leadership |
| **Quarterly Recap** | "Provides constructive analysis of monthly/quarterly recaps at the business channel level by country" |
| **OTB Tracker** | "Maintains in-season data via monthly OTB by reviewing sales, inventory and identifying opportunities and risks" |
| **SKU Performance** | "Identify/react to in-season misses/opportunities at the gender/category/division/style/SKU level" |

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

All data is simulated using seeded NumPy random generators — no real Skechers data is used. Values (AUR, unit volumes, inventory levels) are calibrated to reflect realistic international footwear planning ranges.
