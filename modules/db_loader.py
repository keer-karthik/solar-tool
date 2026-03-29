import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "electricity_bills.db"


def load_bills(db_path=DB_PATH):
    conn = sqlite3.connect(str(db_path))
    df = pd.read_sql_query("SELECT * FROM electricity_bills ORDER BY bill_date", conn)
    conn.close()
    return derive_bill_periods(df)


def derive_bill_periods(df):
    """Add period_start, period_end, period_days, rate_per_unit to a raw bills DataFrame.
    Works with both the SQLite schema and user-uploaded CSVs."""
    df = df.copy()
    df["bill_date"] = pd.to_datetime(df["bill_date"])
    df = df.sort_values("bill_date").reset_index(drop=True)
    df["period_start"] = df["bill_date"].shift(1)
    df.loc[0, "period_start"] = df.loc[0, "bill_date"] - pd.Timedelta(days=60)
    df["period_end"] = df["bill_date"]
    df["period_days"] = (df["period_end"] - df["period_start"]).dt.days
    df["rate_per_unit"] = (df["total_charges"] / df["consumption_units"]).round(2)
    return df
