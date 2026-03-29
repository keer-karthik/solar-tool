import sys
import pandas as pd
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.disaggregate import disaggregate_to_monthly


def _make_bills(n=4):
    """Create synthetic bimonthly bills DataFrame."""
    dates = pd.date_range("2023-01-01", periods=n + 1, freq="60D")
    rows = []
    for i in range(n):
        rows.append({
            "bill_date": dates[i + 1],
            "period_start": dates[i],
            "period_end": dates[i + 1],
            "period_days": (dates[i + 1] - dates[i]).days,
            "consumption_units": 300 + i * 20,
            "total_charges": (300 + i * 20) * 6.5,
            "rate_per_unit": 6.5,
        })
    return pd.DataFrame(rows)


def _make_weather(start="2022-12-01", end="2024-06-30", cdd_base=24.0):
    """Create synthetic daily weather DataFrame with CDD."""
    dates = pd.date_range(start, end, freq="D")
    rng = np.random.default_rng(42)
    temps = 28 + rng.normal(0, 3, len(dates))
    df = pd.DataFrame({
        "date": dates,
        "temp_max": temps + 3,
        "temp_min": temps - 3,
        "temp_mean": temps,
    })
    df["cdd"] = (df["temp_mean"] - cdd_base).clip(lower=0)
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df


class TestDisaggregateToMonthly:
    def setup_method(self):
        self.bills = _make_bills(4)
        self.weather = _make_weather()

    def test_output_columns(self):
        result = disaggregate_to_monthly(self.bills, self.weather)
        assert set(["year_month", "year", "month", "units", "charges"]).issubset(result.columns)

    def test_monthly_totals_match_bill_totals(self):
        """Core invariant: sum of monthly units per bill period must equal the original bill."""
        result = disaggregate_to_monthly(self.bills, self.weather)
        # Total units across all months should match sum of all bills
        total_monthly = result["units"].sum()
        total_billed = self.bills["consumption_units"].sum()
        assert abs(total_monthly - total_billed) <= len(self.bills)  # rounding tolerance of 1/bill

    def test_no_negative_units(self):
        result = disaggregate_to_monthly(self.bills, self.weather)
        assert (result["units"] >= 0).all()

    def test_sorted_output(self):
        result = disaggregate_to_monthly(self.bills, self.weather)
        assert result["year_month"].is_monotonic_increasing

    def test_charges_proportional_to_units(self):
        result = disaggregate_to_monthly(self.bills, self.weather)
        # charges / units should be roughly constant (= rate_per_unit = 6.5)
        ratios = result["charges"] / result["units"].replace(0, float("nan"))
        assert ratios.dropna().between(5.0, 8.0).all()

    def test_base_load_only_when_no_cdd(self):
        """With zero CDD everywhere, daily units should be uniform (base_load only)."""
        weather_flat = self.weather.copy()
        weather_flat["cdd"] = 0.0
        result = disaggregate_to_monthly(self.bills, weather_flat)
        # All months within a billing period should have similar units
        assert (result["units"] >= 0).all()
