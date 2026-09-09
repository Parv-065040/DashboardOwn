# DashboardOwn

**A member-owned analytics workforce cooperative for Indian SMEs.**

Built for the *Co-operative / Employee-Owned Business Ideathon* (hosted by Kairos Creative, certificates by Zone by The Park, on Unstop — prize pool ₹1,00,000).

> DashboardOwn connects freelance BI/data analysts (Power BI, Excel, SQL) with SMEs that need dashboards and reporting but can't justify a full-time hire — through a platform the analysts collectively own. Members keep **85%** of billed value instead of the 40–50% a typical agency or marketplace takes. The cooperative operates on a capped **12–15%** fee, one member = one vote, no VC ownership, no founder veto.

---

## Status

| Round | Status |
|---|---|
| Round 1 — Written idea | ✅ Submitted and shortlisted |
| Round 2 — Financial model + jury conversation | 🔄 In progress (window: 7–12 Sep 2026) |

---

## What's in this repo

| File | What it is |
|---|---|
| `DashboardOwn_Financial_Model.xlsx` | The working financial model — 10 sheets, 230+ live formulas, zero calc errors. Assumptions, project mix, 12-month build, break-even, stress tests, scaling scenarios, SME/CAC economics, and an executive dashboard with charts. Change any blue input cell and everything recalculates. |
| `DashboardOwn_Website.html` | The stakeholder-facing pitch site. Four separate views (SME / Analyst / Cooperative-Ops / Jury), each with its own section tabs — covers the model, the economics, governance, risks, and jury Q&A prep in one place. Open directly in a browser, no server needed. |
| `DashboardOwn_Product_Demo.html` | An interactive click-through demo of what the actual product looks like once the business launches — three logged-in-feeling app views (Customer, Analyst, Governance) with sample data, working buttons, live charts, and DashboardOwn/"DQ" branding. No backend — state resets on reload. |

All three files are self-contained. Clone the repo and open the `.html` files directly in a browser; open the `.xlsx` in Excel, Google Sheets, or LibreOffice.

---

## The model, in five numbers

| | |
|---|---|
| Member share (base case) | **85%** |
| Cooperative fee (base case) | **15%** |
| Weighted avg. project value | **₹58,500** |
| Contribution per average project | **₹7,020** |
| Monthly break-even GMV | **≈ ₹12.5L** |

These are working assumptions to validate through a pilot — not proven market facts. The financial model and website both flag every hypothesis explicitly rather than presenting them as certainties.

---

## How the cooperative works

1. An SME describes a business problem (not a tool request).
2. It's structured into scope, effort and price — AI-assisted, human-reviewed.
3. A curated shortlist of 2–3 verified analysts (or a small team) is matched.
4. The SME selects, contracts, and pays by milestone.
5. Delivery happens inside a project workspace with risk-based QA.
6. On acceptance, the member is paid 85% of GMV; the cooperative keeps 12–15%.

Governance runs on one member, one vote: a Member Assembly sets the fee ceiling and economic rights, a term-limited 5-person Council handles oversight and appeals, and day-to-day operations executes within that mandate — so daily work doesn't wait on a vote, but core economics can never move without one.

---

## Biggest known risk

**SME demand and repeat purchase rate — not analyst supply.** If members are onboarded faster than projects arrive, utilization collapses and the model breaks. The pilot plan tests this first: 10–20 SMEs, 10–20 paid/pilot projects, tracked for 90 days, before scaling member supply further.

---

## Tech notes

- `DashboardOwn_Financial_Model.xlsx` — built with `openpyxl`, verified with a LibreOffice headless recalculation pass (0 formula errors across 230+ formulas).
- Both `.html` files are single-file, dependency-light builds — Chart.js is loaded from a CDN for charts; everything else is plain HTML/CSS/vanilla JS. No build step, no npm install.

---

## Roadmap

- [x] Round 1 written idea
- [x] Round 2 financial model
- [x] Stakeholder pitch website
- [x] Interactive product demo
- [ ] Pilot: 10–20 SMEs, 20–30 verified analysts, one narrow category
- [ ] Validate: SME CAC, repeat purchase rate, reserve policy, legal entity structure

---

## License / usage

Built as an ideathon submission. No license has been chosen yet — treat as all-rights-reserved unless the author states otherwise.
