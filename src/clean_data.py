"""
Step 1: Clean the raw startup funding dataset.

The raw data (2,372 funding deals, Jan 2015 - Aug 2017) has real-world quality issues:
- Dates in mixed formats: dd/mm/yyyy, d/mm/yyyy, dd/mm.yyyy
- Funding amounts stored as text with commas ("1,300,000"), many missing
- Same investment type spelled multiple ways ("Seed Funding" vs "SeedFunding")
- Same city spelled multiple ways ("Bangalore" vs "Bengaluru", "Gurgaon" vs "Gurugram")
- Industry verticals with inconsistent casing ("ECommerce", "eCommerce", "E-Commerce")

Run:  python src/clean_data.py
Output: data/startup_funding_clean.csv
"""

import pandas as pd
import numpy as np

RAW_PATH = "data/startup_funding_raw.csv"
CLEAN_PATH = "data/startup_funding_clean.csv"


def clean_dates(s: pd.Series) -> pd.Series:
    """Fix typos like '12/05.2015' and parse mixed dd/mm/yyyy formats."""
    s = s.str.replace(".", "/", regex=False).str.replace("//", "/", regex=False)
    return pd.to_datetime(s, format="%d/%m/%Y", dayfirst=True, errors="coerce")


def clean_amount(s: pd.Series) -> pd.Series:
    """Convert '1,300,000' text to numeric USD. Non-numeric -> NaN (undisclosed)."""
    s = s.astype(str).str.replace(",", "", regex=False).str.strip()
    return pd.to_numeric(s, errors="coerce")


def standardize_investment_type(s: pd.Series) -> pd.Series:
    """Collapse spelling variants into 4 canonical categories."""
    mapping = {
        "seed funding": "Seed Funding",
        "seedfunding": "Seed Funding",
        "crowd funding": "Crowd Funding",
        "crowdfunding": "Crowd Funding",
        "private equity": "Private Equity",
        "privateequity": "Private Equity",
        "debt funding": "Debt Funding",
    }
    key = s.str.strip().str.lower().str.replace(r"\s+", " ", regex=True)
    return key.map(mapping).fillna(s.str.strip())


def standardize_city(s: pd.Series) -> pd.Series:
    """Merge city aliases and strip multi-city entries to the primary city."""
    s = s.str.strip().str.split("/").str[0].str.strip()
    aliases = {
        "Bengaluru": "Bangalore",
        "Gurugram": "Gurgaon",
        "Delhi": "New Delhi",
        "Nw Delhi": "New Delhi",
        "New delhi": "New Delhi",
    }
    return s.replace(aliases)


def standardize_industry(s: pd.Series) -> pd.Series:
    """Normalize casing variants of the same vertical."""
    s = s.str.strip()
    aliases = {
        "eCommerce": "E-Commerce",
        "ECommerce": "E-Commerce",
        "Ecommerce": "E-Commerce",
        "E-commerce": "E-Commerce",
    }
    return s.replace(aliases)


def main():
    df = pd.read_csv(RAW_PATH)
    n_raw = len(df)

    df["Date"] = clean_dates(df["Date"])
    df["AmountInUSD"] = clean_amount(df["AmountInUSD"])
    df["InvestmentType"] = standardize_investment_type(df["InvestmentType"].astype(str))
    df["CityLocation"] = standardize_city(df["CityLocation"].astype(str).replace("nan", np.nan))
    df["IndustryVertical"] = standardize_industry(df["IndustryVertical"].astype(str).replace("nan", np.nan))
    df["StartupName"] = df["StartupName"].str.strip()

    # Derived columns for time-series analysis
    df["Year"] = df["Date"].dt.year
    df["YearMonth"] = df["Date"].dt.to_period("M").astype(str)
    df["AmountDisclosed"] = df["AmountInUSD"].notna()

    # Drop rows where the date could not be parsed (unusable for trend analysis)
    df = df.dropna(subset=["Date"])

    df.to_csv(CLEAN_PATH, index=False)

    print(f"Raw rows:            {n_raw}")
    print(f"Clean rows:          {len(df)}")
    print(f"Disclosed amounts:   {df['AmountDisclosed'].sum()} "
          f"({df['AmountDisclosed'].mean():.0%})")
    print(f"Investment types:    {df['InvestmentType'].nunique()} canonical categories")
    print(f"Date range:          {df['Date'].min().date()} to {df['Date'].max().date()}")
    print(f"Saved -> {CLEAN_PATH}")


if __name__ == "__main__":
    main()
