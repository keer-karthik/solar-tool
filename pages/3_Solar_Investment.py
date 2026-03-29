import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from modules.db_loader import load_bills
from modules.weather import get_weather_data
from modules.disaggregate import disaggregate_to_monthly
from modules.solar import get_solar_data, monthly_generation
from modules.savings import simulate_savings, annual_savings
from modules.financials import npv, irr, payback_period, lcoe, project_cashflows
from modules.theme import apply_theme, COLORS, PLOTLY_COLORS

st.set_page_config(page_title="Solar Investment", layout="wide")
apply_theme()

CHART_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Lato, sans-serif", color=COLORS["black"]),
    title_font=dict(family="Instrument Serif, serif", size=22, color=COLORS["black"]),
    xaxis=dict(gridcolor="rgba(0,0,0,0.05)", tickfont=dict(color=COLORS["black"])),
    yaxis=dict(gridcolor="rgba(0,0,0,0.08)", tickfont=dict(color=COLORS["black"])),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["black"])),
    margin=dict(t=50, b=40, l=40, r=20),
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.header("System Configuration")
system_kw = st.sidebar.slider("System Size (kWp)", 1.0, 10.0, 5.0, 0.5,
    help="TANGEDCO net metering capped at 10 kWp for residential LT-1A consumers.")
cost_per_kw = st.sidebar.slider("Gross Cost per kWp (INR)", 40_000, 1_00_000, 65_000, 1_000,
    help="All-in installed cost before subsidies. Typical Chennai range: ₹60k–₹75k/kWp for 3–5 kW systems (2024–25).")
battery_kwh = st.sidebar.slider("Battery Capacity (kWh)", 0.0, 20.0, 0.0, 1.0,
    help="Batteries are NOT covered by PM Surya Ghar or CM Solar Scheme subsidies.")
battery_cost_kwh = st.sidebar.slider("Battery Cost (INR/kWh)", 10_000, 40_000, 22_000, 1_000,
    help="Typical residential LFP installed cost in India: ₹20k–₹26k/kWh (2024–25).")
performance_ratio = st.sidebar.slider("Performance Ratio", 0.65, 0.90, 0.75, 0.01,
    help="Chennai-specific recommendation: 0.75–0.78. Hot climate + coastal dust reduce output vs. STC. "
         "Source: Frontiers coastal India PV study (2022).")
export_rate = st.sidebar.slider("Export Credit (INR/kWh)", 0.0, 12.0, 3.61, 0.01,
    help="Under TNERC net billing (Order No. 8 of 2021): ₹3.61/kWh for systems ≤10 kW. "
         "Under pure net metering (1:1 energy offset), set this to your marginal tariff rate (~₹8–₹11.55/kWh).")

st.sidebar.header("Government Subsidies")
apply_central = st.sidebar.checkbox("PM Surya Ghar Muft Bijli Yojana", value=True,
    help="Central govt subsidy: ₹30k (1kW) / ₹60k (2kW) / ₹78k (3kW+). "
         "Only grid-connected systems from MNRE-approved vendors. Batteries excluded. "
         "Valid until 31 March 2026. Source: pmsuryaghar.gov.in")
apply_state = st.sidebar.checkbox("TN CM Solar Rooftop Scheme", value=True,
    help="Tamil Nadu state subsidy: ₹20,000/kW for domestic TANGEDCO consumers. "
         "Applied through TEDA. Includes 5-year free O&M. Source: myscheme.gov.in / TEDA")

st.sidebar.header("Financial Parameters")
discount_rate_pct = st.sidebar.slider("Discount Rate (%)", 5.0, 15.0, 8.0, 0.5)
lifespan = st.sidebar.slider("Project Lifespan (years)", 10, 30, 25)
degradation_rate_pct = st.sidebar.slider("Annual Degradation (%)", 0.3, 1.0, 0.5, 0.1,
    help="MNRE standard: 0.5%/year for monocrystalline PERC. "
         "Source: Frontiers coastal India PV study (2022).")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
bills_df = st.session_state.get("user_bills") or load_bills()
_bills_key = st.session_state.get("user_bills_key", "default")


@st.cache_data(ttl=3600)
def load_all(_bills, bills_key):
    weather = get_weather_data()
    monthly = disaggregate_to_monthly(_bills, weather)
    solar = get_solar_data()
    return monthly, solar


monthly_df, solar_df = load_all(bills_df, _bills_key)

savings_df = simulate_savings(
    monthly_df, solar_df, system_kw, battery_kwh, performance_ratio, export_rate
)

# ---------------------------------------------------------------------------
# Cost & subsidy calculation
# ---------------------------------------------------------------------------
gross_system_cost = system_kw * cost_per_kw
battery_cost = battery_kwh * battery_cost_kwh
gross_total = gross_system_cost + battery_cost

# Central PM Surya Ghar (batteries explicitly excluded)
if apply_central:
    if system_kw <= 1:
        central_subsidy = 30_000
    elif system_kw <= 2:
        central_subsidy = 60_000
    else:
        central_subsidy = 78_000
else:
    central_subsidy = 0

# Tamil Nadu CM Solar Rooftop Scheme: ₹20,000/kW
state_subsidy = (min(system_kw, 10.0) * 20_000) if apply_state else 0

total_subsidy = central_subsidy + state_subsidy
net_system_cost = max(0, gross_system_cost - total_subsidy)
net_total_cost = net_system_cost + battery_cost

# ---------------------------------------------------------------------------
# Financial model (uses NET cost after subsidies)
# ---------------------------------------------------------------------------
discount_rate = discount_rate_pct / 100
degradation_rate = degradation_rate_pct / 100

annual = annual_savings(savings_df)
avg_annual_savings_inr = annual["savings_inr"].mean()
avg_annual_gen_kwh = annual["solar_gen_kwh"].mean()

cashflows = project_cashflows(
    net_system_cost, battery_cost, avg_annual_savings_inr, lifespan,
    degradation_rate=degradation_rate
)
project_npv = npv(discount_rate, cashflows)
project_irr = irr(cashflows)
project_payback = payback_period(cashflows)
project_lcoe = lcoe(net_system_cost, avg_annual_gen_kwh, lifespan, discount_rate,
                    degradation_rate=degradation_rate)

# ---------------------------------------------------------------------------
# Header & KPIs
# ---------------------------------------------------------------------------
st.header("Solar Investment Analysis")
st.caption("Chennai (TANGEDCO LT-1A) · Irradiance: Open-Meteo Archive API · "
           "Policy: TNERC Order No. 8 of 2021 · Costs: 2024–25 market rates")

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Gross Cost", f"₹{gross_total:,.0f}")
c2.metric("Subsidies", f"₹{total_subsidy:,.0f}",
          delta=f"−₹{total_subsidy:,.0f}", delta_color="normal")
c3.metric("Net Cost", f"₹{net_total_cost:,.0f}")
c4.metric("NPV", f"₹{project_npv:,.0f}")
c5.metric("IRR", f"{project_irr * 100:.1f}%" if project_irr is not None else "N/A")
c6.metric("Payback", f"{project_payback:.1f} yrs" if project_payback is not None else "N/A")

c7, c8 = st.columns(2)
c7.metric("LCOE", f"₹{project_lcoe}/kWh",
          help="Levelized Cost of Energy: net cost ÷ lifetime discounted generation")
c8.metric("Avg Annual Savings", f"₹{avg_annual_savings_inr:,.0f}")

st.divider()

# ---------------------------------------------------------------------------
# Chart 1: Monthly solar generation vs consumption
# ---------------------------------------------------------------------------
mon_gen = monthly_generation(solar_df, system_kw, performance_ratio)
merged = savings_df.merge(mon_gen[["year_month", "gen_kwh"]], on="year_month", how="left")

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=merged["year_month"], y=merged["consumption_kwh"], name="Consumption",
    marker_color=COLORS["olive"],
))
fig1.add_trace(go.Bar(
    x=merged["year_month"], y=merged["gen_kwh"], name="Solar Generation",
    marker_color=COLORS["harvest_gold"],
))
fig1.update_layout(
    **CHART_LAYOUT,
    title="Monthly Solar Generation vs Consumption",
    barmode="group", xaxis_title="", yaxis_title="kWh", xaxis_tickangle=-45,
)
st.plotly_chart(fig1, use_container_width=True, theme=None)

# ---------------------------------------------------------------------------
# Chart 2: Grid consumption before vs after solar
# ---------------------------------------------------------------------------
fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=savings_df["year_month"], y=savings_df["consumption_kwh"],
    name="Grid without Solar", marker_color=COLORS["black"], opacity=0.7,
))
fig2.add_trace(go.Bar(
    x=savings_df["year_month"], y=savings_df["grid_kwh"],
    name="Grid with Solar", marker_color=COLORS["harvest_gold"],
))
fig2.update_layout(
    **CHART_LAYOUT,
    title="Grid Consumption: Before vs After Solar",
    barmode="overlay", xaxis_title="", yaxis_title="kWh", xaxis_tickangle=-45,
)
st.plotly_chart(fig2, use_container_width=True, theme=None)

# ---------------------------------------------------------------------------
# Chart 3: Cumulative cash flow
# ---------------------------------------------------------------------------
cum_cf = []
running = 0.0
for cf in cashflows:
    running += cf
    cum_cf.append(running)

years_axis = list(range(len(cashflows)))
dot_colors = [COLORS["harvest_gold"] if v >= 0 else COLORS["black"] for v in cum_cf]

fig3 = go.Figure()
fig3.add_trace(go.Scatter(
    x=years_axis, y=cum_cf, mode="lines+markers",
    line=dict(color=COLORS["harvest_gold"], width=2),
    marker=dict(color=dot_colors, size=6),
    hovertemplate="Year %{x}: ₹%{y:,.0f}<extra></extra>",
))
fig3.add_hline(y=0, line_dash="dash", line_color=COLORS["olive"], line_width=1.5)
fig3.update_layout(
    **CHART_LAYOUT,
    title=f"Cumulative Cash Flow over {lifespan}-Year Project Life (after subsidies)",
    xaxis_title="Year", yaxis_title="INR",
)
st.plotly_chart(fig3, use_container_width=True, theme=None)

# ---------------------------------------------------------------------------
# Annual performance table
# ---------------------------------------------------------------------------
st.subheader("Annual Historical Performance")
ann_display = annual.rename(columns={
    "year": "Year",
    "consumption_kwh": "Consumption (kWh)",
    "solar_gen_kwh": "Solar Gen (kWh)",
    "solar_used_kwh": "Solar Used (kWh)",
    "grid_kwh": "Grid (kWh)",
    "exported_kwh": "Exported (kWh)",
    "savings_inr": "Savings (INR)",
    "bill_without_solar_inr": "Bill Before (INR)",
    "bill_with_solar_inr": "Bill After (INR)",
    "self_consumption_pct": "Self-Use (%)",
    "solar_fraction_pct": "Solar Fraction (%)",
})
st.dataframe(ann_display.set_index("Year"), use_container_width=True)

# ---------------------------------------------------------------------------
# Year-by-year financial projection
# ---------------------------------------------------------------------------
st.subheader(f"{lifespan}-Year Financial Projection")
proj_rows = []
running = 0.0
for t, cf in enumerate(cashflows):
    running += cf
    proj_rows.append({
        "Year": t,
        "Cash Flow (INR)": f"₹{cf:,.0f}",
        "Cumulative (INR)": f"₹{running:,.0f}",
        "Discounted CF (INR)": f"₹{cf / (1 + discount_rate) ** t:,.0f}",
    })
st.dataframe(pd.DataFrame(proj_rows).set_index("Year"), use_container_width=True)

st.info(
    f"Avg annual generation: **{avg_annual_gen_kwh:,.0f} kWh** · "
    f"Avg annual savings: **₹{avg_annual_savings_inr:,.0f}** · "
    f"{lifespan}-year NPV: **₹{project_npv:,.0f}**"
)

# ---------------------------------------------------------------------------
# Policy & Assumptions (sources)
# ---------------------------------------------------------------------------
with st.expander("Policy, Assumptions & Sources"):
    st.markdown("""
    #### TANGEDCO Net Metering
    - Governed by **TNERC Order No. 8 of 2021** (22 Oct 2021)
    - Eligible: LT-1A domestic consumers up to **10 kWp**
    - Export model: energy banking — surplus units carry forward, settled annually; credit capped at **90% of annual import**
    - Net billing alternative: **₹3.61/kWh** feed-in tariff for systems ≤10 kW (revision to ₹3.99/kWh under consultation)
    - Apply via TNEB USRP portal: [tnebltd.gov.in/usrp](https://www.tnebltd.gov.in/usrp/)
    - Sources: [Mercom India](https://www.mercomindia.com/tamil-nadu-sets-generic-tariff-%E2%82%B93-61-kwh-for-rooftop-solar-10-kw) · [Saurenergy](https://www.saurenergy.com/solar-energy-news/tamil-nadu-guidelines-net-metering-rooftop-solar) · [TNERC Draft GISS Regs 2024](https://energy.prayaspune.org/images/pdf/Draft_TNERC_GISS_regs_2024.pdf)

    #### Government Subsidies
    - **PM Surya Ghar Muft Bijli Yojana** (Central): ₹30k / ₹60k / ₹78k for 1 / 2 / 3+ kWp. Valid until 31 March 2026. MNRE-empanelled vendors only. **Batteries excluded.**
      Source: [pmsuryaghar.gov.in](https://pmsuryaghar.gov.in/) · [SolarSquare guide](https://www.solarsquare.in/blog/solar-panel-subsidy-in-india-under-pm-surya-ghar-muft-bijli-yojana/)
    - **TN CM Solar Rooftop Capital Incentive Scheme** (State): ₹20,000/kW for TANGEDCO domestic consumers. Apply through TEDA. Includes 5-year free O&M.
      Source: [myscheme.gov.in](https://dev.myscheme.gov.in/schemes/cmsrcis) · [IEA policy entry](https://www.iea.org/policies/6133-tamil-nadu-incentive-for-domestic-solar-rooftops)

    #### System Costs (2024–25)
    - Gross installed cost (3–5 kWp, Chennai): **₹60,000–₹75,000/kWp**
    - Battery (LFP, residential, installed): **₹20,000–₹26,000/kWh** — no subsidy available
    - Sources: [elsol.co.in](https://elsol.co.in/solar-panel-installation-price-subsidy-in-tamil-nadu/) · [Sunsure Energy 2025](https://sunsure-energy.com/solar-energy-in-tamil-nadu-an-overview-of-subsidies-and-incentives-in-2025/)

    #### Solar Resource & Performance (Chennai)
    - Annual average GHI: **~5.35 kWh/m²/day** (1,953 kWh/m²/year)
    - Specific yield (AC): **~1,400–1,600 kWh/kWp/year** for typical rooftop
    - Recommended Performance Ratio: **0.75–0.78** — reduced by high ambient temps (35–40°C summer) and coastal dust
    - Panel degradation: **0.5%/year** (MNRE standard for monocrystalline PERC)
    - Sources: [Solar Mango Chennai guide](https://www.solarmango.com/in/region/chennai) · [EAI India rooftop output](https://www.eai.in/ref/ae/sol/rooftop/power_output) · [Frontiers coastal India PV study](https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2022.857948/full)

    #### TANGEDCO LT-1A Tariff (effective 1 July 2025 — TNERC Order SMT.No.6 of 2025)
    | Slab | Consumer Rate |
    |---|---|
    | 0–100 units | ₹0/unit (free) |
    | 101–200 units | ₹2.35/unit |
    | 201–400 units | ₹4.70/unit |
    | 401–500 units | ₹6.30/unit |
    | 501–600 units | ₹8.40/unit |
    | 601–800 units | ₹9.45/unit |
    | 801–1,000 units | ₹10.50/unit |
    | >1,000 units | ₹11.55/unit |

    Billing is **telescopic** (each slab rate applies only to units in that slab). Fixed charge: **₹0/month** for domestic consumers.
    Source: [TNEB Bill Calculator](https://tnebbillcalculator.com/tneb-tariff-details/) · [TNERC Tariff Orders](https://www.tnerc.tn.gov.in/website/TariffOrders.aspx)

    #### Model Assumptions & Limitations
    - Savings are estimated using **historical average rate** (total charges ÷ total units from your bills). For households with high consumption hitting upper slabs, solar savings are higher at the margin — this model may slightly underestimate ROI.
    - Daily consumption is assumed **uniform within each month** (no hourly load profile available).
    - Battery model uses a simplified daily dispatch; actual savings depend on your consumption timing relative to solar generation.
    - Irradiance data sourced live from **Open-Meteo Archive API** (Chennai: 13.08°N, 80.27°E).
    - O&M cost assumed at **1% of system cost/year** (if you take the CM Scheme's 5-year free O&M, set it to 0% for years 1–5).
    """)

with st.expander("System Details"):
    st.json({
        "system_kw": system_kw,
        "gross_system_cost_inr": round(gross_system_cost),
        "central_subsidy_inr": central_subsidy,
        "state_subsidy_inr": round(state_subsidy),
        "net_system_cost_inr": round(net_system_cost),
        "battery_kwh": battery_kwh,
        "battery_cost_inr": round(battery_cost),
        "net_total_cost_inr": round(net_total_cost),
        "performance_ratio": performance_ratio,
        "export_credit_inr_per_kwh": export_rate,
        "degradation_rate_pct": degradation_rate_pct,
        "avg_annual_gen_kwh": round(avg_annual_gen_kwh),
        "avg_annual_savings_inr": round(avg_annual_savings_inr),
        "npv_inr": round(project_npv),
        "irr_pct": round(project_irr * 100, 2) if project_irr is not None else None,
        "payback_years": project_payback,
        "lcoe_inr_per_kwh": project_lcoe,
        "discount_rate_pct": discount_rate_pct,
        "lifespan_years": lifespan,
    })
