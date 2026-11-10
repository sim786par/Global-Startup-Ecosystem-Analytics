from __future__ import annotations

import os
from typing import Optional, Iterable

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

load_dotenv()

TABLE_CANDIDATES = {
    "startups": ["startups", "startup_details", "startup"],
    "funding": ["funding_rounds", "funding_round_details", "funding"],
    "investors": ["investors", "investors_details", "investor_details", "investor"],
    "quarterly": ["quarterly_summary", "quarterly_summaries"],
}

COLUMN_CANDIDATES = {
    "startup_id": ["startup_id", "id"],
    "startup_name": ["startup_name", "name", "company_name"],
    "industry": ["industry", "sector", "category"],
    "country": ["country", "country_name"],
    "city": ["city"],
    "employees": ["employees", "employee_count", "num_employees", "employee_size"],
    "revenue_status": ["revenue_status", "revenue_stage", "profitability_status"],
    "round_id": ["round_id", "funding_round_id", "id"],
    "funding_stage": ["funding_stage", "stage", "round_type"],
    "amount": ["amount_raised", "amount_million_usd", "funding_amount", "amount", "raised_amount"],
    "valuation": ["valuation", "valuation_million_usd", "post_money_valuation"],
    "funding_date": ["funding_date", "date", "announced_date"],
    "lead_investor": ["lead_investor", "investor_name", "lead_investor_name"],
    "investor_id": ["investor_id", "id"],
    "investor_name": ["investor_name", "name"],
    "investor_type": ["investor_type", "type", "category"],
    "aum": ["aum", "assets_under_management", "aum_million_usd"],
    "deal_activity": ["deal_activity", "number_of_deals", "deals_count", "deal_count"],
    "quarter": ["quarter", "quarter_label", "year_quarter", "period"],
    "total_funding": ["total_funding", "total_funding_million_usd", "funding_amount"],
    "deal_count": ["deal_count", "total_deals", "number_of_deals"],
    "market_growth": ["market_growth", "growth_rate", "growth_pct", "quarterly_growth"],
    "year": ["year"],
}


def get_engine() -> Engine:
    """Create a SQLAlchemy engine from DATABASE_URL or individual DB_* variables."""
    url = os.getenv("DATABASE_URL")
    if not url:
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME", "startup_analytics")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")
        if not password:
            raise RuntimeError(
                "Database credentials missing. Set DATABASE_URL or DB_PASSWORD in .env."
            )
        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
    return create_engine(url, pool_pre_ping=True)


def list_tables(engine: Engine) -> list[str]:
    return inspect(engine).get_table_names()


def resolve_table(engine: Engine, logical_name: str) -> Optional[str]:
    existing = set(list_tables(engine))
    for candidate in TABLE_CANDIDATES.get(logical_name, [logical_name]):
        if candidate in existing:
            return candidate
    return None


def get_columns(engine: Engine, table_name: str) -> list[str]:
    return [c["name"] for c in inspect(engine).get_columns(table_name)]


def resolve_column(columns: Iterable[str], logical_name: str) -> Optional[str]:
    existing = set(columns)
    for candidate in COLUMN_CANDIDATES.get(logical_name, [logical_name]):
        if candidate in existing:
            return candidate
    return None


def read_table(engine: Engine, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
    # Table names come from SQLAlchemy inspection, not user input.
    q = f'SELECT * FROM "{table_name}"'
    if limit is not None:
        q += f" LIMIT {int(limit)}"
    return pd.read_sql(text(q), engine)


def table_info(engine: Engine) -> dict[str, dict]:
    info = {}
    for logical in TABLE_CANDIDATES:
        table = resolve_table(engine, logical)
        if table:
            info[logical] = {
                "table": table,
                "columns": get_columns(engine, table),
                "rows": int(pd.read_sql(text(f'SELECT COUNT(*) AS n FROM "{table}"'), engine).iloc[0, 0]),
            }
    return info


def _select_expr(col: Optional[str], alias: str, table_alias: str = "") -> str:
    if not col:
        return f"NULL AS {alias}"
    prefix = f"{table_alias}." if table_alias else ""
    return f'{prefix}"{col}" AS "{alias}"'


def get_startup_funding(engine: Engine) -> pd.DataFrame:
    """Return one row per startup with cumulative funding, when required columns exist."""
    st = resolve_table(engine, "startups")
    fr = resolve_table(engine, "funding")
    if not st:
        return pd.DataFrame()
    sc = get_columns(engine, st)
    startup_id = resolve_column(sc, "startup_id")
    name = resolve_column(sc, "startup_name")
    industry = resolve_column(sc, "industry")
    country = resolve_column(sc, "country")
    employees = resolve_column(sc, "employees")
    revenue = resolve_column(sc, "revenue_status")

    if not fr:
        cols = [c for c in [startup_id, name, industry, country, employees, revenue] if c]
        return read_table(engine, st)[cols] if cols else read_table(engine, st)

    fc = get_columns(engine, fr)
    f_startup_id = resolve_column(fc, "startup_id")
    amount = resolve_column(fc, "amount")
    if not startup_id or not f_startup_id or not amount:
        return read_table(engine, st)

    # Quote identifiers discovered from database metadata.
    fields = [
        _select_expr(f"s.{startup_id}" if False else startup_id, "startup_id", "s"),
        _select_expr(name, "startup_name", "s"),
        _select_expr(industry, "industry", "s"),
        _select_expr(country, "country", "s"),
        _select_expr(employees, "employees", "s"),
        _select_expr(revenue, "revenue_status", "s"),
        f'SUM(f."{amount}") AS total_funding',
    ]
    join = f'FROM "{st}" s LEFT JOIN "{fr}" f ON s."{startup_id}" = f."{f_startup_id}"'
    group_cols = [f's."{startup_id}"']
    for col in [name, industry, country, employees, revenue]:
        if col:
            group_cols.append(f's."{col}"')
    q = f"SELECT {', '.join(fields)} {join} GROUP BY {', '.join(group_cols)}"
    return pd.read_sql(text(q), engine)


def get_funding_records(engine: Engine) -> pd.DataFrame:
    fr = resolve_table(engine, "funding")
    st = resolve_table(engine, "startups")
    if not fr:
        return pd.DataFrame()
    fc = get_columns(engine, fr)
    amount = resolve_column(fc, "amount")
    date = resolve_column(fc, "funding_date")
    stage = resolve_column(fc, "funding_stage")
    valuation = resolve_column(fc, "valuation")
    startup_id = resolve_column(fc, "startup_id")
    fields = [
        _select_expr(resolve_column(fc, "round_id"), "round_id", "f"),
        _select_expr(startup_id, "startup_id", "f"),
        _select_expr(stage, "funding_stage", "f"),
        _select_expr(amount, "amount_raised", "f"),
        _select_expr(valuation, "valuation", "f"),
        _select_expr(date, "funding_date", "f"),
        _select_expr(resolve_column(fc, "lead_investor"), "lead_investor", "f"),
    ]
    join = f'FROM "{fr}" f'
    if st and startup_id:
        sc = get_columns(engine, st)
        sid = resolve_column(sc, "startup_id")
        sname = resolve_column(sc, "startup_name")
        if sid and sname:
            fields.append(_select_expr(sname, "startup_name", "s"))
            join += f' LEFT JOIN "{st}" s ON f."{startup_id}" = s."{sid}"'
    q = f"SELECT {', '.join(fields)} {join}"
    return pd.read_sql(text(q), engine)


def get_investor_data(engine: Engine) -> pd.DataFrame:
    table = resolve_table(engine, "investors")
    if not table:
        return pd.DataFrame()
    df = read_table(engine, table)
    cols = get_columns(engine, table)
    rename = {}
    for logical, target in [
        ("investor_name", "investor_name"),
        ("investor_type", "investor_type"),
        ("aum", "aum"),
        ("deal_activity", "deal_activity"),
    ]:
        source = resolve_column(cols, logical)
        if source and source != target:
            rename[source] = target
    return df.rename(columns=rename)


def get_quarterly_data(engine: Engine) -> pd.DataFrame:
    table = resolve_table(engine, "quarterly")
    return read_table(engine, table) if table else pd.DataFrame()


def main() -> None:
    engine = get_engine()
    print("\n=== PostgreSQL tables and columns ===")
    info = table_info(engine)
    if not info:
        print("No recognized project tables found. Available tables:", list_tables(engine))
        return
    for logical, details in info.items():
        print(f"\n{logical} -> {details['table']} ({details['rows']} rows)")
        print(", ".join(details["columns"]))

    print("\n=== Startup funding preview ===")
    startup_funding = get_startup_funding(engine)
    print(startup_funding.head(10).to_string(index=False))

    print("\n=== Funding records preview ===")
    funding = get_funding_records(engine)
    print(funding.head(10).to_string(index=False))

    print("\n=== Investor preview ===")
    investors = get_investor_data(engine)
    if not investors.empty:
        print(investors.head(10).to_string(index=False))
    else:
        print("Investor table not found.")

    engine.dispose()


if __name__ == "__main__":
    main()
