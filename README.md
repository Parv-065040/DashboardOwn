# DashboardOwn — CFO Financial Dashboard

> A member-owned, cooperative gig-work platform — modelled and visualized from the ground up as a live financial dashboard.

## The idea

Most gig platforms take a cut of every transaction and keep the economics opaque —
workers see their payout, the platform sees everything. **DashboardOwn** flips that:
it's a cooperative marketplace model where earning members share in the platform's
economics, and the platform's own health (GMV, cooperative revenue, break-even
position) is tracked with the same rigor a CFO would apply to any business.

This repo is the financial instrumentation layer for that idea — a dashboard that
answers the questions a CFO or board would actually ask:
- Are we above or below break-even, and by how much?
- What's driving GMV growth — more members, more hours, or more projects?
- How exposed are we if demand drops or costs rise?
- Are members being paid fairly and consistently as the platform scales?

## What's in the dashboard

Built on twelve months of platform data (Jan–Dec 2026) and re-implements the
project's original Power BI DAX logic natively in Python, so every number on
screen is calculated live from the source data — nothing is hardcoded.

| Tab | What it shows |
|---|---|
| **Cover** | Title page with the DO mark and FY2026 headline numbers |
| **Executive Summary** | KPI cards, a revenue → operating surplus bridge (waterfall), a break-even coverage gauge, and auto-generated CFO commentary that reacts to the numbers |
| **Growth & Trend** | Month-over-month growth rates, a GMV composition sunburst, and monthly cost/revenue layering |
| **Member Economics** | An animated bubble chart of headcount vs. utilization, a member-growth funnel, and a conditionally-formatted utilization table |
| **Scenario Planner** | Six live what-if scenarios (Base, Demand Downside/Upside, Fee Increase, Cost Pressure, Combined Stress) — every chart and card recalculates on click |
| **SME & Effort** | Unit-economics assumptions (project value, contribution, CAC) and sensitivity to a 20% effort overrun |

## The financial model, in short

- Cooperative fee: **15%** of GMV · Variable cost: **3%** of GMV
- Member share of GMV: **85%**
- Break-even GMV = Fixed Cost ÷ (Fee % − Variable %)
- Scenario planning re-bases GMV by a demand factor and re-runs the same math
  under different fee/cost assumptions

## Tech stack

- **Streamlit** for the app and layout
- **Plotly** for the interactive charts (waterfall, sunburst, funnel, animated bubble, gauge)
- **Pandas / NumPy** for all calculations — growth rates, break-even, scenario math
- No database, no backend — a self-contained app that reads two CSVs and computes everything at runtime

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data

- `data/DashboardOwn_Clean_Dataset.csv` — the 12-month operating dataset (members, hours, projects, GMV, costs, surplus)
- `data/Scenarios.csv` — the what-if scenario table driving the Scenario Planner

Swap in a refreshed export with the same column structure and the whole dashboard updates — no code changes required.

## Author

Built by **Parv**, Team Spartans — PGDM (Business Data Analytics), FORE School of Management.
