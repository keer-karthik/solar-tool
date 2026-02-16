import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from modules.db_loader import load_bills
from modules.weather import get_weather_data
from modules.disaggregate import disaggregate_to_monthly
from modules.theme import apply_theme, COLORS, PLOTLY_COLORS

st.set_page_config(page_title="Historical Dashboard", layout="wide")
apply_theme()

CHART_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Lato, sans-serif", color=COLORS["black"]),
    title_font=dict(family="Instrument Serif, serif", size=22, color=COLORS["black"]),
    xaxis=dict(gridcolor="rgba(0,0,0,0.05)"),
    yaxis=dict(gridcolor="rgba(0,0,0,0.08)"),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    margin=dict(t=50, b=40, l=40, r=20),
)

MONTH_NAMES = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
               7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}


@st.cache_data(ttl=3600)
def load_all():
    bills = load_bills()
    weather = get_weather_data()
    monthly = disaggregate_to_monthly(bills, weather)
    return bills, monthly


bills_df, monthly_df = load_all()

# --- Sidebar ---
years = sorted(monthly_df["year"].unique())
selected = st.sidebar.multiselect("Years", years, default=years)
show_raw = st.sidebar.checkbox("Show raw bimonthly data")

filtered = monthly_df[monthly_df["year"].isin(selected)]

# --- KPIs ---
st.header("Historical Consumption")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Consumption", f"{filtered['units'].sum():,} kWh")
c2.metric("Avg Monthly", f"{filtered['units'].mean():,.0f} kWh")
c3.metric("Latest Rate", f"\u20B9{bills_df['rate_per_unit'].iloc[-1]:.2f}/kWh")
c4.metric("Total Spend", f"\u20B9{filtered['charges'].sum():,}")

# --- Monthly consumption chart ---
view = st.radio("View", ["Timeline", "Year-over-Year"], horizontal=True)

if view == "Timeline":
    fig = px.bar(filtered, x="year_month", y="units",
                 labels={"units": "kWh", "year_month": ""},
                 title="Monthly Electricity Consumption")
    fig.update_traces(marker_color=COLORS["harvest_gold"])
    fig.update_layout(**CHART_LAYOUT, xaxis_tickangle=-45)
else:
    tmp = filtered.copy()
    tmp["month_name"] = tmp["month"].map(MONTH_NAMES)
    tmp["year"] = tmp["year"].astype(str)
    fig = px.bar(tmp, x="month_name", y="units", color="year", barmode="group",
                 title="Year-over-Year Comparison",
                 labels={"units": "kWh", "month_name": ""},
                 color_discrete_sequence=PLOTLY_COLORS,
                 category_orders={"month_name": list(MONTH_NAMES.values())})
    fig.update_layout(**CHART_LAYOUT)

st.plotly_chart(fig, use_container_width=True)

# --- Monthly charges chart ---
if view == "Timeline":
    fig2 = px.bar(filtered, x="year_month", y="charges",
                  labels={"charges": "INR", "year_month": ""},
                  title="Monthly Electricity Bill")
    fig2.update_traces(marker_color=COLORS["olive"])
    fig2.update_layout(**CHART_LAYOUT, xaxis_tickangle=-45)
else:
    tmp2 = filtered.copy()
    tmp2["month_name"] = tmp2["month"].map(MONTH_NAMES)
    tmp2["year"] = tmp2["year"].astype(str)
    fig2 = px.bar(tmp2, x="month_name", y="charges", color="year", barmode="group",
                  title="Year-over-Year Bill Comparison",
                  labels={"charges": "INR", "month_name": ""},
                  color_discrete_sequence=PLOTLY_COLORS,
                  category_orders={"month_name": list(MONTH_NAMES.values())})
    fig2.update_layout(**CHART_LAYOUT)

st.plotly_chart(fig2, use_container_width=True)

# --- Rate trend ---
fig3 = go.Figure()
fig3.add_trace(go.Scatter(
    x=bills_df["bill_date"], y=bills_df["rate_per_unit"],
    mode="lines+markers",
    line=dict(color=COLORS["harvest_gold"], width=2),
    marker=dict(color=COLORS["black"], size=6),
    hovertemplate="%{x|%b %Y}: %{y:.2f} INR/kWh<extra></extra>",
))
fig3.update_layout(**CHART_LAYOUT, title="Electricity Rate Trend",
                   xaxis_title="", yaxis_title="INR/kWh", showlegend=False)
st.plotly_chart(fig3, use_container_width=True)

# --- Annual summary ---
annual = filtered.groupby("year").agg(
    total_kwh=("units", "sum"), total_inr=("charges", "sum"),
    avg_monthly=("units", "mean"), peak_month=("units", "max"), low_month=("units", "min"),
).round(0).astype(int)
st.subheader("Annual Summary")
st.dataframe(annual, use_container_width=True)

# --- Raw data ---
if show_raw:
    st.subheader("Raw Bimonthly Bills")
    st.dataframe(bills_df[["bill_date", "consumption_units", "total_charges",
                           "rate_per_unit", "period_days"]].set_index("bill_date"),
                 use_container_width=True)
