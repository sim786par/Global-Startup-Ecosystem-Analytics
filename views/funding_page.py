import streamlit as st
import plotly as px
import plotly.express as pe
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sql_analysis as queries

def render_page(engine):
    h_col1, h_col2 = st.columns(2)
    with h_col1:
        st.title("Funding Intelligence")
    with h_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        with engine.connect() as conn:
            directory = queries.get_funding_directory(conn)
        csv_data = directory.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Export Funding List",data=csv_data,
                           file_name="Funding_Directory.csv",use_container_width=True,
                           mime="text/csv")
    # filters
    with engine.connect() as conn:
        filters = queries.get_funding_filters(conn)
    with st.container(border=True):
        col1,col2,col3 = st.columns(3)
        with col1 :
            selected_quarter = st.selectbox("Quarters",[f"All Quarter({len(filters['quarters'])})"]+filters["quarters"])
        with col2 :
            selected_stage = st.selectbox("Funding Stage",[f"All funding stages({len(filters['funding_stages'])})"]+filters["funding_stages"])
        with col3:
            selected_sector = st.selectbox("sectors",[f"All sectors({len(filters['sectors'])})"]+filters["sectors"])
    # kpi cards
    with engine.connect() as conn:
        kpis = queries.funding_kpi_card(conn)
    if not kpis.empty:
        kpi = kpis.iloc[0]
        f1,f2,f3,f4,f5 = st.columns(5)
        with f1:
            with st.container(border=True):
                st.metric("TOTAL CAPITAL DEPLOYED",f"${kpi['total_capital']:,}M")
                st.caption("Aggregate financial volumne")
        with f2:
            with st.container(border=True):
                 st.metric("TOTAL FUNDING ROUNDS",f"{kpi['total_rounds']:,}")
                 st.caption("Closed financial events")
        with f3:
            with st.container(border=True):
                st.metric("AVERAGE DEAL CHECK",f"${kpi['avg_deal_millions']:,}M")
                st.caption("Average Deal in the financial events")
        with f4:
            with st.container(border=True):
                st.metric("TOTAL PRE-MONEY VALUATION",f"${kpi['pre_money']:,}M")
                st.caption("Enterprise starting line")
        with f5:
            with st.container(border=True):
                st.metric("TOTAL POST-MONEY VALUATION",f"${kpi['post_money']:,}M")
                st.caption("Enterprise baseline")
    st.markdown("---",unsafe_allow_html=True)
    # quarterly distribution + capital stages
    mid1,mid2 = st.columns(2)
    with mid1:
        with st.container(border=True):
            st.subheader("Quarterly Funding Dynamics")
            st.caption("Capital deployed ($M) compared with quarterly transaction volume")
            with engine.connect() as conn:
                trends = queries.get_funding_trend(conn)
            if not trends.empty:
                fig_q = make_subplots(specs=[[{"secondary_y":True}]])
                fig_q.add_trace(
                    go.Scatter(
                        x=trends['quarter'],y=trends['funding_amount'],name="Capital ($M)",
                        fill='tozeroy',line=dict(color="#4f46e5", width=3),fillcolor="rgba(79,70,229,0.12)"
                    ),secondary_y=False
                )
                fig_q.add_trace(
                    go.Scatter(
                        x=trends['quarter'],y=trends['deal_volume'],name='Deal Volume',
                        line=dict(color="#0d9488", width=2.5, dash="dot")
                    ),secondary_y=True
                )
                fig_q.update_layout(
                    height=290,margin=dict(t=15,l=10,b=10,r=10),
                    hovermode="x unified",legend = dict(orientation='h',yanchor='bottom',y=1.02,xanchor='right',x=1)
                    )
                st.plotly_chart(fig_q,use_container_width=True)

    with mid2:
        with st.container(border=True):
            st.subheader("Capital by Stage")
            st.caption("Average vs. median check size by stage ($M)")
            with engine.connect() as conn:
                stage = queries.get_funding_stage_by_amount(conn)
            if not stage.empty:
                max_val = stage["average_funding"].max()
                for _,row in stage.iterrows():
                    stage_name = row['funding_stage']
                    avg_m = row['average_funding']
                    med_m = row['median_check_millions']
                    avg_pct = int((avg_m/max_val)*100) if max_val>0 else 0
                    med_pct = int((med_m/max_val)*100) if max_val>0 else 0

                    st.markdown(
                        f"""<div style="margin-bottom: 14px;">
                            <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                                <b>{stage_name}</b>
                                <span style="font-size: 11px; color: #475569;">Avg: <b>${avg_m}M</b> · Med: <b>${med_m}M</b></span>
                            </div>
                            <div style="background-color: #e2e8f0; border-radius: 4px; height: 6px; margin-bottom: 3px;">
                                <div style="background-color: #4f46e5; width: {avg_pct}%; height: 6px; border-radius: 4px;"></div>
                            </div>
                            <div style="background-color: #e2e8f0; border-radius: 4px; height: 5px;">
                                <div style="background-color: #0d9488; width: {med_pct}%; height: 5px; border-radius: 4px;"></div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
    st.markdown("---", unsafe_allow_html=True)
    # top 10 startups
    with st.container(border=True):
        st.subheader("Top 10 Most Funded Global Entities (Cumulative)")
        st.caption("Lifetime equity capital absorbed by institutional applications ($ Billions)")
        with engine.connect() as conn:
            startup10 = queries.get_startup_by_funding(conn)
        if not startup10.empty:
            max_cum = startup10['amount'].max()
            left_col,right_col = st.columns(2)

            for idx,row in startup10.iterrows():
                rank = idx+1
                target_col = left_col if rank<=5 else right_col
                bar_pct = int((row['amount']/max_cum)*100) if max_cum>0 else 0
                with target_col:
                    st.markdown(
                        f"""<div style="margin-bottom: 14px;">
                            <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                                <b>{row['startup_name']}</b>
                                <span style="font-size: 11px; color: #475569;">AMOUNT: <b>${row['amount']:.2f}M</b> </span>
                            </div>
                            <div style="background-color: #e2e8f0; border-radius: 4px; height: 6px; margin-bottom: 3px;">
                            <div style="background-color: "#4f46e5"; width: {bar_pct}%; height: 6px; border-radius: 4px;"></div>
                           """,unsafe_allow_html=True
                    )
    chart1,chart2 =st.columns(2)
    with chart1:
        with st.container(border=True):
            st.subheader("Geographic Concentration")
            st.caption("Institutional capital flows by sovereign domicile ($M)")
            with engine.connect() as conn:
                geo = queries.get_highest_funding_by_country(conn)
            fig_map = pe.choropleth(
                geo,locations="country",locationmode="country names",
                color = "total_funding_raised",hover_name="country",color_continuous_scale=px.colors.sequential.Purples,
                labels={"total_funding_raised": "Funding Amount"}
            )
            fig_map.update_layout(height=290,margin=dict(t=15,l=10,b=10,r=10),
            geo=dict(showframe=False, showcoastlines=True, projection_type='winkel tripel'),
            )
            st.plotly_chart(fig_map,use_container_width=True)
    with chart2:
        with st.container(border=True):
            st.subheader("Quarter By Amount")
            with engine.connect() as conn:
                quar = queries.get_funding_trend(conn)
            fig_sector_bar = pe.bar(
                quar, y="funding_amount", x="quarter", 
                color="funding_amount", color_continuous_scale="Teal"
            )
            fig_sector_bar.update_layout(template="plotly_white", yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
            st.plotly_chart(fig_sector_bar, use_container_width=True)
    
    with st.container(border=True):
                st.subheader("Funding Directory")
                st.caption("Explore deployment velocity, syndication co-investors, and core portfolio focus domains.")
            
                search_query = st.text_input("🔍 Search quarter or stage...", placeholder="e.g. Seed,Q1...")
                filtered_dir = directory.copy()
                if search_query:
                    filtered_dir = filtered_dir[
                        filtered_dir['quarter'].str.contains(search_query, case=False, na=False) |
                        filtered_dir['funding_stage'].str.contains(search_query, case=False, na=False)
                    ]
                st.dataframe(
                    filtered_dir,column_config={
                        "quarter": "QUARTER",
                        "funding_stage": "FUNDING STAGE",
                        "funding_date": "FUNDING DATE",
                        "country": "COUNTRY",
                        "investor_type": "INVESTOR TYPE",
                        "amount_million_usd": st.column_config.NumberColumn("FUNDING AMOUNT", format="$%,.1fM"),
                        "pre_money_valuation_million_usd": st.column_config.NumberColumn("PRE-MONEY VALUATION", format="$%,.1fM"),
                        "post_money_valuation_million_usd": st.column_config.NumberColumn("POST-MONEY VALUATION", format="$%,.1fM"),
                        "top_sector": "TOP SECTOR"
                    },
                    hide_index=True,
                    use_container_width=True
                )
    # render_page(engine)
            


