# DashboardOwn — CFO Financial Dashboard (Streamlit)

An interactive, CFO-level financial dashboard for the DashboardOwn cooperative
platform model. Every KPI, growth rate, break-even figure, and scenario output
is calculated **inside `app.py`** from the two source CSVs — nothing is
hardcoded from the numbers themselves, only the model assumptions stated in
the original DAX pack (fee %, variable cost %, etc.).

## What's included
```
├── app.py                          # the whole app — 6 tabs
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml                 # navy/gold theme
└── data/
    ├── DashboardOwn_Clean_Dataset.csv   # your 12-month source data
    └── Scenarios.csv                    # what-if scenario table
```

## Tabs
1. **Cover** — title page with the "DO" logo mark and FY2026 headline stats
2. **Executive Summary** — KPI cards, a revenue→surplus waterfall bridge, a break-even gauge, and auto-generated CFO commentary
3. **Growth & Trend** — MoM growth rates, a GMV composition sunburst, and cost/revenue layering by month
4. **Member Economics** — an animated bubble chart, a member-growth funnel, and a conditionally-formatted utilization table
5. **Scenario Planner** — click between 6 live scenarios (Base, Demand Downside/Upside, Fee Increase, Cost Pressure, Combined Stress); every card and chart recalculates
6. **SME & Effort** — unit-economics assumptions and 20%-effort-overrun sensitivity

A sidebar lets you filter the reporting period (months) and switch currency display between auto/Lakh/Crore/raw ₹.

## Run it locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Open the URL it prints (usually `http://localhost:8501`).

## Put it on GitHub
```bash
git init
git add .
git commit -m "DashboardOwn CFO dashboard"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

## Deploy on Streamlit Community Cloud (free)
1. Go to **share.streamlit.io** and sign in with GitHub.
2. Click **New app**, pick your repo/branch, and set the main file path to `app.py`.
3. Deploy. First build takes 1–2 minutes while it installs `requirements.txt`.
4. Any future `git push` to `main` auto-redeploys.

No secrets, API keys, or external services are required — the app is fully
self-contained once the two CSVs are in `data/`.

## Updating the data
Replace `data/DashboardOwn_Clean_Dataset.csv` with a refreshed export in the
same column format (`Month, Active_Earning_Members, Hours_Per_Member,
Total_Member_Hours, Projects, GMV, Member_Earnings, Cooperative_Revenue,
Variable_Cost, Contribution, Fixed_Cost, Operating_Surplus`) and the whole
dashboard recalculates — no code changes needed. To add or edit what-if
scenarios, edit `data/Scenarios.csv` (columns: `Scenario,
Cooperative_Fee_Pct, Variable_Cost_Pct, Demand_Factor`).

## Verified before delivery
This app was smoke-tested end-to-end in a sandboxed environment before
handoff: syntax-checked, booted under a real Streamlit server (HTTP 200),
and executed standalone against the actual dataset with no exceptions. Key
figures were cross-checked by hand (e.g. December break-even coverage =
234.4%, FY2026 total GMV = ₹5.22 Cr, FY2026 operating surplus = ₹28.99 L).
