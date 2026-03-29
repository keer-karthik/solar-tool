import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from modules.db_loader import load_bills
from modules.weather import get_weather_data
from modules.disaggregate import disaggregate_to_monthly
from modules.prediction import build_features, train_model, predict_future
from modules.theme import apply_theme, COLORS, PLOTLY_COLORS

st.set_page_config(page_title="Consumption Prediction", layout="wide")
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

# --- Sidebar ---
cdd_base = st.sidebar.slider("CDD Base Temp (\u00b0C)", 20.0, 28.0, 24.0, 0.5)
base_load = st.sidebar.slider("Base Load (kWh/day)", 4.0, 15.0, 8.0, 0.5)
horizon = st.sidebar.slider("Forecast Months", 6, 24, 12)


bills_df = st.session_state.get("user_bills") or load_bills()
_bills_key = st.session_state.get("user_bills_key", "default")


@st.cache_data(ttl=3600)
def load_and_model(_bills, bills_key, cdd_base, base_load):
    weather = get_weather_data(cdd_base=cdd_base)
    monthly = disaggregate_to_monthly(_bills, weather, base_load=base_load)
    feat = build_features(monthly, weather)
    model, fitted, metrics = train_model(feat)
    return weather, model, fitted, metrics


weather_df, model, fitted_df, metrics = load_and_model(bills_df, _bills_key, cdd_base, base_load)

# --- KPIs ---
st.header("Consumption Prediction")
c1, c2 = st.columns(2)
c1.metric("Model R\u00b2", f"{metrics['r2']:.3f}")
c2.metric("Mean Abs Error", f"{metrics['mae']:.0f} kWh/month")

# --- Actual vs Predicted ---
fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=fitted_df["year_month"], y=fitted_df["units"], name="Actual",
    marker_color=COLORS["light_gold"],
))
fig1.add_trace(go.Scatter(
    x=fitted_df["year_month"], y=fitted_df["predicted_units"],
    name="Predicted", mode="lines+markers",
    line=dict(color=COLORS["harvest_gold"], width=2),
    marker=dict(color=COLORS["black"], size=5),
))
fig1.update_layout(**CHART_LAYOUT, title="Actual vs Predicted Monthly Consumption",
                   xaxis_title="", yaxis_title="kWh", xaxis_tickangle=-45)
st.plotly_chart(fig1, width="stretch", theme=None)

# --- Forecast ---
last_idx = fitted_df["trend"].iloc[-1]
forecast_df = predict_future(model, weather_df, last_idx, months_ahead=horizon)

hist = fitted_df[["year_month", "units"]].rename(columns={"units": "kWh"})
hist["type"] = "Historical"
fut = forecast_df[["year_month", "predicted_units"]].rename(columns={"predicted_units": "kWh"})
fut["type"] = "Forecast"
combined = pd.concat([hist, fut], ignore_index=True)

fig2 = px.bar(combined, x="year_month", y="kWh", color="type",
              title=f"{horizon}-Month Consumption Forecast",
              labels={"year_month": ""},
              color_discrete_map={"Historical": COLORS["olive"], "Forecast": COLORS["harvest_gold"]})
fig2.update_layout(**CHART_LAYOUT, xaxis_tickangle=-45)
st.plotly_chart(fig2, width="stretch", theme=None)

# --- CDD Scatter ---
fig3 = px.scatter(fitted_df, x="monthly_cdd", y="units", color="year",
                  trendline="ols", title="Consumption vs Cooling Degree Days",
                  labels={"monthly_cdd": "Monthly CDD", "units": "kWh"},
                  color_discrete_sequence=PLOTLY_COLORS)
fig3.update_layout(**CHART_LAYOUT)
st.plotly_chart(fig3, width="stretch", theme=None)

# --- Forecast table ---
rate = (fitted_df["charges"].sum() / fitted_df["units"].sum()) if fitted_df["units"].sum() > 0 else 6.58

forecast_table = forecast_df[["year_month", "predicted_units"]].copy()
forecast_table["est_cost_inr"] = (forecast_table["predicted_units"] * rate).round(0).astype(int)
forecast_table.columns = ["Month", "Predicted kWh", "Est. Cost (INR)"]
st.subheader("Forecast Details")
st.dataframe(forecast_table.set_index("Month"), width="stretch")

annual_forecast = forecast_table["Predicted kWh"].sum()
annual_cost = forecast_table["Est. Cost (INR)"].sum()
st.info(f"Projected next {horizon} months: **{annual_forecast:,} kWh** | **\u20B9{annual_cost:,}**")

# --- Model details ---
with st.expander("Model Details"):
    st.json(metrics)
