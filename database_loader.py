import tomllib
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# 1. Load your Render PostgreSQL credentials from .streamlit/secrets.toml
with open(".streamlit/secrets.toml", "rb") as f:
    db_config = tomllib.load(f)["postgres"]

# 2. Read the 4 CSV files from your 'dataset/' folder
funding = pd.read_csv("dataset/funding_rounds.csv")
startups = pd.read_csv("dataset/startups.csv")
summary = pd.read_csv("dataset/quarterly_summary.csv")
investors = pd.read_csv("dataset/investors.csv")

# 3. Connect directly to your Render cloud database (SSL required)
db_url = URL.create(**db_config)
engine = create_engine(
    db_url,
    connect_args={"sslmode": "require"}
)

with engine.connect() as conn:
    print("Connected to database:", conn.execute(text("SELECT current_database()")).scalar())

# 4. Upload all 4 datasets to PostgreSQL
datasets = {
    "funding_round_details": funding,
    "investors_details": investors,
    "quarterly_summary": summary,
    "startup_details": startups
}

for tablename, dataframe in datasets.items():
    dataframe.to_sql(
        name=tablename,
        con=engine,
        if_exists="replace",
        index=False
    )
    print(f"{tablename} uploaded successfully ({len(dataframe)} rows)")

# 5. Verify all 4 tables exist in your Render database
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE';
    """))
    print("Tables verified in Render DB:", [row for row in result])
