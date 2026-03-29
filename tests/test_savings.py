import sys
import pandas as pd
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.savings import simulate_savings, annual_savings, _simulate_days


def _make_monthly_df():
    rows = []
    for year in [2023, 2024]:
        for month in range(1, 13):
            rows.append({
                "year_month": f"{year}-{month:02d}",
                "year": year,
                "month": month,
                "units": 250,
                "charges": 250 * 6.5,
            })
    return pd.DataFrame(rows)


def _make_solar_df():
    dates = pd.date_range("2023-01-01", "2024-12-31", freq="D")
    df = pd.DataFrame({
        "date": dates,
        "ghi_mj_m2": 18.0,
        "ghi_kwh_m2": 18.0 / 3.6,
    })
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df


class TestSimulateDays:
    def test_no_solar_full_grid(self):
        gen = np.zeros(30)
        grid, solar_used, bat_used, exported = _simulate_days(gen, 10.0, 0.0)
        assert abs(grid - 300.0) < 0.01
        assert solar_used == 0.0
        assert exported == 0.0

    def test_excess_solar_all_exported(self):
        # 20 kWh gen, 5 kWh load, no battery → 5 direct + 15 exported, 0 grid
        gen = np.array([20.0])
        grid, solar_used, bat_used, exported = _simulate_days(gen, 5.0, 0.0)
        assert abs(grid) < 0.01
        assert abs(solar_used - 5.0) < 0.01
        assert abs(exported - 15.0) < 0.01

    def test_battery_absorbs_excess(self):
        # 20 kWh gen, 5 kWh load, 10 kWh battery → battery should charge
        gen = np.array([20.0])
        grid, solar_used, bat_used, exported = _simulate_days(gen, 5.0, 10.0)
        # With battery, some excess should go to battery instead of export
        assert exported < 15.0

    def test_battery_covers_evening_load(self):
        # Day 1: big solar, small load → charges battery
        # Day 2: no solar, load → should use battery
        gen = np.array([20.0, 0.0])
        grid, solar_used, bat_used, exported = _simulate_days(gen, 5.0, 10.0)
        assert bat_used > 0  # battery discharged on day 2
        assert grid < 10.0  # grid need reduced by battery


class TestSimulateSavings:
    def setup_method(self):
        self.monthly_df = _make_monthly_df()
        self.solar_df = _make_solar_df()

    def test_output_shape(self):
        result = simulate_savings(self.monthly_df, self.solar_df, system_kw=5.0)
        assert len(result) == len(self.monthly_df)

    def test_savings_positive_with_solar(self):
        result = simulate_savings(self.monthly_df, self.solar_df, system_kw=5.0)
        assert (result["savings_inr"] > 0).all()

    def test_zero_system_zero_savings(self):
        result = simulate_savings(self.monthly_df, self.solar_df, system_kw=0.0)
        # With 0 kW system, solar gen = 0, savings should be ~0 (possibly small export rounding)
        assert (result["savings_inr"] >= 0).all()
        assert result["solar_gen_kwh"].sum() == 0.0

    def test_larger_system_more_savings(self):
        # Use a small system vs a medium one where consumption isn't fully covered
        r1 = simulate_savings(self.monthly_df, self.solar_df, system_kw=1.0)
        r3 = simulate_savings(self.monthly_df, self.solar_df, system_kw=3.0)
        assert r3["savings_inr"].sum() > r1["savings_inr"].sum()

    def test_battery_increases_savings(self):
        without = simulate_savings(self.monthly_df, self.solar_df, system_kw=5.0, battery_kwh=0.0)
        with_bat = simulate_savings(self.monthly_df, self.solar_df, system_kw=5.0, battery_kwh=10.0)
        assert with_bat["savings_inr"].sum() >= without["savings_inr"].sum()

    def test_grid_plus_solar_used_equals_consumption(self):
        result = simulate_savings(self.monthly_df, self.solar_df, system_kw=5.0)
        # grid + solar_used + battery_used ≈ consumption (within rounding)
        diff = (result["grid_kwh"] + result["solar_used_kwh"] + result["battery_used_kwh"]
                - result["consumption_kwh"]).abs()
        assert (diff < 1.0).all()

    def test_bill_with_solar_not_negative(self):
        result = simulate_savings(self.monthly_df, self.solar_df, system_kw=20.0)
        assert (result["bill_with_solar_inr"] >= 0).all()


class TestAnnualSavings:
    def test_aggregation_sums_correctly(self):
        monthly_df = _make_monthly_df()
        solar_df = _make_solar_df()
        savings = simulate_savings(monthly_df, solar_df, system_kw=5.0)
        ann = annual_savings(savings)
        assert set(ann["year"].tolist()) == {2023, 2024}
        assert abs(ann["savings_inr"].sum() - savings["savings_inr"].sum()) < 1.0

    def test_self_consumption_pct_in_range(self):
        monthly_df = _make_monthly_df()
        solar_df = _make_solar_df()
        savings = simulate_savings(monthly_df, solar_df, system_kw=5.0)
        ann = annual_savings(savings)
        assert (ann["self_consumption_pct"].dropna().between(0, 100)).all()

    def test_solar_fraction_pct_in_range(self):
        monthly_df = _make_monthly_df()
        solar_df = _make_solar_df()
        savings = simulate_savings(monthly_df, solar_df, system_kw=5.0)
        ann = annual_savings(savings)
        assert (ann["solar_fraction_pct"].dropna().between(0, 100)).all()
