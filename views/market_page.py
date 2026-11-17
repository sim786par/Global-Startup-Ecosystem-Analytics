import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import sql_analysis as queries

def render_page(engine):
    
    h1,h2 = st.columns(2)
    with h1:
        st.title("Market Growth Trends")
    with h2:
        st.markdown("<br>", unsafe_allow_html=True)
        with engine.connect() as conn:
            directory = queries.get_market_quarterly_metrics(conn)
        csv_data = directory.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Export Market Growth",data=csv_data,
                           file_name="market_Directory.csv",use_container_width=True,
                            mime="text/csv")
    # filters
    with engine.connect() as conn:
        filters = queries.get_market_filter_options(conn)
        with st.container(border=True):
            col1,col2,col3 = st.columns(3)
            with col1 :
                selected_quarter = st.selectbox("Quarters",[f"All Quarter({len(filters['quarters'])})"]+filters["quarters"])
            with col2 :
                selected_period = st.selectbox("Funding Period",[f"All funding periods({len(filters['periods'])})"]+filters["periods"])
            with col3:
                selected_sector = st.selectbox("Funding Years",[f"All Funding Years({len(filters['years'])})"]+filters["years"])
    # kpi cards
    kpis = directory.copy()
    if not kpis.empty:
        latest = kpis.iloc[-1]

        funding_b = (latest['funding_m'] or 0) / 1000.0
        qoq_val = float(latest['qoq_growth_pct']) if pd.notnull(latest['qoq_growth_pct']) else 0.0
        deals_qoq = float(latest['deals_qoq_pct']) if pd.notnull(latest['deals_qoq_pct']) else 0.0
        val_qoq = float(latest['val_qoq_pct']) if pd.notnull(latest['val_qoq_pct']) else 0.0
        k1, k2, k3, k4 = st.columns(4)
    with k1:
        with st.container(border=True):
            st.metric("TOTAL QUARTERLY FUNDING", f"${funding_b:.1f}B", f"{qoq_val:+.1f}% QoQ")
            st.caption(f"Latest deployment ({latest['period']})")
    with k2:
        with st.container(border=True):
            st.metric("TOTAL DEALS RECORDED", f"{int(latest['deals']):,}", f"{deals_qoq:+.1f}% QoQ")
            st.caption("Global equity & convertible rounds")
    with k3:
        with st.container(border=True):
            st.metric("AVERAGE STARTUP VALUATION", f"${latest['median_val_m']:.1f}M", f"{val_qoq:+.1f}% QoQ")
            st.caption("Weighted post-money median")
    with k4:
        with st.container(border=True):
            regime = "Disciplined Rebound Phase" if qoq_val >= 0 else "Contraction Phase"
            st.metric("MARKET GROWTH RATE", f"{qoq_val:+.1f}%", regime)
            st.caption("QoQ expansion velocity")
    st.markdown("---",unsafe_allow_html=True)
    df_filtered = directory.copy()
    mid_col1, mid_col2 = st.columns([1.6, 1])

    # Left Card: Quarterly Market Growth & Aggregate Funding Area Chart
    with mid_col1:
        with st.container(border=True):
            st.subheader("Quarterly Market Growth & Aggregate Funding")
            st.caption("Capital deployed ($M) across quarters demonstrating inflection points, expansion, and recovery.")

            fig_area = px.area(
                df_filtered,
                x="period",
                y="funding_m",
                markers=True,
                labels={"funding_m": "Funding ($M)", "period": "Quarter"},
                color_discrete_sequence=["#4f46e5"]
            )
            fig_area.update_traces(
                line=dict(width=3, color="#4f46e5"),
                fillcolor="rgba(79, 70, 229, 0.14)"
            )
            fig_area.update_layout(
                height=290,
                margin=dict(t=15, b=10, l=10, r=10),
                template="plotly_white",
                hovermode="x unified",
                xaxis_title=None
            )
            st.plotly_chart(fig_area, use_container_width=True)

            st.markdown(
                f"""
                <div style="background-color: #eef2ff; padding: 10px 14px; border-radius: 8px; font-size: 12px; color: #312e81; border: 1px solid #c7d2fe;">
                    📈 <b>Market Trajectory:</b> Latest period ({latest['period']}) recorded <b>${funding_b:.1f}B</b> deployed with a <b>{qoq_val:+.1f}%</b> quarter-over-quarter shift.
                </div>
                """,
                unsafe_allow_html=True
            )

    # Right Card: Funding Velocity / Momentum (Divergent Horizontal Bars)
    with mid_col2:
        with st.container(border=True):
            st.subheader("Funding Velocity / Momentum")
            st.caption("QoQ funding acceleration (+) vs contraction (-)")

            df_vel = df_filtered.dropna(subset=['qoq_growth_pct']).tail(8).copy()
            if not df_vel.empty:
                df_vel['Direction'] = df_vel['qoq_growth_pct'].apply(lambda x: "Acceleration" if x >= 0 else "Contraction")

                fig_vel = px.bar(
                    df_vel,
                    x="qoq_growth_pct",
                    y="period",
                    orientation="h",
                    text="qoq_growth_pct",
                    color="Direction",
                    color_discrete_map={"Acceleration": "#059669", "Contraction": "#dc2626"}
                )
                fig_vel.update_traces(texttemplate="%{text:+.1f}%", textposition="outside")
                fig_vel.update_layout(
                    height=330,
                    margin=dict(t=10, b=10, l=10, r=35),
                    template="plotly_white",
                    xaxis_title=None,
                    yaxis_title=None,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_vel,use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)

# VALUATION BY STAGE + DEAL COUNT & MEDIAN SIZE
    b_col1, b_col2 = st.columns(2)

    # Left Card: Average Valuation Progression by Stage
    with b_col1:
        with st.container(border=True):
            st.subheader("Average Valuation Progression by Stage")
            st.caption("Post-money valuations ($M) illustrating stage expansion")

            with engine.connect() as conn:
                df_stage_val = queries.get_valuation_by_stage_progression(conn)

            if not df_stage_val.empty:
                top_stages = df_stage_val['funding_stage'].value_counts().head(4).index.tolist()
                df_stage_plot = df_stage_val[df_stage_val['funding_stage'].isin(top_stages)]

                fig_stage_line = px.line(
                    df_stage_plot,
                    x="period",
                    y="avg_valuation_m",
                    color="funding_stage",
                    markers=True,
                    labels={"avg_valuation_m": "Avg Valuation ($M)", "period": "Quarter", "funding_stage": "Stage"},
                    color_discrete_sequence=["#4f46e5", "#0d9488", "#94a3b8", "#7c3aed"]
                )
                fig_stage_line.update_layout(
                    height=270,
                    margin=dict(t=15, b=10, l=10, r=10),
                    template="plotly_white",
                    xaxis_title=None,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
                )
                st.plotly_chart(fig_stage_line, use_container_width=True)
            else:
                st.info("Stage-level valuation breakdown unavailable for this filter.")

    # Right Card: Deal Count Per Quarter & Median Size
    with b_col2:
        with st.container(border=True):
            st.subheader("Deal Count Per Quarter & Median Size")
            st.caption("Transaction density alongside median financing check sizes")

            fig_deals = px.bar(
                df_filtered,
                x="period",
                y="deals",
                color="median_deal_m",
                text="deals",
                labels={"deals": "Total Deals", "period": "Quarter", "median_deal_m": "Median Deal ($M)"},
                color_continuous_scale=["#c7d2fe", "#4f46e5"]
            )
            fig_deals.update_traces(textposition="outside")
            fig_deals.update_layout(
                height=270,
                margin=dict(t=15, b=10, l=10, r=10),
                template="plotly_white",
                xaxis_title=None,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_deals, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    #  MACRO CYCLE RECORD
    st.subheader("🏆 Macro Cycle Record Milestones")
    st.caption("Historical extremes across the tracked multi-year horizon")
    peak_fund_row = directory.loc[directory['funding_m'].idxmax()]
    peak_deals_row = directory.loc[directory['deals'].idxmax()]
    df_valid_qoq = directory.dropna(subset=['qoq_growth_pct'])
    max_growth_row = df_valid_qoq.loc[df_valid_qoq['qoq_growth_pct'].idxmax()] if not df_valid_qoq.empty else peak_fund_row
    min_growth_row = df_valid_qoq.loc[df_valid_qoq['qoq_growth_pct'].idxmin()] if not df_valid_qoq.empty else peak_fund_row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        with st.container(border=True):
            st.caption("HIGHEST FUNDING QUARTER")
            st.markdown(f"### {peak_fund_row['period']}")
            st.markdown(f"${peak_fund_row['funding_m']/1000:.1f}B Deployed")
            st.caption("Peak ecosystem capital deployment quarter.")
    with m2:
        with st.container(border=True):
            st.caption("HIGHEST DEAL VOLUME QUARTER")
            st.markdown(f"### {peak_deals_row['period']}")
            st.markdown(f"{int(peak_deals_row['deals']):,} Recorded Deals")
            st.caption("Maximum transaction velocity across stages.")
    with m3:
        with st.container(border=True):
            st.caption("STRONGEST FUNDING GROWTH")
            st.markdown(f"### {max_growth_row['period']}")
            g_pct = max_growth_row.get('qoq_growth_pct', 0)
            st.markdown(f"{g_pct:+.1f}% QoQ Surge")
            st.caption("Fastest sequential quarter expansion.")
    with m4:
        with st.container(border=True):
            st.caption("LARGEST FUNDING DECLINE")
            st.markdown(f"### {min_growth_row['period']}")
            d_pct = min_growth_row.get('qoq_growth_pct', 0)
            st.markdown(f"{d_pct:+.1f}% QoQ Contraction")
            st.caption("Steepest sequential capital pullback.")
