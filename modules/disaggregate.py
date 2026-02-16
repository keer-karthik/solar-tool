import pandas as pd

BASE_LOAD_DAILY = 8.0  # kWh/day


def disaggregate_to_monthly(bills_df, weather_df, base_load=BASE_LOAD_DAILY):
    records = []

    for _, bill in bills_df.iterrows():
        start, end = bill["period_start"], bill["period_end"]
        units = bill["consumption_units"]
        rate = bill["rate_per_unit"]

        mask = (weather_df["date"] > start) & (weather_df["date"] <= end)
        pw = weather_df.loc[mask].copy()

        if pw.empty:
            ym = end.strftime("%Y-%m")
            records.append({"year_month": ym, "year": end.year, "month": end.month,
                            "units": units, "charges": units * rate})
            continue

        N = len(pw)
        total_cdd = pw["cdd"].sum()

        k = (units - N * base_load) / total_cdd if total_cdd > 0 else 0
        if k < 0:
            k = 0

        if k > 0:
            pw["daily_units"] = base_load + k * pw["cdd"]
        else:
            pw["daily_units"] = units / N

        # Normalize to match bill total exactly
        pw["daily_units"] *= units / pw["daily_units"].sum()

        pw["year_month"] = pw["date"].dt.to_period("M")
        for ym, grp in pw.groupby("year_month"):
            records.append({
                "year_month": str(ym), "year": ym.year, "month": ym.month,
                "units": round(grp["daily_units"].sum(), 1),
                "charges": round(grp["daily_units"].sum() * rate, 2),
            })

    result = pd.DataFrame(records)
    result = result.groupby(["year_month", "year", "month"], as_index=False).agg(
        units=("units", "sum"), charges=("charges", "sum")
    )
    result = result.sort_values("year_month").reset_index(drop=True)
    result["units"] = result["units"].round(0).astype(int)
    result["charges"] = result["charges"].round(0).astype(int)
    return result
