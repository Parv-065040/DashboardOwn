"""
DashboardOwn — CFO Financial Dashboard

Drop-in replacement for the previous app.py.

Data sources:
    data/DashboardOwn_Clean_Dataset_CORRECTED.csv
    data/Scenarios_CORRECTED.csv

The corrected CSVs preserve the underlying financial model and accounting
identities. All dashboard KPIs are derived from those files at runtime.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

# ============================================================
# 0. PAGE CONFIG & THEME
# ============================================================
st.set_page_config(
    page_title="DashboardOwn — CFO Dashboard",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

INK = "#0B2545"
GOLD = "#C9A227"
SLATE = "#5C6B7A"
LINE = "#DADFE3"
POSITIVE = "#2F6F4E"
NEGATIVE = "#A6432F"
PAPER = "#F7F5F0"
SURFACE = "#FFFFFF"
SOFT_GREEN = "#E4EFE9"
SOFT_RED = "#F5E7E3"
MID_BLUE = "#7C9CBF"
MID_GREY = "#AEB8C2"

CHART_COLORWAY = [INK, GOLD, MID_BLUE, POSITIVE, NEGATIVE, MID_GREY]

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'IBM Plex Sans', sans-serif;
    }}
    .stApp {{ background-color: {PAPER}; }}
    h1, h2, h3 {{ font-family: 'Source Serif 4', serif !important; color: {INK}; }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    .logo-badge {{
        display:inline-flex; align-items:center; justify-content:center;
        width:44px; height:44px; border-radius:8px;
        background:{INK}; color:{GOLD};
        font-family:'Source Serif 4', serif; font-weight:700; font-size:18px;
        margin-right:12px; border:1px solid {GOLD};
    }}
    .brand-row {{ display:flex; align-items:center; margin-bottom:4px; }}
    .brand-name {{ font-family:'Source Serif 4', serif; font-size:20px; font-weight:600; color:{INK}; }}
    .brand-name span {{ color:{GOLD}; }}

    .kpi-card {{
        background:{SURFACE}; border:1px solid {LINE}; border-radius:6px;
        padding:16px 18px; margin-bottom:6px; min-height:105px;
    }}
    .kpi-label {{ font-size:12px; color:{SLATE}; font-weight:600; margin-bottom:8px; }}
    .kpi-value {{ font-family:'Source Serif 4', serif; font-size:26px; font-weight:600; color:{INK}; line-height:1.15; }}
    .kpi-delta {{ font-size:12px; font-weight:500; margin-top:6px; }}
    .kpi-sub {{ font-size:11px; color:{SLATE}; margin-top:4px; }}

    .status-banner {{
        border-left:4px solid {GOLD}; background:{SURFACE};
        border-radius:4px; padding:16px 18px; font-size:14.5px; line-height:1.5;
    }}
    .flag-pill {{
        display:inline-block; padding:2px 10px; border-radius:10px; font-size:12px; font-weight:600;
    }}
    .flag-good {{ background:{SOFT_GREEN}; color:{POSITIVE}; }}
    .flag-bad {{ background:{SOFT_RED}; color:{NEGATIVE}; }}
    .section-note {{ font-size:12px; color:{SLATE}; font-style:italic; margin-top:6px; }}
    hr {{ border-color:{LINE}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Sans, sans-serif", color=INK, size=12),
    colorway=CHART_COLORWAY,
    margin=dict(l=45, r=45, t=50, b=45),
)


def html(s: str) -> str:
    return " ".join(line.strip() for line in s.strip().splitlines() if line.strip())


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def style_fig(fig, title=None, height=360, margins=None):
    layout = dict(PLOTLY_LAYOUT)
    layout["margin"] = margins or PLOTLY_LAYOUT["margin"]
    fig.update_layout(**layout, height=height)
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=14, family="IBM Plex Sans"), x=0))
    fig.update_xaxes(gridcolor=LINE, zerolinecolor=LINE)
    fig.update_yaxes(gridcolor=LINE, zerolinecolor=LINE)
    return fig


# ============================================================
# 1. DATA LOADING
# ============================================================
DATA_DIR = Path(__file__).parent / "data"

FINANCIAL_FILE = DATA_DIR / "DashboardOwn_Clean_Dataset_CORRECTED.csv"
SCENARIO_FILE = DATA_DIR / "Scenarios_CORRECTED.csv"

# Graceful fallback makes the app usable if the user has not renamed the files
# yet, while the corrected files remain the preferred source.
FINANCIAL_FALLBACK = DATA_DIR / "DashboardOwn_Clean_Dataset.csv"
SCENARIO_FALLBACK = DATA_DIR / "Scenarios.csv"


@st.cache_data(show_spinner=False)
def load_financials() -> pd.DataFrame:
    source = FINANCIAL_FILE if FINANCIAL_FILE.exists() else FINANCIAL_FALLBACK
    df = pd.read_csv(source, parse_dates=["Month"])
    df = df.sort_values("Month").reset_index(drop=True)
    df["MonthLabel"] = df["Month"].dt.strftime("%b %Y")
    return df


@st.cache_data(show_spinner=False)
def load_scenarios() -> pd.DataFrame:
    source = SCENARIO_FILE if SCENARIO_FILE.exists() else SCENARIO_FALLBACK
    return pd.read_csv(source)


try:
    raw = load_financials()
    scenarios_df = load_scenarios()
except FileNotFoundError:
    st.error(
        "Could not find the financial data. Put the corrected CSVs inside a `data` "
        "folder next to `app.py`."
    )
    st.stop()

# Schema validation prevents silent chart failures if the wrong CSV is supplied.
REQUIRED_FINANCIAL_COLUMNS = {
    "Month", "Active_Earning_Members", "Hours_Per_Member", "Total_Member_Hours",
    "Projects", "GMV", "Member_Earnings", "Cooperative_Revenue", "Variable_Cost",
    "Contribution", "Fixed_Cost", "Operating_Surplus"
}
REQUIRED_SCENARIO_COLUMNS = {"Scenario", "Cooperative_Fee_Pct", "Variable_Cost_Pct", "Demand_Factor"}

missing_financial = REQUIRED_FINANCIAL_COLUMNS.difference(raw.columns)
missing_scenarios = REQUIRED_SCENARIO_COLUMNS.difference(scenarios_df.columns)
if missing_financial or missing_scenarios:
    st.error(
        f"Data schema mismatch. Missing financial columns: {sorted(missing_financial)}; "
        f"missing scenario columns: {sorted(missing_scenarios)}."
    )
    st.stop()

# ============================================================
# 2. MODEL ASSUMPTIONS
# ============================================================
FEE_PCT = 0.15
VARIABLE_PCT = 0.03
BE_DIVISOR = FEE_PCT - VARIABLE_PCT
AVG_PROJECT_VALUE = 58500
AVG_PROJECT_HOURS = 31.6
MEMBER_SHARE = 0.85
MEMBER_UTILIZATION_TARGET = 30
PROJECT_FILL_RATE_TARGET = 0.85
REPEAT_SME_GMV_TARGET = 0.50
EFFORT_OVERRUN_MAX = 0.20
PAYMENT_TIMELINESS_TARGET = 0.95
FIRST_PASS_ACCEPTANCE_TARGET = 0.90

# ============================================================
# 3. DERIVED FIELDS
# ============================================================
df = raw.copy()

df["Cooperative_Take_Rate"] = np.divide(df.Cooperative_Revenue, df.GMV, out=np.zeros(len(df)), where=df.GMV.ne(0))
df["Member_Share_Pct"] = np.divide(df.Member_Earnings, df.GMV, out=np.zeros(len(df)), where=df.GMV.ne(0))
df["Contribution_Margin_Pct"] = np.divide(df.Contribution, df.GMV, out=np.zeros(len(df)), where=df.GMV.ne(0))
df["Effective_Member_Rate"] = np.divide(df.Member_Earnings, df.Total_Member_Hours, out=np.zeros(len(df)), where=df.Total_Member_Hours.ne(0))
df["GMV_Per_Member"] = np.divide(df.GMV, df.Active_Earning_Members, out=np.zeros(len(df)), where=df.Active_Earning_Members.ne(0))
df["Contribution_Per_Project"] = np.divide(df.Contribution, df.Projects, out=np.zeros(len(df)), where=df.Projects.ne(0))
df["Avg_Project_Value"] = np.divide(df.GMV, df.Projects, out=np.zeros(len(df)), where=df.Projects.ne(0))
df["Member_Earnings_Per_Project"] = np.divide(df.Member_Earnings, df.Projects, out=np.zeros(len(df)), where=df.Projects.ne(0))

df["Breakeven_GMV"] = df.Fixed_Cost / BE_DIVISOR
df["Breakeven_Projects"] = df.Fixed_Cost / (AVG_PROJECT_VALUE * BE_DIVISOR)
df["Breakeven_Gap"] = df.GMV - df.Breakeven_GMV
df["Breakeven_Coverage_Pct"] = np.divide(df.GMV, df.Breakeven_GMV, out=np.zeros(len(df)), where=df.Breakeven_GMV.ne(0))

df["GMV_MoM"] = df.GMV.pct_change()
df["Revenue_MoM"] = df.Cooperative_Revenue.pct_change()
df["Surplus_MoM"] = df.Operating_Surplus.pct_change()
df["Member_Earnings_Growth"] = df.Member_Earnings.pct_change()

df["Financial_Health_Flag"] = np.where(df.Operating_Surplus >= 0, "Healthy", "Loss")
df["Breakeven_Flag"] = np.where(df.GMV >= df.Breakeven_GMV, "Above Break-even", "Below Break-even")
df["Utilization_Flag"] = np.where(df.Hours_Per_Member >= MEMBER_UTILIZATION_TARGET, "On Target", "Below Target")


def ceo_status(row) -> str:
    if row.Operating_Surplus < 0:
        return "Action required: cooperative is below operating break-even."
    if row.Hours_Per_Member < MEMBER_UTILIZATION_TARGET:
        return "Watch: member utilization is below the 30-hour mature-state target."
    if row.Contribution_Margin_Pct < 0.10:
        return "Warning: contribution margin is under pressure."
    return "Core economics are within the current base-case guardrails."


def ceo_growth(mom) -> str:
    if pd.isna(mom):
        return "N/A (first month on record)"
    if mom > 0.10:
        return "Strong growth"
    if mom > 0:
        return "Positive growth"
    if mom == 0:
        return "Flat"
    return "Declining"


df["CEO_Status"] = df.apply(ceo_status, axis=1)
df["CEO_Growth_Signal"] = df["GMV_MoM"].apply(ceo_growth)

BASE_AVG_PROJECT_CONTRIBUTION = AVG_PROJECT_VALUE * BE_DIVISOR
ANNUAL_CONTRIBUTION_PER_SME = BASE_AVG_PROJECT_CONTRIBUTION * 2.5
CONTRIBUTION_CAC = ANNUAL_CONTRIBUTION_PER_SME / 5000

BASE_MEMBER_RATE_PER_HR = df.Member_Earnings.sum() / df.Total_Member_Hours.sum()
SCENARIO_EFFECTIVE_RATE_PER_HR = df.Member_Earnings.sum() / (df.Total_Member_Hours.sum() * (1 + EFFORT_OVERRUN_MAX))


# ============================================================
# 4. FORMATTING HELPERS
# ============================================================
def fmt_inr(value, unit="auto"):
    if pd.isna(value):
        return "—"
    if unit == "auto":
        unit = "cr" if abs(value) >= 1e7 else "lakh"
    if unit == "cr":
        return f"₹{value / 1e7:,.2f} Cr"
    if unit == "lakh":
        return f"₹{value / 1e5:,.1f} L"
    return f"₹{value:,.0f}"


def fmt_pct(value, decimals=1):
    if pd.isna(value):
        return "—"
    return f"{value * 100:.{decimals}f}%"


def kpi_card(label, value, delta=None, positive=True, sublabel=None):
    delta_html = ""
    if delta is not None:
        color = POSITIVE if positive else NEGATIVE
        arrow = "▲" if positive else "▼"
        delta_html = f'<div class="kpi-delta" style="color:{color};">{arrow} {delta}</div>'
    sub_html = f'<div class="kpi-sub">{sublabel}</div>' if sublabel else ""
    st.markdown(
        html(
            f"""<div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}{sub_html}
            </div>"""
        ),
        unsafe_allow_html=True,
    )


def flag_pill(text, good):
    cls = "flag-good" if good else "flag-bad"
    return f'<span class="flag-pill {cls}">{text}</span>'


# ============================================================
# 5. SIDEBAR / GLOBAL SLICERS
# ============================================================
with st.sidebar:
    st.markdown(
        html(
            f"""<div class="brand-row">
            <div class="logo-badge">DO</div>
            <div class="brand-name">Dashboard<span>Own</span></div>
            </div>"""
        ),
        unsafe_allow_html=True,
    )
    st.caption("CFO Financial Dashboard · 12M illustrative model")
    st.markdown("---")

    month_options = df["MonthLabel"].tolist()
    month_range = st.select_slider(
        "Reporting period",
        options=month_options,
        value=(month_options[0], month_options[-1]),
        help="This slicer controls every data-driven dashboard tab, including the scenario planner.",
    )

    start_idx = month_options.index(month_range[0])
    end_idx = month_options.index(month_range[1])
    view = df.iloc[start_idx:end_idx + 1].reset_index(drop=True)

    currency_unit = st.radio("Currency display", ["Auto", "Lakh (L)", "Crore (Cr)", "Raw ₹"], index=0)
    unit_map = {"Auto": "auto", "Lakh (L)": "lakh", "Crore (Cr)": "cr", "Raw ₹": "raw"}
    UNIT = unit_map[currency_unit]

    st.markdown("---")
    st.caption(
        "Source: corrected DashboardOwn CSVs. Financial logic is derived live; "
        "the source data contains the model assumptions rather than observed company performance."
    )

if len(view) == 0:
    st.warning("Select at least one month in the sidebar to see the dashboard.")
    st.stop()

latest = view.iloc[-1]
prior = view.iloc[-2] if len(view) > 1 else None

# ============================================================
# 6. TABS
# ============================================================
tab_cover, tab_exec, tab_growth, tab_members, tab_scenario, tab_sme = st.tabs(
    ["🏠 Cover", "📊 Executive Summary", "📈 Growth & Trend", "👥 Member Economics", "🎯 Scenario Planner", "🧮 SME & Effort"]
)

# ============================================================
# TAB 0 — COVER
# ============================================================
with tab_cover:
    st.markdown(
        html(
            f"""<div style="background:{INK}; border-radius:10px; padding:48px 44px; color:white; margin-bottom:24px;">
            <div style="display:flex; align-items:center; margin-bottom:24px;">
                <div style="width:56px; height:56px; border-radius:10px; background:{GOLD}; color:{INK};
                            display:flex; align-items:center; justify-content:center; font-family:'Source Serif 4', serif;
                            font-weight:700; font-size:24px; margin-right:16px; border:1px solid rgba(255,255,255,0.4);">DO</div>
                <div>
                    <div style="font-size:13px; letter-spacing:0.02em; color:{GOLD};">CFO FINANCIAL REVIEW — 12M MODEL</div>
                    <div style="font-family:'Source Serif 4', serif; font-size:22px; font-weight:600;">DashboardOwn</div>
                </div>
            </div>
            <div style="font-family:'Source Serif 4', serif; font-size:38px; font-weight:600; max-width:760px; line-height:1.15; margin-bottom:16px;">
                Cooperative platform economics, from GMV to operating surplus.
            </div>
            <div style="font-size:15.5px; color:rgba(255,255,255,0.75); max-width:620px; line-height:1.6;">
                A live 12-month view of member earnings, cooperative economics, break-even position,
                utilization and scenario resilience — driven by the underlying financial model.
            </div>
            </div>"""
        ),
        unsafe_allow_html=True,
    )

    period_gmv = view.GMV.sum()
    period_surplus = view.Operating_Surplus.sum()
    period_revenue = view.Cooperative_Revenue.sum()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("GMV in Selected Period", fmt_inr(period_gmv, "cr"))
    with c2:
        kpi_card("Operating Surplus", fmt_inr(period_surplus, UNIT if UNIT != "auto" else "lakh"))
    with c3:
        kpi_card("Latest Active Members", f"{int(latest.Active_Earning_Members)}")
    with c4:
        kpi_card("Co-op Fee / Variable Cost", f"{FEE_PCT * 100:.0f}% / {VARIABLE_PCT * 100:.0f}%")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**How to read this dashboard**")
    st.markdown(
        """
        - **Executive Summary** — current-period economics, bridge to surplus and break-even position
        - **Growth & Trend** — monthly growth, cost layers and scale indicators
        - **Member Economics** — headcount, utilization and effective member pay rate
        - **Scenario Planner** — fee, cost and demand stress cases over the selected period
        - **SME & Effort** — unit economics, utilization target and effort-overrun sensitivity
        """
    )
    st.caption(f"Reporting period: {month_range[0]} – {month_range[1]}")

# ============================================================
# TAB 1 — EXECUTIVE SUMMARY
# ============================================================
with tab_exec:
    st.markdown("### Executive Summary")
    st.caption(
        f"Latest month in view: **{latest.MonthLabel}**"
        + (f" · compared against **{prior.MonthLabel}**" if prior is not None else "")
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        delta = latest.GMV_MoM if prior is not None else None
        kpi_card("Total GMV", fmt_inr(latest.GMV, UNIT), fmt_pct(delta) + " MoM" if delta is not None and not pd.isna(delta) else None, positive=(delta or 0) >= 0)
    with c2:
        delta = latest.Surplus_MoM if prior is not None else None
        kpi_card("Operating Surplus", fmt_inr(latest.Operating_Surplus, UNIT), fmt_pct(delta) + " MoM" if delta is not None and not pd.isna(delta) else None, positive=(delta or 0) >= 0)
    with c3:
        kpi_card("Contribution Margin", fmt_pct(latest.Contribution_Margin_Pct))
    with c4:
        kpi_card("Break-even Coverage", fmt_pct(latest.Breakeven_Coverage_Pct))

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.4, 1])

    with col_left:
        st.markdown("**Cooperative Revenue → Operating Surplus Bridge**")
        wf = go.Figure(
            go.Waterfall(
                orientation="v",
                measure=["relative", "relative", "total", "relative", "total"],
                x=["Co-op Revenue", "Variable Cost", "Contribution", "Fixed Cost", "Operating Surplus"],
                y=[latest.Cooperative_Revenue, -latest.Variable_Cost, 0, -latest.Fixed_Cost, 0],
                text=[
                    fmt_inr(latest.Cooperative_Revenue, UNIT),
                    f"-{fmt_inr(latest.Variable_Cost, UNIT)}",
                    fmt_inr(latest.Contribution, UNIT),
                    f"-{fmt_inr(latest.Fixed_Cost, UNIT)}",
                    fmt_inr(latest.Operating_Surplus, UNIT),
                ],
                textposition="outside",
                connector=dict(line=dict(color=LINE)),
                increasing=dict(marker=dict(color=INK)),
                decreasing=dict(marker=dict(color=NEGATIVE)),
                totals=dict(marker=dict(color=GOLD)),
            )
        )
        st.plotly_chart(style_fig(wf, height=390, margins=dict(l=35, r=35, t=55, b=55)), use_container_width=True)
        st.caption(f"Latest month: {latest.MonthLabel}. GMV is the client transaction value; only the cooperative fee enters cooperative revenue.")

    with col_right:
        st.markdown("**Break-even Coverage**")
        coverage = float(latest.Breakeven_Coverage_Pct * 100)
        gauge_max = max(150, min(300, coverage * 1.15))
        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=coverage,
                number={"suffix": "%", "font": {"size": 38, "color": INK}},
                gauge={
                    "axis": {"range": [0, gauge_max], "tickwidth": 1, "dtick": 50},
                    "bar": {"color": INK, "thickness": 0.35},
                    "steps": [
                        {"range": [0, min(100, gauge_max)], "color": SOFT_RED},
                        {"range": [min(100, gauge_max), gauge_max], "color": SOFT_GREEN},
                    ],
                    "threshold": {"line": {"color": GOLD, "width": 4}, "thickness": 0.8, "value": 100},
                },
            )
        )
        st.plotly_chart(style_fig(gauge, height=255, margins=dict(l=25, r=25, t=30, b=15)), use_container_width=True)

        good_health = latest.Financial_Health_Flag == "Healthy"
        good_be = latest.Breakeven_Flag == "Above Break-even"
        good_util = latest.Utilization_Flag == "On Target"
        st.markdown(
            html(
                f"""<div class="status-banner">
                Financial health: {flag_pill(latest.Financial_Health_Flag, good_health)}<br><br>
                Break-even position: {flag_pill(latest.Breakeven_Flag, good_be)}<br><br>
                Member utilization: {flag_pill(latest.Utilization_Flag, good_util)}
                <hr>
                <b>CEO Status:</b> {latest.CEO_Status}<br>
                <b>Growth Signal:</b> {latest.CEO_Growth_Signal}
                </div>"""
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**GMV & Operating Surplus Trend**")
    trend = go.Figure()
    trend.add_bar(x=view.MonthLabel, y=view.GMV, name="GMV", marker_color=hex_to_rgba(GOLD, 0.55), yaxis="y")
    trend.add_trace(go.Scatter(x=view.MonthLabel, y=view.Operating_Surplus, name="Operating Surplus", mode="lines+markers", line=dict(color=INK, width=2.5), yaxis="y2"))
    trend.update_layout(
        yaxis=dict(title="GMV", tickformat="~s"),
        yaxis2=dict(title="Operating Surplus", overlaying="y", side="right", showgrid=False, tickformat="~s"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(style_fig(trend, height=370), use_container_width=True)

# ============================================================
# TAB 2 — GROWTH & TREND
# ============================================================
with tab_growth:
    st.markdown("### Growth & Trend")
    st.caption("All charts respond to the reporting-period slicer in the sidebar.")

    growth_view = view.dropna(subset=["GMV_MoM"])
    if len(growth_view) > 0:
        fig_mom = go.Figure()
        fig_mom.add_trace(go.Scatter(x=growth_view.MonthLabel, y=growth_view.GMV_MoM, name="GMV", mode="lines+markers", line=dict(color=INK)))
        fig_mom.add_trace(go.Scatter(x=growth_view.MonthLabel, y=growth_view.Revenue_MoM, name="Co-op Revenue", mode="lines+markers", line=dict(color=GOLD)))
        fig_mom.add_trace(go.Scatter(x=growth_view.MonthLabel, y=growth_view.Surplus_MoM, name="Operating Surplus", mode="lines+markers", line=dict(color=POSITIVE)))
        fig_mom.update_yaxes(tickformat=".0%")
        fig_mom.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
        st.plotly_chart(style_fig(fig_mom, "Month-over-Month Growth Rates", height=360), use_container_width=True)
    else:
        st.info("Select at least two consecutive months in the sidebar to see month-over-month growth.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**GMV Allocation — Selected Period**")
        allocation = pd.DataFrame({
            "Category": ["Member Earnings", "Cooperative Revenue"],
            "Value": [view.Member_Earnings.sum(), view.Cooperative_Revenue.sum()],
        })
        alloc_fig = px.bar(allocation, x="Value", y="Category", orientation="h", text="Value")
        alloc_fig.update_traces(marker_color=[MID_BLUE, GOLD], texttemplate="₹%{x:,.0f}", textposition="outside")
        alloc_fig.update_xaxes(tickformat="~s")
        st.plotly_chart(style_fig(alloc_fig, height=260), use_container_width=True)
        st.caption("Member earnings plus cooperative revenue reconcile to total GMV for the selected period.")

        st.markdown("**Cooperative Cost Stack by Month**")
        stack = go.Figure()
        stack.add_bar(x=view.MonthLabel, y=view.Cooperative_Revenue, name="Co-op Revenue", marker_color=INK)
        stack.add_bar(x=view.MonthLabel, y=view.Variable_Cost, name="Variable Cost", marker_color=GOLD)
        stack.add_bar(x=view.MonthLabel, y=view.Fixed_Cost, name="Fixed Cost", marker_color=MID_GREY)
        stack.update_layout(barmode="group", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
        st.plotly_chart(style_fig(stack, height=320), use_container_width=True)
        st.caption("Grouped rather than stacked: revenue, variable cost and fixed cost are not additive components of one total.")

    with col_b:
        st.markdown("**Break-even Position by Month**")
        be_fig = go.Figure()
        be_fig.add_trace(go.Bar(x=view.MonthLabel, y=view.GMV, name="Actual GMV", marker_color=GOLD))
        be_fig.add_trace(go.Scatter(x=view.MonthLabel, y=view.Breakeven_GMV, name="Break-even GMV", mode="lines+markers", line=dict(color=INK, width=2.5)))
        be_fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
        be_fig.update_yaxes(tickformat="~s", title="₹")
        st.plotly_chart(style_fig(be_fig, height=320), use_container_width=True)

        st.markdown("**Scale Indicators — First vs. Last Month**")
        first, last = view.iloc[0], view.iloc[-1]
        drivers = pd.DataFrame({
            "Indicator": ["Active Members", "Hours / Member", "Equivalent Projects"],
            "Growth": [
                (last.Active_Earning_Members - first.Active_Earning_Members) / first.Active_Earning_Members if first.Active_Earning_Members else np.nan,
                (last.Hours_Per_Member - first.Hours_Per_Member) / first.Hours_Per_Member if first.Hours_Per_Member else np.nan,
                (last.Projects - first.Projects) / first.Projects if first.Projects else np.nan,
            ],
        })
        fig_drv = px.bar(drivers, x="Growth", y="Indicator", orientation="h", text=drivers.Growth.apply(lambda v: fmt_pct(v, 0)))
        fig_drv.update_traces(marker_color=[INK, GOLD, POSITIVE], textposition="outside")
        fig_drv.update_xaxes(tickformat=".0%")
        st.plotly_chart(style_fig(fig_drv, height=260), use_container_width=True)
        st.caption("These are scale indicators, not a causal decomposition of GMV growth.")

# ============================================================
# TAB 3 — MEMBER ECONOMICS
# ============================================================
with tab_members:
    st.markdown("### Member Economics")
    st.caption("How earning-member headcount, utilization and pay rates moved across the selected period.")

    col_a, col_b = st.columns([1.3, 1])
    with col_a:
        st.markdown("**Hours per Member vs. Active Members**")
        bubble = px.scatter(
            view,
            x="Hours_Per_Member",
            y="Active_Earning_Members",
            size="GMV",
            color="MonthLabel",
            hover_data={
                "MonthLabel": True,
                "GMV": ":,.0f",
                "Projects": ":.1f",
                "Effective_Member_Rate": ":,.0f",
                "Hours_Per_Member": ":.1f",
                "Active_Earning_Members": ":,.0f",
            },
            size_max=42,
        )
        bubble.update_layout(showlegend=False)
        bubble.update_xaxes(title="Hours / Member / Month")
        bubble.update_yaxes(title="Active Earning Members")
        st.plotly_chart(style_fig(bubble, height=380), use_container_width=True)
        st.caption("Each point is a month; bubble size represents GMV. No animation is used, so the chart remains stable and filter-responsive.")

    with col_b:
        st.markdown("**Active Earning Members Trend**")
        member_fig = go.Figure()
        member_fig.add_trace(go.Scatter(x=view.MonthLabel, y=view.Active_Earning_Members, mode="lines+markers", line=dict(color=INK, width=2.5), name="Active Members"))
        member_fig.update_yaxes(title="Members", rangemode="tozero")
        st.plotly_chart(style_fig(member_fig, height=380), use_container_width=True)
        st.caption("This is a time-series trend, not a funnel; members are not being lost at each month.")

    st.markdown("**Monthly Utilization Detail**")
    detail = view[["MonthLabel", "Active_Earning_Members", "Hours_Per_Member", "Effective_Member_Rate", "Utilization_Flag"]].copy()
    detail.columns = ["Month", "Active Members", "Hours / Member", "Effective ₹ / Hour", "Utilization"]
    detail["Effective ₹ / Hour"] = detail["Effective ₹ / Hour"].round(2)

    def highlight_util(row):
        color = SOFT_GREEN if row["Utilization"] == "On Target" else SOFT_RED
        return [f"background-color: {color}" if col == "Utilization" else "" for col in row.index]

    st.dataframe(detail.style.apply(highlight_util, axis=1), use_container_width=True, hide_index=True)

    rate_range = view.Effective_Member_Rate.max() - view.Effective_Member_Rate.min()
    if rate_range < 1:
        st.info(
            f"Effective member pay rate is flat at roughly ₹{view.Effective_Member_Rate.mean():.2f}/hr across the selected period. "
            "The model holds the weighted member rate broadly constant as scale grows."
        )

# ============================================================
# TAB 4 — SCENARIO PLANNER
# ============================================================
with tab_scenario:
    st.markdown("### Scenario Planner")
    st.caption("Scenario outputs are re-based on the selected reporting period, so the sidebar slicer affects this tab too.")

    period_gmv = view.GMV.sum()
    period_fixed = view.Fixed_Cost.sum()

    def compute_scenario(fee, var_pct, demand):
        denominator = fee - var_pct
        gmv = period_gmv * demand
        coop_rev = gmv * fee
        var_cost = gmv * var_pct
        contrib = coop_rev - var_cost
        surplus = contrib - period_fixed
        be_gmv = period_fixed / denominator if denominator > 0 else np.inf
        be_gap = gmv - be_gmv if np.isfinite(be_gmv) else -np.inf
        margin = contrib / gmv if gmv else np.nan
        return dict(gmv=gmv, coop_rev=coop_rev, var_cost=var_cost, contrib=contrib, surplus=surplus, be_gmv=be_gmv, be_gap=be_gap, margin=margin)

    scenario_names = scenarios_df["Scenario"].tolist()
    default_idx = scenario_names.index("Base") if "Base" in scenario_names else 0
    selected_name = st.radio("Scenario", scenario_names, index=default_idx, horizontal=True)
    sel_row = scenarios_df.loc[scenarios_df.Scenario == selected_name].iloc[0]
    result = compute_scenario(sel_row.Cooperative_Fee_Pct, sel_row.Variable_Cost_Pct, sel_row.Demand_Factor)
    base_row = scenarios_df.loc[scenarios_df.Scenario == "Base"].iloc[0] if "Base" in scenario_names else scenarios_df.iloc[default_idx]
    base_result = compute_scenario(base_row.Cooperative_Fee_Pct, base_row.Variable_Cost_Pct, base_row.Demand_Factor)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Scenario GMV", fmt_inr(result["gmv"], "cr"))
    with c2:
        kpi_card("Scenario Operating Surplus", fmt_inr(result["surplus"], UNIT))
    with c3:
        kpi_card("Contribution Margin", fmt_pct(result["margin"]))
    with c4:
        kpi_card("Break-even Gap", fmt_inr(result["be_gap"], UNIT))

    st.markdown("<br>", unsafe_allow_html=True)
    all_results = scenarios_df.apply(
        lambda r: compute_scenario(r.Cooperative_Fee_Pct, r.Variable_Cost_Pct, r.Demand_Factor), axis=1
    )
    scenarios_df_display = scenarios_df.copy()
    scenarios_df_display["Operating Surplus"] = [r["surplus"] for r in all_results]
    scenarios_df_display["is_selected"] = scenarios_df_display.Scenario == selected_name

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Operating Surplus by Scenario**")
        bar = px.bar(
            scenarios_df_display,
            x="Scenario",
            y="Operating Surplus",
            color="is_selected",
            color_discrete_map={True: GOLD, False: hex_to_rgba(INK, 0.33)},
        )
        bar.update_layout(showlegend=False)
        bar.update_yaxes(tickformat="~s")
        st.plotly_chart(style_fig(bar, height=340), use_container_width=True)

    with col_b:
        st.markdown("**Surplus Delta vs. Base Case**")
        scenarios_df_display["Delta vs Base"] = scenarios_df_display["Operating Surplus"] - base_result["surplus"]
        tornado = px.bar(
            scenarios_df_display[scenarios_df_display.Scenario != "Base"],
            x="Delta vs Base",
            y="Scenario",
            orientation="h",
            color="Delta vs Base",
            color_continuous_scale=[NEGATIVE, LINE, POSITIVE],
        )
        tornado.update_layout(coloraxis_showscale=False)
        tornado.update_xaxes(tickformat="~s")
        st.plotly_chart(style_fig(tornado, height=340), use_container_width=True)

    diff = base_result["surplus"] - result["surplus"]
    if selected_name == "Base":
        st.markdown(
            html(
                f"""<div class="status-banner"><b>Base case</b> uses the current {sel_row.Cooperative_Fee_Pct * 100:.0f}% fee /
                {sel_row.Variable_Cost_Pct * 100:.0f}% variable cost structure at {sel_row.Demand_Factor:.2f}x demand —
                operating surplus of {fmt_inr(result['surplus'], UNIT)} for the selected period.</div>"""
            ),
            unsafe_allow_html=True,
        )
    else:
        direction = "downside" if diff >= 0 else "upside"
        pct_of_base = abs(diff) / abs(base_result["surplus"]) if base_result["surplus"] else np.nan
        st.markdown(
            html(
                f"""<div class="status-banner">Versus Base, <b>{selected_name}</b> shifts operating surplus by
                {'-' if diff >= 0 else '+'}{fmt_inr(abs(diff), UNIT)} — a {direction} of roughly {fmt_pct(pct_of_base)}.
                </div>"""
            ),
            unsafe_allow_html=True,
        )

    with st.expander("View underlying Scenarios table"):
        st.dataframe(scenarios_df, use_container_width=True, hide_index=True)

# ============================================================
# TAB 5 — SME & EFFORT
# ============================================================
with tab_sme:
    st.markdown("### SME & Effort Economics")
    st.caption("Model assumptions and delivery-effort sensitivity. Assumptions are hypotheses, not measured live KPIs.")

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Base Avg. Project Contribution", fmt_inr(BASE_AVG_PROJECT_CONTRIBUTION, "raw"), sublabel="₹58,500 project value × 12% contribution margin")
    with c2:
        kpi_card("Annual Contribution per SME", fmt_inr(ANNUAL_CONTRIBUTION_PER_SME, "raw"), sublabel="Illustrative 2.5 projects/year assumption")
    with c3:
        kpi_card("Contribution-to-CAC Ratio", f"{CONTRIBUTION_CAC:.2f}x", sublabel="Illustrative ₹5,000 CAC assumption")

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Member Utilization — Latest Month vs. Target**")
        util_max = max(40, MEMBER_UTILIZATION_TARGET + 10, float(latest.Hours_Per_Member) * 1.25)
        util_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=float(latest.Hours_Per_Member),
                number={"suffix": " hrs", "font": {"size": 38, "color": INK}},
                gauge={
                    "axis": {"range": [0, util_max], "tickwidth": 1, "dtick": 10},
                    "bar": {"color": INK, "thickness": 0.35},
                    "steps": [
                        {"range": [0, MEMBER_UTILIZATION_TARGET], "color": SOFT_RED},
                        {"range": [MEMBER_UTILIZATION_TARGET, util_max], "color": SOFT_GREEN},
                    ],
                    "threshold": {"line": {"color": GOLD, "width": 4}, "thickness": 0.8, "value": MEMBER_UTILIZATION_TARGET},
                },
            )
        )
        st.plotly_chart(style_fig(util_gauge, height=275, margins=dict(l=25, r=25, t=35, b=15)), use_container_width=True)
        st.caption(f"Target: {MEMBER_UTILIZATION_TARGET} hrs/member/month · {latest.MonthLabel} actual shown against it.")

    with col_b:
        st.markdown("**Effort-Overrun Sensitivity**")
        eff_fig = go.Figure(
            go.Bar(
                x=["Base Member ₹/Hour", f"At {EFFORT_OVERRUN_MAX * 100:.0f}% Overrun"],
                y=[BASE_MEMBER_RATE_PER_HR, SCENARIO_EFFECTIVE_RATE_PER_HR],
                marker_color=[INK, NEGATIVE],
                text=[f"₹{BASE_MEMBER_RATE_PER_HR:,.0f}", f"₹{SCENARIO_EFFECTIVE_RATE_PER_HR:,.0f}"],
                textposition="outside",
            )
        )
        eff_fig.update_yaxes(title="Effective member ₹ / hour", rangemode="tozero")
        st.plotly_chart(style_fig(eff_fig, height=275), use_container_width=True)
        st.caption("Same member earnings, but 20% more delivery hours. This is a sensitivity test, not an observed overrun.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**KPI Target Reference**")
    kpi_targets = pd.DataFrame(
        {
            "KPI": [
                "Member Utilization (hrs/member/mo)",
                "Project Fill Rate",
                "Repeat SME GMV Share",
                "Effort Overrun (max)",
                "Payment Timeliness",
                "First-Pass Acceptance",
            ],
            "Target": [
                f"{MEMBER_UTILIZATION_TARGET} hrs",
                fmt_pct(PROJECT_FILL_RATE_TARGET),
                fmt_pct(REPEAT_SME_GMV_TARGET),
                fmt_pct(EFFORT_OVERRUN_MAX),
                fmt_pct(PAYMENT_TIMELINESS_TARGET),
                fmt_pct(FIRST_PASS_ACCEPTANCE_TARGET),
            ],
            "Measured in this dataset?": ["Yes — see gauge above", "No", "No", "No — sensitivity input", "No", "No"],
        }
    )
    st.dataframe(kpi_targets, use_container_width=True, hide_index=True)
    st.caption("Only member utilization is directly represented in the supplied monthly dataset; the other guardrails require operational source columns.")
