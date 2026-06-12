"""
Step 2: Load the cleaned dataset into SQLite so analysis can be done in SQL.

Run:  python src/load_to_db.py
Output: data/funding.db  (table: funding_deals)
"""

import sqlite3
import pandas as pd

CLEAN_PATH = "data/startup_funding_clean.csv"
DB_PATH = "data/funding.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS funding_deals (
    deal_id          INTEGER PRIMARY KEY,
    deal_date        DATE,
    startup_name     TEXT,
    industry         TEXT,
    sub_vertical     TEXT,
    city             TEXT,
    investors        TEXT,
    investment_type  TEXT,
    amount_usd       REAL,
    year             INTEGER,
    year_month       TEXT,
    amount_disclosed INTEGER
);
"""


def main():
    df = pd.read_csv(CLEAN_PATH, parse_dates=["Date"])

    out = pd.DataFrame({
        "deal_id": df["SNo"],
        "deal_date": df["Date"].dt.date,
        "startup_name": df["StartupName"],
        "industry": df["IndustryVertical"],
        "sub_vertical": df["SubVertical"],
        "city": df["CityLocation"],
        "investors": df["InvestorsName"],
        "investment_type": df["InvestmentType"],
        "amount_usd": df["AmountInUSD"],
        "year": df["Year"],
        "year_month": df["YearMonth"],
        "amount_disclosed": df["AmountDisclosed"].astype(int),
    })

    con = sqlite3.connect(DB_PATH)
    con.executescript("DROP TABLE IF EXISTS funding_deals;" + SCHEMA)
    out.to_sql("funding_deals", con, if_exists="append", index=False)

    n = con.execute("SELECT COUNT(*) FROM funding_deals").fetchone()[0]
    print(f"Loaded {n} deals into {DB_PATH} (table: funding_deals)")
    con.close()


if __name__ == "__main__":
    main()
