import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "electricity_bills.db"


def load_bills(db_path=DB_PATH):
    conn = sqlite3.connect(str(db_path))
    df = pd.read_sql_query("SELECT * FROM electricity_bills ORDER BY bill_date", conn)
    conn.close()

    df["bill_date"] = pd.to_datetime(df["bill_date"])
    df["period_start"] = df["bill_date"].shift(1)
    df.loc[0, "period_start"] = df.loc[0, "bill_date"] - pd.Timedelta(days=60)
    df["period_end"] = df["bill_date"]
    df["period_days"] = (df["period_end"] - df["period_start"]).dt.days
    df["rate_per_unit"] = (df["total_charges"] / df["consumption_units"]).round(2)

    return df
