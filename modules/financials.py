def npv(discount_rate, cashflows):
    """
    Net Present Value.
    cashflows[0] = year-0 investment (typically negative).
    cashflows[1:] = annual net cash flows.
    """
    return sum(cf / (1 + discount_rate) ** t for t, cf in enumerate(cashflows))


def irr(cashflows, guess=0.10, max_iter=500, tol=1e-7):
    """
    Internal Rate of Return via Newton-Raphson iteration.
    Returns None if the investment is never paid back or no solution converges.
    """
    if not cashflows or cashflows[0] >= 0:
        return None

    rate = guess
    for _ in range(max_iter):
        f = sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))
        df_dr = sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cashflows))
        if abs(df_dr) < 1e-14:
            break
        step = f / df_dr
        rate -= step
        if rate <= -1:
            rate = -0.9
        if abs(step) < tol:
            return round(rate, 6)
    return None


def payback_period(cashflows):
    """
    Simple (undiscounted) payback period in years.
    cashflows[0] = investment (negative). Returns None if never recovered.
    Uses linear interpolation within the recovery year.
    """
    cumulative = 0.0
    for t, cf in enumerate(cashflows):
        prev = cumulative
        cumulative += cf
        if cumulative >= 0 and t > 0:
            fraction = (-prev / cf) if cf != 0 else 0
            return round((t - 1) + fraction, 2)
    return None


def lcoe(system_cost_inr, annual_gen_kwh, lifespan_years, discount_rate,
         degradation_rate=0.007, om_pct=0.01):
    """
    Levelized Cost of Energy in INR/kWh.

    Numerator:   upfront system cost + discounted O&M over project life
    Denominator: discounted energy generation over project life (degraded annually)
    om_pct:      O&M as a fraction of system cost per year (default 1%)
    """
    om_annual = om_pct * system_cost_inr
    discounted_costs = system_cost_inr + sum(
        om_annual / (1 + discount_rate) ** t for t in range(1, lifespan_years + 1)
    )
    discounted_gen = sum(
        annual_gen_kwh * (1 - degradation_rate) ** (t - 1) / (1 + discount_rate) ** t
        for t in range(1, lifespan_years + 1)
    )
    return round(discounted_costs / discounted_gen, 2) if discounted_gen > 0 else 0.0


def project_cashflows(
    system_cost_inr,
    battery_cost_inr,
    annual_savings_inr,
    lifespan_years,
    degradation_rate=0.007,
    om_pct=0.01,
):
    """
    Build annual cashflow array for NPV/IRR analysis.

    Year 0: -(system_cost + battery_cost)
    Year t: annual_savings × (1 - degradation)^(t-1) - O&M
    """
    om_annual = om_pct * system_cost_inr
    cfs = [-(system_cost_inr + battery_cost_inr)]
    for t in range(1, lifespan_years + 1):
        cf = annual_savings_inr * (1 - degradation_rate) ** (t - 1) - om_annual
        cfs.append(cf)
    return cfs
