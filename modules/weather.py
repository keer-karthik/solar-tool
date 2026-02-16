import requests
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

CACHE_PATH = Path(__file__).parent.parent / "data" / "weather_cache.csv"
CHENNAI_LAT = 13.08
CHENNAI_LON = 80.27
CDD_BASE = 24.0


def fetch_weather(start_date, end_date):
    resp = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": CHENNAI_LAT,
            "longitude": CHENNAI_LON,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean",
            "timezone": "Asia/Kolkata",
        },
        timeout=30,
    )
    resp.raise_for_status()
    d = resp.json()["daily"]
    return pd.DataFrame({
        "date": pd.to_datetime(d["time"]),
        "temp_max": d["temperature_2m_max"],
        "temp_min": d["temperature_2m_min"],
        "temp_mean": d["temperature_2m_mean"],
    })


def get_weather_data(cdd_base=CDD_BASE, force_refresh=False):
    yesterday = (date.today() - timedelta(days=2)).isoformat()

    if not force_refresh and CACHE_PATH.exists():
        cached = pd.read_csv(CACHE_PATH, parse_dates=["date"])
        last = cached["date"].max().date().isoformat()
        if last >= yesterday:
            return _add_cdd(cached, cdd_base)
        fresh = fetch_weather(
            (cached["date"].max().date() + timedelta(days=1)).isoformat(), yesterday
        )
        combined = pd.concat([cached, fresh], ignore_index=True)
        combined.to_csv(CACHE_PATH, index=False)
        return _add_cdd(combined, cdd_base)

    df = fetch_weather("2022-01-01", yesterday)
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CACHE_PATH, index=False)
    return _add_cdd(df, cdd_base)


def _add_cdd(df, cdd_base=CDD_BASE):
    df = df.copy()
    df["cdd"] = (df["temp_mean"] - cdd_base).clip(lower=0)
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df
