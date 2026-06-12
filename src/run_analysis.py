"""
Step 3: Run the SQL analysis and generate charts.

Executes every query in sql/analysis_queries.sql against data/funding.db,
prints the results, and saves four charts to outputs/.

Run:  python src/run_analysis.py
"""

import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DB_PATH = "data/funding.db"
SQL_PATH = "sql/analysis_queries.sql"

plt.rcParams.update({"figure.dpi": 130, "font.size": 9, "axes.grid": True,
                     "grid.alpha": 0.3, "axes.spines.top": False,
                     "axes.spines.right": False})


def run_all_queries(con):
    """Execute each query in the SQL file and print labelled results."""
    with open(SQL_PATH) as f:
        sql = f.read()
    # Split on the query separator comments (each query ends with ;)
    queries = [q.strip() for q in sql.split(";") if q.strip() and "SELECT" in q.upper()]
    for i, q in enumerate(queries, 1):
        df = pd.read_sql_query(q, con)
        print(f"\n========== Query {i} ==========")
        print(df.to_string(index=False))


def make_charts(con):
    # Chart 1: Yearly deals and capital
    yearly = pd.read_sql_query("""
        SELECT year, COUNT(*) AS deals, SUM(amount_usd)/1e9 AS usd_bn
        FROM funding_deals GROUP BY year ORDER BY year
    """, con)
    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax1.bar(yearly["year"].astype(str), yearly["deals"], color="#4C72B0", alpha=0.85)
    ax1.set_ylabel("Number of deals")
    ax2 = ax1.twinx()
    ax2.plot(yearly["year"].astype(str), yearly["usd_bn"], color="#C44E52",
             marker="o", linewidth=2)
    ax2.set_ylabel("Disclosed capital (USD bn)", color="#C44E52")
    ax2.grid(False)
    ax1.set_title("Indian Startup Funding by Year (2015\u20132017)")
    fig.tight_layout()
    fig.savefig("outputs/01_yearly_trend.png")

    # Chart 2: Top cities by deals
    cities = pd.read_sql_query("""
        SELECT city, COUNT(*) AS deals FROM funding_deals
        WHERE city IS NOT NULL AND city != 'nan'
        GROUP BY city ORDER BY deals DESC LIMIT 8
    """, con)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(cities["city"][::-1], cities["deals"][::-1], color="#55A868")
    ax.set_xlabel("Number of deals")
    ax.set_title("Top Startup Hubs by Deal Count")
    fig.tight_layout()
    fig.savefig("outputs/02_top_cities.png")

    # Chart 3: Seed vs PE mix over time
    mix = pd.read_sql_query("""
        SELECT year, investment_type, COUNT(*) AS deals
        FROM funding_deals
        WHERE investment_type IN ('Seed Funding', 'Private Equity')
        GROUP BY year, investment_type
    """, con).pivot(index="year", columns="investment_type", values="deals")
    mix_pct = mix.div(mix.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(7, 4))
    mix_pct.plot(kind="bar", stacked=True, ax=ax,
                 color=["#C44E52", "#4C72B0"], rot=0)
    ax.set_ylabel("% of deals")
    ax.set_title("Funding Mix Shift: Seed vs Private Equity")
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig("outputs/03_funding_mix.png")

    # Chart 4: Monthly deal momentum
    monthly = pd.read_sql_query("""
        SELECT year_month, COUNT(*) AS deals
        FROM funding_deals GROUP BY year_month ORDER BY year_month
    """, con)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(monthly["year_month"], monthly["deals"], color="#4C72B0", linewidth=1.8)
    ax.set_ylabel("Deals per month")
    ax.set_title("Monthly Deal Momentum")
    ticks = monthly["year_month"][::4]
    ax.set_xticks(ticks)
    ax.set_xticklabels(ticks, rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig("outputs/04_monthly_momentum.png")

    print("\nSaved 4 charts to outputs/")


def main():
    con = sqlite3.connect(DB_PATH)
    run_all_queries(con)
    make_charts(con)
    con.close()


if __name__ == "__main__":
    main()
