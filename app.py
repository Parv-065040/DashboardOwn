"""
DashboardOwn — CFO Financial Dashboard
Built entirely from data/DashboardOwn_Clean_Dataset.csv and data/Scenarios.csv.
All KPIs, growth rates, break-even math, and scenario outputs are calculated
in this file using the same formulas as the DashboardOwn Power BI DAX pack —
nothing is hardcoded from the source data itself.
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

CHART_COLORWAY = [INK, GOLD, "#7C9CBF", POSITIVE, NEGATIVE, "#AEB8C2"]

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'IBM Plex Sans', sans-serif;
    }}
    .stApp {{ background-color: {PAPER}; }}

    h1, h2, h3 {{ font-family: 'Source Serif 4', serif !important; color: {INK}; }}

    /* Hide default Streamlit chrome for a cleaner boardroom feel */
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
        padding:16px 18px; margin-bottom:6px;
    }}
    .kpi-label {{ font-size:12px; color:{SLATE}; font-weight:600; margin-bottom:8px; }}
    .kpi-value {{ font-family:'Source Serif 4', serif; font-size:26px; font-weight:600; color:{INK}; }}
    .kpi-delta {{ font-size:12px; font-weight:500; margin-top:6px; }}
    .kpi-sub {{ font-size:11px; color:{SLATE}; margin-top:4px; }}

    .status-banner {{
        border-left:4px solid {GOLD}; background:{SURFACE};
        border-radius:4px; padding:16px 18px; font-size:14.5px; line-height:1.5;
    }}
    .flag-pill {{
        display:inline-block; padding:2px 10px; border-radius:10px; font-size:12px; font-weight:600;
    }}
    .flag-good {{ background:#E4EFE9; color:{POSITIVE}; }}
    .flag-bad {{ background:#F5E7E3; color:{NEGATIVE}; }}

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
    margin=dict(l=10, r=10, t=40, b=10),
)


def html(s: str) -> str:
    """Collapse a multi-line HTML string to one line before handing it to
    st.markdown(unsafe_allow_html=True). A blank/whitespace-only interior line
    (e.g. when an optional f-string fragment is empty) can make Streamlit's
    markdown parser end the raw-HTML block early and render the remaining
    indented lines as a literal code block instead of HTML. Flattening removes
    that failure mode entirely, regardless of parser version."""
    return " ".join(line.strip() for line in s.strip().splitlines() if line.strip())


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert a '#RRGGBB' color to an 'rgba(r,g,b,a)' string. Some Plotly
    versions (e.g. 5.x, which this app targets) reject 8-digit hex-with-alpha
    colors like '#RRGGBBAA', so rgba() is the portable way to get transparency."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def style_fig(fig, title=None, height=360):
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=14, family="IBM Plex Sans"), x=0))
    fig.update_xaxes(gridcolor=LINE, zerolinecolor=LINE)
    fig.update_yaxes(gridcolor=LINE, zerolinecolor=LINE)
    return fig


# ============================================================
# 1. DATA LOADING
# ============================================================
DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_financials() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "DashboardOwn_Clean_Dataset.csv", parse_dates=["Month"])
    df = df.sort_values("Month").reset_index(drop=True)
    df["MonthLabel"] = df["Month"].dt.strftime("%b %Y")
    return df


@st.cache_data
def load_scenarios() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "Scenarios.csv")


try:
    raw = load_financials()
    scenarios_df = load_scenarios()
except FileNotFoundError as e:
    st.error(
        "Could not find the data files. Make sure `data/DashboardOwn_Clean_Dataset.csv` "
        "and `data/Scenarios.csv` sit alongside app.py in the repo."
    )
    st.stop()

# ============================================================
# 2. MODEL ASSUMPTIONS (as stated in the DashboardOwn DAX pack)
# ============================================================
FEE_PCT = 0.15
VARIABLE_PCT = 0.03
BE_DIVISOR = FEE_PCT - VARIABLE_PCT  # 0.12
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
# 3. DERIVED FIELDS — every metric computed here, not in the CSV
# ============================================================
df = raw.copy()

df["Cooperative_Take_Rate"] = df.Cooperative_Revenue / df.GMV
df["Member_Share_Pct"] = df.Member_Earnings / df.GMV
df["Contribution_Margin_Pct"] = df.Contribution / df.GMV
df["Effective_Member_Rate"] = df.Member_Earnings / df.Total_Member_Hours
df["GMV_Per_Member"] = df.GMV / df.Active_Earning_Members
df["Contribution_Per_Project"] = df.Contribution / df.Projects
df["Avg_Project_Value"] = df.GMV / df.Projects
df["Member_Earnings_Per_Project"] = df.Member_Earnings / df.Projects

df["Breakeven_GMV"] = df.Fixed_Cost / BE_DIVISOR
df["Breakeven_Projects"] = df.Fixed_Cost / (AVG_PROJECT_VALUE * BE_DIVISOR)
df["Breakeven_Gap"] = df.GMV - df.Breakeven_GMV
df["Breakeven_Coverage_Pct"] = df.GMV / df.Breakeven_GMV

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
    if row.Hours_Per_Member < 20:
        return "Warning: member utilization is below the pilot target."
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

# SME economics — constants stated in the DAX pack's model assumptions
BASE_AVG_PROJECT_CONTRIBUTION = AVG_PROJECT_VALUE * BE_DIVISOR
ANNUAL_CONTRIBUTION_PER_SME = BASE_AVG_PROJECT_CONTRIBUTION * 2.5
CONTRIBUTION_CAC = ANNUAL_CONTRIBUTION_PER_SME / 5000

# Effort-overrun measures (Section 7) — computed on full-period totals
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
        return f"₹{value/1e7:,.2f} Cr"
    if unit == "lakh":
        return f"₹{value/1e5:,.1f} L"
    return f"₹{value:,.0f}"


def fmt_pct(value, decimals=1):
    if pd.isna(value):
        return "—"
    return f"{value*100:.{decimals}f}%"


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
# 5. SIDEBAR
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
    st.caption("CFO Financial Dashboard · FY2026")
    st.markdown("---")

    month_options = df["MonthLabel"].tolist()
    month_range = st.select_slider(
        "Reporting period",
        options=month_options,
        value=(month_options[0], month_options[-1]),
        help="Filters Executive Summary, Growth and Member Economics views. Scenario Planner always uses the full year.",
    )
    start_idx = month_options.index(month_range[0])
    end_idx = month_options.index(month_range[1])
    view = df.iloc[start_idx : end_idx + 1].reset_index(drop=True)

    currency_unit = st.radio("Currency display", ["Auto", "Lakh (L)", "Crore (Cr)", "Raw ₹"], index=0)
    unit_map = {"Auto": "auto", "Lakh (L)": "lakh", "Crore (Cr)": "cr", "Raw ₹": "raw"}
    UNIT = unit_map[currency_unit]

    st.markdown("---")
    st.caption(
        "All figures are calculated live from `DashboardOwn_Clean_Dataset.csv` "
        "using the same formulas as the DashboardOwn Power BI DAX pack — nothing "
        "shown here is hardcoded."
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

# ---------------------------------------------------------------
# TAB 0 — COVER
# ---------------------------------------------------------------
with tab_cover:
    st.markdown(
        html(
            f"""
        <div style="background:{INK}; border-radius:10px; padding:56px 48px; color:white; margin-bottom:24px;">
            <div style="display:flex; align-items:center; margin-bottom:28px;">
                <div style="width:56px; height:56px; border-radius:10px; background:{GOLD}; color:{INK};
                            display:flex; align-items:center; justify-content:center; font-family:'Source Serif 4', serif;
                            font-weight:700; font-size:24px; margin-right:16px; border:1px solid rgba(255,255,255,0.4);">DO</div>
                <div>
                    <div style="font-size:13px; letter-spacing:0.02em; color:{GOLD};">CFO FINANCIAL REVIEW — FY2026</div>
                    <div style="font-family:'Source Serif 4', serif; font-size:22px; font-weight:600;">DashboardOwn</div>
                </div>
            </div>
            <div style="font-family:'Source Serif 4', serif; font-size:38px; font-weight:600; max-width:720px; line-height:1.15; margin-bottom:16px;">
                Cooperative platform economics, from GMV to operating surplus.
            </div>
            <div style="font-size:15.5px; color:rgba(255,255,255,0.75); max-width:560px; line-height:1.6;">
                A twelve-month read on the DashboardOwn marketplace: member earnings, cooperative
                take rate, break-even position, and where the model is headed next — built live
                from the underlying financial data, with an interactive what-if scenario planner.
            </div>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )

    annual_gmv = df.GMV.sum()
    annual_surplus = df.Operating_Surplus.sum()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("FY2026 Total GMV", fmt_inr(annual_gmv, "cr"))
    with c2:
        kpi_card("FY2026 Operating Surplus", fmt_inr(annual_surplus, UNIT if UNIT != "auto" else "lakh"))
    with c3:
        kpi_card("Active Members, Dec 2026", f"{int(df.iloc[-1].Active_Earning_Members)}")
    with c4:
        kpi_card("Cooperative Fee / Variable Cost", f"{FEE_PCT*100:.0f}% / {VARIABLE_PCT*100:.0f}%")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**How to read this dashboard**")
    st.markdown(
        """
        - **Executive Summary** — current-period KPIs, the revenue-to-surplus bridge, and auto-generated CFO commentary
        - **Growth & Trend** — month-over-month growth rates and where GMV is composed from
        - **Member Economics** — headcount, utilization and earnings-rate trends across the cooperative
        - **Scenario Planner** — live what-if modelling across six fee/cost/demand scenarios
        - **SME & Effort** — unit economics assumptions and effort-overrun sensitivity
        """
    )
    st.caption(f"Reporting period selected: {month_range[0]} – {month_range[1]} · use the sidebar to change it.")

# ---------------------------------------------------------------
# TAB 1 — EXECUTIVE SUMMARY
# ---------------------------------------------------------------
with tab_exec:
    st.markdown(f"### Executive Summary")
    st.caption(f"Latest month in view: **{latest.MonthLabel}**" + (f" · compared against **{prior.MonthLabel}**" if prior is not None else ""))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        delta = latest.GMV_MoM if prior is not None else None
        kpi_card("Total GMV", fmt_inr(latest.GMV, UNIT), fmt_pct(delta) + " MoM" if delta is not None and not pd.isna(delta) else None, positive=(delta or 0) >= 0)
    with c2:
        delta = latest.Surplus_MoM if prior is not None else None
        kpi_card("Operating Surplus", fmt_inr(latest.Operating_Surplus, UNIT), fmt_pct(delta) + " MoM" if delta is not None and not pd.isna(delta) else None, positive=(delta or 0) >= 0)
    with c3:
        kpi_card("Contribution Margin %", fmt_pct(latest.Contribution_Margin_Pct))
    with c4:
        kpi_card("Break-even Coverage %", fmt_pct(latest.Breakeven_Coverage_Pct))

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.4, 1])

    with col_left:
        st.markdown("**Revenue → Operating Surplus Bridge**")
        wf = go.Figure(
            go.Waterfall(
                orientation="v",
                measure=["relative", "relative", "total", "relative", "total"],
                x=["Cooperative Revenue", "Variable Cost", "Contribution", "Fixed Cost", "Operating Surplus"],
                y=[latest.Cooperative_Revenue, -latest.Variable_Cost, 0, -latest.Fixed_Cost, 0],
                text=[fmt_inr(latest.Cooperative_Revenue, UNIT), f"-{fmt_inr(latest.Variable_Cost, UNIT)}", fmt_inr(latest.Contribution, UNIT), f"-{fmt_inr(latest.Fixed_Cost, UNIT)}", fmt_inr(latest.Operating_Surplus, UNIT)],
                connector=dict(line=dict(color=LINE)),
                increasing=dict(marker=dict(color=INK)),
                decreasing=dict(marker=dict(color=NEGATIVE)),
                totals=dict(marker=dict(color=GOLD)),
            )
        )
        st.plotly_chart(style_fig(wf, height=380), use_container_width=True)
        st.caption(f"Bridge shown for {latest.MonthLabel}. Totals are auto-computed by Plotly's waterfall logic, not hand-entered.")

    with col_right:
        st.markdown("**Break-even Coverage**")
        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=latest.Breakeven_Coverage_Pct * 100,
                number={"suffix": "%"},
                gauge={
                    "axis": {"range": [0, max(150, latest.Breakeven_Coverage_Pct * 120)]},
                    "bar": {"color": INK},
                    "steps": [
                        {"range": [0, 100], "color": "#F5E7E3"},
                        {"range": [100, max(150, latest.Breakeven_Coverage_Pct * 120)], "color": "#E4EFE9"},
                    ],
                    "threshold": {"line": {"color": GOLD, "width": 4}, "thickness": 0.8, "value": 100},
                },
            )
        )
        st.plotly_chart(style_fig(gauge, height=230), use_container_width=True)

        good_health = latest.Financial_Health_Flag == "Healthy"
        good_be = latest.Breakeven_Flag == "Above Break-even"
        good_util = latest.Utilization_Flag == "On Target"
        st.markdown(
            html(
                f"""
            <div class="status-banner">
                Financial health: {flag_pill(latest.Financial_Health_Flag, good_health)}<br><br>
                Break-even position: {flag_pill(latest.Breakeven_Flag, good_be)}<br><br>
                Member utilization: {flag_pill(latest.Utilization_Flag, good_util)}
                <hr>
                <b>CEO Status:</b> {latest.CEO_Status}<br>
                <b>Growth Signal:</b> {latest.CEO_Growth_Signal}
            </div>
            """
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**GMV & Operating Surplus Trend**")
    trend = go.Figure()
    trend.add_bar(x=view.MonthLabel, y=view.GMV, name="GMV", marker_color=hex_to_rgba(GOLD, 0.55), yaxis="y")
    trend.add_trace(go.Scatter(x=view.MonthLabel, y=view.Operating_Surplus, name="Operating Surplus", mode="lines+markers", line=dict(color=INK, width=2.5), yaxis="y2"))
    trend.update_layout(
        yaxis=dict(title="GMV", side="left"),
        yaxis2=dict(title="Operating Surplus", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(style_fig(trend, height=360), use_container_width=True)

# ---------------------------------------------------------------
# TAB 2 — GROWTH & TREND
# ---------------------------------------------------------------
with tab_growth:
    st.markdown("### Growth & Trend")
    st.caption("Month-over-month growth and where GMV is composed from, across the selected reporting period.")

    growth_view = view.dropna(subset=["GMV_MoM"])
    fig_mom = go.Figure()
    if len(growth_view) > 0:
        fig_mom.add_trace(go.Scatter(x=growth_view.MonthLabel, y=growth_view.GMV_MoM, name="GMV MoM %", mode="lines+markers", line=dict(color=INK)))
        fig_mom.add_trace(go.Scatter(x=growth_view.MonthLabel, y=growth_view.Revenue_MoM, name="Revenue MoM %", mode="lines+markers", line=dict(color=GOLD)))
        fig_mom.add_trace(go.Scatter(x=growth_view.MonthLabel, y=growth_view.Surplus_MoM, name="Surplus MoM %", mode="lines+markers", line=dict(color=POSITIVE)))
        fig_mom.update_yaxes(tickformat=".0%")
        fig_mom.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
        st.plotly_chart(style_fig(fig_mom, "Month-over-Month Growth Rates", height=360), use_container_width=True)
    else:
        st.info("Select at least two consecutive months in the sidebar to see month-over-month growth.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**GMV Composition — Where the Money Goes**")
        sun_labels = ["GMV", "Member Earnings", "Cooperative Revenue", "Variable Cost", "Contribution", "Fixed Cost", "Operating Surplus"]
        gmv_total = view.GMV.sum()
        member_total = view.Member_Earnings.sum()
        coop_total = view.Cooperative_Revenue.sum()
        var_total = view.Variable_Cost.sum()
        contrib_total = view.Contribution.sum()
        fixed_total = view.Fixed_Cost.sum()
        surplus_total = view.Operating_Surplus.sum()
        sun_parents = ["", "GMV", "GMV", "Cooperative Revenue", "Cooperative Revenue", "Contribution", "Contribution"]
        sun_values = [gmv_total, member_total, coop_total, var_total, contrib_total, fixed_total, max(surplus_total, 0)]
        sun = go.Figure(
            go.Sunburst(
                labels=sun_labels,
                parents=sun_parents,
                values=sun_values,
                branchvalues="total",
                marker=dict(colors=[INK, "#7C9CBF", GOLD, NEGATIVE, "#8DA9C4", NEGATIVE, POSITIVE]),
            )
        )
        st.plotly_chart(style_fig(sun, height=380), use_container_width=True)
        st.caption("Sized by cumulative ₹ across the selected period. Operating Surplus is floored at zero for display where the period nets negative.")

    with col_b:
        st.markdown("**Revenue & Cost Layers by Month**")
        stack = go.Figure()
        stack.add_bar(x=view.MonthLabel, y=view.Cooperative_Revenue, name="Cooperative Revenue", marker_color=INK)
        stack.add_bar(x=view.MonthLabel, y=view.Variable_Cost, name="Variable Cost", marker_color=GOLD)
        stack.add_bar(x=view.MonthLabel, y=view.Fixed_Cost, name="Fixed Cost", marker_color="#AEB8C2")
        stack.update_layout(barmode="stack", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
        st.plotly_chart(style_fig(stack, height=380), use_container_width=True)

    st.markdown("**GMV Growth Drivers — First vs. Last Month in View**")
    first, last = view.iloc[0], view.iloc[-1]
    drivers = pd.DataFrame(
        {
            "Driver": ["Active Members", "Hours / Member", "Projects"],
            "Growth": [
                (last.Active_Earning_Members - first.Active_Earning_Members) / first.Active_Earning_Members if first.Active_Earning_Members else np.nan,
                (last.Hours_Per_Member - first.Hours_Per_Member) / first.Hours_Per_Member if first.Hours_Per_Member else np.nan,
                (last.Projects - first.Projects) / first.Projects if first.Projects else np.nan,
            ],
        }
    )
    fig_drv = px.bar(drivers, x="Growth", y="Driver", orientation="h", text=drivers.Growth.apply(lambda v: fmt_pct(v, 0)))
    fig_drv.update_traces(marker_color=[INK, GOLD, POSITIVE])
    fig_drv.update_xaxes(tickformat=".0%")
    st.plotly_chart(style_fig(fig_drv, height=260), use_container_width=True)
    st.caption("A static stand-in for a click-to-explain decomposition tree, comparing the first and last month currently in view.")

# ---------------------------------------------------------------
# TAB 3 — MEMBER ECONOMICS
# ---------------------------------------------------------------
with tab_members:
    st.markdown("### Member Economics")
    st.caption("How earning-member headcount, utilization and pay rates moved together across the selected period.")

    col_a, col_b = st.columns([1.3, 1])
    with col_a:
        st.markdown("**Hours per Member vs. Active Members** *(bubble size = GMV, animated by month)*")
        bubble = px.scatter(
            view,
            x="Hours_Per_Member",
            y="Active_Earning_Members",
            size="GMV",
            color="MonthLabel",
            animation_frame="MonthLabel",
            size_max=48,
            range_x=[0, view.Hours_Per_Member.max() * 1.2],
            range_y=[0, view.Active_Earning_Members.max() * 1.2],
        )
        bubble.update_layout(showlegend=False)
        st.plotly_chart(style_fig(bubble, height=380), use_container_width=True)

    with col_b:
        st.markdown("**Active Earning Members Growth**")
        funnel = go.Figure(
            go.Funnel(
                y=view.MonthLabel,
                x=view.Active_Earning_Members,
                textinfo="value",
                marker=dict(color=INK),
                connector=dict(line=dict(color=LINE)),
            )
        )
        st.plotly_chart(style_fig(funnel, height=380), use_container_width=True)
        st.caption("Read top-to-bottom as cohort growth over time, not conversion drop-off.")

    st.markdown("**Monthly Utilization Detail**")
    detail = view[["MonthLabel", "Active_Earning_Members", "Hours_Per_Member", "Effective_Member_Rate", "Utilization_Flag"]].copy()
    detail.columns = ["Month", "Active Members", "Hours / Member", "Effective ₹ / Hour", "Utilization"]
    detail["Effective ₹ / Hour"] = detail["Effective ₹ / Hour"].round(2)

    def highlight_util(row):
        color = "#E4EFE9" if row["Utilization"] == "On Target" else "#F5E7E3"
        return [f"background-color: {color}" if col == "Utilization" else "" for col in row.index]

    st.dataframe(detail.style.apply(highlight_util, axis=1), use_container_width=True, hide_index=True)

    rate_range = view.Effective_Member_Rate.max() - view.Effective_Member_Rate.min()
    if rate_range < 1:
        st.info(
            f"Effective member pay rate is flat at roughly ₹{view.Effective_Member_Rate.mean():.2f}/hr across every month in view — "
            "the model holds this constant as scale grows. Worth confirming with the CFO whether that's a deliberate policy."
        )

# ---------------------------------------------------------------
# TAB 4 — SCENARIO PLANNER
# ---------------------------------------------------------------
with tab_scenario:
    st.markdown("### Scenario Planner")
    st.caption("Annual figures re-based on fee %, variable cost % and demand factor. Always uses the full FY2026 dataset, independent of the sidebar date filter.")

    annual_gmv = df.GMV.sum()
    annual_fixed = df.Fixed_Cost.sum()

    def compute_scenario(fee, var_pct, demand):
        gmv = annual_gmv * demand
        coop_rev = gmv * fee
        var_cost = gmv * var_pct
        contrib = coop_rev - var_cost
        surplus = contrib - annual_fixed
        be_gmv = annual_fixed / (fee - var_pct)
        be_gap = gmv - be_gmv
        margin = contrib / gmv if gmv else np.nan
        return dict(gmv=gmv, coop_rev=coop_rev, var_cost=var_cost, contrib=contrib, surplus=surplus, be_gmv=be_gmv, be_gap=be_gap, margin=margin)

    scenario_names = scenarios_df["Scenario"].tolist()
    selected_name = st.radio("Scenario", scenario_names, horizontal=True)
    sel_row = scenarios_df.loc[scenarios_df.Scenario == selected_name].iloc[0]
    result = compute_scenario(sel_row.Cooperative_Fee_Pct, sel_row.Variable_Cost_Pct, sel_row.Demand_Factor)
    base_row = scenarios_df.loc[scenarios_df.Scenario == "Base"].iloc[0]
    base_result = compute_scenario(base_row.Cooperative_Fee_Pct, base_row.Variable_Cost_Pct, base_row.Demand_Factor)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Scenario GMV", fmt_inr(result["gmv"], "cr"))
    with c2:
        kpi_card("Scenario Operating Surplus", fmt_inr(result["surplus"], UNIT))
    with c3:
        kpi_card("Contribution Margin %", fmt_pct(result["margin"]))
    with c4:
        kpi_card("Break-even Gap", fmt_inr(result["be_gap"], UNIT))

    st.markdown("<br>", unsafe_allow_html=True)
    all_results = scenarios_df.apply(lambda r: compute_scenario(r.Cooperative_Fee_Pct, r.Variable_Cost_Pct, r.Demand_Factor), axis=1)
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
        st.plotly_chart(style_fig(tornado, height=340), use_container_width=True)

    diff = base_result["surplus"] - result["surplus"]
    if selected_name == "Base":
        st.markdown(
            html(
                f"""<div class="status-banner"><b>Base case</b> holds the current {FEE_PCT*100:.0f}% fee / {VARIABLE_PCT*100:.0f}% variable
            cost structure at 1.0x demand — annual operating surplus of {fmt_inr(result['surplus'], UNIT)}.</div>"""
            ),
            unsafe_allow_html=True,
        )
    else:
        direction = "a downside" if diff >= 0 else "an upside"
        pct_of_base = abs(diff) / base_result["surplus"] if base_result["surplus"] else np.nan
        st.markdown(
            html(
                f"""<div class="status-banner">Versus Base, <b>{selected_name}</b> shifts annual operating surplus by
            {'-' if diff >= 0 else '+'}{fmt_inr(abs(diff), UNIT)} — {direction} of roughly {fmt_pct(pct_of_base)}.</div>"""
            ),
            unsafe_allow_html=True,
        )

    with st.expander("View underlying Scenarios table"):
        st.dataframe(scenarios_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------
# TAB 5 — SME & EFFORT
# ---------------------------------------------------------------
with tab_sme:
    st.markdown("### SME & Effort Economics")
    st.caption("Unit-economics assumptions stated in the model, and sensitivity to a 20% effort overrun.")

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Base Avg. Project Contribution", fmt_inr(BASE_AVG_PROJECT_CONTRIBUTION, "raw"), sublabel="₹58,500 project value × 12% margin")
    with c2:
        kpi_card("Annual Contribution per SME", fmt_inr(ANNUAL_CONTRIBUTION_PER_SME, "raw"), sublabel="Assumes 2.5 projects/year")
    with c3:
        kpi_card("Contribution-to-CAC Ratio", f"{CONTRIBUTION_CAC:.2f}x", sublabel="Against a ₹5,000 CAC assumption")

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Member Utilization — Latest Month vs. Target**")
        util_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=latest.Hours_Per_Member,
                number={"suffix": " hrs"},
                gauge={
                    "axis": {"range": [0, max(40, latest.Hours_Per_Member * 1.3)]},
                    "bar": {"color": INK},
                    "threshold": {"line": {"color": GOLD, "width": 4}, "thickness": 0.8, "value": MEMBER_UTILIZATION_TARGET},
                    "steps": [{"range": [0, MEMBER_UTILIZATION_TARGET], "color": "#F5E7E3"}, {"range": [MEMBER_UTILIZATION_TARGET, max(40, latest.Hours_Per_Member * 1.3)], "color": "#E4EFE9"}],
                },
            )
        )
        st.plotly_chart(style_fig(util_gauge, height=260), use_container_width=True)
        st.caption(f"Target: {MEMBER_UTILIZATION_TARGET} hrs/member/month · {latest.MonthLabel} actual shown against it.")

    with col_b:
        st.markdown("**Effort-Overrun Sensitivity**")
        eff_fig = go.Figure(
            go.Bar(
                x=["Base Member ₹/Hour", f"At {EFFORT_OVERRUN_MAX*100:.0f}% Effort Overrun"],
                y=[BASE_MEMBER_RATE_PER_HR, SCENARIO_EFFECTIVE_RATE_PER_HR],
                marker_color=[INK, NEGATIVE],
                text=[f"₹{BASE_MEMBER_RATE_PER_HR:,.2f}", f"₹{SCENARIO_EFFECTIVE_RATE_PER_HR:,.2f}"],
                textposition="outside",
            )
        )
        st.plotly_chart(style_fig(eff_fig, height=260), use_container_width=True)
        st.caption("Effective member ₹/hour if delivery hours run 20% over plan for the same total member earnings — computed from full-period totals.")

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
            "Measured in this dataset?": ["Yes — see gauge above", "No", "No", "No (used as a sensitivity input above)", "No", "No"],
        }
    )
    st.dataframe(kpi_targets, use_container_width=True, hide_index=True)
    st.caption(
        "Targets are the guardrails defined in the DAX pack's model assumptions. Only Member Utilization has an "
        "actual value in the provided dataset — the rest would need their own source columns to track live."
    )
