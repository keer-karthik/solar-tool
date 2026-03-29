import streamlit as st
import pandas as pd
import io
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from modules.db_loader import load_bills, derive_bill_periods
from modules.theme import apply_theme, COLORS

st.set_page_config(page_title="Upload Bills", layout="wide")
apply_theme()

REQUIRED_COLS = {"bill_date", "consumption_units", "total_charges"}

TEMPLATE_CSV = """bill_date,consumption_units,total_charges
2022-01-15,285,1852.50
2022-03-18,310,2015.00
2022-05-20,395,2568.75
2022-07-22,420,2730.00
2022-09-25,390,2535.00
2022-11-28,310,2015.00
"""

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.header("Upload Your Electricity Bills")
st.markdown(
    "Replace the default household data with your own TANGEDCO bills. "
    "All analysis across the dashboard will update automatically."
)

# ---------------------------------------------------------------------------
# Current data status
# ---------------------------------------------------------------------------
if "user_bills" in st.session_state:
    meta = st.session_state.get("user_bills_meta", {})
    n = len(st.session_state["user_bills"])
    st.success(
        f"Using **your uploaded data** — {n} bills "
        f"({meta.get('date_range', '')}). "
        "Navigate to any page to see your results."
    )
    if st.button("Revert to default data"):
        for k in ["user_bills", "user_bills_key", "user_bills_meta"]:
            st.session_state.pop(k, None)
        st.rerun()
else:
    st.info("Currently using the **default dataset** (Chennai household, Mar 2022 – Jan 2026).")

st.divider()

# ---------------------------------------------------------------------------
# Template download
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("Step 1 — Download the template")
    st.markdown(
        "Your CSV needs three columns:\n\n"
        "| Column | Description |\n"
        "|---|---|\n"
        "| `bill_date` | Date on the bill (`YYYY-MM-DD`) |\n"
        "| `consumption_units` | Units consumed (kWh) |\n"
        "| `total_charges` | Total bill amount (INR) |\n\n"
        "One row per bill. Bills can be monthly or bimonthly. "
        "Minimum **4 bills** required for prediction to work well."
    )
    st.download_button(
        label="Download CSV template",
        data=TEMPLATE_CSV,
        file_name="bills_template.csv",
        mime="text/csv",
    )

# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
with col_right:
    st.subheader("Step 2 — Upload your CSV")
    uploaded = st.file_uploader("Choose a CSV file", type=["csv"], label_visibility="collapsed")

    if uploaded:
        try:
            df_raw = pd.read_csv(uploaded)
            df_raw.columns = [c.strip().lower().replace(" ", "_") for c in df_raw.columns]

            # Validate required columns
            missing = REQUIRED_COLS - set(df_raw.columns)
            if missing:
                st.error(f"Missing columns: {', '.join(sorted(missing))}")
                st.stop()

            # Parse and validate
            df_raw["bill_date"] = pd.to_datetime(df_raw["bill_date"], dayfirst=False)
            df_raw["consumption_units"] = pd.to_numeric(df_raw["consumption_units"], errors="coerce")
            df_raw["total_charges"] = pd.to_numeric(df_raw["total_charges"], errors="coerce")

            bad_rows = df_raw[
                df_raw["consumption_units"].isna() |
                df_raw["total_charges"].isna() |
                (df_raw["consumption_units"] <= 0) |
                (df_raw["total_charges"] <= 0)
            ]
            if not bad_rows.empty:
                st.error(f"{len(bad_rows)} row(s) have missing or non-positive values. Fix them and re-upload.")
                st.dataframe(bad_rows, use_container_width=True)
                st.stop()

            if len(df_raw) < 4:
                st.warning("Fewer than 4 bills — prediction accuracy will be very low.")

            # Derive period columns
            bills_df = derive_bill_periods(df_raw[["bill_date", "consumption_units", "total_charges"]])

            # Preview
            st.success(f"Parsed **{len(bills_df)} bills** successfully.")
            date_range = (
                f"{bills_df['bill_date'].min().strftime('%b %Y')} – "
                f"{bills_df['bill_date'].max().strftime('%b %Y')}"
            )

            preview = bills_df[["bill_date", "consumption_units", "total_charges",
                                 "period_days", "rate_per_unit"]].copy()
            preview["bill_date"] = preview["bill_date"].dt.strftime("%Y-%m-%d")
            preview.columns = ["Bill Date", "Units (kWh)", "Charges (INR)",
                                "Period (days)", "Rate (INR/kWh)"]
            st.dataframe(preview.set_index("Bill Date"), use_container_width=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("Total bills", len(bills_df))
            c2.metric("Date range", date_range)
            c3.metric("Avg rate", f"₹{bills_df['rate_per_unit'].mean():.2f}/kWh")

            # Confirm
            if st.button("Use this data across the dashboard", type="primary"):
                st.session_state["user_bills"] = bills_df
                st.session_state["user_bills_key"] = f"uploaded_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                st.session_state["user_bills_meta"] = {"date_range": date_range, "n": len(bills_df)}
                st.rerun()

        except Exception as e:
            st.error(f"Could not parse file: {e}")
