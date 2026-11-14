import streamlit as st
import plotly.express as px
import pandas as pd
import sql_analysis as queries

def render_page(engine):
    h_col1,h_col2 = st.columns([4,1])
    with h_col1:
        st.title("Investor Intelligence")
        st.markdown("Understand venture capital activity, institutional profiles, deployment capacity, and syndication velocity.")
    with h_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        with engine.connect() as conn:
            directory = queries.get_full_investor_directory(conn)
        csv_data = directory.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Export Investor List",
                           data=csv_data,file_name="investor_directory.csv",
                            mime="text/csv",
                            use_container_width=True)

    # FILTER BAR
    with engine.connect() as conn:
        filters = queries.get_investor_filter_options(conn)
    with st.container(border=True):
        f1,f2,f3 = st.columns(3)
        with f1:
            selected_type = st.selectbox("Investor Type",[f"All Investor Types({len(filters['types'])})"]+filters['types'])
        with f2:
            seleccted_country = st.selectbox("Countries",[f"Country distribution({len(filters['countries'])})"]+filters['countries'])
        with f3:
            selected_sector = st.selectbox("Sectors",[f"All Sectors({len(filters['sectors'])})"]+filters['sectors'])
    st.markdown("<br>", unsafe_allow_html=True)
    # KPI CARDS
    with engine.connect() as conn:
        kpis = queries.get_investor_kpi(conn)
    if not kpis.empty:
        kpi = kpis.iloc[0]
        total_amount = kpi['amount']

        k1,k2,k3,k4 = st.columns(4)
        with k1:
            with st.container(border=True):
                st.metric("Total Investors Tracked", f"{int(kpi['total_investors']):,}", "+8.4% YoY")
                st.caption("Active institutional syndicates & VC funds")
        with k2:
            with st.container(border=True):
                st.metric("Total Investment Deals", f"{int(kpi['total_deals']):,}", "+14.2% YoY")
                st.caption("Closed equity participations")
        with k3:
            with st.container(border=True):
                st.metric("Average Deal Size", f"${kpi['avg_deal']}M", "-2.1% YoY", delta_color="inverse")
                st.caption("Blended early & growth rounds")
        with k4:
            with st.container(border=True):
                st.metric("Global Managed AUM", f"${kpi['amount']:.2f}T", "+18.1% YoY")
                st.caption("Active dry powder + deployed capital")
    st.markdown("<br>", unsafe_allow_html=True)
    # MOST ACY=TIVE INVESTOR TYPE BREAKDOWN

    mid1,mid2 = st.columns([1.4,1])
    with mid1:
        with st.container(border=True):
            st.subheader("Most Active Investors")

            with engine.connect() as conn:
                active = queries.get_active_investor(conn)
            if not active.empty:
                max_deal = active['total_deals'].max()
                total_deals_in = active['total_deals'].sum()
            for _,row in active.iterrows():
                name = row['investor_name']
                inv_type = row['investor_type']
                deals = int(row['total_deals'])
                bar_pct = int((deals / max_deal) * 100) if max_deal > 0 else 0
                share_pct = (deals / total_deals_in) * 100 if total_deals_in > 0 else 0

                st.markdown(
                    f"""
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">                                
                            <span><b>{name}</b> <span style="color: #64748b; font-size: 12px;">· {inv_type}</span></span>
                            <span><b>{deals} deals</b> <span style="color: #64748b; font-size: 11px;">({share_pct:.1f}% share)</span></span>
                        </div>
                        <div style="background-color: #e2e8f0; border-radius: 6px; height: 8px; width: 100%;">
                            <div style="background-color: #4f46e5; width: {bar_pct}%; height: 8px; border-radius: 6px;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    with mid2:
        with st.container(border=True):
            st.subheader("Investor Type Breakdown")
            with engine.connect() as conn:
                df_types = queries.get_investor_type_distribution(conn)
            if not df_types.empty:
                total_firms = int(df_types['investor_count'].sum())
                st.caption(f"Entity distribution {total_firms:,}")
                colors = ["#4f46e5", "#0d9488", "#2563eb", "#7c3aed", "#94a3b8"]
                fig_donut = px.pie(df_types,values="investor_count",names="investor_type",hole=0.68,color_discrete_sequence=colors)
                fig_donut.update_traces(textinfo="none")
                fig_donut.update_layout(showlegend=False,height=190,margin=dict(t=5,b=5,l=5,r=5),
                                        annotations=[dict(
                        text=f"<b>{total_firms:,}</b><br><span style='font-size:10px; color:gray;'>TRACKED FIRMS</span>",
                        x=0.5, y=0.5, font_size=18, showarrow=False
                    )])
                st.plotly_chart(fig_donut,use_container_width=True)
                for idx, row in df_types.iterrows():
                    dot_color = colors[idx % len(colors)]
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: space-between; font-size: 12px; padding: 4px 0; border-bottom: 1px solid #f1f5f9;">
                            <span><span style="color: {dot_color};">●</span> <b>{row['investor_type']}</b></span>
                            <span><b>{row['percentage_share']:.0f}%</b> <span style="color: #64748b;">({int(row['investor_count']):,})</span></span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
    st.markdown("<br>", unsafe_allow_html=True)

    # deal size by investor class
    b_col1,b_col2,b_col3 = st.columns([1.2,1.2,1])
    with b_col1:
        with st.container(border=True):
            st.subheader("Deal Size by Investor Class")
            with engine.connect() as conn:
                class_size = queries.get_average_deal_size(conn)
            if not class_size.empty:
                fig_bar = px.bar(class_size,x="investor_type",y="avg_deal_size_millions",color="investor_type",
                                 color_discrete_sequence=["#0f766e", "#2563eb", "#4f46e5", "#7c3aed", "#94a3b8"])
                fig_bar.update_layout(showlegend=False,
                                      yaxis=dict(showticklabels=True,showgrid=True))
                st.plotly_chart(fig_bar,use_container_width=True)
    with b_col2:
        # with st.container(border=True):
            st.subheader("Top Capital Bases (AUM)")
            st.caption("Aggregate active funds managed globally ($M)")
            if not class_size.empty:
                max_aum = class_size['total_invested_million_usd'].max()
                for _, row in class_size.head(5).iterrows():
                    aum_val = row['total_invested_million_usd']
                    pct = int((aum_val / max_aum) * 100) if max_aum > 0 else 0
                    display_aum = f"${aum_val/1000:.1f}B" if aum_val >= 1000 else f"${aum_val:.0f}M"
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: space-between; font-size: 15px; padding: 8px 0; border-bottom: 1px solid #f1f5f9;">
                            <span><span style="color: {dot_color};">●</span> <b>{row['investor_name']}</b></span>
                            <span><b>{pct:.0f}%</b> <span style="color: #64748b;">({display_aum})</span></span>
                        </div>
                        <div style="background-color: #e2e8f0; border-radius: 6px; height: 20px; width: 100%;">
                        <div style="background-color: #4f46e5; width: {pct}%; height: 18px; border-radius: 6px;"></div>
                        </div>
                        """,unsafe_allow_html=True
                    )
    with b_col3:
        with st.container(border=True):
            st.subheader("Capital Concentration")
            with engine.connect() as conn:
                conc = queries.get_funding_concentration(conn)
            if not conc.empty:
                top_20_count = max(1, int(len(conc) * 0.2))
                top_20_share = conc.head(top_20_count)['individual_share_pct'].sum()
                st.caption(f"Pareto distribution: Top 20% capture {top_20_share:.0f}% of capital")
                top_5 = conc.head(5)[['investor_name', 'capital_invested']].rename(
                    columns={'investor_name': 'Label', 'capital_invested': 'Capital'}
                )
                rest_cap = conc.iloc[5:]['capital_invested'].sum()
                if rest_cap > 0:
                    rest_row = pd.DataFrame({'Label': ['Remaining Ecosystem'], 'Capital': [rest_cap]})
                    pareto_tiles = pd.concat([top_5, rest_row], ignore_index=True)
                else:
                    pareto_tiles = top_5
                lunar_colors = ["#2b5f8d", "#a2d1fd", "#e9f5ff", "#dfc4f6", "#f074be", "#cbe1ce"]
                fig_tree = px.treemap(pareto_tiles,path=["Label"],values="Capital",color="Label",
                                      color_discrete_sequence=lunar_colors)
                fig_tree.update_traces(textinfo="label+percent root")
                fig_tree.update_layout(height=300, margin=dict(t=5, b=5, l=5, r=5))
                st.plotly_chart(fig_tree, use_container_width=True)
    st.markdown("---", unsafe_allow_html=True)
    # directory table
    with st.container(border=True):
            st.subheader("Institutional Investor Directory")
            st.caption("Explore deployment velocity, syndication co-investors, and core portfolio focus domains.")
        
            search_query = st.text_input("🔍 Search investor or sector...", placeholder="e.g. Sequoia, AI...")
            filtered_dir = directory.copy()
            if search_query:
                filtered_dir = filtered_dir[
                    filtered_dir['investor_name'].str.contains(search_query, case=False, na=False) |
                    filtered_dir['top_sector'].str.contains(search_query, case=False, na=False)
                ]
            st.dataframe(
                filtered_dir,column_config={
                    "investor_name": "INVESTOR ENTITY",
                    "investor_type": "ENTITY TYPE",
                    "country": "HEADQUARTERS",
                    "founded_year": st.column_config.NumberColumn("FOUNDED YEAR", format="%d"),
                    "total_amount": st.column_config.NumberColumn("TOTAL AUM", format="$%,.1fB"),
                    "total_deals": st.column_config.NumberColumn("DEALS", format="%d"),
                    "invested_amount": st.column_config.NumberColumn("INVESTED AMOUNT", format="$%,.1fM"),
                    "top_sector": "CORE FOCUS"
                },
                hide_index=True,
                use_container_width=True
            )
# render_page(engine)