import streamlit as st
import plotly.express as px
import sql_analysis as queries 

def render_page(engine):
    # header 
    header_col1, header_col2 = st.columns([3,1])
    with header_col1:
        st.title("Startup Intelligence")
        st.markdown("Explore startup distribution, industry performance")
    with header_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("📥 Export CSV", use_container_width=True)

    # filter options on top
    with engine.connect() as conn:
        filter_data = queries.get_filter_options(conn)

    country_options = [f"All Countries ({len(filter_data['countries'])})"]+filter_data["countries"]
    sector_options = [f"All Sectors ({len(filter_data['sectors'])})"]+filter_data["sectors"]
    status_options = ["All Statuses"] + filter_data['statuses']
    with st.container(border= True):
        f1,f2,f3 = st.columns(3)
        with f1:
            selected_country = st.selectbox("Geographical Scope",country_options)
        with f2:
            selected_sector = st.selectbox("Industry Sector",sector_options)
        with f3:
            selected_status = st.selectbox("REVENUE STATUS", status_options)

    with engine.connect() as conn:
        kpis = queries.get_high_level_kpis(conn)
    if not kpis.empty:
        kpi_row = kpis.iloc[0]
        m1,m2,m3,m4 = st.columns(4)
        with m1:
            st.metric(label="Total Startups",value=f"{kpi_row['total_startups']:,}",delta="+12.3% vs prior cycle")
        with m2:
            st.metric(label="Tracked Industries", value=f"{kpi_row['total_sectors']}", delta="Active Venture investments", delta_color="off")
        with m3:
            st.metric(label="Countries Represented", value=f"{kpi_row['total_countries']}", delta="Global Jurisdictions", delta_color="off")
        with m4:
            st.metric(label="Average Headcount", value=f"{int(kpi_row['avg_headcount'])} FTE", delta="+5.1% Expansion rate")
    st.markdown("---")
    # gegraphical visual vs industry 
    chart_col1,chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("Startup Distribution by Country")
        with engine.connect() as conn:
            geo = queries.get_geographic_distribution(conn)
        fig_map = px.choropleth(
            geo,locations="country",locationmode="country names", # Works with standard country names like "India", "United States"
            color="startup_count",hover_name="country",color_continuous_scale=px.colors.sequential.Purples,
            labels={"startup_count": "Startups"}
        )
        fig_map.update_layout(margin=dict(t=10, b=10, l=10, r=10),
            geo=dict(showframe=False, showcoastlines=True, projection_type='winkel tripel'),
            
        )
        st.plotly_chart(fig_map,use_container_width=True)
        st.subheader("Top 5 Startup Countries")
        fig_map = px.pie(
            geo.head(5), names="country", values="startup_count", 
            hole=0.5, color_discrete_sequence=px.colors.sequential.Purples_r
        )
        fig_map.update_layout(template="plotly_white", showlegend=True, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_map, use_container_width=True)
    with chart_col2:
        st.subheader("Startups by Industry")
        st.caption("Recent sector count & ecosystem share benchmarks.")
        with engine.connect() as conn:
            sector = queries.get_sector_investment_data(conn)
        fig_sector_bar = px.bar(
            sector, y="total_investment", x="sector", 
            color="total_investment", color_continuous_scale="Teal"
        )
        fig_sector_bar.update_layout(template="plotly_white", yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
        st.plotly_chart(fig_sector_bar, use_container_width=True)
        st.subheader("Top 5 sectors By Total Investments")
        fig_map = px.pie(
                sector.head(5), names="sector", values="total_investment", 
                hole=0.5, color_discrete_sequence=px.colors.sequential.Teal_r
                )
        fig_map.update_layout(template="plotly_white", showlegend=True, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("---")
    # REVENUE SPREADS VS. EMPLOYEE SIZES DEMOGRAPHICS
    spread1,spread2 = st.columns(2)
    with spread1:
    # Wrap the entire visual inside a clean bordered card container
        with st.container(border=True):
            st.subheader("Revenue Status Breakdown")
            st.caption("Solvency & financial self-sustainability")

        # 1. Fetch live revenue distribution from your PostgreSQL database
            with engine.connect() as conn:
                revenue = queries.get_revenue_status_distribution(conn)

            if not revenue.empty:
            # Calculate total entities for the center of the donut
                total_entities = revenue['startup_count'].sum()
                total_formatted = f"{total_entities/1000:.1f}k" if total_entities >= 1000 else f"{total_entities}"

            # Map distinct colors to match your mockup (Emerald, Teal, Indigo)
                color_map = {
                    "Profitable": "#047857",
                    "Loss Making": "#0f5e6e",
                    "Loss / Scaling": "#0f5e6e",
                    "Pre-Revenue": "#4f46e5"
                }

            # 2. Split the card into Donut Chart (left) and Custom Legend Cards (right)
                donut_col, legend_col = st.columns([1.2, 1.2])

                with donut_col:
                    fig_rev = px.pie(
                        revenue,
                    values="startup_count",
                    names="revenue_status",
                    hole=0.68,  # Creates the thin ring look from your design
                    color="revenue_status",
                    color_discrete_map=color_map
                )
                    fig_rev.update_traces(textinfo="none", hoverinfo="label+percent+value")
                
                # Place the big entity count right inside the donut hole
                    fig_rev.update_layout(
                    showlegend=False,
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=220,
                    annotations=[
                        dict(
                            text=f"<b>{total_formatted}</b><br><span style='font-size:11px; color:gray;'>ENTITIES</span>",
                            x=0.5, y=0.5, font_size=22, showarrow=False
                        )
                    ]
                )
                    st.plotly_chart(fig_rev, use_container_width=True)

                with legend_col:
                # Render custom KPI badge rows for each revenue category
                    for _, row in revenue.iterrows():
                        status = row['revenue_status']
                        count = int(row['startup_count'])
                        pct = row['percentage']
                        badge_color = color_map.get(status, "#4f46e5")

                        st.markdown(
                            f"""
                            <div style="background-color: #f8fafc; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #e2e8f0;">
                                <div style="display: flex; align-items: center;">
                                    <span style="height: 12px; width: 12px; background-color: {badge_color}; border-radius: 3px; display: inline-block; margin-right: 10px;"></span>
                                <div>
                                    <div style="font-weight: 600; font-size: 13px; color: #1e293b;">{status}</div>
                                    <div style="font-size: 11px; color: #64748b;">{count:,} firms</div>
                                </div>
                            </div>
                            <div style="font-weight: 700; font-size: 15px; color: {badge_color};">{pct:.0f}%</div>
                        </div>
                            """,
                            unsafe_allow_html=True
                    )

            # 3. Bottom Dynamic Insight Banner
            profitable_row = revenue[revenue['revenue_status'].str.contains('Profit', case=False, na=False)]
            prof_pct = profitable_row['percentage'].iloc[0] if not profitable_row.empty else 0

            st.markdown(
                f"""
                <div style="background-color: #eff6ff; padding: 10px 14px; border-radius: 8px; margin-top: 8px; font-size: 12px; color: #1e3a8a; border: 1px solid #dbeafe;">
                    ℹ️ <b>{prof_pct:.0f}% profitability</b> across active tracked entities in the current database scope.
                </div>
                """,
                unsafe_allow_html=True
            )
    with spread2:
        st.subheader("Employee Size Distribution")
        with engine.connect() as conn:
            df_size = queries.get_employee_distribution(conn)
        fig_size_bar = px.bar(df_size, x="company_size_tier", y="startup_count", color="company_size_tier", color_discrete_sequence=px.colors.qualitative.Safe)
        fig_size_bar.update_layout(template="plotly_white", showlegend=False)
        st.plotly_chart(fig_size_bar, use_container_width=True)

    st.markdown("---")
    # DETAILED FEATURED PORTFOLIO
    st.subheader("Featured Portfolio Cohort")
    st.caption("Validated financial metrics, funding rounds, and verified FTE counters.")
    
    with engine.connect() as conn:
        df_cohort = queries.get_startup_table(conn)
    st.dataframe(
        df_cohort,
        column_config={
            "startup_name": "STARTUP NAME",
            "sector_category": "SECTOR CATEGORY",
            "jurisdiction": "JURISDICTION",
            "headcount": st.column_config.NumberColumn("HEADCOUNT", format="%d FTE"),
            "revenue_profile": "REVENUE PROFILE",
            "aggregate_funding": st.column_config.NumberColumn("FUNDING", format="$%,.0f")
        },
        hide_index=True,
        use_container_width=True
    )
# render_page(engine)
