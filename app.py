# app.py
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Import your 4 separate page files from the views folder
from views import startup_page, funding_page, investors_page, market_page

# 1. Global Page Configuration
st.set_page_config(page_title="Startup Ecosystem Hub", page_icon="🚀", layout="wide")

# 2. Cached Database Engine (Created once, shared across all 4 files)
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="Simran@2754",
    host="localhost",
    port=5432,
    database="startup_ecosystem"
)

@st.cache_resource
def get_db_engine(url):
    return create_engine(url)

engine = get_db_engine(db_url)

# 3. Sidebar Navigation Menu
st.sidebar.title("Navigation Hub")
selection = st.sidebar.radio(
    "Select Analysis View:",
    [
        "🏢 Startup Intelligence",
        "💰 Funding & Stages",
        "🤝 Investor Profiles",
        "📈 Market Growth Trends"
    ]
)

# 4. Route to the Selected File
if selection == "🏢 Startup Intelligence":
    startup_page.render_page(engine)
elif selection == "💰 Funding & Stages":
    funding_page.render_page(engine)
elif selection == "🤝 Investor Profiles":
    investors_page.render_page(engine)
elif selection == "📈 Market Growth Trends":
    market_page.render_page(engine)
