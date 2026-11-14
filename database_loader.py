import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

funding = pd.read_csv("funding_rounds.csv")
startups = pd.read_csv("startups.csv")
summary = pd.read_csv("quarterly_summary.csv")
investors = pd.read_csv("investors.csv")

admin_url = URL.create(
    drivername = "postgresql+psycopg2",
    username = "postgres",
    password = "Simran@2754",
    host = "localhost",
    port = 5432,
    database = "postgres"
)
admin_engine = create_engine(admin_url)
with admin_engine.connect() as conn:
    print(conn.execute(text("SELECT current_database()")).scalar()) 
    databases = conn.execute(text("SELECT datname FROM pg_database")).fetchall()

    for db in databases:
        print(db[0])
with admin_engine.connect() as conn:
    conn.execute(text("COMMIT"))
    conn.execute(text("CREATE DATABASE startup_ecosystem"))

print("Database created!")

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

datasets ={
    "funding_round_details": funding,
    "investors_details": investors,
    "quarterly_summary": summary,
    "startup_details": startups
}
for tablename, dataframe in datasets.items():
    dataframe.to_sql(
        name= tablename,con = engine, if_exists = "replace",index = False)
    print(f"{tablename} connected successfully")
with engine.connect() as conn:

    result = conn.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE';
    """))

    for row in result:
        print(row[0])
query = """
Select table_name, column_name, data_type,is_nullable
From information_schema.columns
where table_schema = 'public'
Order by table_name,ordinal_position;
"""
with engine.connect() as conn:
    result = conn.execute(text(query))
    for row in result:
        print(row)
        
query = """
Select startup_id,startup_name, funding_date
from funding_round_details
limit 5;
"""
with engine.connect() as conn:
    result = conn.execute(text(query))
    for row in result:
        print(row)