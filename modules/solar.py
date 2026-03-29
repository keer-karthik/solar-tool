import requests
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

SOLAR_CACHE_PATH = Path(__file__).parent.parent / "data" / "solar_cache.csv"
CHENNAI_LAT = 13.08
CHENNAI_LON = 80.27
DEFAULT_PERFORMANCE_RATIO = 0.80


def fetch_solar(start_date, end_date):
    resp = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": CHENNAI_LAT,
            "longitude": CHENNAI_LON,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "shortwave_radiation_sum",
            "timezone": "Asia/Kolkata",
        },
        timeout=30,
    )
    resp.raise_for_status()
    d = resp.json()["daily"]
    df = pd.DataFrame({
        "date": pd.to_datetime(d["time"]),
        "ghi_mj_m2": d["shortwave_radiation_sum"],
    })
    df["ghi_kwh_m2"] = (df["ghi_mj_m2"] / 3.6).round(4)
    return df


def get_solar_data(force_refresh=False):
    """
    Returns daily Chennai solar irradiance data, fetched from Open-Meteo and cached to CSV.
    ghi_kwh_m2: Global Horizontal Irradiance in kWh/m² (converted from MJ/m²)
    """
    yesterday = (date.today() - timedelta(days=2)).isoformat()

    if not force_refresh and SOLAR_CACHE_PATH.exists():
        cached = pd.read_csv(SOLAR_CACHE_PATH, parse_dates=["date"])
        last = cached["date"].max().date().isoformat()
        if last >= yesterday:
            return _add_cols(cached)
        fresh = fetch_solar(
            (cached["date"].max().date() + timedelta(days=1)).isoformat(), yesterday
        )
        combined = pd.concat([cached, fresh], ignore_index=True)
        combined.to_csv(SOLAR_CACHE_PATH, index=False)
        return _add_cols(combined)

    df = fetch_solar("2022-01-01", yesterday)
    SOLAR_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SOLAR_CACHE_PATH, index=False)
    return _add_cols(df)


def _add_cols(df):
    df = df.copy()
    if "ghi_kwh_m2" not in df.columns:
        df["ghi_kwh_m2"] = (df["ghi_mj_m2"] / 3.6).round(4)
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df


def daily_generation(solar_df, system_kw, performance_ratio=DEFAULT_PERFORMANCE_RATIO):
    """
    Returns solar_df with gen_kwh column added.
    Formula: gen_kwh = ghi_kwh_m2 × system_kw × performance_ratio
    (1 kWp panel rated at 1000 W/m² STC, so kWh = kWp × GHI_kWh/m² × PR)
    """
    df = solar_df.copy()
    df["gen_kwh"] = (df["ghi_kwh_m2"] * system_kw * performance_ratio).round(3)
    return df


def monthly_generation(solar_df, system_kw, performance_ratio=DEFAULT_PERFORMANCE_RATIO):
    """Returns DataFrame with year, month, year_month, gen_kwh (monthly totals)."""
    daily = daily_generation(solar_df, system_kw, performance_ratio)
    result = daily.groupby(["year", "month"]).agg(gen_kwh=("gen_kwh", "sum")).reset_index()
    result["gen_kwh"] = result["gen_kwh"].round(1)
    result["year_month"] = result.apply(
        lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1
    )
    return result
