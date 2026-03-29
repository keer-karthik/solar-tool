import pandas as pd
import numpy as np
from calendar import monthrange
from .solar import daily_generation


def simulate_savings(
    monthly_df,
    solar_df,
    system_kw,
    battery_kwh=0.0,
    performance_ratio=0.80,
    export_rate_inr=2.0,
):
    """
    Simulate monthly savings from solar + optional battery against historical consumption.

    Battery dispatch logic (per day):
      1. Solar directly offsets load
      2. Excess solar charges battery (capped at capacity)
      3. Any remaining excess solar is exported to grid
      4. Remaining load draws from battery
      5. Any remaining load comes from the grid

    Args:
        monthly_df: disaggregated monthly consumption DataFrame (units, charges, year, month)
        solar_df: daily solar irradiance DataFrame from get_solar_data()
        system_kw: solar system peak power in kWp
        battery_kwh: battery storage capacity in kWh (0 = no battery)
        performance_ratio: system performance ratio (inverter + wiring losses, typical 0.75–0.85)
        export_rate_inr: credit rate per exported kWh (TANGEDCO net metering)

    Returns:
        DataFrame with per-month savings breakdown.
    """
    avg_rate = _avg_rate(monthly_df)
    day_solar = daily_generation(solar_df, system_kw, performance_ratio)

    results = []
    for _, row in monthly_df.iterrows():
        y, m = int(row["year"]), int(row["month"])
        days = monthrange(y, m)[1]
        monthly_units = float(row["units"])
        daily_load = monthly_units / days

        mask = (day_solar["year"] == y) & (day_solar["month"] == m)
        gen_arr = day_solar.loc[mask, "gen_kwh"].values

        if len(gen_arr) == 0:
            gen_arr = np.zeros(days)

        grid, solar_used, bat_used, exported = _simulate_days(
            gen_arr, daily_load, battery_kwh
        )

        bill_before = monthly_units * avg_rate
        bill_after = max(0.0, grid * avg_rate - exported * export_rate_inr)

        results.append({
            "year_month": row["year_month"],
            "year": y,
            "month": m,
            "consumption_kwh": monthly_units,
            "solar_gen_kwh": round(float(gen_arr.sum()), 1),
            "solar_used_kwh": round(solar_used, 1),
            "battery_used_kwh": round(bat_used, 1),
            "exported_kwh": round(exported, 1),
            "grid_kwh": round(grid, 1),
            "bill_without_solar_inr": round(bill_before, 0),
            "bill_with_solar_inr": round(bill_after, 0),
            "savings_inr": round(bill_before - bill_after, 0),
        })

    return pd.DataFrame(results)


def _simulate_days(gen_arr, daily_load, battery_kwh, battery_eff=0.90):
    """Run a simplified daily dispatch simulation for one month."""
    battery_soc = battery_kwh * 0.5  # start at 50% state of charge
    total_grid = total_solar_used = total_bat_used = total_exported = 0.0

    for gen in gen_arr:
        direct = min(gen, daily_load)
        rem_load = daily_load - direct
        excess = gen - direct

        if battery_kwh > 0 and excess > 0:
            headroom = (battery_kwh - battery_soc) / battery_eff
            charged = min(excess, max(0.0, headroom))
            battery_soc += charged * battery_eff
            excess -= charged

        if battery_kwh > 0 and rem_load > 0:
            discharged = min(rem_load, battery_soc)
            battery_soc -= discharged
            rem_load -= discharged
            total_bat_used += discharged

        total_grid += rem_load
        total_solar_used += direct
        total_exported += excess

    return total_grid, total_solar_used, total_bat_used, total_exported


def _avg_rate(monthly_df):
    total_units = monthly_df["units"].sum()
    total_charges = monthly_df["charges"].sum()
    return (total_charges / total_units) if total_units > 0 else 6.58


def annual_savings(savings_df):
    """Aggregate monthly savings DataFrame to annual totals."""
    ann = savings_df.groupby("year").agg(
        consumption_kwh=("consumption_kwh", "sum"),
        solar_gen_kwh=("solar_gen_kwh", "sum"),
        solar_used_kwh=("solar_used_kwh", "sum"),
        grid_kwh=("grid_kwh", "sum"),
        exported_kwh=("exported_kwh", "sum"),
        savings_inr=("savings_inr", "sum"),
        bill_without_solar_inr=("bill_without_solar_inr", "sum"),
        bill_with_solar_inr=("bill_with_solar_inr", "sum"),
    ).reset_index()
    ann["self_consumption_pct"] = (
        ann["solar_used_kwh"] / ann["solar_gen_kwh"].replace(0, float("nan")) * 100
    ).round(1)
    ann["solar_fraction_pct"] = (
        ann["solar_used_kwh"] / ann["consumption_kwh"].replace(0, float("nan")) * 100
    ).round(1)
    return ann
