import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

db_url = URL.create(
    drivername = "postgresql+psycopg2",
    username = "postgres",
    password = "Simran@2754",
    host = "localhost",
    port = 5432,
    database = "startup_ecosystem"
)
engine = create_engine(db_url)
with engine.connect() as conn:
    print(conn.execute(text("SELECT current_database()")).scalar())

#filter options
def get_filter_options(conn):
    countries_q ="""
    SELECT DISTINCT country FROM startup_details
    ORDER BY country;"""
    countries = pd.read_sql_query(text(countries_q),conn)['country'].tolist()

    sector_q = """
    SELECT DISTINCT sector FROM startup_details
    ORDER BY sector;"""
    sector = pd.read_sql_query(text(sector_q),conn)['sector'].tolist()

    # Fetch unique revenue statuses
    statuses_q = "SELECT DISTINCT revenue_status FROM startup_details ORDER BY revenue_status ASC;"
    statuses = pd.read_sql_query(text(statuses_q), conn)['revenue_status'].tolist()
    return {
        "countries": countries,
        "sectors": sector,
        "statuses": statuses,
    }
# kpi card details
def get_high_level_kpis(conn):
    query ="""
    SELECT
        COUNT(DISTINCT startup_id) AS total_startups,
        COUNT(DISTINCT sector) AS total_sectors,
        COUNT(DISTINCT country) AS total_countries,
        ROUND(AVG(employee_count::INT), 0) AS avg_headcount
        FROM startup_details;
        """
    return pd.read_sql_query(text(query),conn)
# Which startups have raised the highest funding?
def get_startup_table(conn):
    query = """
    SELECT 
    s.startup_name,
    s.sector AS sector_category,
    s.country AS jurisdiction,
    s.employee_count::INT AS headcount,
    s.revenue_status AS revenue_profile,
    COALESCE(SUM(f.amount_million_usd::NUMERIC), 0) AS aggregate_funding
FROM startup_details AS s
LEFT JOIN funding_round_details AS f
    ON s.startup_id = f.startup_id
GROUP BY 
    s.startup_id,
    s.startup_name,
    s.sector,
    s.country,
    s.employee_count,
    s.revenue_status
LIMIT 5;

    """
    return pd.read_sql_query(text(query), conn)
# # Which industries are experiencing the fastest growth?
# def get_highest_industry(conn):
#     query="""
#     SELECT 
#         s.sector AS industry,
#         count(DISTINCT s.startup_id) AS total_startup,
#         SUM(f.amount_million_usd) AS total_funding_raised
#     FROM startup_details AS s
#     LEFT JOIN funding_round_details AS f ON s.startup_id = f.startup_id
#     GROUP BY s.sector
#     ORDER BY total_funding_raised DESC;
#     """
#     return pd.read_sql_query(text(query),conn)
# How are startups distributed across different countries?
def get_geographic_distribution(conn):
    query="""
    SELECT 
        country, COUNT(startup_id) AS startup_count,
        ROUND(COUNT(startup_id)*100.0/SUM(COUNT(startup_id)) OVER(),2) AS percentage
        FROM startup_details
        GROUP BY country
        ORDER BY startup_count DESC;

    """
    return pd.read_sql_query(text(query),conn)
# How does revenue status vary across startups?
def get_revenue_status_distribution(conn):
    query = """
    SELECT 
        revenue_status,
        COUNT(startup_id) AS startup_count,
        ROUND(COUNT(startup_id) * 100.0 / SUM(COUNT(startup_id)) OVER(), 2) AS percentage
    FROM startup_details
    WHERE revenue_status IS NOT NULL AND revenue_status <> ''
    GROUP BY revenue_status
    ORDER BY startup_count DESC;
    """
    return pd.read_sql_query(text(query), conn)
# What is the distribution of startup employee sizes?
def get_employee_distribution(conn):
    query="""
    SELECT 
        CASE 
            WHEN employee_count <= 10 THEN '1-10 (Micro)'
            WHEN employee_count <= 50 THEN '11-50 (Small)'
            WHEN employee_count <= 250 THEN '51-250 (Medium)'
            WHEN employee_count <= 1000 THEN '251-1000 (Large)'
            ELSE '1000+ (Enterprise)'
        END AS company_size_tier,
        COUNT(startup_id) AS startup_count
    FROM startup_details
    WHERE employee_count IS NOT NULL AND employee_count >= 0
    GROUP BY 
        CASE 
            WHEN employee_count <= 10 THEN '1-10 (Micro)'
            WHEN employee_count <= 50 THEN '11-50 (Small)'
            WHEN employee_count <= 250 THEN '51-250 (Medium)'
            WHEN employee_count <= 1000 THEN '251-1000 (Large)'
            ELSE '1000+ (Enterprise)'
        END
    ORDER BY MIN(employee_count) ASC;
    """
    return pd.read_sql_query(text(query), conn)
# What is the average funding amount at each funding stage?
def get_funding_stage_by_amount(conn):
    query="""
    SELECT 
        funding_stage,
        ROUND(AVG(amount_million_usd::NUMERIC), 2) AS average_funding
        FROM funding_round_details
        GROUP BY funding_stage
        ORDER BY funding_stage;
    """
    return pd.read_sql_query(text(query), conn)
# How have funding trends changed over different quarters?
def get_funding_trend(conn):
    query="""
    SELECT 
        quarter,
        SUM(amount_million_usd) AS funding_amount
        FROM funding_round_details
        GROUP BY quarter
        ORDER BY quarter;
    """
    return pd.read_sql_query(text(query), conn)
# Which countries receive the highest funding?
def get_highest_funding_by_country(conn):
    query = """
    SELECT 
        country,
        SUM(amount_million_usd::NUMERIC) AS total_funding_raised
    FROM funding_round_details
    WHERE country IS NOT NULL
      AND amount_million_usd IS NOT NULL
    GROUP BY country
    ORDER BY total_funding_raised DESC; 
    """
    return pd.read_sql_query(text(query), conn)
# Which countries receive the highest startup funding?
def get_top_startup_per_country(conn):
    query = """
    WITH ranked_startups AS (
        SELECT 
            country,
            startup_name,
            SUM(amount_million_usd::NUMERIC) AS individual_funding,
            ROW_NUMBER() OVER(PARTITION BY country ORDER BY SUM(amount_million_usd::NUMERIC) DESC) as rank
        FROM funding_round_details
        WHERE country IS NOT NULL
          AND amount_million_usd IS NOT NULL
        GROUP BY country, startup_name
    )
    SELECT country, startup_name, individual_funding
    FROM ranked_startups
    WHERE rank = 1
    ORDER BY individual_funding DESC;
    """
    return pd.read_sql_query(text(query), conn)
# Which sectors attract the most investment?
def get_sector_investment_data(conn):
    query = """
    SELECT 
        sector,
        SUM(amount_million_usd::NUMERIC) AS total_investment,
        AVG(amount_million_usd::NUMERIC) AS average_deal_size,
        SUM(num_investors::INT) AS total_investor_appearances
    FROM funding_round_details
    WHERE sector IS NOT NULL AND amount_million_usd IS NOT NULL 
    GROUP BY sector
    ORDER BY total_investment DESC; 
    """
    return pd.read_sql_query(text(query), conn)
# Who are the most active investors? tOP 10 
def get_active_investor(conn):
    query="""
    SELECT 
        investor_name, total_deals_in_dataset AS total_deals,
        total_invested_million_usd,investor_type
    FROM investors_details
    ORDER BY total_deals
    LIMIT 10;
    """
    return pd.read_sql_query(text(query), conn)
# investor directory
def get_full_investor_directory(conn):
    query="""
    SELECT 
        investor_name,investor_type,
        hq_country AS country,
        founded_year,aum_billion_usd AS Total_amount,
        total_deals_in_dataset AS total_deals,
        total_invested_million_usd AS invested_amount,top_sector
    FROM investors_details;
    """
    return pd.read_sql_query(text(query), conn)
# investor filters
def get_investor_filter_options(conn):
    types = pd.read_sql_query(text("SELECT DISTINCT investor_type FROM investors_details ORDER BY investor_type;"), conn)['investor_type'].tolist()
    country = pd.read_sql_query(text("SELECT DISTINCT hq_country FROM investors_details ORDER BY hq_country;"), conn)['hq_country'].tolist()
    sector = pd.read_sql_query(text("SELECT DISTINCT top_sector FROM investors_details ORDER BY top_sector;"), conn)['top_sector'].tolist()
    return {"types":types,"countries":country,"sectors":sector}
# kpi cards
def get_investor_kpi(conn):
    query = """
    SELECT 
        COUNT(*) AS total_investors,
        COALESCE(SUM(total_deals_in_dataset),0) AS total_deals,
        ROUND(AVG(total_invested_million_usd::NUMERIC/NULLIF(total_deals_in_dataset::INT,0)),1) AS avg_deal,
        SUM(aum_billion_usd::NUMERIC) AS amount
    FROM investors_details
    """
    return pd.read_sql_query(text(query), conn)
# Investor Type Breakdown
def get_investor_type_distribution(conn):
    query = """
    SELECT 
        investor_type,
        COUNT(*) AS investor_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentage_share
    FROM investors_details
    WHERE investor_type IS NOT NULL
    GROUP BY investor_type
    ORDER BY investor_count DESC;
    """
    return pd.read_sql_query(text(query), conn)
# deal size distribution
def get_average_deal_size(conn):
    query = """
    SELECT 
        investor_name,
        investor_type,
        total_deals_in_dataset,total_invested_million_usd,
        ROUND((total_invested_million_usd::NUMERIC/ NULLIF(total_deals_in_dataset::INT, 0)), 2) AS avg_deal_size_millions
    FROM investors_details
    WHERE investor_name IS NOT NULL
    ORDER BY avg_deal_size_millions DESC;
    """
    return pd.read_sql_query(text(query), conn)
# concentration
def get_funding_concentration(conn):
    query = """
    WITH total_pool AS (
        SELECT SUM(total_invested_million_usd) AS global_total_capital 
        FROM investors_details
        WHERE total_invested_million_usd IS NOT NULL AND total_invested_million_usd > 0
    ),
    ordered_investors AS (
        SELECT 
            investor_name,
            total_invested_million_usd AS capital_invested,
            (total_invested_million_usd::NUMERIC * 100.0 / (SELECT global_total_capital FROM total_pool)) AS individual_share_pct
        FROM investors_details
        WHERE investor_name IS NOT NULL AND total_invested_million_usd IS NOT NULL AND total_invested_million_usd > 0
        ORDER BY capital_invested DESC
    )
    SELECT 
        investor_name,
        capital_invested,
        ROUND(individual_share_pct::NUMERIC, 4) AS individual_share_pct,
        ROUND(SUM(individual_share_pct::NUMERIC) OVER(ORDER BY capital_invested DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_share_pct,
        ROUND(ROW_NUMBER() OVER(ORDER BY capital_invested DESC) * 100.0 / COUNT(*) OVER(), 2) AS cumulative_investor_pct
    FROM ordered_investors;
    """
    return pd.read_sql_query(text(query), conn)
def get_quarterly_market_growth(conn):
    query = """
    SELECT 
        period,
        year::INT AS funding_year,
        quarter AS funding_quarter,
        total_deals::INT AS deals_count,
        total_funding_million_usd::NUMERIC AS total_capital_raised,
        avg_deal_size_million_usd::NUMERIC AS avg_deal_size,
        median_deal_size_million_usd::NUMERIC AS median_deal_size,
        median_valuation_million_usd::NUMERIC AS median_startup_valuation,
        unique_startups::INT AS startups_count,
        unique_investors::INT AS investors_count
    FROM quarterly_summary
    WHERE period IS NOT NULL AND period <> ''
    -- Orders chronologically by year first, then by the quarterly sequence
    ORDER BY year ASC, quarter ASC; 
    """
    return pd.read_sql_query(text(query), conn)
def get_comprehensive_market_trends(conn):
    query = """
    SELECT 
        period,
        year::INT AS funding_year,
        quarter AS funding_quarter,
        total_deals::INT AS funding_deals_count,
        total_funding_million_usd::NUMERIC AS total_capital_raised,
        median_valuation_million_usd::NUMERIC AS median_startup_valuation,
       
        ROUND(
            (total_funding_million_usd::NUMERIC - LAG(total_funding_million_usd::NUMERIC) OVER (ORDER BY year ASC, quarter ASC))
            , 2
        ) AS quarter_over_quarter_acceleration
    FROM quarterly_summary
    WHERE period IS NOT NULL
    ORDER BY year ASC, quarter ASC;
    """
    return pd.read_sql_query(text(query), conn)

with engine.connect() as conn:
    print(get_active_investor(conn))