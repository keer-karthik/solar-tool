import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.financials import npv, irr, payback_period, lcoe, project_cashflows


def test_npv_zero_rate():
    # At 0% discount rate, NPV is just the sum of cashflows
    cfs = [-1000, 300, 300, 300, 300]
    assert abs(npv(0.0, cfs) - 200) < 0.01


def test_npv_positive_rate():
    # -1000 upfront, 400/year for 3 years at 10%
    # NPV = -1000 + 400/1.1 + 400/1.21 + 400/1.331 ≈ -5.26
    cfs = [-1000, 400, 400, 400]
    result = npv(0.10, cfs)
    assert abs(result - (-5.26)) < 0.01


def test_npv_negative_investment_only():
    cfs = [-500]
    assert npv(0.08, cfs) == -500


def test_irr_known_value():
    # -1000 now, +1100 in one year → IRR = 10%
    cfs = [-1000, 1100]
    result = irr(cfs)
    assert result is not None
    assert abs(result - 0.10) < 1e-4


def test_irr_typical_solar():
    # Typical solar: -325000 cost, ~50000/yr for 25 years → IRR ~15%
    cfs = [-325_000] + [50_000] * 25
    result = irr(cfs)
    assert result is not None
    assert 0.10 < result < 0.20


def test_irr_no_return():
    # All negative cashflows → no IRR
    assert irr([-1000, -100, -100]) is None


def test_irr_positive_initial():
    # Positive initial cashflow → undefined IRR
    assert irr([1000, -100]) is None


def test_payback_exact():
    # -1000, +500/yr → payback at exactly year 2
    cfs = [-1000, 500, 500, 500]
    assert payback_period(cfs) == 2.0


def test_payback_fractional():
    # -1000, +600, +600 → payback at 1 + (400/600) = 1.67 years
    cfs = [-1000, 600, 600]
    result = payback_period(cfs)
    assert abs(result - 1.67) < 0.01


def test_payback_never():
    cfs = [-1000, 10, 10]
    assert payback_period(cfs) is None


def test_lcoe_reasonable_range():
    # 5 kW system at 65k/kW = 325k, 7000 kWh/yr, 25 years, 8% discount
    result = lcoe(325_000, 7000, 25, 0.08)
    # Should be between 3 and 10 INR/kWh for a reasonable Chennai system
    assert 3.0 < result < 10.0


def test_project_cashflows_length():
    cfs = project_cashflows(325_000, 0, 50_000, 25)
    assert len(cfs) == 26  # year 0 + 25 years


def test_project_cashflows_year0():
    cfs = project_cashflows(300_000, 50_000, 40_000, 20)
    assert cfs[0] == -350_000


def test_project_cashflows_degradation():
    cfs = project_cashflows(100_000, 0, 20_000, 5, degradation_rate=0.01, om_pct=0.0)
    # Year 1: 20000, Year 2: 20000*(1-0.01)^1, ...
    assert abs(cfs[1] - 20_000) < 0.01
    assert abs(cfs[2] - 20_000 * 0.99) < 0.01
    assert cfs[2] < cfs[1]
