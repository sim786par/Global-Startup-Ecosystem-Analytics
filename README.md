# Global-Startup-Ecosystem-Analytics
## 📖 Project Overview

Global Startup Ecosystem Analytics is an interactive data analytics dashboard that provides comprehensive insights into startup funding, investor activity, industry growth, and market trends. The project leverages Python-based data analysis and visualization techniques to transform raw startup data into meaningful business insights. It enables users to explore startup performance, funding patterns, investor behavior, and quarterly market growth through interactive dashboards.

## Problem Statement

Startups generate large amounts of funding and market data, but it is often scattered across different sources, making it difficult to analyze investment trends, industry growth, and regional startup performance. This project provides an interactive analytics dashboard to explore the global startup ecosystem and support data-driven decision-making.

## Solution

Develop an interactive analytics dashboard that consolidates startup, funding, and investor data into a single platform. The dashboard provides insights into funding trends, startup growth, investor activity, and industry performance through dynamic visualizations and data analysis.

## Dataset used
[Global Startup Funding Rounds 2020–2026](https://www.kaggle.com/datasets/meruvakodandasuraj/global-startup-funding-rounds-20202026?resource=download) - from kaggle

Dataset Files
| File                    | Records | Description                                                         |
|-------------------------|--------:|---------------------------------------------------------------------|
| `funding_rounds.csv`    | 2,818   | Individual funding rounds with amounts, valuations, and investors. |
| `startups.csv`          | 1,747   | Startup profiles including sector, location, employees, and revenue status. |
| `investors.csv`         | 73      | Lead investor profiles with type, AUM, and deal activity. |
| `quarterly_summary.csv` | 25      | Aggregated quarterly market metrics. |

## 📊 Business Questions Answered

### 🚀 Startup Analysis
- Which startups have raised the highest funding?
- Which industries are experiencing the fastest growth?
- How are startups distributed across different countries?
- How does revenue status vary across startups?
- What is the distribution of startup employee sizes?

### 💰 Funding Analysis
- What is the average funding amount at each funding stage?
- Which funding rounds received the largest investments?
- How have funding trends changed over different quarters?
- Which countries receive the highest startup funding?
- Which sectors attract the most investment?

### 👥 Investor Analysis
- Who are the most active investors?
- What is the distribution of investor types?
- What is the average deal size for investors?
- Which investors have the highest Assets Under Management (AUM)?
- How concentrated is startup funding among investors?

### 📈 Market Analysis
- How has the startup market grown quarterly?
- How have startup valuations changed over time?
- How many funding deals occur each quarter?
- Is startup funding accelerating or slowing down over time?

# 🌍 Global Startup Ecosystem Analytics

## 📖 Project Overview

Global Startup Ecosystem Analytics is an interactive data analytics dashboard that provides comprehensive insights into startup funding, investor activity, industry growth, and market trends. The project leverages Python-based data analysis and visualization techniques to transform raw startup data into meaningful business insights. It enables users to explore startup performance, funding patterns, investor behavior, and quarterly market growth through interactive dashboards.

---

## 🛠️ Tech Stack

### Programming Language
- Python

### Libraries
- Pandas
- NumPy
- Matplotlib
- Plotly
- Dash
- SQLite3

### Database
- SQLite

### Development Tools
- Jupyter Notebook
- VS Code
- Git & GitHub

## 📈 Dashboard Features

### 🏠 Executive Dashboard
- Total Startups
- Total Funding
- Total Investors
- Average Valuation
- Quarterly Market Growth

### 🚀 Startup Analytics
- Top-Funded Startups
- Startup Distribution by Country
- Industry-wise Startup Distribution
- Employee Size Analysis
- Revenue Status Comparison

### 💰 Funding Analytics
- Funding by Stage
- Funding by Country
- Funding by Sector
- Largest Funding Rounds
- Quarterly Funding Trends

### 👥 Investor Analytics
- Most Active Investors
- Investor Type Distribution
- Top Investors by AUM
- Average Deal Size
- Funding Concentration

### 📊 Market Analytics
- Quarterly Market Growth
- Average Valuation Trend
- Number of Deals per Quarter
- Funding Growth Analysis

### 🔍 Interactive Features
- Filter by Country
- Filter by Industry
- Filter by Funding Stage
- Filter by Quarter
- Dynamic Charts and KPIs

## 📁 Project Structure

```
Global-Startup-Ecosystem-Analytics/
│
├── data/
│   ├── startups.csv
│   ├── funding_rounds.csv
│   ├── investors.csv
│   └── quarterly_summary.csv
│
├── assets/
│   ├── styles.css
│   └── images/
│
├── notebooks/
│   ├── data_cleaning.ipynb
│   ├── exploratory_analysis.ipynb
│   └── feature_engineering.ipynb
│
├── dashboard/
│   ├── app.py
│   ├── layouts.py
│   ├── callbacks.py
│   └── components.py
│
├── database/
│   └── startup_data.db
│
├── screenshots/
│
├── requirements.txt
├── README.md
└── LICENSE

