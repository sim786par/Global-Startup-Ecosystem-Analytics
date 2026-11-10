"""
app.py
Global Startup Ecosystem Analytics — Streamlit dashboard.

Run from the project root:
    streamlit run app.py

Expected .env:
    DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/startup_analytics

This dashboard introspects the PostgreSQL schema and supports common table/column
name variants. If your schema differs, update TABLE_CANDIDATES and COLUMN_CANDIDATES
in sql_ana.py rather than changing the dashboard queries everywhere.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sql_ana import (
    get_engine, table_info, resolve_table, get_columns, resolve_column,
    read_table, get_startup_funding, get_funding_records,
    get_investor_data, get_quarterly_data
)

load_dotenv()

# ------------------------------ Page setup ---------------------------------
st.set_page_config(
    page_title="Global Startup Ecosystem Analytics",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------ Styling ------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #F5F7FB; color: #1F2937; }
[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid #263244;
}
[data-testid="stSidebar"] * { color: #E5E7EB !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: transparent;
    border-radius: 9px;
    padding: 8px 10px;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #263449;
}
.block-container { padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1600px; }
h1, h2, h3 { color: #111827; letter-spacing: -0.035em; }
h1 { font-size: 2rem !important; font-weight: 800 !important; }
h2 { font-size: 1.15rem !important; font-weight: 700 !important; }
h3 { font-size: 1rem !important; font-weight: 700 !important; }
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E7EAF1;
    padding: 16px 17px;
    border-radius: 13px;
    box-shadow: 0 3px 12px rgba(15, 23, 42, 0.035);
}
[data-testid="stMetricLabel"] { color: #6B7280 !important; font-size: .78rem; }
[data-testid="stMetricValue"] { color: #111827 !important; font-weight: 800; }
div[data-testid="stPlotlyChart"] {
    background: #FFFFFF;
    border: 1px solid #E7EAF1;
    border-radius: 13px;
    padding: 8px;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #E7EAF1;
    border-radius: 12px;
    overflow: hidden;
}
div.stButton > button {
    border-radius: 9px;
    border: 1px solid #D9DDF0;
    font-weight: 600;
}
.small-muted { color: #6B7280; font-size: .83rem; }
.section-gap { margin-top: 1rem; }
</style>
""", unsafe_allow_html=True)

PRIMARY = "#4F46E5"
CYAN = "#06B6D4"
GREEN = "#10B981"
RED = "#EF4444"
NAVY = "#111827"
PALETTE = ["#4F46E5", "#06B6D4", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#64748B"]

# ------------------------------ Data layer ---------------------------------
@st.cache_resource
def load_engine():
    return get_engine()


@st.cache_data(ttl=300, show_spinner=False)
def load_all_data():
    engine = load_engine()
    return {
        "info": table_info(engine),
        "startup": get_startup_funding(engine),
        "funding": get_funding_records(engine),
        "investors": get_investor_data(engine),
        "quarterly": get_quarterly_data(engine),
    }


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    # Standardize common source-column names to dashboard names.
    mapping = {
        "name": "startup_name", "company_name": "startup_name",
        "sector": "industry", "country_name": "country",
        "employee_count": "employees", "num_employees": "employees",
        "revenue_stage": "revenue_status", "profitability_status": "revenue_status",
        "stage": "funding_stage", "amount": "amount_raised",
        "amount_million_usd": "amount_raised", "funding_amount": "amount_raised",
        "post_money_valuation": "valuation", "valuation_million_usd": "valuation",
        "date": "funding_date", "announced_date": "funding_date",
        "type": "investor_type", "assets_under_management": "aum",
        "aum_million_usd": "aum", "quarter_label": "quarter",
        "year_quarter": "quarter", "growth_rate": "market_growth",
        "growth_pct": "market_growth", "total_deals": "deal_count",
        "number_of_deals": "deal_count",
    }
    for old, new in mapping.items():
        if old in out.columns and new not in out.columns:
            out = out.rename(columns={old: new})
    return out


def numeric_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[col], errors="coerce")


def money(value, suffix="M"):
    if pd.isna(value):
        return "—"
    value = float(value)
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:,.1f}K"
    return f"${value:,.2f}"


def first_existing(df, choices):
    for col in choices:
        if col in df.columns:
            return col
    return None


def add_page_header(title, subtitle):
    c1, c2 = st.columns([5, 1.4])
    with c1:
        st.markdown(f"<div class='small-muted'>GLOBAL STARTUP ANALYTICS  /  INTELLIGENCE</div>", unsafe_allow_html=True)
        st.title(title)
        st.markdown(f"<div class='small-muted'>{subtitle}</div>", unsafe_allow_html=True)
    with c2:
        st.write("")
        if st.button("↻  Refresh data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()


def kpi_row(items):
    cols = st.columns(len(items))
    for col, (label, value, delta, help_text) in zip(cols, items):
        with col:
            st.metric(label, value, delta=delta, help=help_text)


def chart_layout(fig, height=310):
    fig.update_layout(
        height=height,
        margin=dict(l=15, r=15, t=42, b=15),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter, sans-serif", color="#374151", size=11),
        title_font=dict(size=14, color="#111827"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(bgcolor="#111827", font_color="white"),
    )
    fig.update_xaxes(showgrid=False, linecolor="#E5E7EB")
    fig.update_yaxes(gridcolor="#EEF0F5", zeroline=False)
    return fig


def show_empty(message="No matching data is available for this chart."):
    st.info(message)


def apply_filters(df, filters):
    if df.empty:
        return df
    result = df.copy()
    for col, selected in filters.items():
        if col in result.columns and selected:
            result = result[result[col].astype(str).isin([str(x) for x in selected])]
    return result


def sidebar_navigation():
    with st.sidebar:
        st.markdown("## 🚀 GLOBAL STARTUP")
        st.caption("VENTURE INTELLIGENCE PLATFORM")
        st.markdown("---")
        st.markdown("**ANALYTICS CORE**")
        page = st.radio(
            "Navigate",
            ["Startup Analysis", "Funding Analysis", "Investor Analysis", "Market Analysis"],
            label_visibility="collapsed",
            key="page_nav"
        )
        st.markdown("---")
        st.caption("WORKSPACE")
        st.markdown("⚙️ Settings")
        st.markdown("ⓘ About Project")
        st.markdown("---")
        st.caption("◉ Analytics Workspace")
        st.caption("Global Startup Ecosystem")
    return page


# ------------------------------ Load data ----------------------------------
page = sidebar_navigation()

try:
    data = load_all_data()
except Exception as exc:
    st.error("Could not connect to PostgreSQL.")
    st.markdown(
        "Check that PostgreSQL is running, the database exists, and your "
        "`DATABASE_URL` in `.env` is correct."
    )
    with st.expander("Technical details"):
        st.exception(exc)
    st.stop()

startup = normalize_columns(data["startup"])
funding = normalize_columns(data["funding"])
investors = normalize_columns(data["investors"])
quarterly = normalize_columns(data["quarterly"])

with st.sidebar:
    st.markdown("---")
    if st.button("Clear dashboard cache", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Data refresh cache: 5 minutes")

# Global date filter applied to funding-related analyses.
if not funding.empty and "funding_date" in funding.columns:
    funding["funding_date"] = pd.to_datetime(funding["funding_date"], errors="coerce")

# ------------------------------ Page 1 -------------------------------------
if page == "Startup Analysis":
    add_page_header(
        "Startup Intelligence",
        "Explore startup distribution, industry performance, business scale and revenue status across global markets."
    )

    if startup.empty:
        show_empty("The startup table could not be found or contains no records.")
        st.stop()

    startup = normalize_columns(startup)
    country_col = first_existing(startup, ["country"])
    industry_col = first_existing(startup, ["industry"])
    revenue_col = first_existing(startup, ["revenue_status"])
    employee_col = first_existing(startup, ["employees"])
    name_col = first_existing(startup, ["startup_name"])

    with st.container():
        f1, f2, f3, f4 = st.columns([1.25, 1.25, 1.25, 1.1])
        country_options = sorted(startup[country_col].dropna().astype(str).unique()) if country_col else []
        industry_options = sorted(startup[industry_col].dropna().astype(str).unique()) if industry_col else []
        revenue_options = sorted(startup[revenue_col].dropna().astype(str).unique()) if revenue_col else []
        with f1:
            selected_countries = st.multiselect("Geographic scope", country_options, placeholder="All countries")
        with f2:
            selected_industries = st.multiselect("Industry sector", industry_options, placeholder="All industries")
        with f3:
            selected_revenue = st.multiselect("Revenue status", revenue_options, placeholder="All statuses")
        with f4:
            employee_range = None
            if employee_col:
                emp = numeric_series(startup, employee_col).dropna()
                if not emp.empty:
                    low, high = int(emp.min()), int(emp.max())
                    employee_range = st.slider("Headcount range", low, max(low, high), (low, max(low, high)))

    sf = startup.copy()
    if country_col and selected_countries:
        sf = sf[sf[country_col].astype(str).isin(selected_countries)]
    if industry_col and selected_industries:
        sf = sf[sf[industry_col].astype(str).isin(selected_industries)]
    if revenue_col and selected_revenue:
        sf = sf[sf[revenue_col].astype(str).isin(selected_revenue)]
    if employee_col and employee_range:
        emp_values = numeric_series(sf, employee_col)
        sf = sf[emp_values.between(employee_range[0], employee_range[1])]

    total_startups = len(sf)
    total_industries = sf[industry_col].nunique() if industry_col else 0
    total_countries = sf[country_col].nunique() if country_col else 0
    avg_employees = numeric_series(sf, employee_col).mean() if employee_col else np.nan

    kpi_row([
        ("TOTAL STARTUPS", f"{total_startups:,}", None, "Number of startups after selected filters."),
        ("TRACKED INDUSTRIES", f"{total_industries:,}", None, "Distinct industries in the filtered dataset."),
        ("COUNTRIES REPRESENTED", f"{total_countries:,}", None, "Distinct countries in the filtered dataset."),
        ("AVERAGE HEADCOUNT", f"{avg_employees:,.0f}" if pd.notna(avg_employees) else "—", None, "Mean employee count where available."),
    ])

    left, right = st.columns([1.15, 1])
    with left:
        st.subheader("Startup Distribution by Country")
        if country_col:
            geo = sf[country_col].value_counts().rename_axis("country").reset_index(name="startup_count")
            # Plotly's location matching works best with ISO-3. Fall back to a ranked bar chart.
            iso_map = {
                "United States": "USA", "United States Of America": "USA", "USA": "USA",
                "United Kingdom": "GBR", "UK": "GBR", "India": "IND", "Canada": "CAN",
                "Germany": "DEU", "France": "FRA", "Singapore": "SGP", "Australia": "AUS",
                "China": "CHN", "Japan": "JPN", "Israel": "ISR", "Netherlands": "NLD",
                "Sweden": "SWE", "Switzerland": "CHE", "Brazil": "BRA",
            }
            geo["iso"] = geo["country"].map(iso_map)
            if geo["iso"].notna().sum() >= 3:
                fig = px.choropleth(
                    geo.dropna(subset=["iso"]), locations="iso", color="startup_count",
                    hover_name="country", color_continuous_scale=["#E0E7FF", PRIMARY, "#312E81"],
                    title="Startup footprint by country"
                )
            else:
                fig = px.bar(geo.head(15).sort_values("startup_count"), x="startup_count", y="country",
                             orientation="h", color_discrete_sequence=[PRIMARY], title="Top countries by startup count")
            st.plotly_chart(chart_layout(fig, 340), use_container_width=True)
        else:
            show_empty("Country column not found.")
    with right:
        st.subheader("Startups by Industry")
        if industry_col:
            ind = sf[industry_col].value_counts().head(12).sort_values().rename_axis("industry").reset_index(name="count")
            fig = px.bar(ind, x="count", y="industry", orientation="h", color_discrete_sequence=[PRIMARY])
            st.plotly_chart(chart_layout(fig, 340), use_container_width=True)
        else:
            show_empty("Industry column not found.")

    left, right = st.columns(2)
    with left:
        st.subheader("Revenue Status Breakdown")
        if revenue_col and not sf[revenue_col].dropna().empty:
            rev = sf[revenue_col].value_counts().rename_axis("status").reset_index(name="count")
            fig = px.pie(rev, names="status", values="count", hole=.66, color_discrete_sequence=PALETTE)
            fig.update_traces(textposition="inside", textinfo="percent")
            st.plotly_chart(chart_layout(fig, 290), use_container_width=True)
        else:
            show_empty("Revenue status data is unavailable.")
    with right:
        st.subheader("Employee Size Distribution")
        if employee_col:
            emp = numeric_series(sf, employee_col).dropna()
            if not emp.empty:
                bins = [-1, 10, 50, 200, 500, float("inf")]
                labels = ["1–10", "11–50", "51–200", "201–500", "500+"]
                groups = pd.cut(emp, bins=bins, labels=labels)
                counts = groups.value_counts().reindex(labels, fill_value=0).rename_axis("size").reset_index(name="startups")
                fig = px.bar(counts, x="size", y="startups", color_discrete_sequence=[CYAN])
                st.plotly_chart(chart_layout(fig, 290), use_container_width=True)
            else:
                show_empty("Employee values are not numeric.")
        else:
            show_empty("Employee count column not found.")

    st.subheader("Featured Startup Directory")
    if not sf.empty:
        display_cols = [c for c in ["startup_name", "industry", "country", "employees", "revenue_status", "total_funding"] if c in sf.columns]
        if display_cols:
            table = sf[display_cols].copy()
            if "total_funding" in table.columns:
                table["total_funding"] = pd.to_numeric(table["total_funding"], errors="coerce")
            st.dataframe(table.sort_values("total_funding", ascending=False, na_position="last") if "total_funding" in table else table,
                         use_container_width=True, hide_index=True)
            st.download_button("↓ Export startup CSV", sf.to_csv(index=False).encode("utf-8"),
                               "startup_analysis.csv", "text/csv")
        else:
            st.dataframe(sf, use_container_width=True, hide_index=True)
    else:
        show_empty()

# ------------------------------ Page 2 -------------------------------------
elif page == "Funding Analysis":
    add_page_header(
        "Funding Intelligence",
        "Analyze investment patterns, funding stages, geographic concentration and startup financing trends."
    )
    if funding.empty:
        show_empty("The funding-round table could not be found or contains no records.")
        st.stop()

    fc = funding.copy()
    stage_col = first_existing(fc, ["funding_stage"])
    date_col = first_existing(fc, ["funding_date"])
    amount_col = first_existing(fc, ["amount_raised"])
    valuation_col = first_existing(fc, ["valuation"])
    country_col = first_existing(fc, ["country"])
    industry_col = first_existing(fc, ["industry"])

    # Enrich funding records with startup profile columns if not already included.
    if not startup.empty and "startup_id" in fc.columns and "startup_id" in startup.columns:
        enrich_cols = [c for c in ["startup_id", "country", "industry", "startup_name"] if c in startup.columns and c not in fc.columns]
        if enrich_cols:
            fc = fc.merge(startup[enrich_cols], on="startup_id", how="left")
            country_col = country_col or first_existing(fc, ["country"])
            industry_col = industry_col or first_existing(fc, ["industry"])

    f1, f2, f3 = st.columns(3)
    stage_options = sorted(fc[stage_col].dropna().astype(str).unique()) if stage_col else []
    country_options = sorted(fc[country_col].dropna().astype(str).unique()) if country_col else []
    with f1:
        selected_stages = st.multiselect("Funding stage", stage_options, placeholder="All stages")
    with f2:
        selected_countries = st.multiselect("Country", country_options, placeholder="All countries")
    with f3:
        year_options = sorted(fc[date_col].dropna().dt.year.unique().tolist()) if date_col else []
        selected_years = st.multiselect("Year", year_options, placeholder="All years")

    if stage_col and selected_stages:
        fc = fc[fc[stage_col].astype(str).isin(selected_stages)]
    if country_col and selected_countries:
        fc = fc[fc[country_col].astype(str).isin(selected_countries)]
    if date_col and selected_years:
        fc = fc[fc[date_col].dt.year.isin(selected_years)]

    amounts = numeric_series(fc, amount_col) if amount_col else pd.Series(dtype=float)
    valuations = numeric_series(fc, valuation_col) if valuation_col else pd.Series(dtype=float)
    total_funding = amounts.sum(min_count=1)
    avg_funding = amounts.mean()
    avg_valuation = valuations.mean()

    kpi_row([
        ("TOTAL CAPITAL DEPLOYED", money(total_funding) if pd.notna(total_funding) else "—", None, "Sum of available funding-round amounts."),
        ("TOTAL FUNDING ROUNDS", f"{len(fc):,}", None, "Funding records after filters."),
        ("AVERAGE DEAL SIZE", money(avg_funding) if pd.notna(avg_funding) else "—", None, "Mean funding amount per round."),
        ("AVERAGE POST-MONEY VALUATION", money(avg_valuation) if pd.notna(avg_valuation) else "—", None, "Mean valuation where available."),
    ])

    left, right = st.columns([1.35, .85])
    with left:
        st.subheader("Quarterly Funding Dynamics")
        if date_col and amount_col:
            trend = fc.dropna(subset=[date_col]).copy()
            trend["period"] = trend[date_col].dt.to_period("Q").astype(str)
            trend = trend.groupby("period", as_index=False)[amount_col].sum()
            fig = px.area(trend, x="period", y=amount_col, markers=True,
                          color_discrete_sequence=[PRIMARY])
            fig.update_traces(line=dict(width=3), fillcolor="rgba(79,70,229,.12)")
            st.plotly_chart(chart_layout(fig, 330), use_container_width=True)
        else:
            show_empty("Funding date or amount column not found.")
    with right:
        st.subheader("Capital by Stage")
        if stage_col and amount_col:
            stage = fc.groupby(stage_col, dropna=False)[amount_col].sum().sort_values(ascending=True).reset_index()
            fig = px.bar(stage, x=amount_col, y=stage_col, orientation="h", color_discrete_sequence=[CYAN])
            st.plotly_chart(chart_layout(fig, 330), use_container_width=True)
        else:
            show_empty("Funding stage or amount column not found.")

    left, right = st.columns(2)
    with left:
        st.subheader("Geographic Concentration")
        if country_col and amount_col:
            country = fc.groupby(country_col)[amount_col].sum().nlargest(12).sort_values().reset_index()
            fig = px.bar(country, x=amount_col, y=country_col, orientation="h", color_discrete_sequence=[PRIMARY])
            st.plotly_chart(chart_layout(fig, 300), use_container_width=True)
        else:
            show_empty("Country or funding amount is unavailable.")
    with right:
        st.subheader("Leading Industry Sectors")
        if industry_col and amount_col:
            industry = fc.groupby(industry_col)[amount_col].sum().nlargest(10).sort_values().reset_index()
            fig = px.bar(industry, x=amount_col, y=industry_col, orientation="h",
                         color_discrete_sequence=[GREEN])
            st.plotly_chart(chart_layout(fig, 300), use_container_width=True)
        else:
            show_empty("Industry or funding amount is unavailable.")

    st.subheader("Largest Funding Rounds")
    if amount_col:
        table_cols = [c for c in ["startup_name", date_col, stage_col, amount_col, valuation_col, "lead_investor"] if c and c in fc.columns]
        top_rounds = fc.sort_values(amount_col, ascending=False, na_position="last").head(20)
        st.dataframe(top_rounds[table_cols] if table_cols else top_rounds,
                     use_container_width=True, hide_index=True)
        st.download_button("↓ Export funding rounds", top_rounds.to_csv(index=False).encode("utf-8"),
                           "largest_funding_rounds.csv", "text/csv")
        if "startup_name" in fc.columns:
            top_startups = fc.groupby("startup_name")[amount_col].sum().nlargest(10).sort_values().reset_index()
            st.subheader("Top 10 Most Funded Startups (Cumulative)")
            fig = px.bar(top_startups, x=amount_col, y="startup_name", orientation="h",
                         color_discrete_sequence=[PRIMARY])
            st.plotly_chart(chart_layout(fig, 340), use_container_width=True)

# ------------------------------ Page 3 -------------------------------------
elif page == "Investor Analysis":
    add_page_header(
        "Investor Intelligence",
        "Understand venture capital activity, investor profiles, investment capacity and deal participation."
    )
    if investors.empty:
        show_empty("The investor table could not be found or contains no records.")
        st.stop()

    iv = normalize_columns(investors)
    type_col = first_existing(iv, ["investor_type"])
    aum_col = first_existing(iv, ["aum"])
    activity_col = first_existing(iv, ["deal_activity"])
    name_col = first_existing(iv, ["investor_name"])

    f1, f2 = st.columns(2)
    type_options = sorted(iv[type_col].dropna().astype(str).unique()) if type_col else []
    with f1:
        selected_types = st.multiselect("Investor type", type_options, placeholder="All investor types")
    with f2:
        if aum_col:
            aum = numeric_series(iv, aum_col).dropna()
            aum_range = st.slider("AUM range", float(aum.min()), float(max(aum.max(), aum.min())),
                                  (float(aum.min()), float(max(aum.max(), aum.min())))) if not aum.empty else None
        else:
            aum_range = None

    ivf = iv.copy()
    if type_col and selected_types:
        ivf = ivf[ivf[type_col].astype(str).isin(selected_types)]
    if aum_col and aum_range:
        ivf = ivf[numeric_series(ivf, aum_col).between(*aum_range)]

    total_investors = len(ivf)
    total_deals = numeric_series(ivf, activity_col).sum() if activity_col else np.nan
    total_aum = numeric_series(ivf, aum_col).sum() if aum_col else np.nan
    avg_deal = (
        numeric_series(ivf, "total_investment_amount").sum() / total_deals
        if "total_investment_amount" in ivf.columns and pd.notna(total_deals) and total_deals > 0
        else np.nan
    )

    kpi_row([
        ("TOTAL INVESTORS", f"{total_investors:,}", None, "Investor profiles after filters."),
        ("RECORDED DEAL ACTIVITY", f"{total_deals:,.0f}" if pd.notna(total_deals) else "—", None, "Sum of deal activity if supplied by source."),
        ("TOTAL AUM", money(total_aum) if pd.notna(total_aum) else "—", None, "Sum of AUM values; confirm units in source."),
        ("AVERAGE DEAL SIZE", money(avg_deal) if pd.notna(avg_deal) else "N/A", None, "Requires investor-level total invested amount; not inferred from AUM."),
    ])

    left, right = st.columns([1.35, .85])
    with left:
        st.subheader("Most Active Investors")
        if name_col and activity_col:
            active = ivf.sort_values(activity_col, ascending=False).head(12).copy()
            fig = px.bar(active.sort_values(activity_col), x=activity_col, y=name_col,
                         orientation="h", color_discrete_sequence=[PRIMARY])
            st.plotly_chart(chart_layout(fig, 360), use_container_width=True)
        else:
            show_empty("Investor name or deal activity column not found.")
    with right:
        st.subheader("Investor Type Breakdown")
        if type_col:
            typ = ivf[type_col].value_counts().rename_axis("investor_type").reset_index(name="count")
            fig = px.pie(typ, names="investor_type", values="count", hole=.65,
                         color_discrete_sequence=PALETTE)
            st.plotly_chart(chart_layout(fig, 360), use_container_width=True)
        else:
            show_empty("Investor type column not found.")

    left, right = st.columns(2)
    with left:
        st.subheader("Top Investors by AUM")
        if name_col and aum_col:
            top_aum = ivf.nlargest(10, aum_col).sort_values(aum_col)
            fig = px.bar(top_aum, x=aum_col, y=name_col, orientation="h",
                         color_discrete_sequence=[CYAN])
            st.plotly_chart(chart_layout(fig, 300), use_container_width=True)
        else:
            show_empty("AUM or investor name column not found.")
    with right:
        st.subheader("Investor Capital Concentration")
        if name_col and aum_col:
            conc = ivf.nlargest(12, aum_col)
            fig = px.treemap(conc, path=[name_col], values=aum_col,
                             color=aum_col, color_continuous_scale="Teal")
            st.plotly_chart(chart_layout(fig, 300), use_container_width=True)
        else:
            show_empty("AUM data is unavailable.")

    st.subheader("Institutional Investor Directory")
    display_cols = [c for c in [name_col, type_col, aum_col, activity_col] if c]
    if display_cols:
        directory = ivf[display_cols].sort_values(activity_col, ascending=False) if activity_col else ivf[display_cols]
        st.dataframe(directory, use_container_width=True, hide_index=True)
        st.download_button("↓ Export investor directory", directory.to_csv(index=False).encode("utf-8"),
                           "investor_directory.csv", "text/csv")
    else:
        st.dataframe(ivf, use_container_width=True, hide_index=True)

# ------------------------------ Page 4 -------------------------------------
elif page == "Market Analysis":
    add_page_header(
        "Market Intelligence",
        "Track global venture capital performance, quarterly growth, valuation movements and investment momentum."
    )

    qd = normalize_columns(quarterly)
    if qd.empty:
        # Build quarterly trends from funding rounds if aggregate table is absent.
        if not funding.empty and "funding_date" in funding.columns and "amount_raised" in funding.columns:
            tmp = funding.dropna(subset=["funding_date"]).copy()
            tmp["quarter"] = tmp["funding_date"].dt.to_period("Q").astype(str)
            qd = tmp.groupby("quarter").agg(
                total_funding=("amount_raised", "sum"),
                deal_count=("amount_raised", "count"),
                average_valuation=("valuation", "mean") if "valuation" in tmp.columns else ("amount_raised", "mean")
            ).reset_index()
        else:
            show_empty("Quarterly summary is unavailable and funding records cannot generate a quarterly trend.")
            st.stop()

    quarter_col = first_existing(qd, ["quarter"])
    qfund_col = first_existing(qd, ["total_funding", "amount_raised"])
    deals_col = first_existing(qd, ["deal_count"])
    growth_col = first_existing(qd, ["market_growth"])
    avg_val_col = first_existing(qd, ["average_valuation", "avg_valuation", "valuation"])

    f1, f2 = st.columns(2)
    if quarter_col:
        quarter_options = qd[quarter_col].dropna().astype(str).unique().tolist()
        with f1:
            selected_quarters = st.multiselect("Quarter", sorted(quarter_options), placeholder="All quarters")
        with f2:
            years = sorted(qd["year"].dropna().unique().tolist()) if "year" in qd.columns else []
            selected_market_years = st.multiselect("Year", years, placeholder="All years") if years else []
    else:
        selected_quarters, selected_market_years = [], []

    qf = qd.copy()
    if quarter_col and selected_quarters:
        qf = qf[qf[quarter_col].astype(str).isin(selected_quarters)]
    if "year" in qf.columns and selected_market_years:
        qf = qf[qf["year"].isin(selected_market_years)]

    total_market_funding = numeric_series(qf, qfund_col).sum(min_count=1) if qfund_col else np.nan
    total_market_deals = numeric_series(qf, deals_col).sum(min_count=1) if deals_col else np.nan
    avg_market_valuation = numeric_series(qf, avg_val_col).mean() if avg_val_col else np.nan
    latest_growth = numeric_series(qf, growth_col).dropna().iloc[-1] if growth_col and not numeric_series(qf, growth_col).dropna().empty else np.nan

    kpi_row([
        ("TOTAL QUARTERLY FUNDING", money(total_market_funding) if pd.notna(total_market_funding) else "—", None, "Sum of quarterly funding values in the filtered period."),
        ("TOTAL DEALS", f"{total_market_deals:,.0f}" if pd.notna(total_market_deals) else "—", None, "Sum of quarterly deal counts."),
        ("AVERAGE VALUATION", money(avg_market_valuation) if pd.notna(avg_market_valuation) else "—", None, "Average valuation metric if supplied."),
        ("LATEST MARKET GROWTH", f"{latest_growth:+.1f}%" if pd.notna(latest_growth) else "—", None, "Uses the latest available growth field; verify its unit."),
    ])

    left, right = st.columns([1.3, .9])
    with left:
        st.subheader("Quarterly Market Growth & Aggregate Funding")
        if quarter_col and qfund_col:
            plotdf = qf.copy()
            fig = px.line(plotdf, x=quarter_col, y=qfund_col, markers=True,
                          color_discrete_sequence=[PRIMARY])
            fig.update_traces(line=dict(width=3))
            st.plotly_chart(chart_layout(fig, 340), use_container_width=True)
        else:
            show_empty("Quarter or total funding column not found.")
    with right:
        st.subheader("Funding Velocity Monitoring")
        if quarter_col and growth_col:
            vel = qf[[quarter_col, growth_col]].copy()
            vel[growth_col] = numeric_series(vel, growth_col)
            vel = vel.dropna().tail(12)
            vel["direction"] = np.where(vel[growth_col] >= 0, "Growth", "Contraction")
            fig = px.bar(vel, x=growth_col, y=quarter_col, orientation="h",
                         color="direction", color_discrete_map={"Growth": GREEN, "Contraction": RED})
            st.plotly_chart(chart_layout(fig, 340), use_container_width=True)
        else:
            show_empty("Market growth field not available in quarterly summary.")

    left, right = st.columns(2)
    with left:
        st.subheader("Average Valuation Progression")
        if quarter_col and avg_val_col:
            fig = px.line(qf, x=quarter_col, y=avg_val_col, markers=True,
                          color_discrete_sequence=[CYAN])
            st.plotly_chart(chart_layout(fig, 300), use_container_width=True)
        else:
            show_empty("Average valuation metric is not available.")
    with right:
        st.subheader("Deal Count Per Quarter")
        if quarter_col and deals_col:
            fig = px.bar(qf, x=quarter_col, y=deals_col, color_discrete_sequence=[PRIMARY])
            st.plotly_chart(chart_layout(fig, 300), use_container_width=True)
        else:
            show_empty("Quarterly deal count is not available.")

    st.subheader("Market Performance Summary")
    if qfund_col and not qf.empty:
        best_idx = numeric_series(qf, qfund_col).idxmax()
        worst_idx = numeric_series(qf, qfund_col).idxmin()
        c1, c2, c3 = st.columns(3)
        c1.metric("Highest funding quarter", str(qf.loc[best_idx, quarter_col]) if quarter_col else "—")
        c2.metric("Highest funding", money(qf.loc[best_idx, qfund_col]))
        c3.metric("Lowest funding", money(qf.loc[worst_idx, qfund_col]))
    st.dataframe(qf, use_container_width=True, hide_index=True)
    st.download_button("↓ Export market summary", qf.to_csv(index=False).encode("utf-8"),
                       "market_analysis.csv", "text/csv")

# ------------------------------ Footer -------------------------------------
st.markdown("---")
st.caption("Global Startup Ecosystem Analytics · PostgreSQL + Python + Streamlit + Plotly")
