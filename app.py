import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from modules.theme import apply_theme, COLORS

st.set_page_config(page_title="Chennai Electricity Dashboard", page_icon="⚡", layout="wide")
apply_theme()

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.title("Chennai Household Electricity Dashboard")
st.markdown(
    "#### Understand your energy past · predict your future · size your solar investment"
)

# Data status banner
if "user_bills" in st.session_state:
    meta = st.session_state.get("user_bills_meta", {})
    st.success(
        f"Using your uploaded data — {meta.get('n', '?')} bills "
        f"({meta.get('date_range', '')}). Navigate to any page in the sidebar."
    )
else:
    st.info(
        "Showing the default dataset (Chennai household, Mar 2022 – Jan 2026). "
        "**Upload your own TANGEDCO bills** on the Upload Bills page to personalise the analysis."
    )

st.divider()

# ---------------------------------------------------------------------------
# Feature cards
# ---------------------------------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("### 📊 Historical Dashboard")
    st.markdown(
        "Visualise your actual electricity consumption and billing history. "
        "See month-by-month trends, year-over-year comparisons, and how your "
        "effective rate per unit has changed over time."
    )
    st.markdown(
        "**What you get:**\n"
        "- Monthly kWh and INR charts\n"
        "- Year-over-year comparison view\n"
        "- Rate trend over time\n"
        "- Annual summary table"
    )

with c2:
    st.markdown("### 🔮 Consumption Prediction")
    st.markdown(
        "A Ridge regression model trained on your billing history and Chennai "
        "weather data (Cooling Degree Days) forecasts your consumption up to "
        "24 months ahead."
    )
    st.markdown(
        "**What you get:**\n"
        "- Actual vs. predicted overlay\n"
        "- Adjustable CDD base temperature\n"
        "- Consumption vs. heat scatter plot\n"
        "- Forecast table with estimated costs"
    )

with c3:
    st.markdown("### ☀️ Solar Investment")
    st.markdown(
        "Model the financial return of a rooftop solar system against your real "
        "consumption data. Includes government subsidies, TANGEDCO net metering "
        "policy, and battery storage simulation."
    )
    st.markdown(
        "**What you get:**\n"
        "- NPV, IRR, payback period, LCOE\n"
        "- PM Surya Ghar + TN CM scheme subsidies\n"
        "- Daily battery dispatch simulation\n"
        "- 25-year cash flow projection"
    )

st.divider()

# ---------------------------------------------------------------------------
# How it works
# ---------------------------------------------------------------------------
st.markdown("### How it works")

s1, s2, s3, s4 = st.columns(4)
s1.markdown("**① Upload your bills**\nGo to *Upload Bills* and upload a CSV with your TANGEDCO bill dates, units consumed, and total charges. Or skip this to explore with the default data.")
s2.markdown("**② Explore history**\nThe *Historical Dashboard* disaggregates your bimonthly bills into monthly estimates using Chennai temperature data from the Open-Meteo archive.")
s3.markdown("**③ See the forecast**\n*Consumption Prediction* trains a regression model on your data and projects forward, accounting for seasonal temperature patterns.")
s4.markdown("**④ Size your solar**\n*Solar Investment* runs your consumption against real Chennai irradiance data to calculate savings and payback with current market costs.")

st.divider()

# ---------------------------------------------------------------------------
# Data sources & methodology
# ---------------------------------------------------------------------------
with st.expander("Data sources & methodology"):
    st.markdown("""
    | Data | Source |
    |---|---|
    | Electricity bills | Your TANGEDCO bills (uploaded CSV) or the bundled default dataset |
    | Daily temperature | [Open-Meteo Archive API](https://open-meteo.com/) — Chennai 13.08°N 80.27°E |
    | Solar irradiance | [Open-Meteo Archive API](https://open-meteo.com/) — `shortwave_radiation_sum` (MJ/m²/day) |
    | TANGEDCO tariff | TNERC Order SMT.No.6 of 2025 (effective 1 July 2025) |
    | Net metering policy | TNERC Order No. 8 of 2021 |
    | Central subsidy | [PM Surya Ghar Muft Bijli Yojana](https://pmsuryaghar.gov.in/) |
    | State subsidy | TN CM Solar Rooftop Capital Incentive Scheme (TEDA) |
    | Solar performance | [Frontiers coastal India PV study (2022)](https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2022.857948/full) |

    **Disaggregation model:** bimonthly bills are split into monthly estimates using a linear Cooling Degree Day model
    (`daily_units = base_load + k × CDD`), normalised to match each bill total exactly.

    **Prediction model:** Ridge regression with features — monthly CDD sum, cyclical month encoding (sin/cos), and a
    linear trend index. Trained on all available historical months.

    **Solar generation:** `gen_kWh = GHI_kWh/m² × system_kWp × performance_ratio`
    (1 kWp rated at 1000 W/m² STC).

    **Battery model:** simplified daily dispatch — solar offsets load directly, excess charges the battery,
    remaining excess is exported, remaining load draws from battery then grid.
    """)
