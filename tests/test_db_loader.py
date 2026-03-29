import sys
import pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.db_loader import load_bills

DB_PATH = Path(__file__).parent.parent / "data" / "electricity_bills.db"


class TestLoadBills:
    def setup_method(self):
        self.df = load_bills(DB_PATH)

    def test_returns_dataframe(self):
        assert isinstance(self.df, pd.DataFrame)

    def test_expected_columns(self):
        required = {"bill_date", "consumption_units", "total_charges",
                    "rate_per_unit", "period_start", "period_end", "period_days"}
        assert required.issubset(self.df.columns)

    def test_records_count(self):
        assert len(self.df) == 24

    def test_period_days_positive(self):
        assert (self.df["period_days"] > 0).all()

    def test_period_days_reasonable(self):
        # Bimonthly bills: expect 50–70 day periods
        assert self.df["period_days"].between(45, 75).all()

    def test_rate_per_unit_positive(self):
        assert (self.df["rate_per_unit"] > 0).all()

    def test_period_start_before_end(self):
        assert (self.df["period_start"] < self.df["period_end"]).all()

    def test_period_end_equals_bill_date(self):
        assert (self.df["period_end"] == self.df["bill_date"]).all()

    def test_consumption_positive(self):
        assert (self.df["consumption_units"] > 0).all()

    def test_sorted_by_bill_date(self):
        assert self.df["bill_date"].is_monotonic_increasing

    def test_rate_calculation(self):
        # rate_per_unit should equal total_charges / consumption_units
        expected = (self.df["total_charges"] / self.df["consumption_units"]).round(2)
        assert (self.df["rate_per_unit"] == expected).all()
